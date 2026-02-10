"""
Сервис для работы с таблицей лидеров.

Основные функции:
- get_leaderboard() - получить топ N игроков с позициями и статистикой
"""

from sqlalchemy import select, func, case, or_, and_, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Float

from app.models import User, Match
from app.schemas.leaderboard import LeaderboardResponse, LeaderboardEntry


async def get_leaderboard(
    limit: int,
    current_user: User,
    session: AsyncSession,
) -> LeaderboardResponse:
    """
    Получить таблицу лидеров с позицией текущего пользователя.

    Алгоритм:
    1. CTE: подсчитать статистику всех пользователей (матчи, победы)
    2. Добавить ROW_NUMBER() для позиций, отсортировать по rating DESC
    3. Выбрать топ N записей
    4. Если текущий пользователь не в топе, отдельно запросить его статистику

    Args:
        limit: Количество записей в топе (1-100)
        current_user: Текущий авторизованный пользователь
        session: Асинхронная сессия БД

    Returns:
        LeaderboardResponse с entries и опциональной current_user_entry
    """

    # ========================================================================
    # Построить CTE для подсчёта статистики всех пользователей
    # ========================================================================

    # Подсчёт матчей и побед для каждого пользователя
    user_stats_cte = (
        select(
            User.id,
            User.username,
            User.rating,
            func.count(
                case(
                    (Match.status == "finished", 1),
                    else_=None
                )
            ).label("matches_played"),
            func.count(
                case(
                    (Match.winner_id == User.id, 1),
                    else_=None
                )
            ).label("wins"),
        )
        .select_from(User)
        .outerjoin(
            Match,
            and_(
                or_(
                    Match.player1_id == User.id,
                    Match.player2_id == User.id,
                ),
                Match.status == "finished",
            ),
        )
        .group_by(User.id, User.username, User.rating)
        .having(
            func.count(
                case(
                    (Match.status == "finished", 1),
                    else_=None
                )
            ) > 0
        )
        .cte("user_stats")
    )

    # ========================================================================
    # Выбрать топ N с позициями (используя ROW_NUMBER)
    # ========================================================================

    leaderboard_query = (
        select(
            user_stats_cte.c.id,
            user_stats_cte.c.username,
            user_stats_cte.c.rating,
            user_stats_cte.c.matches_played,
            user_stats_cte.c.wins,
            (
                cast(user_stats_cte.c.wins, Float)
                / func.nullif(user_stats_cte.c.matches_played, 0)
                * 100
            ).label("win_rate"),
        )
        .select_from(user_stats_cte)
        .order_by(
            user_stats_cte.c.rating.desc(),
            user_stats_cte.c.wins.desc(),
            user_stats_cte.c.username.asc(),
        )
        .limit(limit)
    )

    # Выполнить запрос
    result = await session.execute(leaderboard_query)
    rows = result.all()

    # ========================================================================
    # Преобразовать результаты с позициями
    # ========================================================================

    entries = []
    current_user_in_top = False

    for position, row in enumerate(rows, start=1):
        entry = LeaderboardEntry(
            position=position,
            user_id=row.id,
            username=row.username,
            rating=row.rating,
            matches_played=row.matches_played,
            wins=row.wins,
            win_rate=round(row.win_rate or 0, 2),
            is_current_user=(row.id == current_user.id),
        )
        entries.append(entry)

        if row.id == current_user.id:
            current_user_in_top = True

    # ========================================================================
    # Если текущий пользователь не в топе, запросить его статистику отдельно
    # ========================================================================

    current_user_entry = None

    if not current_user_in_top:
        # Найти статистику текущего пользователя
        user_stat_result = await session.execute(
            select(
                User.id,
                User.username,
                User.rating,
                func.count(
                    case(
                        (Match.status == "finished", 1),
                        else_=None
                    )
                ).label("matches_played"),
                func.count(
                    case(
                        (Match.winner_id == User.id, 1),
                        else_=None
                    )
                ).label("wins"),
            )
            .select_from(User)
            .outerjoin(
                Match,
                and_(
                    or_(
                        Match.player1_id == User.id,
                        Match.player2_id == User.id,
                    ),
                    Match.status == "finished",
                ),
            )
            .where(User.id == current_user.id)
            .group_by(User.id, User.username, User.rating)
        )
        user_stat_row = user_stat_result.one_or_none()

        if user_stat_row and user_stat_row.matches_played > 0:
            # Вычислить позицию текущего пользователя
            # = 1 + количество пользователей с рейтингом выше
            position_result = await session.execute(
                select(func.count())
                .select_from(user_stats_cte)
                .where(user_stats_cte.c.rating > current_user.rating)
            )
            position = (position_result.scalar() or 0) + 1

            win_rate = (
                user_stat_row.wins / user_stat_row.matches_played * 100
                if user_stat_row.matches_played > 0
                else 0.0
            )

            current_user_entry = LeaderboardEntry(
                position=position,
                user_id=user_stat_row.id,
                username=user_stat_row.username,
                rating=user_stat_row.rating,
                matches_played=user_stat_row.matches_played,
                wins=user_stat_row.wins,
                win_rate=round(win_rate, 2),
                is_current_user=True,
            )

    # ========================================================================
    # Подсчитать общее количество пользователей в рейтинге
    # ========================================================================

    total_result = await session.execute(
        select(func.count()).select_from(user_stats_cte)
    )
    total_users = total_result.scalar() or 0

    # ========================================================================
    # Вернуть ответ
    # ========================================================================

    return LeaderboardResponse(
        entries=entries,
        total_users=total_users,
        current_user_entry=current_user_entry,
    )
