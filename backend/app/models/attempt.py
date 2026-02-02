from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserTaskAttempt(Base):
    """
    Модель попытки решения задачи пользователем.

    Хранит историю всех попыток (как правильных, так и неправильных)
    для построения статистики и аналитики прогресса пользователя.
    """

    __tablename__ = "user_task_attempts"

    # Foreign key на пользователя (кто решал)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Индекс для быстрой фильтрации попыток пользователя
    )

    # Foreign key на задачу (что решал)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Индекс для фильтрации попыток по задаче
    )

    # Ответ пользователя (сохраняем для аналитики и возможного review)
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Правильность ответа
    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        index=True  # Индекс для быстрого подсчёта правильных ответов
    )

    # Композитные индексы для эффективных запросов статистики
    __table_args__ = (
        # Для запросов "все попытки пользователя по конкретной задаче"
        Index('ix_user_task_attempts_user_task', 'user_id', 'task_id'),
        # Для запросов "правильные попытки пользователя"
        Index('ix_user_task_attempts_user_correct', 'user_id', 'is_correct'),
        # Для запросов "последние попытки пользователя" (с сортировкой)
        Index('ix_user_task_attempts_user_created', 'user_id', 'created_at'),
    )
