"""
Pydantic схемы для таблицы лидеров (leaderboard).

Включает модели для одной позиции в рейтинге и полного ответа API.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LeaderboardEntry(BaseModel):
    """
    Одна позиция в таблице лидеров.

    Содержит информацию об игроке, его рейтинге и статистике побед.
    """

    position: int = Field(
        ...,
        ge=1,
        description="Место в рейтинге (1 = лучший)"
    )
    user_id: int = Field(
        ...,
        description="ID пользователя"
    )
    username: str = Field(
        ...,
        description="Имя пользователя"
    )
    rating: int = Field(
        ...,
        ge=0,
        description="Рейтинг игрока"
    )
    matches_played: int = Field(
        ...,
        ge=0,
        description="Количество завершённых матчей"
    )
    wins: int = Field(
        ...,
        ge=0,
        description="Количество побед"
    )
    win_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Процент побед (0-100)"
    )
    is_current_user: bool = Field(
        default=False,
        description="Это текущий авторизованный пользователь"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "position": 1,
                    "user_id": 1,
                    "username": "champion",
                    "rating": 1250,
                    "matches_played": 15,
                    "wins": 12,
                    "win_rate": 80.0,
                    "is_current_user": False
                }
            ]
        }
    )


class LeaderboardResponse(BaseModel):
    """
    Ответ API с таблицей лидеров.

    Содержит список топ игроков и отдельно позицию текущего пользователя,
    если тот не входит в топ N.
    """

    entries: List[LeaderboardEntry] = Field(
        ...,
        description="Список записей таблицы лидеров (отсортирован по рейтингу)"
    )
    total_users: int = Field(
        ...,
        ge=0,
        description="Общее количество пользователей в рейтинге (с хотя бы одним матчем)"
    )
    current_user_entry: Optional[LeaderboardEntry] = Field(
        None,
        description="Запись текущего пользователя (если не входит в топ N)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entries": [
                        {
                            "position": 1,
                            "user_id": 1,
                            "username": "champion",
                            "rating": 1250,
                            "matches_played": 15,
                            "wins": 12,
                            "win_rate": 80.0,
                            "is_current_user": False
                        }
                    ],
                    "total_users": 42,
                    "current_user_entry": None
                }
            ]
        }
    )
