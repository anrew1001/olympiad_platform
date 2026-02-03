"""
Скрипт для пересоздания таблиц в БД.
Используется для применения изменений в моделях во время разработки.
"""
import asyncio
from sqlalchemy import text

from app.database import async_engine
from app.models.base import Base
# Импортируем все модели, чтобы они зарегистрировались в metadata
from app.models import User, Task, UserTaskAttempt, UserAchievement, Match, MatchTask, MatchAnswer  # noqa: F401


async def recreate_tables():
    """Удаляет и создаёт заново все таблицы"""
    async with async_engine.begin() as conn:
        # Удаление всех таблиц
        print("Удаление существующих таблиц...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ Таблицы удалены")

        # Создание всех таблиц заново
        print("Создание таблиц...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Таблицы созданы успешно")


if __name__ == "__main__":
    print("Пересоздание таблиц БД...")
    asyncio.run(recreate_tables())
    print("Готово!")
