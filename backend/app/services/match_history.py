"""
Service layer для работы с историей PvP матчей пользователя.

Основные функции:
- get_match_history() - получить список матчей с фильтрами
- get_match_detail() - получить детали конкретного матча
- get_match_stats() - получить статистику и график рейтинга
"""

from math import ceil
from typing import Optional
from sqlalchemy import select, func, or_, and_, case, cast, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.types import Float

from app.models import Match, User, MatchTask, MatchAnswer, Task
from app.schemas.match_history import (
    MatchHistoryItem,
    PaginatedMatchHistoryResponse,
    MatchDetailResponse,
    TaskSolutionInfo,
    MatchStatsResponse,
    RatingHistoryPoint,
    OpponentInfo,
    TopicStats,
)


# ============================================================================
# GET /api/users/me/matches - История с пагинацией и фильтрами
# ============================================================================

async def get_match_history(
    user_id: int,
    page: int,
    per_page: int,
    status: Optional[str],
    result: Optional[str],
    opponent_username: Optional[str],
    sort_by: str,
    order: str,
    session: AsyncSession,
) -> PaginatedMatchHistoryResponse:
    """
    Получить список матчей пользователя с поддержкой фильтров, сортировки и пагинации.

    Фильтры:
    - status: finished, active, all
    - result: won, lost, draw, all
    - opponent_username: поиск по имени (ILIKE)
    - sort_by: finished_at, rating_change
    - order: asc, desc

    Оптимизации:
    - joinedload() для избежания N+1 queries
    - Composite indexes на (player_id, finished_at DESC)
    - Пагинация через LIMIT/OFFSET
    """

    # Базовый query с eager loading relationships
    query = (
        select(Match)
        .where(
            or_(
                Match.player1_id == user_id,
                Match.player2_id == user_id,
            )
        )
        .options(
            joinedload(Match.player1),
            joinedload(Match.player2),
        )
    )

    # Фильтр по статусу
    if status and status != "all":
        query = query.where(Match.status == status)

    # Фильтр по результату (won/lost/draw)
    if result and result != "all":
        if result == "won":
            # Пользователь выиграл
            query = query.where(Match.winner_id == user_id)
        elif result == "lost":
            # Пользователь проиграл (матч завершён, но не он победил)
            query = query.where(
                and_(
                    Match.winner_id.isnot(None),
                    Match.winner_id != user_id,
                )
            )
        elif result == "draw":
            # Ничья (матч завершён, но нет победителя)
            query = query.where(
                and_(
                    Match.winner_id.is_(None),
                    Match.status == "finished",
                )
            )

    # Фильтр по имени соперника (ILIKE для case-insensitive поиска)
    if opponent_username:
        query = query.where(
            or_(
                Match.player1.has(
                    User.username.ilike(f"%{opponent_username}%")
                ),
                Match.player2.has(
                    User.username.ilike(f"%{opponent_username}%")
                ),
            )
        )

    # Сортировка
    sort_column = getattr(Match, sort_by, Match.finished_at)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Подсчёт общего количества для пагинации
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Применение LIMIT/OFFSET
    offset = (page - 1) * per_page
    query = query.limit(per_page).offset(offset)

    # Выполнение query
    result_obj = await session.execute(query)
    matches = result_obj.scalars().unique().all()

    # Конвертация ORM объектов в Pydantic models
    items = [_build_history_item(match, user_id) for match in matches]

    # Расчёт количества страниц
    pages = ceil(total / per_page) if total > 0 else 0

    return PaginatedMatchHistoryResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


def _build_history_item(match: Match, user_id: int) -> MatchHistoryItem:
    """
    Построить MatchHistoryItem из Match ORM объекта.

    Определяет:
    - Кто соперник (player1 или player2)
    - Мой счёт и счёт соперника
    - Результат матча (won/lost/draw)
    - Изменение рейтинга
    """

    # Определить соперника и счёты в зависимости от позиции
    if match.player1_id == user_id:
        opponent = match.player2
        my_score = match.player1_score
        opponent_score = match.player2_score
        my_rating_change = match.player1_rating_change
    else:
        opponent = match.player1
        my_score = match.player2_score
        opponent_score = match.player1_score
        my_rating_change = match.player2_rating_change

    # Определить результат матча
    result = None
    if match.winner_id == user_id:
        result = "won"
    elif match.winner_id and match.winner_id != user_id:
        result = "lost"
    elif match.status == "finished" and not match.winner_id:
        result = "draw"

    return MatchHistoryItem(
        match_id=match.id,
        status=match.status,
        result=result,
        opponent=OpponentInfo(
            id=opponent.id,
            username=opponent.username,
            rating=opponent.rating,
        ),
        my_score=my_score,
        opponent_score=opponent_score,
        my_rating_change=my_rating_change,
        finished_at=match.finished_at,
        created_at=match.created_at,
    )


# ============================================================================
# GET /api/users/me/matches/{match_id} - Детали матча
# ============================================================================

async def get_match_detail(
    match_id: int,
    user_id: int,
    session: AsyncSession,
) -> MatchDetailResponse:
    """
    Получить полную информацию о конкретном матче.

    Включает:
    - Информацию о сопернике
    - Список задач с информацией о решениях
    - Времена отправки ответов

    Предполагает, что user_id уже проверен (участник матча).
    """

    # Получить матч с загруженными relationships
    result = await session.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(
            joinedload(Match.player1),
            joinedload(Match.player2),
            joinedload(Match.tasks).joinedload(MatchTask.task),
        )
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Матч {match_id} не найден")

    # Определить соперника
    if match.player1_id == user_id:
        opponent = match.player2
        my_score = match.player1_score
        opponent_score = match.player2_score
        my_rating_change = match.player1_rating_change
    else:
        opponent = match.player1
        my_score = match.player2_score
        opponent_score = match.player1_score
        my_rating_change = match.player2_rating_change

    # Определить результат
    result_str = None
    if match.winner_id == user_id:
        result_str = "won"
    elif match.winner_id and match.winner_id != user_id:
        result_str = "lost"
    elif match.status == "finished" and not match.winner_id:
        result_str = "draw"

    # Получить информацию о решениях для каждой задачи
    tasks_info = []
    for match_task in sorted(match.tasks, key=lambda t: t.task_order):
        # Получить ответы обоих игроков на эту задачу
        my_answer_result = await session.execute(
            select(MatchAnswer).where(
                and_(
                    MatchAnswer.match_id == match_id,
                    MatchAnswer.user_id == user_id,
                    MatchAnswer.task_id == match_task.task_id,
                )
            )
        )
        my_answer = my_answer_result.scalar_one_or_none()

        opponent_answer_result = await session.execute(
            select(MatchAnswer).where(
                and_(
                    MatchAnswer.match_id == match_id,
                    MatchAnswer.user_id == opponent.id,
                    MatchAnswer.task_id == match_task.task_id,
                )
            )
        )
        opponent_answer = opponent_answer_result.scalar_one_or_none()

        tasks_info.append(
            TaskSolutionInfo(
                task_id=match_task.task_id,
                title=match_task.task.title,
                difficulty=match_task.task.difficulty,
                order=match_task.task_order,
                solved_by_me=bool(my_answer and my_answer.is_correct),
                solved_by_opponent=bool(
                    opponent_answer and opponent_answer.is_correct
                ),
                my_answer_time=my_answer.submitted_at if my_answer else None,
                opponent_answer_time=(
                    opponent_answer.submitted_at if opponent_answer else None
                ),
            )
        )

    return MatchDetailResponse(
        match_id=match.id,
        status=match.status,
        result=result_str,
        opponent=OpponentInfo(
            id=opponent.id,
            username=opponent.username,
            rating=opponent.rating,
        ),
        my_score=my_score,
        opponent_score=opponent_score,
        my_rating_change=my_rating_change,
        tasks=tasks_info,
        finished_at=match.finished_at,
        created_at=match.created_at,
    )


# ============================================================================
# GET /api/users/me/matches/stats - Статистика и график рейтинга
# ============================================================================

async def get_match_stats(
    user_id: int,
    session: AsyncSession,
) -> MatchStatsResponse:
    """
    Получить статистику по матчам и историю рейтинга.

    Возвращает:
    - Количество побед/поражений/ничьих
    - Win rate в процентах
    - История рейтинга за последние 50 матчей

    История рейтинга отсортирована по дате (возрастание) для графика.
    """

    # Получить все завершённые матчи пользователя
    result = await session.execute(
        select(Match)
        .where(
            and_(
                or_(
                    Match.player1_id == user_id,
                    Match.player2_id == user_id,
                ),
                Match.status == "finished",
            )
        )
        .order_by(Match.finished_at.desc())
    )
    matches = result.scalars().all()

    # Подсчитать результаты
    won = 0
    lost = 0
    draw = 0

    for match in matches:
        if match.winner_id == user_id:
            won += 1
        elif match.winner_id and match.winner_id != user_id:
            lost += 1
        elif not match.winner_id:
            draw += 1

    total = won + lost + draw
    win_rate = (won / total * 100) if total > 0 else 0.0

    # Построить историю рейтинга (последние 50 матчей, отсортировано по дате возрастанием)
    rating_history = []

    # Взять последние 50 матчей и развернуть для отображения
    recent_matches = matches[:50][::-1]  # Переворачиваем чтобы самые старые были первыми

    for match in recent_matches:
        if match.player1_id == user_id:
            rating_change = match.player1_rating_change or 0
        else:
            rating_change = match.player2_rating_change or 0

        # Получить текущий рейтинг пользователя из User модели
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Рейтинг после матча = текущий рейтинг (он уже обновлён в User.rating)
        # Но нам нужен рейтинг ИМЕННО после этого матча
        # Это будет current_rating - sum(rating_changes после этого матча)
        # Для простоты: рейтинг после = текущий + (все изменения после этого матча)
        # Вычислим сумму изменений всех матчей ПОСЛЕ этого

        future_result = await session.execute(
            select(func.sum(
                case(
                    (Match.player1_id == user_id, Match.player1_rating_change),
                    else_=Match.player2_rating_change
                )
            )).where(
                and_(
                    or_(
                        Match.player1_id == user_id,
                        Match.player2_id == user_id,
                    ),
                    Match.status == "finished",
                    Match.finished_at > match.finished_at,
                )
            )
        )
        future_change = future_result.scalar() or 0
        rating_after_match = user.rating - future_change

        rating_history.append(
            RatingHistoryPoint(
                match_id=match.id,
                rating=rating_after_match,
                rating_change=rating_change,
                created_at=match.finished_at,
            )
        )

    return MatchStatsResponse(
        total_matches=total,
        won=won,
        lost=lost,
        draw=draw,
        win_rate=round(win_rate, 2),
        rating_history=rating_history,
    )


# ============================================================================
# GET /api/users/me/matches/stats (EXTENDED) - Детальная статистика с сериями и анализом тем
# ============================================================================


async def get_detailed_match_stats(
    user_id: int,
    session: AsyncSession,
) -> MatchStatsResponse:
    """
    Получить детальную статистику по матчам с сериями побед/поражений и анализом тем.

    Возвращает:
    - Базовая статистика (W/L/D, win_rate, rating_history)
    - Текущая серия (current_streak)
    - Лучшая серия побед (best_win_streak)
    - Анализ по темам (strongest_topics, weakest_topics)

    Оптимизации:
    - Window functions для эффективного подсчета серий
    - CTE для сложных агрегаций
    - Минимум 3 попытки по теме для статистической значимости
    """

    # ========================================================================
    # 1. БАЗОВАЯ СТАТИСТИКА И ИСТОРИЯ РЕЙТИНГА
    # ========================================================================

    # Получить все завершённые матчи пользователя для базовой статистики
    result = await session.execute(
        select(Match)
        .where(
            and_(
                or_(
                    Match.player1_id == user_id,
                    Match.player2_id == user_id,
                ),
                Match.status == "finished",
            )
        )
        .order_by(Match.finished_at.desc())
    )
    matches = result.scalars().all()

    # Подсчитать результаты
    won = 0
    lost = 0
    draw = 0

    for match in matches:
        if match.winner_id == user_id:
            won += 1
        elif match.winner_id and match.winner_id != user_id:
            lost += 1
        elif not match.winner_id:
            draw += 1

    total = won + lost + draw
    win_rate = (won / total * 100) if total > 0 else 0.0

    # Построить историю рейтинга (последние 50 матчей)
    rating_history = []

    # Взять последние 50 матчей и развернуть для отображения
    recent_matches = matches[:50][::-1]  # От старых к новым

    for match in recent_matches:
        if match.player1_id == user_id:
            rating_change = match.player1_rating_change or 0
        else:
            rating_change = match.player2_rating_change or 0

        # Получить текущий рейтинг пользователя
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Рейтинг после матча = текущий рейтинг - sum(изменений после этого матча)
        future_result = await session.execute(
            select(func.sum(
                case(
                    (Match.player1_id == user_id, Match.player1_rating_change),
                    else_=Match.player2_rating_change
                )
            )).where(
                and_(
                    or_(
                        Match.player1_id == user_id,
                        Match.player2_id == user_id,
                    ),
                    Match.status == "finished",
                    Match.finished_at > match.finished_at,
                )
            )
        )
        future_change = future_result.scalar() or 0
        rating_after_match = user.rating - future_change

        rating_history.append(
            RatingHistoryPoint(
                match_id=match.id,
                rating=rating_after_match,
                rating_change=rating_change,
                created_at=match.finished_at,
            )
        )

    # ========================================================================
    # 2. CURRENT STREAK (Текущая серия побед/поражений)
    # ========================================================================

    current_streak = 0

    if matches:  # Если есть матчи
        # CTE: player_matches - все матчи с классификацией результата
        player_matches_cte = (
            select(
                Match.id,
                Match.finished_at,
                case(
                    (Match.winner_id.is_(None), 0),      # Ничья
                    (Match.winner_id == user_id, 1),    # Победа
                    else_=-1                             # Поражение
                ).label("result")
            )
            .where(
                and_(
                    or_(Match.player1_id == user_id, Match.player2_id == user_id),
                    Match.status == "finished"
                )
            )
            .order_by(Match.finished_at.desc())
            .cte("player_matches")
        )

        # CTE: with_streak_groups - группировка по сериям через ROW_NUMBER difference
        streak_groups_cte = (
            select(
                player_matches_cte.c.result,
                player_matches_cte.c.finished_at,
                (
                    func.row_number().over(order_by=player_matches_cte.c.finished_at.desc()) -
                    func.row_number().over(
                        partition_by=player_matches_cte.c.result,
                        order_by=player_matches_cte.c.finished_at.desc()
                    )
                ).label("streak_group")
            )
            .where(player_matches_cte.c.result != 0)  # Исключить ничьи
            .cte("with_streak_groups")
        )

        # CTE: current_streak_calc - найти самую свежую серию
        current_streak_cte = (
            select(
                streak_groups_cte.c.result,
                func.count().label("streak_length"),
                func.min(streak_groups_cte.c.finished_at).label("streak_start")
            )
            .group_by(streak_groups_cte.c.streak_group, streak_groups_cte.c.result)
            .order_by(literal("streak_start").desc())
            .limit(1)
            .cte("current_streak_calc")
        )

        # Final query for current_streak
        current_streak_query = select(
            func.coalesce(
                current_streak_cte.c.result * current_streak_cte.c.streak_length,
                0
            ).label("current_streak")
        ).select_from(current_streak_cte)

        result = await session.execute(current_streak_query)
        row = result.one_or_none()
        current_streak = row.current_streak if row else 0

    # ========================================================================
    # 3. BEST WIN STREAK (Лучшая серия побед за всё время)
    # ========================================================================

    best_win_streak = 0

    if won > 0:  # Если есть хотя бы одна победа
        # CTE: player_matches - все матчи с флагом победы/не-победы
        player_matches_wins_cte = (
            select(
                Match.finished_at,
                case(
                    (Match.winner_id == user_id, 1),
                    else_=0
                ).label("is_win")
            )
            .where(
                and_(
                    or_(Match.player1_id == user_id, Match.player2_id == user_id),
                    Match.status == "finished"
                )
            )
            .order_by(Match.finished_at.asc())
            .cte("player_matches_wins")
        )

        # CTE: with_streak_groups_wins - группировка серий побед
        streak_groups_wins_cte = (
            select(
                player_matches_wins_cte.c.is_win,
                (
                    func.row_number().over(order_by=player_matches_wins_cte.c.finished_at.asc()) -
                    func.row_number().over(
                        partition_by=player_matches_wins_cte.c.is_win,
                        order_by=player_matches_wins_cte.c.finished_at.asc()
                    )
                ).label("streak_group")
            )
            .cte("with_streak_groups_wins")
        )

        # CTE: win_streaks - подсчёт длин всех серий побед
        win_streaks_cte = (
            select(
                func.count().label("streak_length")
            )
            .select_from(streak_groups_wins_cte)
            .where(streak_groups_wins_cte.c.is_win == 1)
            .group_by(streak_groups_wins_cte.c.streak_group)
            .cte("win_streaks")
        )

        # Final query for best_win_streak
        best_win_streak_query = select(
            func.coalesce(func.max(win_streaks_cte.c.streak_length), 0).label("best_win_streak")
        ).select_from(win_streaks_cte)

        result = await session.execute(best_win_streak_query)
        row = result.one_or_none()
        best_win_streak = row.best_win_streak if row else 0

    # ========================================================================
    # 4. TOPIC STATISTICS (Сильные и слабые темы)
    # ========================================================================

    strongest_topics = []
    weakest_topics = []

    # CTE: topic_stats - агрегация по темам с фильтром >= 3 попытки
    topic_stats_cte = (
        select(
            Task.topic,
            func.count().label("attempts"),
            func.round(
                cast(
                    func.sum(case((MatchAnswer.is_correct, 1), else_=0)),
                    Float
                ) / func.nullif(func.count(), 0) * 100,
                2
            ).label("success_rate")
        )
        .select_from(MatchAnswer)
        .join(Task, Task.id == MatchAnswer.task_id)
        .where(MatchAnswer.user_id == user_id)
        .group_by(Task.topic)
        .having(func.count() >= 3)
        .cte("topic_stats")
    )

    # CTE: ranked_topics - ранжирование по success_rate
    ranked_topics_cte = (
        select(
            topic_stats_cte.c.topic,
            topic_stats_cte.c.success_rate,
            topic_stats_cte.c.attempts,
            func.row_number().over(
                order_by=(topic_stats_cte.c.success_rate.desc(), topic_stats_cte.c.attempts.desc())
            ).label("strongest_rank"),
            func.row_number().over(
                order_by=(topic_stats_cte.c.success_rate.asc(), topic_stats_cte.c.attempts.desc())
            ).label("weakest_rank")
        )
        .cte("ranked_topics")
    )

    # Query for strongest topics (rank <= 3)
    strongest_query = (
        select(
            ranked_topics_cte.c.topic,
            ranked_topics_cte.c.success_rate,
            ranked_topics_cte.c.attempts,
        )
        .where(ranked_topics_cte.c.strongest_rank <= 3)
        .order_by(ranked_topics_cte.c.strongest_rank.asc())
    )

    result = await session.execute(strongest_query)
    strongest_topics = [
        TopicStats(topic=r.topic, success_rate=r.success_rate, attempts=r.attempts)
        for r in result.all()
    ]

    # Query for weakest topics (rank <= 3)
    weakest_query = (
        select(
            ranked_topics_cte.c.topic,
            ranked_topics_cte.c.success_rate,
            ranked_topics_cte.c.attempts,
        )
        .where(ranked_topics_cte.c.weakest_rank <= 3)
        .order_by(ranked_topics_cte.c.success_rate.asc())
    )

    result = await session.execute(weakest_query)
    weakest_topics = [
        TopicStats(topic=r.topic, success_rate=r.success_rate, attempts=r.attempts)
        for r in result.all()
    ]

    # ========================================================================
    # 5. RETURN RESPONSE
    # ========================================================================

    return MatchStatsResponse(
        total_matches=total,
        won=won,
        lost=lost,
        draw=draw,
        win_rate=round(win_rate, 2),
        rating_history=rating_history,
        current_streak=current_streak,
        best_win_streak=best_win_streak,
        strongest_topics=strongest_topics,
        weakest_topics=weakest_topics,
    )
