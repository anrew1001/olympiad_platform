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


class MatchStatus(str, Enum):
    """
    Enum для статуса 1v1 матча.

    Наследуется от str для совместимости с SQLAlchemy Enum типом
    и правильной сериализации значений в БД и JSON.

    Статусы:
    - WAITING: матч ждёт второго игрока или начала
    - ACTIVE: матч идёт, игроки решают задачи
    - FINISHED: матч завершён, рассчитаны баллы и рейтинг
    - CANCELLED: матч отменён (кто-то вышел, произошла ошибка при начале)
    - ERROR: системная ошибка при выполнении матча
    """

    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ERROR = "error"

    def __str__(self) -> str:
        """Возвращает строковое значение статуса"""
        return self.value
