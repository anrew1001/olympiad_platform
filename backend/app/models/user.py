from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# Модель пользователя олимпиадной платформы
class User(Base):
    """
    Модель пользователя с основной информацией для аутентификации
    и идентификации на платформе.
    """

    __tablename__ = "users"

    # Уникальное имя пользователя для входа
    username: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False
    )

    # Электронная почта пользователя
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False
    )

    # Хеш пароля пользователя (не хранится в открытом виде)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    # Рейтинг пользователя на платформе (по умолчанию 1000)
    rating: Mapped[int] = mapped_column(
        default=1000,
        server_default="1000",
        nullable=False
    )

    # Роль пользователя (user, admin, moderator)
    role: Mapped[str] = mapped_column(
        default="user",
        server_default="user",
        index=True,
        nullable=False
    )
