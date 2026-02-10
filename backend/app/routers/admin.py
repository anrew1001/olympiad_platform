import logging
from datetime import datetime
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
