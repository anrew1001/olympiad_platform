from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.config import settings
from app.models import Base


# Создание асинхронного двигателя для подключения к PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
)

# Фабрика для создания асинхронных сессий
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Функция для получения сессии БД (используется как dependency injection в FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД в endpoint'ах.

    Yields:
        AsyncSession: Асинхронная сессия для работы с БД
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Функция для инициализации БД (создание всех таблиц)
async def init_db() -> None:
    """
    Инициализирует базу данных путем создания всех таблиц,
    определенных в моделях через Base.metadata.
    """
    async with async_engine.begin() as conn:
        # Создаем все таблицы на основе определений моделей
        await conn.run_sync(Base.metadata.create_all)
