"""
Загрузка задач из grade10_mix.json в таблицу tasks.

Файл содержит 60 задач по трём предметам:
- informatics (20 задач)
- math (20 задач, будут загружены как "mathematics")
- physics (20 задач)

Запуск:
    cd backend
    python -m scripts.load_grade10_mix
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import and_, select

from app.database import async_session_maker
from app.models import Task


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "tasks" / "grade10_mix.json"
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

# Маппинг: "math" в JSON → "mathematics" в БД (для консистентности со схемой)
SUBJECT_MAPPING = {
    "informatics": "informatics",
    "math": "mathematics",
    "physics": "physics",
}

ALLOWED_SUBJECTS = set(SUBJECT_MAPPING.keys())


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
            raise ValueError(
                f"Задача #{idx} ({item.get('title', 'без названия')}): нет полей {sorted(missing)}"
            )

        # Проверка предмета
        subject = item["subject"]
        if subject not in ALLOWED_SUBJECTS:
            raise ValueError(
                f"Задача #{idx}: неизвестный subject '{subject}'. "
                f"Допустимые: {sorted(ALLOWED_SUBJECTS)}"
            )

        # Проверка сложности
        try:
            difficulty = int(item["difficulty"])
        except (ValueError, TypeError):
            raise ValueError(f"Задача #{idx}: difficulty должен быть целым числом")

        if difficulty < 1 or difficulty > 5:
            raise ValueError(f"Задача #{idx}: difficulty должен быть от 1 до 5")

        # Проверка hints
        hints = item["hints"]
        if not isinstance(hints, list) or not all(isinstance(h, str) for h in hints):
            raise ValueError(f"Задача #{idx}: hints должен быть массивом строк")

        # Объединяем текст с форматами и источником
        text = (
            f"{item['text']}\n\n"
            f"Формат ввода: {item['input_format']}\n"
            f"Формат вывода: {item['output_format']}\n"
            f"Источник: {item['source']}"
        )

        # Маппируем subject через словарь
        mapped_subject = SUBJECT_MAPPING[subject]

        tasks.append(
            {
                "subject": mapped_subject,
                "topic": item["topic"],
                "difficulty": difficulty,
                "title": item["title"],
                "text": text,
                "answer": item["answer"],
                "hints": hints,
            }
        )

    return tasks


async def load_grade10_mix_tasks() -> None:
    """Загружает задачи в БД, пропуская дубли."""
    tasks = load_tasks_from_json()

    async with async_session_maker() as session:
        created = 0
        skipped = 0

        for task_data in tasks:
            # Проверка дубликата по subject, topic, difficulty и title
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

    # Статистика по предметам
    stats_by_subject = {}
    for task in tasks:
        subject = task["subject"]
        stats_by_subject[subject] = stats_by_subject.get(subject, 0) + 1

    print("=" * 70)
    print("Загрузка задач grade10_mix завершена")
    print(f"Файл: {DATA_FILE}")
    print(f"Всего в JSON: {len(tasks)}")
    print(f"Добавлено: {created}")
    print(f"Пропущено (дубли): {skipped}")
    print("\nРазбор по предметам:")
    for subject in sorted(stats_by_subject.keys()):
        count = stats_by_subject[subject]
        print(f"  {subject:20s}: {count:3d} задач")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(load_grade10_mix_tasks())
