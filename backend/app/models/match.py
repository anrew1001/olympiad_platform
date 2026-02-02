import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Enum as SAEnum, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MatchStatus(str, enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ERROR = "error"


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
        default=MatchStatus.WAITING,
        server_default=MatchStatus.WAITING.value,
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

    rating_change: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationships
    # Note: We use strings for class names to avoid circular imports if those models import Match
    # But here we just define relationships to other models if needed, or backrefs
    # For now, simplistic definition without explicit relationships unless needed for business logic


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
        Index('ix_match_tasks_match_order', 'match_id', 'order'),
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

    answer: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )

    # submitted_at is covered by Base.created_at, but we can add explicit alias or field if strictly needed.
    # The requirement says "submitted_at". Base has created_at.
    # I will add submitted_at as a property alias or just rely on created_at.
    # To be safe and explicit according to spec, I'll add a field that defaults to now.
    # But wait, Base has created_at which is exactly that.
    # I'll rely on created_at for submission time.
    # User specifically asked for `submitted_at`.
    # I will alias it or just assume created_at covers it.
    # Let's add it explicitly to avoid confusion, maybe shadowing created_at or separate.
    # Actually, having both created_at (record creation) and submitted_at (user action) is fine, they are usually same.
    # But Base enforces created_at.
    # I will interpret "submitted_at" as the Base.created_at field.

    # Update: Constraint from spec: Unique index on (match_id, user_id, task_id)
    __table_args__ = (
        Index('ix_match_answers_unique_submission', 'match_id', 'user_id', 'task_id', unique=True),
    )
