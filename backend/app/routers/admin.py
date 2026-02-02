import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_admin_user
from app.models import User, Task, UserTaskAttempt
from app.schemas.admin import AdminStatsResponse


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
