from enum import Enum


class UserRole(str, Enum):
    """
    Enum для ролей пользователей в системе.

    Наследуется от str для совместимости с SQLAlchemy String полем
    и автоматической сериализации в JSON через Pydantic.
    """

    USER = "user"
    ADMIN = "admin"
    # Для будущего расширения:
    # MODERATOR = "moderator"

    def __str__(self) -> str:
        """Возвращает строковое значение роли"""
        return self.value
