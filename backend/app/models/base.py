from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Базовый класс для всех моделей
class Base(DeclarativeBase):
    """
    Базовый декларативный класс для всех моделей SQLAlchemy.
    Содержит общие поля: id, created_at, updated_at.
    """

    # Первичный ключ с автоинкрементом
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Время создания записи (устанавливается автоматически на стороне БД)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )

    # Время последнего обновления записи (обновляется автоматически)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
