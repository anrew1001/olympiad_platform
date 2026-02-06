"""
Pydantic-схемы для PvP matchmaking API.

SECURITY: Task.answer НЕ включён ни в одну из схем.
MatchTaskInfo содержит только id, order, title, text, difficulty, hints.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Nested components
# ============================================================================

class OpponentInfo(BaseModel):
    """Краткая информация об игроке в контексте матча."""

    id: int = Field(..., description="ID пользователя")
    username: str = Field(..., description="Имя пользователя")
    rating: int = Field(..., description="Рейтинг пользователя")

    model_config = ConfigDict(from_attributes=True)


class MatchTaskInfo(BaseModel):
    """
    Информация о задаче в матче.

    SECURITY: поле answer отсутствует. Даже если Task.answer загружен в ORM,
    Pydantic не включит его в сериализацию потому что поля нет в схеме.
    """

    task_id: int = Field(..., description="ID задачи")
    order: int = Field(..., description="Порядковый номер задачи в матче (1-5)")
    title: str = Field(..., description="Название задачи")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность от 1 до 5")
    text: str = Field(..., description="Полный текст задачи")
    hints: List[str] = Field(default=[], description="Подсказки")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_match_task(cls, mt: "MatchTask") -> "MatchTaskInfo":  # noqa: F821
        """Создание из MatchTask ORM-объекта. mt.task должен быть загружен."""
        return cls(
            task_id=mt.task_id,
            order=mt.task_order,  # НЕ mt.order, а mt.task_order
            title=mt.task.title,
            difficulty=mt.task.difficulty,
            text=mt.task.text,
            hints=mt.task.hints or [],
        )


# ============================================================================
# Ответ на POST /api/pvp/find
# ============================================================================

class MatchResponse(BaseModel):
    """
    Ответ на запрос поиска матча.

    Если match.status == "waiting" -- пользователь создал матч и ждёт оппонента.
        opponent == None
    Если match.status == "active" -- оппонент найден, матч начал.
        opponent заполнен
    """

    match_id: int = Field(..., description="ID матча")
    status: str = Field(..., description="Статус: 'waiting' или 'active'")
    opponent: Optional[OpponentInfo] = Field(None, description="Информация об оппоненте (None если waiting)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Ответ на GET /api/pvp/match/{match_id}
# ============================================================================

class MatchDetailResponse(BaseModel):
    """
    Полный ответ с информацией о матче.

    Включает оба игрока, задачи и основную информацию.
    player2 может быть None (waiting match).
    """

    match_id: int = Field(..., description="ID матча")
    status: str = Field(..., description="Статус матча")
    player1: OpponentInfo = Field(..., description="Первый игрок (создатель)")
    player2: Optional[OpponentInfo] = Field(None, description="Второй игрок (присоединившийся)")
    player1_score: int = Field(default=0, description="Баллы первого игрока")
    player2_score: int = Field(default=0, description="Баллы второго игрока")
    match_tasks: List[MatchTaskInfo] = Field(default_factory=list, description="Задачи матча")
    created_at: datetime = Field(..., description="Время создания матча")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_match(cls, match: "Match") -> "MatchDetailResponse":  # noqa: F821
        """Конструкция из Match ORM-объекта с загруженными relationships."""
        player1 = OpponentInfo(
            id=match.player1.id,
            username=match.player1.username,
            rating=match.player1.rating,
        )

        player2: Optional[OpponentInfo] = None
        if match.player2 is not None:
            player2 = OpponentInfo(
                id=match.player2.id,
                username=match.player2.username,
                rating=match.player2.rating,
            )

        match_tasks: List[MatchTaskInfo] = []
        if match.tasks:
            match_tasks = [
                MatchTaskInfo.from_match_task(mt)
                for mt in sorted(match.tasks, key=lambda t: t.task_order)
            ]

        return cls(
            match_id=match.id,
            status=match.status.value,
            player1=player1,
            player2=player2,
            player1_score=match.player1_score,
            player2_score=match.player2_score,
            match_tasks=match_tasks,
            created_at=match.created_at,
        )


# ============================================================================
# Ответ на DELETE /api/pvp/find
# ============================================================================

class CancelResponse(BaseModel):
    """Ответ на отмену поиска матча."""

    cancelled: bool = Field(..., description="Был ли матч удалён")

    model_config = ConfigDict(from_attributes=False)
