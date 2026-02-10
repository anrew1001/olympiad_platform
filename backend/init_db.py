#!/usr/bin/env python
"""
Скрипт инициализации БД - загружает данные перед стартом приложения.
Запускается один раз перед gunicorn.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select, func, delete

from app.database import async_session_maker, init_db
from app.models import Task, User
from app.utils.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_tasks_from_json() -> None:
    """Загружает задачи из JSON файла."""
    try:
        async with async_session_maker() as session:
            # Инициализируем БД
            await init_db()
            logger.info("✓ База данных инициализирована")

            # Проверяем нужна ли загрузка
            result = await session.execute(select(func.count(Task.title.distinct())))
            unique_count = result.scalar() or 0

            if unique_count >= 60:
                logger.info(f"✓ База содержит {unique_count} задач, загрузка пропущена")

                # Если есть дубли, удаляем их
                result = await session.execute(select(func.count(Task.id)))
                total = result.scalar() or 0
                if total > 60:
                    # Получаем все задачи и находим дубли
                    result = await session.execute(select(Task).order_by(Task.title, Task.id))
                    all_tasks = result.scalars().all()

                    titles_seen = set()
                    ids_to_delete = []
                    for task in all_tasks:
                        if task.title in titles_seen:
                            ids_to_delete.append(task.id)
                        else:
                            titles_seen.add(task.title)

                    if ids_to_delete:
                        await session.execute(delete(Task).where(Task.id.in_(ids_to_delete)))
                        await session.commit()
                        logger.info(f"✓ Удалены {len(ids_to_delete)} дубли, осталось 60 задач")
                return

            # Ищем JSON файл
            # __file__ = /app/init_db.py, поэтому parent = /app
            json_path = Path(__file__).parent / "data" / "tasks" / "grade10_mix.json"

            if not json_path.exists():
                logger.warning(f"⚠ Файл задач не найден: {json_path}")
                return

            # Загружаем JSON
            with open(json_path, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)

            # Добавляем все задачи
            tasks = []
            for task_data in tasks_data:
                task = Task(
                    subject=task_data.get("subject"),
                    topic=task_data.get("topic"),
                    difficulty=task_data.get("difficulty"),
                    title=task_data.get("title"),
                    text=task_data.get("text"),
                    answer=task_data.get("answer"),
                    hints=task_data.get("hints", [])
                )
                tasks.append(task)

            session.add_all(tasks)
            await session.commit()
            logger.info(f"✓ Загружено {len(tasks)} задач из {json_path.name}")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)


async def create_admin_user() -> None:
    """Создает админ пользователя если его еще нет."""
    try:
        async with async_session_maker() as session:
            # Проверяем существует ли уже админ
            result = await session.execute(select(User).where(User.username == "admin"))
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                logger.info(f"✓ Админ уже существует (ID: {existing_admin.id})")
                return

            # Создаем админа
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role="admin",
                rating=1500,
            )

            session.add(admin)
            await session.commit()
            logger.info("✓ Админ создан: admin / admin123")

    except Exception as e:
        logger.warning(f"⚠ Ошибка создания админа: {e}")


if __name__ == "__main__":
    asyncio.run(load_tasks_from_json())
    asyncio.run(create_admin_user())
    logger.info("✓ Инициализация завершена успешно!")
