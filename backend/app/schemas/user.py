from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Схема для создания нового пользователя
class UserCreate(BaseModel):
    """
    Схема для получения данных при создании нового пользователя.
    Содержит только необходимые поля для регистрации.
    Включает валидацию длины полей и формата email.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Имя пользователя (минимум 3 символа)"
    )
    email: EmailStr = Field(
        ...,
        description="Email пользователя (должен быть валидным)"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Пароль (минимум 6 символов, максимум 72 байта)"
    )

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        """Проверяет что пароль не превышает 72 байта в UTF-8"""
        byte_length = len(v.encode('utf-8'))
        if byte_length > 72:
            raise ValueError(
                f'Пароль слишком длинный ({byte_length} байт). '
                f'Максимум 72 байта (ограничение bcrypt)'
            )
        return v


# Схема для ответа пользователя из API
class UserResponse(BaseModel):
    """
    Схема для возврата данных пользователя в API ответах.
    Не содержит чувствительную информацию (пароль).
    """

    id: int
    username: str
    email: str
    rating: int
    role: str
    created_at: datetime

    # Конфигурация для работы с ORM моделями (from_attributes)
    model_config = ConfigDict(from_attributes=True)


# === Схемы для аутентификации ===

class LoginRequest(BaseModel):
    """
    Схема запроса на вход в систему.

    Используем email как идентификатор пользователя для входа.
    Пароль передается в открытом виде через HTTPS и проверяется
    с помощью bcrypt.checkpw() на сервере.
    """
    email: EmailStr = Field(
        ...,
        description="Email пользователя для входа"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Пароль пользователя"
    )


class TokenResponse(BaseModel):
    """
    Схема ответа с JWT токеном.

    Возвращается после успешной аутентификации (POST /api/auth/login).
    Клиент должен сохранить access_token и передавать его в заголовке
    Authorization: Bearer <access_token> для доступа к защищенным эндпоинтам.
    """
    access_token: str = Field(
        ...,
        description="JWT access токен для аутентификации запросов"
    )
    token_type: str = Field(
        default="bearer",
        description="Тип токена (всегда 'bearer' согласно OAuth2)"
    )
