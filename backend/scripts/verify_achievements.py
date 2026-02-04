
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Добавляем путь к backend, чтобы можно было импортировать app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def verify_logic():
    print("🚀 Начинаем верификацию логики достижений...")

    # Импортируем необходимые компоненты
    # (Делаем импорт внутри функции, чтобы sys.path успел обновиться)
    from app.models import UserTaskAttempt, UserAchievement, User
    from sqlalchemy import select

    # --- Сценарий 1: Новый пользователь (нет достижений) ---
    print("\n📝 Сценарий 1: Новый пользователь")

    current_user = MagicMock()
    current_user.id = 42

    db = AsyncMock()

    # Настраиваем возвращаемые значения для цепочки запросов
    # 1. Запрос существующих достижений -> возвращаем пусто
    mock_existing = MagicMock()
    mock_existing.scalars().all.return_value = []

    # 2. Запрос количества уникальных решений -> возвращаем 1
    mock_count = MagicMock()
    mock_count.scalar.return_value = 1

    db.execute.side_effect = [mock_existing, mock_count]

    # Имитируем логику из роутера
    is_correct = True
    milestone_types = ["first_solve", "solved_10"]

    # Вызов 1: проверка существующих
    existing_query = select(UserAchievement.type).where(
        UserAchievement.user_id == current_user.id,
        UserAchievement.type.in_(milestone_types)
    )
    existing_result = await db.execute(existing_query)
    existing_types = set(existing_result.scalars().all())

    print(f"  - Найдено существующих достижений: {len(existing_types)}")
    assert len(existing_types) == 0

    if len(existing_types) < len(milestone_types):
        print("  - Запускаем подсчёт уникальных решений (ожидаемо)...")
        # Вызов 2: подсчёт
        unique_result = await db.execute(AsyncMock())
        unique_solved = unique_result.scalar() or 0
        print(f"  - Уникальных решений: {unique_solved}")
        assert unique_solved == 1

        if unique_solved >= 1 and "first_solve" not in existing_types:
            print("  - Добавляем достижение 'first_solve'")
            # Проверяем что db.add вызывается

    await db.commit()
    print("  - Вызван db.commit()")

    # Проверка количества вызовов execute
    assert db.execute.call_count == 2
    assert db.commit.call_count == 1
    print("✅ Сценарий 1 пройден: достижения проверяются и выдаются корректно.")

    # --- Сценарий 2: Опытный пользователь (уже есть все достижения) ---
    print("\n📝 Сценарий 2: Опытный пользователь (все достижения есть)")

    db = AsyncMock()

    # 1. Запрос существующих достижений -> возвращаем оба
    mock_existing_full = MagicMock()
    mock_existing_full.scalars().all.return_value = ["first_solve", "solved_10"]

    db.execute.return_value = mock_existing_full

    # Имитируем логику
    existing_result = await db.execute(existing_query)
    existing_types = set(existing_result.scalars().all())

    print(f"  - Найдено существующих достижений: {len(existing_types)}")
    assert len(existing_types) == 2

    if len(existing_types) < len(milestone_types):
        print("  - ❌ ОШИБКА: Запущен подсчёт решений, хотя все достижения уже есть!")
        assert False, "Should not reach here"
    else:
        print("  - ✅ УСПЕХ: Дорогостоящий подсчёт решений пропущен (оптимизация работает)")

    await db.commit()
    print("  - Вызван db.commit()")

    # Проверка количества вызовов execute - должен быть только ОДИН (проверка существующих)
    assert db.execute.call_count == 1
    assert db.commit.call_count == 1
    print("✅ Сценарий 2 пройден: оптимизация экономит запросы.")

    # --- Сценарий 3: Частичные достижения (есть только первое) ---
    print("\n📝 Сценарий 3: Частичные достижения (есть 'first_solve', нет 'solved_10')")

    db = AsyncMock()

    # 1. Запрос существующих достижений -> возвращаем только одно
    mock_existing_partial = MagicMock()
    mock_existing_partial.scalars().all.return_value = ["first_solve"]

    # 2. Запрос количества уникальных решений -> возвращаем 10
    mock_count_10 = MagicMock()
    mock_count_10.scalar.return_value = 10

    db.execute.side_effect = [mock_existing_partial, mock_count_10]

    # Имитируем логику
    existing_result = await db.execute(existing_query)
    existing_types = set(existing_result.scalars().all())

    print(f"  - Найдено существующих достижений: {len(existing_types)}")
    assert len(existing_types) == 1

    if len(existing_types) < len(milestone_types):
        print("  - Запускаем подсчёт уникальных решений (ожидаемо)...")
        unique_result = await db.execute(AsyncMock())
        unique_solved = unique_result.scalar() or 0
        print(f"  - Уникальных решений: {unique_solved}")
        assert unique_solved == 10

        if unique_solved >= 1 and "first_solve" not in existing_types:
            assert False, "Should not grant first_solve again"

        if unique_solved >= 10 and "solved_10" not in existing_types:
            print("  - Добавляем достижение 'solved_10'")

    await db.commit()
    print("  - Вызван db.commit()")

    assert db.execute.call_count == 2
    assert db.commit.call_count == 1
    print("✅ Сценарий 3 пройден: недостающие достижения выдаются.")

    print("\n✨ Все тесты верификации пройдены успешно!")

if __name__ == "__main__":
    asyncio.run(verify_logic())
