import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Enum as SAEnum, Index, DateTime, CheckConstraint, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MatchStatus(str, enum.Enum):
    # Используем нижний регистр для согласования с БД и server_default
    waiting = "waiting"
    active = "active"
    finished = "finished"
    cancelled = "cancelled"
    error = "error"


class Match(Base):
    """
    Модель PvP матча между двумя игроками.
    """
    __tablename__ = "matches"

    player1_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    player2_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, native_enum=False),
        default=MatchStatus.waiting,
        server_default=MatchStatus.waiting.value,
        nullable=False,
        index=True
    )

    player1_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False
    )

    player2_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False
    )

    winner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Изменение рейтинга. Храним для обоих игроков, так как Elo может давать разные дельты
    # (например, новичок получает больше за победу над мастером, чем мастер теряет).
    # Но по ТЗ было одно поле rating_change.
    # User Request: "Продумай хранение rating_change... Либо сделай схему, которая явно хранит изменение... либо опиши"
    # Решение: Добавляем отдельные поля для полной ясности.
    player1_rating_change: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Изменение рейтинга игрока 1 (может быть отрицательным)"
    )

    player2_rating_change: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Изменение рейтинга игрока 2 (может быть отрицательным)"
    )

    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    __table_args__ = (
        # Защита от self-match (игрок не может играть сам с собой)
        CheckConstraint('player1_id != player2_id', name='check_not_self_match'),
    )


class MatchTask(Base):
    """
    Связь матча и задачи. Определяет порядок задач в матче.
    """
    __tablename__ = "match_tasks"

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    __table_args__ = (
        # Индекс для быстрого получения задач матча в нужном порядке
        Index('ix_match_tasks_match_order', 'match_id', 'order'),
        # Уникальность задачи в матче (одна задача не может быть добавлена дважды)
        Index('ix_match_tasks_unique_task', 'match_id', 'task_id', unique=True),
        # Уникальность порядка (на одной позиции только одна задача)
        Index('ix_match_tasks_unique_order', 'match_id', 'order', unique=True),
    )


class MatchAnswer(Base):
    """
    Ответ пользователя на задачу в рамках матча.
    """
    __tablename__ = "match_answers"

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Используем Text для ответа, чтобы не было проблем с длинными строками (согласовано с UserTaskAttempt)
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )

    # Явное поле submitted_at по требованию ревью
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        # Уникальность ответа пользователя на конкретную задачу в конкретном матче
        # При повторной отправке делается UPSERT
        Index('ix_match_answers_unique_submission', 'match_id', 'user_id', 'task_id', unique=True),
    )
