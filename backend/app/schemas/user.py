from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Схема для создания нового пользователя
class UserCreate(BaseModel):
    """
    Схема для получения данных при создании нового пользователя.
    Содержит только необходимые поля для регистрации.
    """

    username: str
    email: str
    password: str


# Схема для ответа пользователя из API
class UserResponse(BaseModel):
    """
    Схема для возврата данных пользователя в API ответах.
    Не содержит чувствительную информацию (пароль).
    """

    id: int
    username: str
    email: str
    created_at: datetime

    # Конфигурация для работы с ORM моделями (from_attributes)
    model_config = ConfigDict(from_attributes=True)
