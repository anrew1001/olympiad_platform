"""
Сервис автоматического подбора матча (matchmaking).

Все функции принимают открытую AsyncSession и НЕ вызывают session.commit().
Commit вызывает роутер. Это позволяет роутеру контролировать границу транзакции.
"""

import logging
from sqlalchemy import select, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.match import Match, MatchTask
from app.models.task import Task
from app.models.user import User
from app.models.enums import MatchStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Константы
# ============================================================================

RATING_RANGE = 200  # ±200 к рейтингу для подбора соперника

# Спецификация задач по сложности: (диапазон difficulty, количество задач)
TASK_SPEC: list[tuple[tuple[int, int], int]] = [
    ((1, 2), 2),   # 2 лёгкие задачи (difficulty 1 или 2)
    ((3, 3), 2),   # 2 средних (difficulty == 3)
    ((4, 5), 1),   # 1 тяжёлая (difficulty 4 или 5)
]


# ============================================================================
# find_or_create_match
# ============================================================================

async def find_or_create_match(
    user_id: int,
    user_rating: int,
    session: AsyncSession,
) -> Match:
    """
    Атомарный поиск или создание матча.

    Алгоритм:
        1. Guard: проверяем что у пользователя нет текущего ACTIVE матча.
           Если есть WAITING матч -- пытаемся найти соперника (решает race condition
           когда оба игрока создают WAITING матчи одновременно).
        2. FOR UPDATE SELECT: ищем waiting-матч в диапазоне рейтингов ±200.
           Блокируем найденную строку чтобы никто другой не смог её забрать.
        3a. Если найдена строка: присваиваем player2_id, status=active, flush, выбираем задачи.
        3b. Если строка не найдена: создаём новый Match с player1_id=user_id, status=waiting
            (или возвращаем существующий WAITING если он уже есть).

    Возвращает:
        Match с заполненными колонками. Relationships НЕ загружены (использовался noload).
        Роутер должен после commit() сделать свежий SELECT для загрузки relationships.

    Raises:
        HTTPException 409: Если пользователь уже в ACTIVE матче.

    НЕ вызывает commit(). Роутер ответственен за commit.
    """
    from fastapi import HTTPException

    logger.debug(f"find_or_create_match: user_id={user_id}, rating={user_rating}")

    # ------------------------------------------------------------------
    # Шаг 1: Guard -- пользователь уже в матче?
    # ------------------------------------------------------------------
    guard_stmt = (
        select(Match)
        .options(
            noload(Match.player1),
            noload(Match.player2),
            noload(Match.winner),
            noload(Match.tasks),
            noload(Match.answers),
        )
        .where(
            or_(
                Match.player1_id == user_id,
                Match.player2_id == user_id,
            ),
            Match.status.in_([MatchStatus.WAITING, MatchStatus.ACTIVE]),
        )
        .limit(1)
        .with_for_update()
    )
    guard_result = await session.execute(guard_stmt)
    existing_match = guard_result.scalar_one_or_none()

    if existing_match is not None:
        # ACTIVE матч -- возвращаем его (для polling - чтобы frontend увидел что матч начался)
        if existing_match.status == MatchStatus.ACTIVE:
            logger.info(
                f"GUARD: user={user_id} already in ACTIVE match {existing_match.id}, returning it"
            )
            return existing_match

        # WAITING матч -- попробуем найти соперника прямо сейчас
        # Это решает race condition когда оба игрока создали WAITING матчи одновременно
        logger.info(
            f"GUARD: user={user_id} has WAITING match {existing_match.id}, "
            f"re-searching for opponent..."
        )

    # ------------------------------------------------------------------
    # Шаг 2: FOR UPDATE -- ищем waiting-матч другого игрока для подбора
    # ------------------------------------------------------------------
    lock_stmt = (
        select(Match)
        .options(
            noload(Match.player1),
            noload(Match.player2),
            noload(Match.winner),
            noload(Match.tasks),
            noload(Match.answers),
        )
        .join(User, User.id == Match.player1_id)
        .where(
            Match.status == MatchStatus.WAITING,
            Match.player1_id != user_id,
            Match.player2_id.is_(None),
            User.rating.between(user_rating - RATING_RANGE, user_rating + RATING_RANGE),
        )
        .order_by(Match.created_at.asc())   # FIFO: самый старый waiting-матч первый
        .limit(1)
        .with_for_update(of=[Match])
    )
    try:
        lock_result = await session.execute(lock_stmt)
        waiting_match = lock_result.scalar_one_or_none()
    except Exception as e:
        logger.exception(f"Error executing FOR UPDATE: {e}")
        raise

    # ------------------------------------------------------------------
    # Шаг 3a: Матч найден -- забираем его
    # ------------------------------------------------------------------
    if waiting_match is not None:
        # Если у нас был свой WAITING матч, удаляем его (мы присоединяемся к чужому)
        if existing_match is not None:
            await session.delete(existing_match)
            logger.info(
                f"MATCH MERGED: deleted own WAITING match {existing_match.id}, "
                f"joining match {waiting_match.id}"
            )

        logger.info(
            f"MATCH JOINED: user={user_id} joined match {waiting_match.id} as player2. "
            f"Opponent player1={waiting_match.player1_id}"
        )
        waiting_match.player2_id = user_id
        waiting_match.status = MatchStatus.ACTIVE

        await session.flush()
        await select_match_tasks(waiting_match.id, session)

        return waiting_match

    # ------------------------------------------------------------------
    # Шаг 3b: Нет доступного матча
    # ------------------------------------------------------------------
    # Если у нас уже есть WAITING матч, просто возвращаем его (продолжаем ждать)
    if existing_match is not None:
        logger.debug(
            f"No opponent found, returning existing WAITING match {existing_match.id}"
        )
        return existing_match

    # Создаём новый waiting-матч
    new_match = Match(
        player1_id=user_id,
        player2_id=None,
        status=MatchStatus.WAITING,
    )
    session.add(new_match)
    await session.flush()

    logger.info(
        f"MATCH CREATED: user={user_id} created new WAITING match {new_match.id}"
    )

    return new_match


# ============================================================================
# select_match_tasks
# ============================================================================

async def select_match_tasks(
    match_id: int,
    session: AsyncSession,
) -> list[MatchTask]:
    """
    Выбирает задачи для матча по спецификации TASK_SPEC и создаёт MatchTask rows.

    Для каждой группы сложности выполняется отдельный запрос:
        SELECT id FROM tasks WHERE difficulty BETWEEN low AND high
        ORDER BY random() LIMIT count

    Использует существующие индексы на difficulty.

    Порядок задач в матче (task_order) присваивается последовательно,
    начиная с 1, в порядке: лёгкие -> средние -> тяжёлые.

    Если в какой-то группе меньше задач чем нужно, берётся столько сколько есть.
    Если всего 0 задач -- матч создаётся без задач (edge case, valid).

    НЕ вызывает commit(). Роутер ответственен.
    """
    created: list[MatchTask] = []
    order_counter = 1

    for (low, high), count in TASK_SPEC:
        # ORDER BY random() -- PostgreSQL-специфичный синтаксис.
        # Проект явно PostgreSQL-only (asyncpg driver в DATABASE_URL).
        task_stmt = (
            select(Task.id)
            .where(Task.difficulty.between(low, high))
            .order_by(func.random())
            .limit(count)
        )
        task_result = await session.execute(task_stmt)
        task_ids = [row[0] for row in task_result.fetchall()]

        if len(task_ids) < count:
            logger.warning(
                f"Not enough tasks for difficulty {low}-{high}: "
                f"requested {count}, found {len(task_ids)}"
            )

        for tid in task_ids:
            mt = MatchTask(
                match_id=match_id,
                task_id=tid,
                task_order=order_counter,
            )
            session.add(mt)
            created.append(mt)
            order_counter += 1

    # flush не вызываем -- роутер может добавить ещё что-то перед commit
    return created


# ============================================================================
# cancel_waiting_match
# ============================================================================

async def cancel_waiting_match(
    user_id: int,
    session: AsyncSession,
) -> int | None:
    """
    Удаляет waiting-матч пользователя.

    Алгоритм:
        1. FOR UPDATE SELECT: находим waiting-матч где player1_id == user_id
           и player2_id IS NULL. Блокируем строку.
        2. Проверяем что блокировка успешна и условия не изменились
           (кто-то мог забрать матч пока мы шли к блокировке).
        3. DELETE.

    Возвращает:
        match_id удалённого матча, или None если нет матча для удаления.

    НЕ вызывает commit().
    """
    # FOR UPDATE: блокируем строку перед DELETE чтобы не удалить матч
    # который другой пользователь уже забрал (race condition с find_or_create_match)
    lock_stmt = (
        select(Match)
        .options(
            noload(Match.player1),
            noload(Match.player2),
            noload(Match.winner),
            noload(Match.tasks),
            noload(Match.answers),
        )
        .where(
            Match.player1_id == user_id,
            Match.player2_id.is_(None),
            Match.status == MatchStatus.WAITING,
        )
        .with_for_update(of=[Match])
        .limit(1)
    )
    lock_result = await session.execute(lock_stmt)
    match = lock_result.scalar_one_or_none()

    if match is None:
        logger.debug(
            f"Cancel attempt by user {user_id}: no WAITING match found to cancel"
        )
        return None

    match_id = match.id

    # DELETE через ORM: session.delete() безопасен.
    # Waiting-матч не имеет child rows (tasks добавляются только при переходе в active).
    await session.delete(match)

    logger.info(
        f"MATCH CANCELLED: user={user_id} cancelled WAITING match {match_id}"
    )

    return match_id
