from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserTaskAttempt, Task, UserAchievement
from app.routers.auth import get_current_user
from app.schemas.stats import (
    UserStatsResponse,
    DifficultyStats,
    RecentActivityItem,
    AchievementItem
)


# API роутер для операций с пользователями
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Получить статистику текущего пользователя",
    description=(
        "Возвращает полную статистику по решению задач для авторизованного пользователя. "
        "Включает общее количество попыток, точность, статистику по сложности, "
        "последнюю активность и полученные достижения."
    )
)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserStatsResponse:
    """
    Получение статистики пользователя.

    Требует JWT аутентификации.
    Возвращает только статистику текущего пользователя (безопасность).

    Args:
        current_user: Текущий авторизованный пользователь (из JWT токена)
        db: Асинхронная сессия БД

    Returns:
        UserStatsResponse: Полная статистика пользователя
    """

    user_id = current_user.id

    # === 1. Общая статистика: общее количество попыток ===
    total_query = select(func.count()).select_from(UserTaskAttempt).where(
        UserTaskAttempt.user_id == user_id
    )
    total_result = await db.execute(total_query)
    total_attempts = total_result.scalar() or 0

    # === 2. Общая статистика: количество правильных попыток ===
    correct_query = select(func.count()).select_from(UserTaskAttempt).where(
        UserTaskAttempt.user_id == user_id,
        UserTaskAttempt.is_correct == True
    )
    correct_result = await db.execute(correct_query)
    correct_attempts = correct_result.scalar() or 0

    # === 3. Общая статистика: уникальные решённые задачи ===
    unique_solved_query = select(
        func.count(func.distinct(UserTaskAttempt.task_id))
    ).where(
        UserTaskAttempt.user_id == user_id,
        UserTaskAttempt.is_correct == True
    )
    unique_result = await db.execute(unique_solved_query)
    unique_solved = unique_result.scalar() or 0

    # === 4. Расчёт точности ===
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0.0

    # === 5. Статистика по сложности (JOIN + GROUP BY) ===
    difficulty_query = select(
        Task.difficulty,
        func.count(func.distinct(
            case(
                (UserTaskAttempt.is_correct == True, UserTaskAttempt.task_id),
                else_=None
            )
        )).label('solved'),
        func.count(UserTaskAttempt.id).label('total_attempts')
    ).select_from(UserTaskAttempt).join(
        Task, UserTaskAttempt.task_id == Task.id
    ).where(
        UserTaskAttempt.user_id == user_id
    ).group_by(
        Task.difficulty
    ).order_by(
        Task.difficulty
    )

    difficulty_result = await db.execute(difficulty_query)
    difficulty_rows = difficulty_result.all()

    by_difficulty = [
        DifficultyStats(
            difficulty=row.difficulty,
            solved=row.solved or 0,
            total_attempts=row.total_attempts or 0
        )
        for row in difficulty_rows
    ]

    # === 6. Недавняя активность (JOIN + ORDER BY + LIMIT) ===
    recent_query = select(
        UserTaskAttempt.task_id,
        Task.title.label('task_title'),
        Task.difficulty.label('task_difficulty'),
        UserTaskAttempt.is_correct,
        UserTaskAttempt.created_at
    ).select_from(UserTaskAttempt).join(
        Task, UserTaskAttempt.task_id == Task.id
    ).where(
        UserTaskAttempt.user_id == user_id
    ).order_by(
        desc(UserTaskAttempt.created_at)
    ).limit(10)

    recent_result = await db.execute(recent_query)
    recent_rows = recent_result.all()

    recent_activity = [
        RecentActivityItem(
            task_id=row.task_id,
            task_title=row.task_title,
            task_difficulty=row.task_difficulty,
            is_correct=row.is_correct,
            created_at=row.created_at
        )
        for row in recent_rows
    ]

    # === 7. Получение достижений пользователя ===
    achievements_query = select(
        UserAchievement.type,
        UserAchievement.title,
        UserAchievement.description,
        UserAchievement.created_at
    ).where(
        UserAchievement.user_id == user_id
    ).order_by(
        desc(UserAchievement.created_at)
    )

    achievements_result = await db.execute(achievements_query)
    achievements_rows = achievements_result.all()

    achievements = [
        AchievementItem(
            type=row.type,
            title=row.title,
            description=row.description,
            unlocked_at=row.created_at
        )
        for row in achievements_rows
    ]

    # === 8. Формирование ответа ===
    return UserStatsResponse(
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy=round(accuracy, 2),  # Округлить до 2 знаков
        unique_solved=unique_solved,
        by_difficulty=by_difficulty,
        recent_activity=recent_activity,
        achievements=achievements
    )
