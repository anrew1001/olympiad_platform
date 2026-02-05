from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    ForeignKey,
    Index,
    Text,
    CheckConstraint,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import MatchStatus


class Match(Base):
    """
    Модель 1v1 матча между двумя игроками.
    Хранит состояние матча, баллы, результат и историю рейтинга.
    """

    __tablename__ = "matches"

    # Первый игрок матча
    player1_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Второй игрок матча
    player2_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Статус матча: waiting, active, finished, cancelled, error
    # SAEnum(MatchStatus, native_enum=False) генерирует VARCHAR + CHECK на PostgreSQL
    # values_callable нужен чтобы хранить .value ("waiting") а не .name ("WAITING")
    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(
            MatchStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=MatchStatus.WAITING,
        server_default=MatchStatus.WAITING.value,
        nullable=False,
        index=True,
    )

    # Количество баллов игрока 1 (сумма за правильные ответы)
    player1_score: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    # Количество баллов игрока 2
    player2_score: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    # Победитель матча (nullable, заполняется когда матч finished)
    winner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Изменение рейтинга для игрока 1 (после окончания матча)
    # Положительное — рейтинг вырос, отрицательное — упал
    player1_rating_change: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Изменение рейтинга для игрока 2
    player2_rating_change: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Время окончания матча (nullable, заполняется когда статус меняется на finished/cancelled)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # ===== Relationships =====

    # Задачи в этом матче (коллекция)
    # lazy="selectin" — async-safe: загружает MatchTask одним IN-query после загрузки Match
    # cascade="all, delete-orphan" — удаляет MatchTask если Match удалён
    # passive_deletes=True — опирается на DB-level CASCADE, не загружает детей перед DELETE
    tasks: Mapped[List["MatchTask"]] = relationship(
        "MatchTask",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Ответы игроков на задачи в матче (коллекция)
    answers: Mapped[List["MatchAnswer"]] = relationship(
        "MatchAnswer",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Игрок 1 (many-to-one)
    # lazy="joined" — async-safe: выполняет JOIN в основном query
    # foreign_keys=[player1_id] необходим потому что есть 3 FK на users.id
    player1: Mapped["User"] = relationship(
        "User",
        foreign_keys=[player1_id],
        lazy="joined",
    )

    # Игрок 2
    player2: Mapped["User"] = relationship(
        "User",
        foreign_keys=[player2_id],
        lazy="joined",
    )

    # Победитель матча (nullable relationship)
    winner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[winner_id],
        lazy="joined",
    )

    __table_args__ = (
        # CHECK: не может быть матча человека с самим собой
        CheckConstraint(
            "player1_id != player2_id",
            name="ck_matches_players_different",
        ),
        # Индексы для типичных запросов
        Index("ix_matches_player1_status", "player1_id", "status"),
        Index("ix_matches_player2_status", "player2_id", "status"),
        Index("ix_matches_status_created", "status", "created_at"),
    )


class MatchTask(Base):
    """
    Модель задачи в матче.
    Связывает матч с задачей и указывает её порядок.
    """

    __tablename__ = "match_tasks"

    # Матч, к которому относится задача
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Задача (которую нужно решить)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Порядковый номер задачи в матче (1, 2, 3, ...)
    # Нет default/server_default — устанавливается явно при создании
    task_order: Mapped[int] = mapped_column(nullable=False)

    # ===== Relationships =====

    # Матч, к которому относится эта задача
    # back_populates="tasks" создаёт двусторонний link с Match.tasks
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="tasks",
        lazy="joined",
    )

    # Сама задача (справочная информация)
    task: Mapped["Task"] = relationship(
        "Task",
        lazy="joined",
    )

    __table_args__ = (
        # Уникальность по (match_id, task_order): одна позиция в матче
        Index(
            "ix_match_tasks_match_order",
            "match_id",
            "task_order",
            unique=True,
        ),
        # Уникальность по (match_id, task_id): одна задача в матче
        # Независимое ограничение от предыдущего
        Index(
            "ix_match_tasks_match_task",
            "match_id",
            "task_id",
            unique=True,
        ),
    )


class MatchAnswer(Base):
    """
    Модель ответа игрока на задачу в матче.
    Хранит текст ответа и результат проверки.

    UPSERT pattern: (match_id, user_id, task_id) — UNIQUE ключ.
    При повторной отправке ответа: SELECT, UPDATE existing row вместо INSERT нового.
    """

    __tablename__ = "match_answers"

    # Матч
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Игрок, который отправил ответ
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Задача, на которую ответили
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Текст ответа, предоставленный игроком
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Правильность ответа (устанавливается сравнением с task.answer или системой проверки)
    is_correct: Mapped[bool] = mapped_column(nullable=False)

    # Время последней отправки ответа
    # server_default: при INSERT устанавливается БД
    # onupdate: при ORM-level UPDATE SQLAlchemy вызывает func.now()
    # Важно: onupdate работает только через ORM, не через raw execute(update(...))
    submitted_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ===== Relationships =====

    # Матч
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="answers",
        lazy="joined",
    )

    # Игрок
    user: Mapped["User"] = relationship(
        "User",
        lazy="joined",
    )

    # Задача
    task: Mapped["Task"] = relationship(
        "Task",
        lazy="joined",
    )

    __table_args__ = (
        # УНИКАЛЬНЫЙ ключ для UPSERT: один ответ на одну задачу одного игрока в матче
        Index(
            "ix_match_answers_match_user_task",
            "match_id",
            "user_id",
            "task_id",
            unique=True,
        ),
        # Вспомогательный индекс: все ответы одного игрока в матче
        Index("ix_match_answers_match_user", "match_id", "user_id"),
    )
