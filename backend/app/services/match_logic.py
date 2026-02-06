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
) -> dict:
    """
    Завершает матч и обновляет рейтинги игроков.

    Использует упрощённую систему рейтинга:
    - Победитель: +15
    - Проигравший: -5
    - Ничья: 0

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций

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

    # 1. Lock match для обновления
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

    # 2. Определить победителя и изменения рейтинга
    if match.player1_score > match.player2_score:
        winner_id = match.player1_id
        player1_change = 15
        player2_change = -5
        logger.info(f"Match {match_id}: Player {match.player1_id} wins ({match.player1_score} vs {match.player2_score})")
    elif match.player2_score > match.player1_score:
        winner_id = match.player2_id
        player1_change = -5
        player2_change = 15
        logger.info(f"Match {match_id}: Player {match.player2_id} wins ({match.player2_score} vs {match.player1_score})")
    else:
        # Ничья
        winner_id = None
        player1_change = 0
        player2_change = 0
        logger.info(f"Match {match_id}: Draw ({match.player1_score} vs {match.player2_score})")

    # 3. Обновить Match
    match.status = MatchStatus.FINISHED
    match.winner_id = winner_id
    match.player1_rating_change = player1_change
    match.player2_rating_change = player2_change
    # finished_at хранится как TIMESTAMP WITHOUT TIME ZONE в БД
    match.finished_at = datetime.utcnow()

    # 4. Обновить рейтинги игроков (ВАЖНО!)
    result = await session.execute(
        select(User).where(User.id == match.player1_id)
    )
    player1 = result.scalar_one()
    old_rating_1 = player1.rating
    player1.rating += player1_change

    result = await session.execute(
        select(User).where(User.id == match.player2_id)
    )
    player2 = result.scalar_one()
    old_rating_2 = player2.rating
    player2.rating += player2_change

    await session.flush()

    logger.info(
        f"Ratings updated - Player1: {old_rating_1}->{player1.rating}, "
        f"Player2: {old_rating_2}->{player2.rating}"
    )

    # 5. Вернуть данные для event'а
    return {
        "winner_id": winner_id,
        "player1_rating_change": player1_change,
        "player1_new_rating": player1.rating,
        "player2_rating_change": player2_change,
        "player2_new_rating": player2.rating,
        "final_scores": {
            "player1_score": match.player1_score,
            "player2_score": match.player2_score,
        },
    }
