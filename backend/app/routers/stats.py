"""
Public stats router - статистика платформы без авторизации
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.models.match import Match
from app.models.enums import MatchStatus

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/public")
async def get_public_stats(
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Публичная статистика платформы (без авторизации)

    Returns:
        - total_tasks: количество задач
        - total_users: количество пользователей
        - total_matches: количество завершённых матчей
        - active_matches: количество активных матчей
    """

    # Total tasks
    task_count_result = await session.execute(
        select(func.count(Task.id))
    )
    total_tasks = task_count_result.scalar() or 0

    # Total users
    user_count_result = await session.execute(
        select(func.count(User.id))
    )
    total_users = user_count_result.scalar() or 0

    # Total finished matches
    finished_count_result = await session.execute(
        select(func.count(Match.id)).where(
            Match.status == MatchStatus.FINISHED
        )
    )
    total_matches = finished_count_result.scalar() or 0

    # Active matches (ACTIVE or WAITING)
    active_count_result = await session.execute(
        select(func.count(Match.id)).where(
            Match.status.in_([MatchStatus.ACTIVE, MatchStatus.WAITING])
        )
    )
    active_matches = active_count_result.scalar() or 0

    return {
        "total_tasks": total_tasks,
        "total_users": total_users,
        "total_matches": total_matches,
        "active_matches": active_matches,
    }
