"""
Инициализация базы данных - создание всех таблиц.

Запуск:
    cd backend
    python -m scripts.init_db
"""

import asyncio

from sqlalchemy import text
from app.database import init_db, async_engine


async def main() -> None:
    """Создаёт все таблицы в БД."""
    print("Инициализация БД...\n")

    # Сначала проверим, какие таблицы уже существуют
    async with async_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        existing = set(row[0] for row in result.fetchall())

    if existing:
        print(f"Найдено существующих таблиц: {sorted(existing)}")
        print("Пропускаем инициализацию (таблицы уже созданы)\n")
    else:
        print("Таблицы не найдены, создаём...\n")
        try:
            await init_db()
            print("✓ Все таблицы созданы!\n")
        except Exception as e:
            print(f"⚠ Ошибка при создании таблиц: {e}\n")
            print("Пытаемся создать только отсутствующие таблицы...\n")

    # Финальная проверка
    async with async_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        final_tables = sorted(row[0] for row in result.fetchall())

    if final_tables:
        print(f"✓ База данных готова!")
        print(f"  Таблицы: {', '.join(final_tables)}")
    else:
        print("✗ Ошибка: таблицы так и не были созданы")


if __name__ == "__main__":
    asyncio.run(main())
