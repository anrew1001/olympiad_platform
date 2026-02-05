"""
FastAPI роутеры для PvP матчей.

Endpoints:
- POST /matches - создать матч
- GET /matches - список активных матчей
- GET /matches/{id} - детали матча
- POST /matches/{id}/answers - отправить ответ на задачу
- POST /matches/{id}/finish - завершить матч
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Match, MatchTask, MatchAnswer, User, Task, MatchStatus

router = APIRouter(prefix="/matches", tags=["matches"])


# ============= Schemas =============

class MatchCreateRequest(BaseModel):
    """Создание матча"""
    player1_id: int
    player2_id: int


class AddTasksRequest(BaseModel):
    """Добавить задачи в матч"""
    task_ids: List[int]


class AnswerSubmitRequest(BaseModel):
    """Отправка ответа"""
    answer: str


# ============= Endpoints =============


@router.post("", summary="Создать новый матч")
async def create_match(
    match_data: MatchCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Создание 1v1 матча между двумя игроками.

    **Параметры:**
    - player1_id: ID первого игрока
    - player2_id: ID второго игрока

    **Ограничения:**
    - player1_id ≠ player2_id (CHECK constraint)
    - Оба игрока должны существовать

    **Возвращает:** объект матча с статусом "waiting"
    """
    player1_id = match_data.player1_id
    player2_id = match_data.player2_id
    # Проверяем что игроки существуют
    result1 = await session.execute(select(User).where(User.id == player1_id))
    user1 = result1.scalar_one_or_none()
    if not user1:
        raise HTTPException(status_code=404, detail=f"Игрок {player1_id} не найден")

    result2 = await session.execute(select(User).where(User.id == player2_id))
    user2 = result2.scalar_one_or_none()
    if not user2:
        raise HTTPException(status_code=404, detail=f"Игрок {player2_id} не найден")

    # Проверяем что это разные игроки
    if player1_id == player2_id:
        raise HTTPException(status_code=400, detail="Нельзя играть с собой")

    # Создаём матч
    match = Match(
        player1_id=player1_id,
        player2_id=player2_id,
        status=MatchStatus.WAITING,
    )
    session.add(match)
    await session.commit()

    return {
        "id": match.id,
        "player1_id": match.player1_id,
        "player2_id": match.player2_id,
        "status": match.status.value,
        "player1_score": match.player1_score,
        "player2_score": match.player2_score,
        "winner_id": match.winner_id,
        "created_at": match.created_at,
        "message": "✓ Матч создан, ожидание второго игрока (статус: waiting)",
    }


@router.get("/{match_id}", summary="Получить информацию о матче")
async def get_match(
    match_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Получить полную информацию о матче.

    Включает:
    - Информацию об обоих игроках
    - Список задач в матче
    - Ответы игроков
    - Статус матча
    """
    result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    # Получаем задачи
    tasks_result = await session.execute(
        select(MatchTask).where(MatchTask.match_id == match_id)
    )
    tasks = tasks_result.scalars().all()

    # Получаем ответы
    answers_result = await session.execute(
        select(MatchAnswer).where(MatchAnswer.match_id == match_id)
    )
    answers = answers_result.scalars().all()

    return {
        "match": {
            "id": match.id,
            "player1": {
                "id": match.player1.id,
                "username": match.player1.username,
                "rating": match.player1.rating,
                "score": match.player1_score,
            },
            "player2": {
                "id": match.player2.id,
                "username": match.player2.username,
                "rating": match.player2.rating,
                "score": match.player2_score,
            },
            "status": match.status.value,
            "created_at": match.created_at.isoformat(),
            "finished_at": match.finished_at.isoformat() if match.finished_at else None,
        },
        "tasks": [
            {
                "order": t.task_order,
                "task_id": t.task_id,
                "title": t.task.title,
                "difficulty": t.task.difficulty,
            }
            for t in tasks
        ],
        "answers": [
            {
                "user_id": a.user_id,
                "task_id": a.task_id,
                "is_correct": a.is_correct,
                "submitted_at": a.submitted_at.isoformat(),
            }
            for a in answers
        ],
    }


@router.post("/{match_id}/tasks", summary="Добавить задачи в матч")
async def add_tasks_to_match(
    match_id: int,
    tasks_data: AddTasksRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Добавить задачи в матч.

    **Параметры:**
    - match_id: ID матча
    - task_ids: Список ID задач

    **Важно:**
    - Задачи должны существовать
    - Одна задача не может быть добавлена дважды
    """
    # Проверяем что матч существует
    match_result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = match_result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    # Проверяем существование задач
    tasks_result = await session.execute(
        select(Task).where(Task.id.in_(tasks_data.task_ids))
    )
    tasks = tasks_result.scalars().all()

    if len(tasks) != len(tasks_data.task_ids):
        raise HTTPException(status_code=404, detail="Некоторые задачи не найдены")

    # Добавляем задачи в матч
    for order, task_id in enumerate(tasks_data.task_ids, start=1):
        match_task = MatchTask(
            match_id=match_id,
            task_id=task_id,
            task_order=order,
        )
        session.add(match_task)

    await session.commit()

    return {
        "match_id": match_id,
        "message": f"✓ Добавлено {len(tasks_data.task_ids)} задач в матч",
        "task_ids": tasks_data.task_ids,
    }


@router.post("/{match_id}/answers", summary="Отправить ответ на задачу")
async def submit_answer(
    match_id: int,
    task_id: int = Query(..., description="ID задачи"),
    user_id: int = Query(..., description="ID пользователя"),
    answer_data: AnswerSubmitRequest = Body(...),
    session: AsyncSession = Depends(get_db),
):
    """
    Отправить ответ на задачу в матче.

    **UPSERT паттерн:**
    - Если ответ уже существует → UPDATE
    - Если нет → INSERT

    **Параметры в query:**
    - match_id: ID матча (в пути)
    - task_id: ID задачи
    - user_id: ID игрока

    **Параметры в body:**
    - answer: Текст ответа

    **Важно:**
    - Уникальность на (match_id, user_id, task_id)
    - submitted_at автоматически обновляется
    """
    answer = answer_data.answer

    # Проверяем что матч существует
    match_result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = match_result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    # Проверяем что задача в матче
    task_result = await session.execute(
        select(MatchTask).where(
            (MatchTask.match_id == match_id)
            & (MatchTask.task_id == task_id)
        )
    )
    match_task = task_result.scalar_one_or_none()
    if not match_task:
        raise HTTPException(status_code=404, detail="Задача не найдена в этом матче")

    # UPSERT: SELECT → UPDATE или INSERT
    result = await session.execute(
        select(MatchAnswer).where(
            (MatchAnswer.match_id == match_id)
            & (MatchAnswer.user_id == user_id)
            & (MatchAnswer.task_id == task_id)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # UPDATE существующего ответа
        existing.answer = answer
        # is_correct должен устанавливаться системой проверки
        # Здесь упрощённо: проверяем содержит ли ответ часть правильного
        existing.is_correct = match_task.task.answer.lower() in answer.lower()
        await session.commit()
        await session.refresh(existing)
        return {
            "action": "updated",
            "message": "✓ Ответ обновлён (UPDATE паттерн)",
            "data": {
                "match_id": existing.match_id,
                "user_id": existing.user_id,
                "task_id": existing.task_id,
                "is_correct": existing.is_correct,
                "submitted_at": existing.submitted_at.isoformat(),
            },
        }
    else:
        # INSERT нового ответа
        new_answer = MatchAnswer(
            match_id=match_id,
            user_id=user_id,
            task_id=task_id,
            answer=answer,
            is_correct=match_task.task.answer.lower() in answer.lower(),
        )
        session.add(new_answer)
        await session.commit()
        await session.refresh(new_answer)
        return {
            "action": "created",
            "message": "✓ Ответ отправлен (INSERT паттерн)",
            "data": {
                "match_id": new_answer.match_id,
                "user_id": new_answer.user_id,
                "task_id": new_answer.task_id,
                "is_correct": new_answer.is_correct,
                "submitted_at": new_answer.submitted_at.isoformat(),
            },
        }


@router.post("/{match_id}/finish", summary="Завершить матч")
async def finish_match(
    match_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Завершить матч и рассчитать результаты.

    **Что происходит:**
    1. Подсчитываются баллы обоих игроков
    2. Определяется победитель
    3. Рассчитывается изменение рейтинга (упрощённо)
    4. Статус меняется на "finished"
    """
    result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    # Подсчитываем баллы
    answers_result = await session.execute(
        select(MatchAnswer).where(MatchAnswer.match_id == match_id)
    )
    answers = answers_result.scalars().all()

    player1_score = sum(
        1 for a in answers if a.user_id == match.player1_id and a.is_correct
    )
    player2_score = sum(
        1 for a in answers if a.user_id == match.player2_id and a.is_correct
    )

    # Определяем победителя
    match.player1_score = player1_score
    match.player2_score = player2_score

    if player1_score > player2_score:
        match.winner_id = match.player1_id
        match.player1_rating_change = 25
        match.player2_rating_change = -25
    elif player2_score > player1_score:
        match.winner_id = match.player2_id
        match.player1_rating_change = -25
        match.player2_rating_change = 25
    else:
        match.player1_rating_change = 0
        match.player2_rating_change = 0

    match.status = MatchStatus.FINISHED
    match.finished_at = datetime.utcnow()

    await session.commit()

    return {
        "match_id": match.id,
        "status": match.status.value,
        "player1": {
            "id": match.player1_id,
            "score": match.player1_score,
            "rating_change": match.player1_rating_change,
        },
        "player2": {
            "id": match.player2_id,
            "score": match.player2_score,
            "rating_change": match.player2_rating_change,
        },
        "winner_id": match.winner_id,
        "finished_at": match.finished_at.isoformat(),
        "message": "✓ Матч завершён",
    }


@router.get("", summary="Список активных матчей")
async def list_active_matches(
    session: AsyncSession = Depends(get_db),
):
    """
    Получить все активные матчи.

    Фильтр: status = 'active'
    """
    result = await session.execute(
        select(Match).where(Match.status == MatchStatus.ACTIVE)
    )
    matches = result.scalars().all()

    return {
        "total": len(matches),
        "matches": [
            {
                "id": m.id,
                "player1": m.player1.username,
                "player2": m.player2.username,
                "score": f"{m.player1_score}-{m.player2_score}",
                "created_at": m.created_at.isoformat(),
            }
            for m in matches
        ],
    }
