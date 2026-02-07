from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models import User, UserTaskAttempt, Task, UserAchievement, Match
from app.dependencies.auth import get_current_user
from app.schemas.stats import (
    UserStatsResponse,
    DifficultyStats,
    RecentActivityItem,
    AchievementItem
)
from app.schemas.match_history import (
    PaginatedMatchHistoryResponse,
    MatchDetailResponse,
    MatchStatsResponse,
)
from app.services.match_history import (
    get_match_history,
    get_match_detail,
    get_match_stats,
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


# ============================================================================
# История PvP матчей
# ============================================================================

@router.get(
    "/me/matches",
    response_model=PaginatedMatchHistoryResponse,
    summary="История PvP матчей пользователя",
    description=(
        "Получить историю всех PvP матчей текущего пользователя с поддержкой "
        "пагинации, фильтрации и сортировки. "
        "Фильтры: status (finished/active/all), result (won/lost/draw/all), "
        "opponent_username (поиск по имени). "
        "Сортировка: finished_at, rating_change."
    ),
    tags=["match-history"],
)
async def get_my_matches(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(10, ge=1, le=50, description="Элементов на странице"),
    status: Optional[str] = Query(
        None,
        description="Фильтр по статусу: finished, active, all"
    ),
    result: Optional[str] = Query(
        None,
        description="Фильтр по результату: won, lost, draw, all"
    ),
    opponent_username: Optional[str] = Query(
        None,
        description="Поиск по имени соперника"
    ),
    sort_by: str = Query(
        "finished_at",
        description="Сортировка по: finished_at, rating_change"
    ),
    order: str = Query(
        "desc",
        description="Порядок сортировки: asc, desc"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMatchHistoryResponse:
    """
    Получение истории PvP матчей текущего пользователя.

    Query параметры позволяют фильтровать и сортировать результаты.
    """
    return await get_match_history(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        status=status,
        result=result,
        opponent_username=opponent_username,
        sort_by=sort_by,
        order=order,
        session=db,
    )


@router.get(
    "/me/matches/stats",
    response_model=MatchStatsResponse,
    summary="Статистика PvP матчей и история рейтинга",
    description=(
        "Получить общую статистику по PvP матчам (W/L/D, win rate) "
        "и историю изменения рейтинга за последние 50 матчей для графика."
    ),
    tags=["match-history"],
)
async def get_my_match_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchStatsResponse:
    """
    Получение статистики по PvP матчам и истории рейтинга.
    """
    return await get_match_stats(current_user.id, db)


@router.get(
    "/me/matches/{match_id}",
    response_model=MatchDetailResponse,
    summary="Детали конкретного PvP матча",
    description=(
        "Получить полную информацию о матче: соперник, задачи, результаты решений, "
        "времена отправки ответов. "
        "Доступно только участникам матча."
    ),
    tags=["match-history"],
    responses={
        404: {"description": "Матч не найден"},
        403: {"description": "Доступ запрещён (вы не участник матча)"},
    },
)
async def get_my_match_detail(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """
    Получение деталей конкретного матча.

    Требует проверки что пользователь является участником (player1 или player2).
    """

    # Проверить что матч существует и пользователь его участник
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Матч не найден"
        )

    if current_user.id not in (match.player1_id, match.player2_id):
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён: вы не участник этого матча"
        )

    return await get_match_detail(match_id, current_user.id, db)
