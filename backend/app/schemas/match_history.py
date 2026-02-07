"""
Pydantic-схемы для API истории PvP матчей пользователя.

Используются в endpoints:
- GET /api/users/me/matches - список с пагинацией
- GET /api/users/me/matches/{match_id} - детали
- GET /api/users/me/matches/stats - статистика
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Nested components
# ============================================================================

class OpponentInfo(BaseModel):
    """Информация о сопернике"""

    id: int = Field(..., description="ID пользователя")
    username: str = Field(..., description="Имя пользователя")
    rating: int = Field(..., description="Рейтинг пользователя")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GET /api/users/me/matches - Список истории с пагинацией
# ============================================================================

class MatchHistoryItem(BaseModel):
    """Элемент в списке истории матчей"""

    match_id: int = Field(..., description="ID матча")
    status: str = Field(..., description="Статус: finished, active, cancelled")
    result: Optional[str] = Field(
        None,
        description="Результат: won, lost, draw (None если не завершён)"
    )
    opponent: OpponentInfo = Field(..., description="Информация о сопернике")
    my_score: int = Field(..., description="Мой счёт")
    opponent_score: int = Field(..., description="Счёт соперника")
    my_rating_change: Optional[int] = Field(
        None,
        description="Изменение моего рейтинга (+15, -5, 0)"
    )
    finished_at: Optional[datetime] = Field(
        None,
        description="Время завершения (NULL если не завершён)"
    )
    created_at: datetime = Field(..., description="Время создания матча")

    model_config = ConfigDict(from_attributes=True)


class PaginatedMatchHistoryResponse(BaseModel):
    """Пагинированный ответ со списком матчей"""

    items: List[MatchHistoryItem] = Field(..., description="Список матчей")
    total: int = Field(..., description="Всего матчей")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Элементов на странице")
    pages: int = Field(..., description="Всего страниц")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GET /api/users/me/matches/{match_id} - Детали матча
# ============================================================================

class TaskSolutionInfo(BaseModel):
    """Информация о решении одной задачи в матче"""

    task_id: int = Field(..., description="ID задачи")
    title: str = Field(..., description="Название задачи")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность 1-5")
    order: int = Field(..., description="Порядок в матче (1-5)")
    solved_by_me: bool = Field(..., description="Решил ли я эту задачу")
    solved_by_opponent: bool = Field(..., description="Решил ли соперник")
    my_answer_time: Optional[datetime] = Field(
        None,
        description="Когда я отправил ответ"
    )
    opponent_answer_time: Optional[datetime] = Field(
        None,
        description="Когда соперник отправил ответ"
    )

    model_config = ConfigDict(from_attributes=True)


class MatchDetailResponse(BaseModel):
    """Полная информация о конкретном матче"""

    match_id: int = Field(..., description="ID матча")
    status: str = Field(..., description="Статус матча")
    result: Optional[str] = Field(
        None,
        description="Результат: won, lost, draw"
    )
    opponent: OpponentInfo = Field(..., description="Информация о сопернике")
    my_score: int = Field(..., description="Мой счёт")
    opponent_score: int = Field(..., description="Счёт соперника")
    my_rating_change: Optional[int] = Field(
        None,
        description="Изменение моего рейтинга"
    )
    tasks: List[TaskSolutionInfo] = Field(
        default_factory=list,
        description="Список задач с информацией о решениях"
    )
    finished_at: Optional[datetime] = Field(
        None,
        description="Время завершения"
    )
    created_at: datetime = Field(..., description="Время создания")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GET /api/users/me/matches/stats - Статистика и график рейтинга
# ============================================================================

class RatingHistoryPoint(BaseModel):
    """Точка на графике истории рейтинга"""

    match_id: int = Field(..., description="ID матча")
    rating: int = Field(..., description="Рейтинг после матча")
    rating_change: int = Field(..., description="Изменение рейтинга (+15, -5, 0)")
    created_at: datetime = Field(..., description="Время завершения матча")

    model_config = ConfigDict(from_attributes=True)


class TopicStats(BaseModel):
    """Статистика по одной теме для анализа сильных/слабых сторон"""

    topic: str = Field(..., description="Название темы (например, 'algorithms', 'graphs')")
    success_rate: float = Field(
        ..., ge=0, le=100, description="Процент правильных ответов (0-100)"
    )
    attempts: int = Field(..., ge=3, description="Количество попыток (минимум 3)")

    model_config = ConfigDict(from_attributes=True)


class MatchStatsResponse(BaseModel):
    """Общая статистика и история рейтинга пользователя"""

    total_matches: int = Field(..., description="Всего сыграно матчей")
    won: int = Field(..., description="Побед")
    lost: int = Field(..., description="Поражений")
    draw: int = Field(..., description="Ничьих")
    win_rate: float = Field(..., description="Процент побед (0-100)")
    rating_history: List[RatingHistoryPoint] = Field(
        default_factory=list,
        description="История рейтинга (последние 50 матчей в порядке возрастания даты)"
    )
    current_streak: int = Field(
        default=0,
        description=(
            "Текущая серия результатов: "
            "положительное = побед подряд, отрицательное = поражений подряд, 0 = нет серии"
        ),
    )
    best_win_streak: int = Field(
        default=0,
        ge=0,
        description="Максимальная серия побед за всё время",
    )
    strongest_topics: List[TopicStats] = Field(
        default_factory=list,
        description="Топ-3 темы с лучшим процентом правильных ответов",
    )
    weakest_topics: List[TopicStats] = Field(
        default_factory=list,
        description="Топ-3 темы с худшим процентом правильных ответов",
    )

    model_config = ConfigDict(from_attributes=True)
