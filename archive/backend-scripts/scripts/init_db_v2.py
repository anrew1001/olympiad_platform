"""
Инициализация БД v2 - прямое создание таблиц.

Запуск:
    cd backend
    python scripts/init_db_v2.py
"""

import asyncio
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Используем синхронный движок для избежания проблем с пулом
DATABASE_URL = "postgresql://olympiad:olympiad@localhost:5432/olympiad"
engine = create_engine(DATABASE_URL, poolclass=NullPool)


def init_db_sync() -> None:
    """Создаёт все таблицы синхронно."""
    print("Инициализация БД (синхронный режим)...\n")

    # Проверка существующих таблиц
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        existing = sorted(row[0] for row in result.fetchall())

        if existing:
            print(f"Найдено таблиц: {', '.join(existing)}")
            print("База уже инициализирована!\n")
            return

        # Импортируем модели и создаём таблицы
        from app.database import Base

        print("Создание таблиц...\n")
        try:
            # Используем синхронный engine
            Base.metadata.create_all(engine)
            print("✓ Таблицы успешно созданы!\n")
        except Exception as e:
            print(f"✗ Ошибка: {e}\n")
            sys.exit(1)

        # Финальная проверка
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = sorted(row[0] for row in result.fetchall())
        print(f"✓ Инициализация завершена!")
        print(f"  Таблицы: {', '.join(tables)}\n")


if __name__ == "__main__":
    init_db_sync()
