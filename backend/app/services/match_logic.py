"""Бизнес-логика для обработки ответов и завершения PvP матчей."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.match import Match, MatchAnswer, MatchTask
from app.models.task import Task
from app.models.user import User
from app.models.enums import MatchStatus
from app.services.elo import calculate_match_rating_changes, apply_rating_bounds

logger = logging.getLogger(__name__)


async def process_answer(
    match_id: int,
    user_id: int,
    task_id: int,
    answer: str,
    session: AsyncSession,
) -> tuple[bool, int]:
    """
    Обрабатывает ответ игрока с UPSERT паттерном и SELECT FOR UPDATE.

    Args:
        match_id: ID матча
        user_id: ID пользователя (игрока)
        task_id: ID задачи
        answer: Текст ответа от игрока
        session: AsyncSession для БД операций

    Returns:
        Кортеж (is_correct, new_score) где:
        - is_correct: True если ответ правильный
        - new_score: Новый общий счёт игрока в этом матче

    Raises:
        ValueError: Если матч или задача не найдены
    """

    # 1. Lock match row для предотвращения race conditions
    # ВАЖНО: с noload() исключаем relationships чтобы избежать LEFT OUTER JOIN
    # PostgreSQL не позволяет FOR UPDATE с nullable side LEFT JOIN
    result = await session.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(noload(Match.player1), noload(Match.player2), noload(Match.winner))
        .with_for_update()
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Match {match_id} not found")

    # 2. Получить правильный ответ задачи
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise ValueError(f"Task {task_id} not found")

    # 3. Нормализовать ответы для сравнения
    normalized_answer = answer.strip().lower()
    normalized_correct = task.answer.strip().lower()
    is_correct = normalized_answer == normalized_correct

    # 4. UPSERT MatchAnswer
    # Сначала проверяем существующий ответ
    result = await session.execute(
        select(MatchAnswer).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == user_id)
            & (MatchAnswer.task_id == task_id)
        )
    )
    existing_answer = result.scalar_one_or_none()

    if existing_answer:
        # UPDATE существующего ответа
        existing_answer.answer = answer
        existing_answer.is_correct = is_correct
        # submitted_at хранится как TIMESTAMP WITHOUT TIME ZONE в БД
        existing_answer.submitted_at = datetime.utcnow()
        logger.debug(
            f"Updated answer for user {user_id} on task {task_id}: {is_correct}"
        )
    else:
        # INSERT нового ответа
        new_answer = MatchAnswer(
            match_id=match_id,
            user_id=user_id,
            task_id=task_id,
            answer=answer,
            is_correct=is_correct,
        )
        session.add(new_answer)
        logger.debug(
            f"Created answer for user {user_id} on task {task_id}: {is_correct}"
        )

    await session.flush()

    # 5. Пересчитать счёт (COUNT правильных ответов)
    result = await session.execute(
        select(func.count(MatchAnswer.id)).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == user_id)
            & (MatchAnswer.is_correct == True)
        )
    )
    new_score = result.scalar() or 0

    # 6. Обновить счёт в Match
    if user_id == match.player1_id:
        match.player1_score = new_score
    elif user_id == match.player2_id:
        match.player2_score = new_score
    else:
        raise ValueError(f"User {user_id} is not a participant in match {match_id}")

    logger.debug(f"Match {match_id} scores: P1={match.player1_score}, P2={match.player2_score}")

    return is_correct, new_score


async def check_match_completion(
    match_id: int,
    session: AsyncSession,
) -> bool:
    """
    Проверяет завершился ли матч.

    Условие завершения (выбрано пользователем):
    - Оба игрока отправили ответы на все задачи матча

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций

    Returns:
        True если матч должен быть завершён, False иначе
    """

    # Получить информацию о матче
    result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        return False

    # Получить количество задач в матче
    result = await session.execute(
        select(func.count(MatchTask.id)).where(MatchTask.match_id == match_id)
    )
    total_tasks = result.scalar() or 0

    if total_tasks == 0:
        return False

    # Получить количество ответов от player1
    result = await session.execute(
        select(func.count(MatchAnswer.id)).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player1_id)
        )
    )
    player1_answered = result.scalar() or 0

    # Получить количество ответов от player2
    result = await session.execute(
        select(MatchAnswer.id)
        .where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player2_id)
        )
        .distinct()
    )
    player2_answered = len((await session.execute(
        select(func.count(MatchAnswer.id)).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player2_id)
        )
    )).all())

    # Использовать более простой способ
    result = await session.execute(
        select(func.count(MatchAnswer.id)).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player2_id)
        )
    )
    player2_answered = result.scalar() or 0

    is_complete = player1_answered >= total_tasks and player2_answered >= total_tasks

    logger.debug(
        f"Match {match_id} completion check: "
        f"P1={player1_answered}/{total_tasks}, P2={player2_answered}/{total_tasks}, "
        f"complete={is_complete}"
    )

    return is_complete


async def finalize_match(
    match_id: int,
    session: AsyncSession,
    reason: str = "completion",
    winner_id: int | None = None,
) -> dict:
    """
    Завершает матч и обновляет рейтинги игроков используя ELO систему.

    Использует классическую ELO формулу:
    - E_a = 1 / (1 + 10^((R_b - R_a) / 400))
    - ΔR = K × (S - E_a), где K=32

    IDEMPOTENCY: Функция идемпотентна. Если матч уже завершён, вернёт
    кешированный результат без повторного обновления рейтингов.

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций
        reason: Причина завершения ("completion" | "forfeit" | "technical_error")
        winner_id: ID победителя (переопределяет winner для forfeit случаев)

    Returns:
        Словарь с данными для match_end события:
        {
            "winner_id": int or None,
            "player1_rating_change": int,
            "player1_new_rating": int,
            "player2_rating_change": int,
            "player2_new_rating": int,
            "final_scores": {
                "player1_score": int,
                "player2_score": int
            }
        }

    Raises:
        ValueError: Если матч не найден
    """

    # 1. Lock match для обновления с IDEMPOTENCY CHECK
    # ВАЖНО: с noload() исключаем relationships чтобы избежать LEFT OUTER JOIN
    result = await session.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(noload(Match.player1), noload(Match.player2), noload(Match.winner))
        .with_for_update()
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Match {match_id} not found")

    # IDEMPOTENCY: Если матч уже завершён, вернуть кешированный результат
    if match.status == MatchStatus.FINISHED:
        logger.info(f"Match {match_id} already FINISHED, returning cached result")
        return {
            "winner_id": match.winner_id,
            "player1_rating_change": match.player1_rating_change or 0,
            "player1_new_rating": 0,  # Не загружаем пользователя, так что ставим 0
            "player2_rating_change": match.player2_rating_change or 0,
            "player2_new_rating": 0,
            "final_scores": {
                "player1_score": match.player1_score,
                "player2_score": match.player2_score,
            },
        }

    if match.status == MatchStatus.ERROR:
        logger.info(f"Match {match_id} already ERROR, cannot finalize")
        raise ValueError(f"Match {match_id} is in ERROR state, cannot finalize")

    if match.status != MatchStatus.ACTIVE:
        raise ValueError(f"Match {match_id} is in {match.status} state, cannot finalize")

    # 2. Определить победителя в зависимости от reason
    if reason == "technical_error":
        # Техническая ошибка: рейтинги не меняются
        winner_id = None
        player1_change = 0
        player2_change = 0
        final_status = MatchStatus.ERROR
        logger.warning(f"Match {match_id}: Technical error - no rating changes")

    elif reason == "forfeit":
        # Forfeit: переданный winner_id определяет победителя
        # Проигравший - тот, кто отключился
        if winner_id is None:
            raise ValueError("For forfeit reason, winner_id must be specified")

        final_status = MatchStatus.FINISHED

        # Загрузить текущие рейтинги для ELO расчётов
        result = await session.execute(
            select(User).where(User.id == match.player1_id)
        )
        player1_user = result.scalar_one()

        result = await session.execute(
            select(User).where(User.id == match.player2_id)
        )
        player2_user = result.scalar_one()

        # Рассчитать ELO с учётом forfeit как полной победы/поражения
        player1_change, player2_change = calculate_match_rating_changes(
            player1_user.rating,
            player2_user.rating,
            winner_id=winner_id,
            p1_id=match.player1_id,
            p2_id=match.player2_id,
        )

        logger.info(
            f"Match {match_id}: Forfeit - Player {winner_id} wins, "
            f"P1 change={player1_change}, P2 change={player2_change}"
        )

    else:  # reason == "completion"
        # Нормальное завершение матча: определяем победителя по счёту
        final_status = MatchStatus.FINISHED

        # Загрузить текущие рейтинги
        result = await session.execute(
            select(User).where(User.id == match.player1_id)
        )
        player1_user = result.scalar_one()

        result = await session.execute(
            select(User).where(User.id == match.player2_id)
        )
        player2_user = result.scalar_one()

        # Определить победителя по счёту
        if match.player1_score > match.player2_score:
            winner_id = match.player1_id
        elif match.player2_score > match.player1_score:
            winner_id = match.player2_id
        else:
            winner_id = None  # Ничья

        # Рассчитать ELO
        player1_change, player2_change = calculate_match_rating_changes(
            player1_user.rating,
            player2_user.rating,
            winner_id=winner_id,
            p1_id=match.player1_id,
            p2_id=match.player2_id,
        )

        logger.info(
            f"Match {match_id}: Completion - Winner={winner_id}, "
            f"Scores: P1={match.player1_score} vs P2={match.player2_score}, "
            f"ELO changes: P1={player1_change:+d}, P2={player2_change:+d}"
        )

    # 3. Обновить Match запись
    match.status = final_status
    match.winner_id = winner_id
    match.player1_rating_change = player1_change
    match.player2_rating_change = player2_change
    # finished_at хранится как TIMESTAMP WITHOUT TIME ZONE в БД
    if reason != "technical_error":
        match.finished_at = datetime.utcnow()

    # 4. Обновить рейтинги игроков (если не техническая ошибка)
    if reason != "technical_error":
        result = await session.execute(
            select(User).where(User.id == match.player1_id)
        )
        player1 = result.scalar_one()
        old_rating_1 = player1.rating
        player1.rating = apply_rating_bounds(player1.rating + player1_change)
        new_rating_1 = player1.rating

        result = await session.execute(
            select(User).where(User.id == match.player2_id)
        )
        player2 = result.scalar_one()
        old_rating_2 = player2.rating
        player2.rating = apply_rating_bounds(player2.rating + player2_change)
        new_rating_2 = player2.rating

        await session.flush()

        logger.info(
            f"Ratings updated - Player1: {old_rating_1}->{new_rating_1} ({player1_change:+d}), "
            f"Player2: {old_rating_2}->{new_rating_2} ({player2_change:+d})"
        )

        return {
            "winner_id": winner_id,
            "player1_rating_change": player1_change,
            "player1_new_rating": new_rating_1,
            "player2_rating_change": player2_change,
            "player2_new_rating": new_rating_2,
            "final_scores": {
                "player1_score": match.player1_score,
                "player2_score": match.player2_score,
            },
        }
    else:
        # Техническая ошибка: рейтинги не меняются
        await session.flush()
        return {
            "winner_id": None,
            "player1_rating_change": 0,
            "player1_new_rating": 0,
            "player2_rating_change": 0,
            "player2_new_rating": 0,
            "final_scores": {
                "player1_score": match.player1_score,
                "player2_score": match.player2_score,
            },
        }


async def finalize_match_forfeit(
    match_id: int,
    user_id_disconnected: int,
    session: AsyncSession,
) -> dict:
    """
    Завершает матч когда один игрок отключился и превысил 30-секундный timeout.

    Отключившийся игрок проигрывает, оставшийся - выигрывает.
    Рейтинги обновляются по ELO системе.

    Args:
        match_id: ID матча
        user_id_disconnected: ID игрока, который отключился
        session: AsyncSession для БД операций

    Returns:
        Словарь с данными для match_end события (см. finalize_match)

    Raises:
        ValueError: Если матч или пользователь не найдены
    """

    # Загрузить матч для определения оставшегося игрока
    result = await session.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(noload(Match.player1), noload(Match.player2), noload(Match.winner))
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Match {match_id} not found")

    # Определить победителя (оставшийся игрок)
    if user_id_disconnected == match.player1_id:
        winner_id = match.player2_id
    elif user_id_disconnected == match.player2_id:
        winner_id = match.player1_id
    else:
        raise ValueError(
            f"User {user_id_disconnected} is not a participant in match {match_id}"
        )

    logger.warning(
        f"Match {match_id}: Forfeit - User {user_id_disconnected} disconnected, "
        f"User {winner_id} wins by forfeit"
    )

    # Использовать finalize_match с forfeit reason
    return await finalize_match(
        match_id,
        session,
        reason="forfeit",
        winner_id=winner_id,
    )


async def handle_technical_error(
    match_id: int,
    session: AsyncSession,
    error_message: str,
) -> None:
    """
    Обрабатывает техническую ошибку матча.

    Устанавливает статус в ERROR и НЕ меняет рейтинги.
    Используется когда оба игрока отключились одновременно или произошла
    критическая ошибка сервера.

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций
        error_message: Описание ошибки для логирования

    Raises:
        ValueError: Если матч не найден
    """

    logger.error(f"Match {match_id}: Technical error - {error_message}")

    # Использовать finalize_match с technical_error reason
    await finalize_match(
        match_id,
        session,
        reason="technical_error",
    )


async def get_match_state(
    match_id: int,
    session: AsyncSession,
) -> dict:
    """
    Получает полное состояние матча для reconnection state_sync.

    Используется для отправки полной информации о матче при переподключении игрока.
    Включает счёты обоих игроков, список решённых задач и время матча.

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций

    Returns:
        Словарь с состоянием матча:
        {
            "player1_id": int,
            "player2_id": int,
            "player1_score": int,
            "player2_score": int,
            "player1_solved_tasks": [task_id, ...],
            "player2_solved_tasks": [task_id, ...],
            "total_tasks": int,
            "time_elapsed": int (seconds),
        }

    Raises:
        ValueError: Если матч не найден
    """

    # Получить информацию о матче
    result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Match {match_id} not found")

    # Получить общее количество задач
    result = await session.execute(
        select(func.count(MatchTask.id)).where(MatchTask.match_id == match_id)
    )
    total_tasks = result.scalar() or 0

    # Получить решённые задачи player1
    result = await session.execute(
        select(MatchAnswer.task_id).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player1_id)
            & (MatchAnswer.is_correct == True)
        )
    )
    player1_solved = [row[0] for row in result.all()]

    # Получить решённые задачи player2
    result = await session.execute(
        select(MatchAnswer.task_id).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == match.player2_id)
            & (MatchAnswer.is_correct == True)
        )
    )
    player2_solved = [row[0] for row in result.all()]

    # Вычислить прошедшее время
    time_elapsed = int((datetime.utcnow() - match.created_at).total_seconds())

    logger.debug(
        f"Match {match_id} state: P1={match.player1_score}, P2={match.player2_score}, "
        f"time_elapsed={time_elapsed}s, total_tasks={total_tasks}"
    )

    return {
        "player1_id": match.player1_id,
        "player2_id": match.player2_id,
        "player1_score": match.player1_score,
        "player2_score": match.player2_score,
        "player1_solved_tasks": player1_solved,
        "player2_solved_tasks": player2_solved,
        "total_tasks": total_tasks,
        "time_elapsed": time_elapsed,
    }


async def activate_match(
    match_id: int,
    session: AsyncSession,
) -> None:
    """
    Переводит матч из WAITING в ACTIVE статус.
    Вызывается когда оба игрока подключены.

    Args:
        match_id: ID матча
        session: Асинхронная сессия БД
    """
    result = await session.execute(
        select(Match).where(Match.id == match_id).with_for_update()
    )
    match = result.scalar_one_or_none()

    if not match:
        raise ValueError(f"Match {match_id} not found")

    if match.status == MatchStatus.WAITING:
        match.status = MatchStatus.ACTIVE
        await session.flush()
        logger.info(f"Match {match_id} activated (status: WAITING → ACTIVE)")
