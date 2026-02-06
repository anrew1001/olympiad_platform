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
        1. Guard: проверяем что у пользователя нет текущего waiting/active матча.
        2. FOR UPDATE SELECT: ищем waiting-матч в диапазоне рейтингов ±200.
           Блокируем найденную строку чтобы никто другой не смог её забрать.
        3a. Если найдена строка: присваиваем player2_id, status=active, flush, выбираем задачи.
        3b. Если строка не найдена: создаём новый Match с player1_id=user_id, status=waiting.

    Возвращает:
        Match с заполненными колонками. Relationships НЕ загружены (использовался noload).
        Роутер должен после commit() сделать свежий SELECT для загрузки relationships.

    Raises:
        HTTPException 409: Если пользователь уже в active/waiting матче.

    НЕ вызывает commit(). Роутер ответственен за commit.
    """
    from fastapi import HTTPException

    logger.debug(f"find_or_create_match: user_id={user_id}, rating={user_rating}")

    # ------------------------------------------------------------------
    # Шаг 1: Guard -- пользователь уже в матче?
    # ------------------------------------------------------------------
    logger.debug("Guard check: searching for existing match...")
    guard_stmt = (
        select(Match.id)
        .where(
            or_(
                Match.player1_id == user_id,
                Match.player2_id == user_id,
            ),
            Match.status.in_([MatchStatus.WAITING, MatchStatus.ACTIVE]),
        )
        .limit(1)
    )
    guard_result = await session.execute(guard_stmt)
    if guard_result.scalar_one_or_none() is not None:
        logger.debug(f"User {user_id} already in a match - 409")
        raise HTTPException(
            status_code=409,
            detail="У вас уже есть активный или ожидающий матч",
        )
    logger.debug("Guard check passed")

    # ------------------------------------------------------------------
    # Шаг 2: FOR UPDATE -- ищем waiting-матч для подбора
    # ------------------------------------------------------------------
    logger.debug("FOR UPDATE SELECT: looking for waiting match...")
    # noload() подавляет все lazy-загрузки (joined и selectin).
    # Без этого SQLAlchemy добавит LEFT JOIN на users (для player1, player2, winner)
    # и отправит selectin-queries на match_tasks и match_answers.
    # Нам не нужны эти данные здесь, и лишние JOINы мешают FOR UPDATE.
    #
    # Явный .join(User, ...) для фильтра по рейтингу.
    # with_for_update(of=[Match]) -- блокирует только строку в matches,
    # не трогает users через JOIN.
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
        logger.debug(f"FOR UPDATE result: match found = {waiting_match is not None}")
    except Exception as e:
        logger.exception(f"Error executing FOR UPDATE: {e}")
        raise

    # ------------------------------------------------------------------
    # Шаг 3a: Матч найден -- забираем его
    # ------------------------------------------------------------------
    if waiting_match is not None:
        waiting_match.player2_id = user_id
        waiting_match.status = MatchStatus.ACTIVE

        # flush: записывает изменения в БД но НЕ коммитит.
        # Нужен потому что select_match_tasks() ниже делает INSERT в match_tasks,
        # и ему нужен match.id (он уже есть, match существовал).
        await session.flush()

        # Выбираем задачи и создаём MatchTask rows в той же транзакции
        await select_match_tasks(waiting_match.id, session)

        return waiting_match

    # ------------------------------------------------------------------
    # Шаг 3b: Матч не найден -- создаём новый waiting-матч
    # ------------------------------------------------------------------
    new_match = Match(
        player1_id=user_id,
        player2_id=None,           # явно None -- ожидает второго игрока
        status=MatchStatus.WAITING,
    )
    session.add(new_match)

    # flush чтобы match.id был присвоен БД (autoincrement)
    # без flush match.id == None и роутер не может его вернуть
    await session.flush()

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
        return None

    match_id = match.id

    # DELETE через ORM: session.delete() безопасен.
    # Waiting-матч не имеет child rows (tasks добавляются только при переходе в active).
    await session.delete(match)

    return match_id
