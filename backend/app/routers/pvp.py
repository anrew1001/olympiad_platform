"""
Роутер для автоматического PvP matchmaking (/api/pvp).

Все эндпоинты требуют JWT авторизацию через get_current_user.
Сессия БД та же что и в get_current_user (FastAPI кэширует Depends(get_db)).
Транзакция уже открыта (autobegin сработал при SELECT в get_current_user).
session.begin() вызывать НЕЛЬЗЯ.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.match import Match
from app.models.user import User
from app.models.enums import MatchStatus
from app.services.matching import find_or_create_match, cancel_waiting_match
from app.schemas.match import MatchResponse, MatchDetailResponse, CancelResponse, OpponentInfo


router = APIRouter(prefix="/api/pvp", tags=["pvp"])


@router.post(
    "/find",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Найти или создать матч",
    description=(
        "Автоматический поиск матча в диапазоне рейтингов ±200. "
        "Если есть waiting-матч -- присоединяется к нему. "
        "Иначе -- создаёт новый waiting-матч."
    ),
)
async def find_match(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),     # та же сессия что в get_current_user
) -> MatchResponse:
    """
    POST /api/pvp/find

    Транзакция уже открыта. Вызываем сервис, потом commit.
    После commit загружаем Match свежим SELECT для relationships.
    """
    # Сервис выполняет guard, FOR UPDATE, flush, но НЕ commit
    match = await find_or_create_match(
        user_id=current_user.id,
        user_rating=current_user.rating,   # rating загружен get_current_user
        session=db,
    )

    # Коммитим всё: Match row + MatchTask rows (если match стал active)
    match_id = match.id
    await db.commit()

    # После commit: свежий SELECT с eager loading relationships
    result = await db.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(joinedload(Match.player1), joinedload(Match.player2))
    )
    match = result.unique().scalar_one()

    # Построение response: opponent зависит от статуса
    opponent = None
    if match.status == MatchStatus.ACTIVE:
        # Мы присоединились к матчу → мы player2, opponent = player1
        opponent = OpponentInfo(
            id=match.player1.id,
            username=match.player1.username,
            rating=match.player1.rating,
        )

    return MatchResponse(
        match_id=match.id,
        status=match.status.value,
        opponent=opponent,
    )


@router.delete(
    "/find",
    response_model=CancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Отменить поиск матча",
    description="Удаляет waiting-матч текущего пользователя.",
)
async def cancel_find(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CancelResponse:
    """
    DELETE /api/pvp/find

    Удаляет waiting-матч. Если пользователь не создал waiting-матч или
    его уже забрал другой игрок -- возвращает {"cancelled": false}.
    """
    match_id = await cancel_waiting_match(user_id=current_user.id, session=db)

    await db.commit()

    return CancelResponse(cancelled=match_id is not None)


@router.get(
    "/match/{match_id}",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить детали матча",
    description="Возвращает полную информацию о матче включая задачи и баллы.",
)
async def get_match_detail(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """
    GET /api/pvp/match/{match_id}

    Простой SELECT. Модельные lazy-стратегии загружают relationships автоматически.
    player2 может быть None (waiting match) -- LEFT JOIN обрабатывает это корректно.
    """
    # Без options() -- используются модельные defaults:
    #   player1, player2, winner: lazy="joined" --> LEFT OUTER JOIN
    #   tasks, answers: lazy="selectin" --> отдельный IN-query
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Матч не найден",
        )

    # Проверка что пользователь -- участник матча
    if current_user.id not in (match.player1_id, match.player2_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не участник этого матча",
        )

    return MatchDetailResponse.from_match(match)
