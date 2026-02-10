from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserAchievement(Base):
    """
    Модель достижения пользователя.

    Система геймификации для мотивации пользователей.
    Хранит достижения, полученные пользователем при решении задач.
    """

    __tablename__ = "user_achievements"

    # Foreign key на пользователя (владелец достижения)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Индекс для получения всех достижений пользователя
    )

    # Уникальный тип достижения ("first_solve", "solved_10", etc.)
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True  # Индекс для поиска по типу
    )

    # Отображаемое название достижения
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    # Описание достижения
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Композитный уникальный индекс: один тип достижения на пользователя
    __table_args__ = (
        Index('ix_user_achievements_user_type', 'user_id', 'type', unique=True),
    )
