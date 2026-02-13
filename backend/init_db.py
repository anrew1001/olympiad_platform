#!/usr/bin/env python
"""
Скрипт инициализации БД - загружает данные перед стартом приложения.
Запускается один раз перед gunicorn.
"""
import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select, func, delete, text

from app.database import async_session_maker, init_db, async_engine
from app.models import Task, User
from app.utils.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def wait_for_db(max_retries: int = 30) -> bool:
    """Ждет пока БД будет готова к подключению."""
    for attempt in range(max_retries):
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✓ База данных готова!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"⏳ Попытка подключения {attempt + 1}/{max_retries}... (ошибка: {type(e).__name__})")
                await asyncio.sleep(1)
            else:
                logger.error(f"❌ Не удалось подключиться к БД после {max_retries} попыток")
                return False
    return False


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

            # Маппинг subject: "math" из JSON -> "mathematics" в БД (для консистентности с фронтенд dropdown)
            SUBJECT_MAPPING = {
                "informatics": "informatics",
                "math": "mathematics",  # JSON содержит "math", а фронтенд ожидает "mathematics"
                "physics": "physics",
            }

            # Добавляем все задачи
            tasks = []
            for task_data in tasks_data:
                raw_subject = task_data.get("subject")
                mapped_subject = SUBJECT_MAPPING.get(raw_subject, raw_subject)

                task = Task(
                    subject=mapped_subject,
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
        return False
    return True


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
                email="admin@gmail.com",
                hashed_password=hash_password("admin123"),
                role="admin",
                rating=1500,
            )

            session.add(admin)
            await session.commit()
            logger.info("✓ Админ создан: admin / admin123")

    except Exception as e:
        logger.warning(f"⚠ Ошибка создания админа: {e}")


async def main() -> None:
    """Main initialization function that runs both tasks in the same event loop."""
    # Сначала ждем пока БД будет готова
    if not await wait_for_db():
        logger.warning("⚠ БД не готова, пропускаем инициализацию")
        return

    await load_tasks_from_json()
    await create_admin_user()
    logger.info("✓ Инициализация завершена успешно!")


if __name__ == "__main__":
    asyncio.run(main())
