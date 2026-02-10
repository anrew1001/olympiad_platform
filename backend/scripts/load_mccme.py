"""
Загрузка задач в стиле informatics.mccme.ru из JSON в таблицу tasks.

Запуск:
    cd backend
    python -m scripts.load_mccme
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import and_, select

from app.database import async_session_maker
from app.models import Task


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "tasks" / "mccme_tasks.json"
REQUIRED_FIELDS = {
    "subject",
    "topic",
    "difficulty",
    "title",
    "text",
    "input_format",
    "output_format",
    "answer",
    "hints",
    "source",
}


def load_tasks_from_json() -> list[dict]:
    """Читает JSON и проверяет обязательные поля."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Файл не найден: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("Ожидается JSON-массив задач")

    tasks: list[dict] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Элемент #{idx} должен быть объектом")

        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            raise ValueError(f"Задача #{idx} ({item.get('title', 'без названия')}): нет полей {sorted(missing)}")

        if item["subject"] != "informatics":
            raise ValueError(f"Задача #{idx}: subject должен быть 'informatics'")

        difficulty = int(item["difficulty"])
        if difficulty < 1 or difficulty > 5:
            raise ValueError(f"Задача #{idx}: difficulty должен быть от 1 до 5")

        hints = item["hints"]
        if not isinstance(hints, list) or not all(isinstance(h, str) for h in hints):
            raise ValueError(f"Задача #{idx}: hints должен быть массивом строк")

        # В таблице tasks нет отдельных полей input/output/source,
        # поэтому сохраняем их в тексте условия в явном виде.
        text = (
            f"{item['text']}\n\n"
            f"Формат ввода: {item['input_format']}\n"
            f"Формат вывода: {item['output_format']}\n"
            f"Источник: {item['source']}"
        )

        tasks.append(
            {
                "subject": item["subject"],
                "topic": item["topic"],
                "difficulty": difficulty,
                "title": item["title"],
                "text": text,
                "answer": item["answer"],
                "hints": hints,
            }
        )

    return tasks


async def load_mccme_tasks() -> None:
    """Загружает задачи в БД, пропуская дубли."""
    tasks = load_tasks_from_json()

    async with async_session_maker() as session:
        created = 0
        skipped = 0

        for task_data in tasks:
            stmt = select(Task.id).where(
                and_(
                    Task.subject == task_data["subject"],
                    Task.topic == task_data["topic"],
                    Task.difficulty == task_data["difficulty"],
                    Task.title == task_data["title"],
                )
            )
            exists = (await session.execute(stmt)).scalar_one_or_none()

            if exists is not None:
                skipped += 1
                continue

            session.add(Task(**task_data))
            created += 1

        await session.commit()

    print("=" * 60)
    print("Загрузка задач MCCME завершена")
    print(f"Файл: {DATA_FILE}")
    print(f"Всего в JSON: {len(tasks)}")
    print(f"Добавлено: {created}")
    print(f"Пропущено (дубли): {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(load_mccme_tasks())
