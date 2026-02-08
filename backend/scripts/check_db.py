"""
Проверка состояния базы данных.

Запуск:
    cd backend
    python -m scripts.check_db
"""

import asyncio

from sqlalchemy import inspect, text
from app.database import async_engine, async_session_maker
from app.models import Base, Task


async def check_db() -> None:
    """Проверяет какие таблицы существуют в БД."""
    print("Проверка базы данных...\n")

    # Проверка таблиц
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result.fetchall()]

            print(f"Таблицы в БД: {tables if tables else 'не найдены'}")

            if "tasks" in tables:
                print(f"  → tasks: существует")
                result = await conn.execute(text("SELECT COUNT(*) FROM tasks"))
                count = result.scalar()
                print(f"    Задач в БД: {count}")
            else:
                print(f"  → tasks: НЕ СУЩЕСТВУЕТ")
    except Exception as e:
        print(f"  ✗ Ошибка при проверке: {e}")

    # Проверка модели
    print(f"\nМодели SQLAlchemy:")
    for table in Base.metadata.tables.values():
        print(f"  → {table.name}")


if __name__ == "__main__":
    asyncio.run(check_db())
