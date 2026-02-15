import logging
from datetime import datetime
from math import ceil
from typing import Optional
import json
import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_admin_user
from app.models import User, Task, UserTaskAttempt
from app.schemas.admin import AdminStatsResponse
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskAdminResponse,
    AdminPaginatedTaskResponse,
)
from app.services.task_generator import TaskGenerator


# Максимальный размер файла для импорта (10MB)
MAX_IMPORT_FILE_SIZE = 10 * 1024 * 1024

# Логирование для audit trail
logger = logging.getLogger(__name__)


# API роутер для админ панели
# ВАЖНО: dependencies=[Depends(get_admin_user)] применяется ко ВСЕМ эндпоинтам роутера
# Это защищает весь роутер, не нужно добавлять проверку к каждому эндпоинту
router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)]  # Глобальная защита для всех endpoints
)


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Получить статистику платформы",
    description=(
        "Возвращает общую статистику платформы для админ панели. "
        "Включает количество пользователей, задач, попыток решений, "
        "процент правильных решений и количество активных пользователей. "
        "Требует роль администратора."
    ),
)
async def get_platform_stats(
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    """
    Получение статистики платформы для админ панели.

    Требует JWT аутентификации с ролью admin.
    Выполняет несколько агрегирующих запросов к БД для сбора метрик.

    Args:
        current_admin: Текущий администратор (из JWT токена с проверкой роли)
        db: Асинхронная сессия БД

    Returns:
        AdminStatsResponse: Полная статистика платформы

    Raises:
        HTTPException 401: Если пользователь не авторизован
        HTTPException 403: Если у пользователя нет прав администратора
    """

    # Логирование доступа к админ панели для audit trail
    logger.info(
        f"Admin stats access: user_id={current_admin.id}, "
        f"username={current_admin.username}, "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

    # === 1. Общее количество пользователей ===
    total_users_query = select(func.count()).select_from(User)
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0

    # === 2. Общее количество задач ===
    total_tasks_query = select(func.count()).select_from(Task)
    total_tasks_result = await db.execute(total_tasks_query)
    total_tasks = total_tasks_result.scalar() or 0

    # === 3. Общее количество попыток ===
    total_attempts_query = select(func.count()).select_from(UserTaskAttempt)
    total_attempts_result = await db.execute(total_attempts_query)
    total_attempts = total_attempts_result.scalar() or 0

    # === 4. Количество правильных попыток ===
    correct_attempts_query = select(func.count()).select_from(UserTaskAttempt).where(
        UserTaskAttempt.is_correct == True
    )
    correct_attempts_result = await db.execute(correct_attempts_query)
    total_correct_attempts = correct_attempts_result.scalar() or 0

    # === 5. Расчёт точности платформы ===
    platform_accuracy = (
        (total_correct_attempts / total_attempts * 100)
        if total_attempts > 0
        else 0.0
    )

    # === 6. Активные пользователи за сегодня ===
    # Определяем начало сегодняшнего дня (UTC)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    active_users_query = select(
        func.count(func.distinct(UserTaskAttempt.user_id))
    ).where(UserTaskAttempt.created_at >= today_start)
    active_users_result = await db.execute(active_users_query)
    active_users_today = active_users_result.scalar() or 0

    # === 7. Формирование ответа ===
    return AdminStatsResponse(
        total_users=total_users,
        total_tasks=total_tasks,
        total_attempts=total_attempts,
        total_correct_attempts=total_correct_attempts,
        platform_accuracy=round(platform_accuracy, 2),  # Округление до 2 знаков
        active_users_today=active_users_today,
    )


# ===================================
# === CRUD ОПЕРАЦИИ ДЛЯ ЗАДАЧ ===
# ===================================


@router.post(
    "/tasks",
    response_model=TaskAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую задачу",
    description="Создание новой задачи олимпиады. Требует роль администратора.",
)
async def create_task(
    task_data: TaskCreate,
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    """
    Создание новой задачи администратором.

    Все поля обязательны, включая правильный ответ (answer).
    Логирует все попытки создания для audit trail.
    """

    # Логирование ПЕРЕД операцией для audit trail
    logger.info(
        f"Admin task creation: admin_id={current_admin.id}, "
        f"admin_username={current_admin.username}, "
        f"task_subject={task_data.subject}, "
        f"task_topic={task_data.topic}, "
        f"task_difficulty={task_data.difficulty}, "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

    # Создание новой задачи
    new_task = Task(
        subject=task_data.subject,
        topic=task_data.topic,
        difficulty=task_data.difficulty,
        title=task_data.title,
        text=task_data.text,
        answer=task_data.answer,
        hints=task_data.hints,
    )

    try:
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        logger.info(
            f"Task created successfully: task_id={new_task.id}, title={new_task.title}"
        )

        return new_task

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Task creation failed with integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать задачу. Возможно, дублирование данных.",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during task creation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.get(
    "/tasks",
    response_model=AdminPaginatedTaskResponse,
    summary="Получить список задач (Admin)",
    description=(
        "Возвращает список задач с возможностью фильтрации и пагинации. "
        "Для администратора ВКЛЮЧАЕТ поле answer в каждой задаче."
    ),
)
async def get_admin_tasks(
    subject: Optional[str] = Query(None, description="Фильтр по предмету"),
    topic: Optional[str] = Query(None, description="Фильтр по теме"),
    difficulty: Optional[int] = Query(None, ge=1, le=5, description="Фильтр по сложности"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminPaginatedTaskResponse:
    """
    Получение списка задач для администратора с фильтрацией и пагинацией.

    ВАЖНО: Возвращает задачи с полем answer (в отличие от публичного /api/tasks).
    """

    # Логирование доступа
    logger.info(
        f"Admin tasks list access: admin_id={current_admin.id}, "
        f"filters=[subject={subject}, topic={topic}, difficulty={difficulty}], "
        f"page={page}"
    )

    # Базовый запрос
    query = select(Task)

    if subject is not None:
        query = query.where(Task.subject == subject)
    if topic is not None:
        query = query.where(Task.topic == topic)
    if difficulty is not None:
        query = query.where(Task.difficulty == difficulty)

    # Подсчет total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Пагинация
    pages = ceil(total / per_page) if total > 0 else 0
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Task.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()

    return AdminPaginatedTaskResponse(
        items=[TaskAdminResponse.model_validate(task) for task in tasks],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ===================================
# === ИМПОРТ/ЭКСПОРТ ЗАДАЧ ===
# ===================================


@router.post(
    "/tasks/import",
    summary="Импорт задач из CSV/JSON",
    description=(
        "Массовая загрузка задач из CSV или JSON файла. "
        "Требует роль администратора. "
        "Поддерживает форматы: application/json, text/csv"
    ),
)
async def import_tasks(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Импорт задач из CSV или JSON файла.

    JSON формат:
    [
        {
            "subject": "математика",
            "topic": "алгебра",
            "difficulty": 3,
            "title": "Уравнение",
            "text": "Решите уравнение...",
            "answer": "42",
            "hints": ["подсказка 1", "подсказка 2"]
        },
        ...
    ]

    CSV формат (с заголовками):
    subject,topic,difficulty,title,text,answer,hints
    математика,алгебра,3,"Уравнение","Решите...","42","подсказка 1;подсказка 2"

    Hints в CSV разделяются точкой с запятой (;)
    """

    logger.info(
        f"Admin tasks import: admin_id={current_admin.id}, "
        f"filename={file.filename}, "
        f"content_type={file.content_type}"
    )

    content = await file.read()

    # Проверка размера файла
    if len(content) > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_IMPORT_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    content_str = content.decode("utf-8")

    tasks_data = []

    try:
        # Определяем формат по content_type или расширению
        is_json = (
            file.content_type == "application/json"
            or (file.filename and file.filename.endswith(".json"))
        )
        is_csv = (
            file.content_type in ["text/csv", "application/csv"]
            or (file.filename and file.filename.endswith(".csv"))
        )

        if is_json:
            # Парсинг JSON
            data = json.loads(content_str)
            if not isinstance(data, list):
                raise ValueError("JSON должен содержать массив объектов задач")
            tasks_data = data

        elif is_csv:
            # Парсинг CSV
            csv_file = StringIO(content_str)
            reader = csv.DictReader(csv_file)

            for row in reader:
                # Обработка hints (разделённые точкой с запятой)
                hints_str = row.get("hints", "")
                hints = [h.strip() for h in hints_str.split(";") if h.strip()] if hints_str else []

                task_dict = {
                    "subject": row["subject"],
                    "topic": row["topic"],
                    "difficulty": int(row["difficulty"]),
                    "title": row["title"],
                    "text": row["text"],
                    "answer": row["answer"],
                    "hints": hints,
                }
                tasks_data.append(task_dict)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый формат файла. Используйте JSON или CSV.",
            )

        # Валидация и создание задач
        created_count = 0
        errors = []

        for idx, task_data in enumerate(tasks_data):
            try:
                # Валидация через Pydantic схему
                validated_task = TaskCreate(**task_data)

                # Создание задачи
                new_task = Task(
                    subject=validated_task.subject,
                    topic=validated_task.topic,
                    difficulty=validated_task.difficulty,
                    title=validated_task.title,
                    text=validated_task.text,
                    answer=validated_task.answer,
                    hints=validated_task.hints,
                )

                db.add(new_task)
                created_count += 1

            except Exception as e:
                errors.append(f"Строка {idx + 1}: {str(e)}")
                logger.warning(f"Failed to import task at index {idx}: {e}")

        # Проверить наличие ошибок ПЕРЕД коммитом
        if errors:
            await db.rollback()
            logger.error(
                f"Tasks import failed: {len(errors)} validation errors out of {len(tasks_data)}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Импорт провален: {len(errors)} ошибок валидации. Первая ошибка: {errors[0]}"
            )

        # Коммит только если НЕТ ошибок
        await db.commit()

        logger.info(
            f"Tasks import completed successfully: created={created_count}, total={len(tasks_data)}"
        )

        return {
            "ok": True,
            "created": created_count,
            "total": len(tasks_data),
            "errors": None,
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка парсинга JSON: {str(e)}",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка импорта: {str(e)}",
        )


@router.get(
    "/tasks/export",
    summary="Экспорт задач в CSV/JSON",
    description=(
        "Скачать все задачи в формате CSV или JSON. "
        "Требует роль администратора. "
        "Параметр format: json (по умолчанию) или csv"
    ),
)
async def export_tasks(
    request: Request,
    format: str = Query("json", pattern="^(json|csv)$", description="Формат экспорта: json или csv"),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Экспорт всех задач в JSON или CSV формате.

    Включает все поля задачи, включая answer (для админов).
    """

    logger.info(
        f"Admin tasks export: admin_id={current_admin.id}, format={format}"
    )

    # Получить origin из request для CORS (fallback на localhost для локальной разработки)
    origin = request.headers.get("origin", "http://localhost:3000")

    # Получить все задачи
    query = select(Task).order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()

    if format == "json":
        # JSON экспорт
        tasks_data = [
            {
                "id": task.id,
                "subject": task.subject,
                "topic": task.topic,
                "difficulty": task.difficulty,
                "title": task.title,
                "text": task.text,
                "answer": task.answer,
                "hints": task.hints,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            }
            for task in tasks
        ]

        json_content = json.dumps(tasks_data, ensure_ascii=False, indent=2)

        return StreamingResponse(
            iter([json_content]),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )

    else:  # format == "csv"
        # CSV экспорт
        output = StringIO()
        fieldnames = ["id", "subject", "topic", "difficulty", "title", "text", "answer", "hints", "created_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for task in tasks:
            # Hints в CSV соединяем точкой с запятой
            hints_str = ";".join(task.hints) if task.hints else ""

            writer.writerow({
                "id": task.id,
                "subject": task.subject,
                "topic": task.topic,
                "difficulty": task.difficulty,
                "title": task.title,
                "text": task.text,
                "answer": task.answer,
                "hints": hints_str,
                "created_at": task.created_at.isoformat() if task.created_at else "",
            })

        csv_content = output.getvalue()

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskAdminResponse,
    summary="Получить задачу по ID (Admin)",
    description="Возвращает полную информацию о задаче ВКЛЮЧАЯ правильный ответ.",
)
async def get_admin_task(
    task_id: int,
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    """Получение детальной информации о задаче для администратора."""

    logger.info(f"Admin task view: admin_id={current_admin.id}, task_id={task_id}")

    # Используем session.get() - самый эффективный способ для PK lookup
    task = await db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )

    return task


@router.put(
    "/tasks/{task_id}",
    response_model=TaskAdminResponse,
    summary="Обновить задачу",
    description="Частичное или полное обновление задачи. Отправляйте только изменённые поля.",
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    """
    Обновление задачи администратором.

    Поддерживает частичное обновление (PATCH-like behavior):
    - Отправляйте только те поля, которые нужно изменить
    - Используется exclude_unset=True для игнорирования None значений
    """

    # Получение существующей задачи
    task = await db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )

    # Логирование ПЕРЕД изменениями
    update_data = task_data.model_dump(exclude_unset=True)
    logger.info(
        f"Admin task update: admin_id={current_admin.id}, "
        f"task_id={task_id}, "
        f"updates={update_data}"
    )

    # Применение обновлений (только переданные поля)
    for field, value in update_data.items():
        setattr(task, field, value)

    try:
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task updated successfully: task_id={task_id}")

        return task

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Task update failed with integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось обновить задачу. Проверьте корректность данных.",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during task update: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.delete(
    "/tasks/{task_id}",
    response_model=dict,
    summary="Удалить задачу",
    description="Удаляет задачу из БД (hard delete). Требует роль администратора.",
)
async def delete_task(
    task_id: int,
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Удаление задачи администратором.

    ВНИМАНИЕ: Это HARD DELETE - задача удаляется из БД безвозвратно.
    Для production рекомендуется использовать soft delete.
    """

    # Получение задачи
    task = await db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )

    # Логирование ПЕРЕД удалением (warning уровень для критических операций)
    logger.warning(
        f"Admin task deletion: admin_id={current_admin.id}, "
        f"task_id={task_id}, "
        f"task_title={task.title}, "
        f"task_subject={task.subject}, "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

    try:
        await db.delete(task)
        await db.commit()

        logger.info(f"Task deleted successfully: task_id={task_id}")

        return {"ok": True, "message": f"Задача {task_id} успешно удалена"}

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Task deletion failed with integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Не удалось удалить задачу. "
                "Существуют связанные записи (попытки решения пользователей)."
            ),
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during task deletion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


# ===================================
# === ГЕНЕРАЦИЯ ВАРИАЦИЙ ЗАДАЧ ===
# ===================================


@router.post(
    "/tasks/{task_id}/generate",
    summary="Генерация вариаций задачи",
    description=(
        "Генерирует вариации задачи на основе параметров. "
        "Требует роль администратора. "
        "Использует шаблоны вида {{param|min:max}} в тексте задачи."
    ),
)
async def generate_task_variations(
    task_id: int,
    count: int = Query(5, ge=1, le=20, description="Количество вариаций (1-20)"),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Генерирует вариации существующей задачи.

    Преобразует задачу в шаблон (если содержит числа) и генерирует вариации
    с случайными параметрами.

    Шаблонный синтаксис:
    - {{param|min:max}} - случайное целое число от min до max
    - {{eval:expression}} - вычисление выражения для answer

    Пример:
    Исходная задача: "Решите уравнение: 3x + 5 = 20"
    Шаблон: "Решите уравнение: {{a|2:10}}x + {{b|5:20}} = {{c|25:60}}"
    Ответ: "{{eval:(c-b)/a}}"
    """

    logger.info(
        f"Admin task variations generation: admin_id={current_admin.id}, "
        f"task_id={task_id}, count={count}"
    )

    # Получить исходную задачу
    task = await db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )

    # Создать шаблон из задачи
    template = {
        "subject": task.subject,
        "topic": task.topic,
        "difficulty": task.difficulty,
        "title": task.title,
        "text": task.text,
        "answer": task.answer,
        "hints": task.hints or [],
    }

    try:
        # Валидация шаблона
        if not TaskGenerator.validate_template(template):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Задача не содержит шаблонных параметров. "
                    "Используйте синтаксис {{param|min:max}} для создания вариаций."
                ),
            )

        # Генерация вариаций
        variations = TaskGenerator.generate_multiple(template, count=count)

        # Сохранение вариаций в БД
        created_tasks = []
        for idx, variation in enumerate(variations):
            new_task = Task(
                subject=variation["subject"],
                topic=variation["topic"],
                difficulty=variation["difficulty"],
                title=f"{variation['title']} (вариация {idx + 1})",
                text=variation["text"],
                answer=variation["answer"],
                hints=variation["hints"],
            )
            db.add(new_task)
            created_tasks.append(new_task)

        await db.commit()

        # Обновить created_tasks с ID
        for task in created_tasks:
            await db.refresh(task)

        logger.info(
            f"Generated {len(created_tasks)} variations for task {task_id}"
        )

        return {
            "ok": True,
            "count": len(created_tasks),
            "task_ids": [t.id for t in created_tasks],
            "message": f"Создано {len(created_tasks)} вариаций задачи",
        }

    except ValueError as e:
        logger.error(f"Template validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации: {str(e)}",
        )
