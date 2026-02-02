from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


# === Схема для статистики по уровню сложности ===

class DifficultyStats(BaseModel):
    """
    Статистика решений по уровню сложности.

    Показывает количество уникальных решённых задач
    и общее количество попыток для каждого уровня.
    """

    difficulty: int = Field(
        ...,
        ge=1,
        le=5,
        description="Уровень сложности (1-5)"
    )
    solved: int = Field(
        ...,
        ge=0,
        description="Количество уникальных решённых задач на этом уровне"
    )
    total_attempts: int = Field(
        ...,
        ge=0,
        description="Общее количество попыток на этом уровне"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "difficulty": 1,
                    "solved": 5,
                    "total_attempts": 8
                }
            ]
        }
    )


# === Схема для элемента недавней активности ===

class RecentActivityItem(BaseModel):
    """
    Элемент недавней активности пользователя.

    Показывает одну попытку решения задачи с её результатом и деталями.
    """

    task_id: int = Field(
        ...,
        description="ID задачи"
    )
    task_title: str = Field(
        ...,
        description="Название задачи"
    )
    task_difficulty: int = Field(
        ...,
        ge=1,
        le=5,
        description="Сложность задачи"
    )
    is_correct: bool = Field(
        ...,
        description="Правильно ли была решена задача"
    )
    created_at: datetime = Field(
        ...,
        description="Время попытки"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "task_id": 2,
                    "task_title": "Площадь треугольника",
                    "task_difficulty": 2,
                    "is_correct": True,
                    "created_at": "2026-01-31T20:30:00"
                }
            ]
        }
    )


# === Схема для элемента достижения ===

class AchievementItem(BaseModel):
    """
    Элемент достижения пользователя.

    Содержит информацию о полученном достижении и времени получения.
    """

    type: str = Field(
        ...,
        description="Уникальный тип достижения (first_solve, solved_10, etc.)"
    )
    title: str = Field(
        ...,
        description="Название достижения"
    )
    description: str = Field(
        ...,
        description="Описание достижения"
    )
    unlocked_at: datetime = Field(
        ...,
        description="Дата и время получения достижения"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "type": "first_solve",
                    "title": "Первый успех",
                    "description": "Решена первая задача на платформе",
                    "unlocked_at": "2026-01-30T14:22:00"
                }
            ]
        }
    )


# === Главная схема ответа со статистикой ===

class UserStatsResponse(BaseModel):
    """
    Полная статистика пользователя по решению задач.

    Включает общую статистику, разбивку по сложности,
    последнюю активность и полученные достижения.
    """

    # Общая статистика
    total_attempts: int = Field(
        ...,
        ge=0,
        description="Общее количество попыток"
    )
    correct_attempts: int = Field(
        ...,
        ge=0,
        description="Количество правильных ответов"
    )
    accuracy: float = Field(
        ...,
        ge=0,
        le=100,
        description="Процент правильных ответов (0-100)"
    )
    unique_solved: int = Field(
        ...,
        ge=0,
        description="Количество уникальных решённых задач"
    )

    # Статистика по сложности
    by_difficulty: List[DifficultyStats] = Field(
        default=[],
        description="Статистика по уровням сложности"
    )

    # Недавняя активность
    recent_activity: List[RecentActivityItem] = Field(
        default=[],
        max_length=10,
        description="Последние 10 попыток решения"
    )

    # Достижения
    achievements: List[AchievementItem] = Field(
        default=[],
        description="Полученные достижения"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_attempts": 15,
                    "correct_attempts": 12,
                    "accuracy": 80.0,
                    "unique_solved": 8,
                    "by_difficulty": [
                        {
                            "difficulty": 1,
                            "solved": 3,
                            "total_attempts": 5
                        },
                        {
                            "difficulty": 2,
                            "solved": 3,
                            "total_attempts": 6
                        }
                    ],
                    "recent_activity": [
                        {
                            "task_id": 2,
                            "task_title": "Площадь треугольника",
                            "task_difficulty": 2,
                            "is_correct": True,
                            "created_at": "2026-01-31T20:30:00"
                        }
                    ],
                    "achievements": [
                        {
                            "type": "first_solve",
                            "title": "Первый успех",
                            "description": "Решена первая задача на платформе",
                            "unlocked_at": "2026-01-30T14:22:00"
                        }
                    ]
                }
            ]
        }
    )
