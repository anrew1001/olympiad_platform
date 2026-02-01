from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task, User
from app.schemas.task import TaskInList, TaskDetail, PaginatedTaskResponse, TaskCheckRequest, TaskCheckResponse
from app.routers.auth import get_current_user


# API роутер для работы с задачами
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=PaginatedTaskResponse,
    summary="Получить список задач",
    description=(
        "Возвращает пагинированный список задач с возможностью фильтрации "
        "по предмету, теме и сложности. Поддерживает пагинацию."
    )
)
async def get_tasks(
    subject: Optional[str] = Query(None, description="Фильтр по предмету (например, informatics)"),
    topic: Optional[str] = Query(None, description="Фильтр по теме (например, algorithms)"),
    difficulty: Optional[int] = Query(None, ge=1, le=5, description="Фильтр по сложности (1-5)"),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Количество задач на странице (max 100)"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedTaskResponse:
    """
    Получение списка задач с фильтрацией и пагинацией.

    Args:
        subject: Фильтр по предмету (опционально)
        topic: Фильтр по теме (опционально)
        difficulty: Фильтр по сложности 1-5 (опционально)
        page: Номер страницы (начиная с 1)
        per_page: Размер страницы (максимум 100)
        db: Асинхронная сессия БД

    Returns:
        PaginatedTaskResponse: Список задач с метаинформацией о пагинации

    Примечание:
        - В ответе НЕ возвращается поле answer (только для проверки на бэкенде)
        - В списке НЕ возвращаются поля text и hints (только краткая информация)
    """

    # Базовый запрос для выборки задач
    query = select(Task)

    # Применение фильтров (динамически добавляем where только если параметр указан)
    if subject is not None:
        query = query.where(Task.subject == subject)

    if topic is not None:
        query = query.where(Task.topic == topic)

    if difficulty is not None:
        query = query.where(Task.difficulty == difficulty)

    # Запрос для подсчёта общего количества задач (с учётом фильтров)
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Вычисление количества страниц
    pages = ceil(total / per_page) if total > 0 else 0

    # Добавление пагинации к основному запросу
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Сортировка по умолчанию (по дате создания, новые первыми)
    query = query.order_by(Task.created_at.desc())

    # Выполнение запроса
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Формирование ответа
    return PaginatedTaskResponse(
        items=[TaskInList.model_validate(task) for task in tasks],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetail,
    summary="Получить задачу по ID",
    description=(
        "Возвращает полную информацию о задаче включая текст условия "
        "и подсказки, но БЕЗ правильного ответа."
    )
)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
) -> Task:
    """
    Получение детальной информации о задаче по ID.

    Args:
        task_id: ID задачи
        db: Асинхронная сессия БД

    Returns:
        TaskDetail: Полная информация о задаче (БЕЗ поля answer)

    Raises:
        HTTPException 404: Если задача с указанным ID не найдена

    Примечание:
        Ответ содержит полный текст условия (text) и подсказки (hints),
        но НЕ содержит правильный ответ (answer) для защиты от читерства.
    """

    # Запрос задачи по ID
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    # Обработка случая, когда задача не найдена
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена"
        )

    # FastAPI автоматически сериализует через TaskDetail
    # (без поля answer, т.к. оно не определено в схеме)
    return task


@router.post(
    "/{task_id}/check",
    response_model=TaskCheckResponse,
    summary="Проверить ответ на задачу",
    description=(
        "Проверяет правильность ответа пользователя на задачу. "
        "Требует авторизации через JWT токен. "
        "При правильном ответе возвращает подтверждение. "
        "При неправильном ответе возвращает правильный ответ."
    )
)
async def check_task_answer(
    task_id: int,
    check_data: TaskCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskCheckResponse:
    """
    Проверка ответа пользователя на задачу.

    Args:
        task_id: ID задачи для проверки
        check_data: Данные с ответом пользователя
        current_user: Текущий авторизованный пользователь (из JWT токена)
        db: Асинхронная сессия БД

    Returns:
        TaskCheckResponse: Результат проверки с сообщением и опционально правильным ответом

    Raises:
        HTTPException 404: Если задача с указанным ID не найдена
        HTTPException 401: Если пользователь не авторизован (обрабатывается в get_current_user)

    Примечание безопасности:
        - Эндпоинт защищён JWT аутентификацией через get_current_user dependency
        - Правильный ответ возвращается ТОЛЬКО при неверном ответе пользователя
        - Сравнение ответов case-insensitive с удалением пробельных символов
    """

    # === 1. Получение задачи из БД ===
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    # Обработка случая, когда задача не найдена
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена"
        )

    # === 2. Нормализация ответов для сравнения ===
    # Приводим оба ответа к нижнему регистру и убираем пробелы по краям
    # Это позволяет игнорировать различия в регистре и лишние пробелы
    user_answer = check_data.answer.strip().lower()
    correct_answer = task.answer.strip().lower()

    # === 3. Проверка правильности ответа ===
    is_correct = (user_answer == correct_answer)

    # === 4. Формирование ответа ===
    if is_correct:
        # Правильный ответ - НЕ раскрываем правильный ответ
        return TaskCheckResponse(
            is_correct=True,
            message="Верно!",
            correct_answer=None
        )
    else:
        # Неправильный ответ - показываем правильный ответ
        # ВАЖНО: используем оригинальный task.answer (не нормализованный),
        # чтобы показать ответ в правильном формате
        return TaskCheckResponse(
            is_correct=False,
            message="Неверно, попробуйте ещё раз",
            correct_answer=task.answer
        )
