from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class Task(Base):
    """
    Модель задачи для олимпиадной платформы.

    Содержит информацию о задаче: предмет, тема, сложность,
    условие, ответ и подсказки.
    """

    __tablename__ = "tasks"

    # Предмет (например, "informatics", "mathematics")
    subject: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # Индекс для фильтрации
    )

    # Тема внутри предмета (например, "algorithms", "graphs")
    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # Индекс для фильтрации
    )

    # Уровень сложности (1-5)
    difficulty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,  # Индекс для фильтрации
    )

    # Краткое название задачи
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Полный текст условия задачи
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # КРИТИЧНО: Правильный ответ (НЕ возвращается в API!)
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Подсказки в формате JSON массива строк
    # Пример: ["Подсказка 1", "Подсказка 2"]
    hints: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default='[]'
    )

    # Композитные индексы для эффективной фильтрации по нескольким полям
    __table_args__ = (
        Index('ix_tasks_subject_difficulty', 'subject', 'difficulty'),
        Index('ix_tasks_topic_difficulty', 'topic', 'difficulty'),
    )
