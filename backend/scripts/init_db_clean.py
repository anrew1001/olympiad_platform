"""
Инициализация БД с очисткой пула соединений.

Запуск:
    cd backend
    python -m scripts.init_db_clean
"""

import asyncio
import sys

from sqlalchemy import text
from app.database import async_engine, async_session_maker
from app.models import Base


async def main() -> None:
    """Инициализирует БД с правильным управлением пулом."""
    print("Инициализация БД...\n")

    # Проверка и создание таблиц
    async with async_engine.begin() as conn:
        # 1. Проверяем существующие таблицы
        try:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            existing = sorted(row[0] for row in result.fetchall())

            if existing:
                print(f"✓ База уже инициализирована!")
                print(f"  Таблицы: {', '.join(existing)}\n")
                return
        except Exception as e:
            print(f"⚠ Ошибка при проверке таблиц: {e}\n")

        # 2. Создаём таблицы
        print("Создание таблиц...\n")
        try:
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Таблицы успешно созданы!\n")
        except Exception as e:
            print(f"✗ Ошибка при создании: {e}\n")
            sys.exit(1)

    # 3. Финальная проверка
    async with async_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = sorted(row[0] for row in result.fetchall())
        print(f"✓ Инициализация завершена!")
        print(f"  Таблицы: {', '.join(tables)}\n")

    # Закрываем пул соединений
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
