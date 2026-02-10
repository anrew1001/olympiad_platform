from pydantic import BaseModel, ConfigDict, Field


class AdminStatsResponse(BaseModel):
    """
    Полная статистика платформы для админ панели.

    Включает общее количество пользователей, задач, попыток решений,
    а также дополнительные метрики для мониторинга состояния платформы.
    """

    # Основные метрики
    total_users: int = Field(
        ...,
        ge=0,
        description="Общее количество зарегистрированных пользователей",
    )
    total_tasks: int = Field(
        ..., ge=0, description="Общее количество задач на платформе"
    )
    total_attempts: int = Field(
        ..., ge=0, description="Общее количество попыток решения задач"
    )

    # Дополнительные метрики (опционально для улучшенной версии)
    total_correct_attempts: int = Field(
        default=0, ge=0, description="Количество правильных решений"
    )
    platform_accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Общая точность решений на платформе (%)",
    )
    active_users_today: int = Field(
        default=0, ge=0, description="Количество активных пользователей за сегодня"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_users": 150,
                    "total_tasks": 42,
                    "total_attempts": 1523,
                    "total_correct_attempts": 987,
                    "platform_accuracy": 64.8,
                    "active_users_today": 23,
                }
            ]
        }
    )
