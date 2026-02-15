"""
Демонстрационные запросы для системы PvP матчей.

Показывает типичные операции:
1. Создание матча
2. Добавление задач в матч
3. Отправка ответов (UPSERT pattern)
4. Поиск активных матчей
5. Завершение матча с расчетом рейтинга
6. Получение истории матчей игрока

Примечание: Требует работающей базы данных!
Запуск: python demo_match_queries.py
"""
import asyncio
from datetime import datetime
from sqlalchemy import select, and_, or_

from app.database import async_session_maker
from app.models import (
    Match,
    MatchTask,
    MatchAnswer,
    MatchStatus,
    User,
    Task,
)


async def demo_create_match(session):
    """Демо 1: Создание нового матча"""
    print("\n" + "=" * 60)
    print("ДЕМО 1: Создание нового матча")
    print("=" * 60)

    # Получаем двух игроков
    result = await session.execute(select(User).limit(2))
    users = result.scalars().all()
    if len(users) < 2:
        print("⚠ Нужно минимум 2 игрока. Создаём тестовых пользователей...")
        user1 = User(
            username="alice",
            email="alice@example.com",
            hashed_password="hashed",
            rating=1200,
        )
        user2 = User(
            username="bob",
            email="bob@example.com",
            hashed_password="hashed",
            rating=1100,
        )
        session.add_all([user1, user2])
        await session.commit()
        users = [user1, user2]

    user1, user2 = users[0], users[1]

    # Создаём матч
    match = Match(
        player1_id=user1.id,
        player2_id=user2.id,
        status=MatchStatus.WAITING,
    )
    session.add(match)
    await session.commit()

    print(f"\n✓ Создан матч:")
    print(f"  ID: {match.id}")
    print(f"  Игрок 1: {user1.username} (рейтинг {user1.rating})")
    print(f"  Игрок 2: {user2.username} (рейтинг {user2.rating})")
    print(f"  Статус: {match.status}")
    print(f"  Создан: {match.created_at.isoformat()}")

    return match.id, user1.id, user2.id


async def demo_add_tasks(session, match_id):
    """Демо 2: Добавление задач в матч"""
    print("\n" + "=" * 60)
    print("ДЕМО 2: Добавление задач в матч")
    print("=" * 60)

    # Получаем или создаём задачи
    result = await session.execute(select(Task).limit(3))
    tasks = result.scalars().all()

    if len(tasks) < 3:
        print("⚠ Нужно минимум 3 задачи. Создаём...")
        tasks_to_create = [
            Task(
                subject="informatics",
                topic="algorithms",
                difficulty=3,
                title="Сортировка",
                text="Отсортируйте массив",
                answer="O(n log n)",
                hints=[],
            ),
            Task(
                subject="informatics",
                topic="graphs",
                difficulty=4,
                title="Графы",
                text="Найдите путь",
                answer="BFS",
                hints=[],
            ),
            Task(
                subject="mathematics",
                topic="geometry",
                difficulty=2,
                title="Геометрия",
                text="Найдите площадь",
                answer="a*h/2",
                hints=[],
            ),
        ]
        session.add_all(tasks_to_create)
        await session.commit()
        tasks = tasks_to_create

    # Добавляем первые 3 задачи в матч
    for i, task in enumerate(tasks[:3], 1):
        mt = MatchTask(
            match_id=match_id,
            task_id=task.id,
            task_order=i,
        )
        session.add(mt)
        print(f"  Задача {i}: {task.title} (сложность {task.difficulty})")

    await session.commit()
    print(f"\n✓ Добавлено 3 задачи в матч {match_id}")


async def demo_submit_answers(session, match_id, player1_id, player2_id):
    """Демо 3: Отправка ответов (UPSERT pattern)"""
    print("\n" + "=" * 60)
    print("ДЕМО 3: Отправка ответов (UPSERT pattern)")
    print("=" * 60)

    # Получаем задачи в матче
    result = await session.execute(
        select(MatchTask).where(MatchTask.match_id == match_id)
    )
    match_tasks = result.scalars().all()

    # Игрок 1 отправляет ответы
    print(f"\n[Игрок 1 отправляет ответы]")
    for i, mt in enumerate(match_tasks[:2], 1):
        ans = MatchAnswer(
            match_id=match_id,
            user_id=player1_id,
            task_id=mt.task_id,
            answer=f"Ответ игрока 1 на задачу {i}",
            is_correct=True,
        )
        session.add(ans)
        print(f"  ✓ Задача {i}: Правильно")

    await session.commit()

    # Игрок 2 отправляет ответы
    print(f"\n[Игрок 2 отправляет ответы]")
    for i, mt in enumerate(match_tasks, 1):
        ans = MatchAnswer(
            match_id=match_id,
            user_id=player2_id,
            task_id=mt.task_id,
            answer=f"Ответ игрока 2 на задачу {i}",
            is_correct=i == 1,  # Правильно только первую
        )
        session.add(ans)
        print(f"  ✓ Задача {i}: {'Правильно' if i == 1 else 'Неправильно'}")

    await session.commit()
    print(f"\n✓ Ответы сохранены")


async def demo_resubmit_answer(session, match_id, player1_id, task_id):
    """Демо 4: Повторная отправка ответа (UPDATE вместо INSERT)"""
    print("\n" + "=" * 60)
    print("ДЕМО 4: Повторная отправка ответа (UPSERT pattern)")
    print("=" * 60)

    # Находим существующий ответ
    result = await session.execute(
        select(MatchAnswer).where(
            and_(
                MatchAnswer.match_id == match_id,
                MatchAnswer.user_id == player1_id,
                MatchAnswer.task_id == task_id,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"\n[Найден существующий ответ]")
        print(f"  Первая отправка: {existing.submitted_at.isoformat()}")
        print(f"  Ответ был: '{existing.answer}'")
        print(f"  Правильность: {existing.is_correct}")

        # Обновляем существующую запись (не создаём новую!)
        import asyncio
        await asyncio.sleep(0.1)  # Имитируем задержку

        existing.answer = "Обновленный ответ игрока 1"
        existing.is_correct = False
        await session.commit()
        await session.refresh(existing)  # Перезагрузить в асинхронном контексте

        print(f"\n[После повторной отправки]")
        print(f"  ID остался тем же: {existing.id}")
        print(f"  Новый ответ: '{existing.answer}'")
        print(f"  Новая правильность: {existing.is_correct}")
        print(f"  Обновлён: {existing.submitted_at.isoformat()}")
        print(f"\n✓ Ответ обновлён (UPDATE, не INSERT)")
    else:
        print("⚠ Ответ не найден")


async def demo_find_active_matches(session, player_id):
    """Демо 5: Поиск активных матчей игрока"""
    print("\n" + "=" * 60)
    print(f"ДЕМО 5: Активные матчи игрока {player_id}")
    print("=" * 60)

    # Запрос: найти все активные матчи где игрок участвует
    result = await session.execute(
        select(Match).where(
            and_(
                Match.status == MatchStatus.ACTIVE,
                or_(
                    Match.player1_id == player_id,
                    Match.player2_id == player_id,
                ),
            )
        )
    )
    matches = result.scalars().all()

    if matches:
        print(f"\n✓ Найдено {len(matches)} активных матчей:")
        for match in matches:
            print(f"\n  Матч #{match.id}")
            print(f"    Статус: {match.status}")
            print(f"    Создан: {match.created_at.isoformat()}")
            print(f"    Мой счёт: {match.player1_score}-{match.player2_score}")
    else:
        print(f"\n⚠ Активных матчей не найдено")


async def demo_finish_match(session, match_id, winner_id):
    """Демо 6: Завершение матча с расчётом Elo"""
    print("\n" + "=" * 60)
    print("ДЕМО 6: Завершение матча и расчёт Elo")
    print("=" * 60)

    # Получаем матч
    match = await session.get(Match, match_id)

    if match:
        print(f"\n[Обновление статуса матча]")
        print(f"  Был статус: {match.status}")

        # Завершаем матч
        match.status = MatchStatus.FINISHED
        match.finished_at = datetime.utcnow()
        match.winner_id = winner_id
        match.player1_score = 2
        match.player2_score = 1

        # Примерный расчёт Elo
        match.player1_rating_change = 15  # Победитель
        match.player2_rating_change = -15  # Проигравший

        await session.commit()

        print(f"  Новый статус: {match.status}")
        print(f"  Завершён: {match.finished_at.isoformat()}")
        print(f"  Победитель: ID {match.winner_id}")
        print(f"  Финальный счёт: {match.player1_score}-{match.player2_score}")
        print(f"  Изменение рейтинга игрока 1: {match.player1_rating_change:+d}")
        print(f"  Изменение рейтинга игрока 2: {match.player2_rating_change:+d}")
        print(f"\n✓ Матч завершён")
    else:
        print(f"⚠ Матч {match_id} не найден")


async def demo_match_history(session, player_id):
    """Демо 7: История матчей игрока"""
    print("\n" + "=" * 60)
    print(f"ДЕМО 7: История матчей игрока {player_id}")
    print("=" * 60)

    # Запрос: все матчи где участвовал игрок (упорядочены по дате)
    result = await session.execute(
        select(Match)
        .where(
            or_(
                Match.player1_id == player_id,
                Match.player2_id == player_id,
            )
        )
        .order_by(Match.created_at.desc())
        .limit(5)
    )
    matches = result.scalars().all()

    if matches:
        print(f"\n✓ Последние матчи (максимум 5):")
        for i, match in enumerate(matches, 1):
            result_str = f"Победитель: ID {match.winner_id}" if match.finished_at else "В процессе"
            print(f"\n  {i}. Матч #{match.id}")
            print(f"     Статус: {match.status}")
            print(f"     Дата: {match.created_at.isoformat()}")
            print(f"     Счёт: {match.player1_score}-{match.player2_score}")
            print(f"     {result_str}")
    else:
        print(f"\n⚠ Матчей не найдено")


async def demo_match_answers_view(session, match_id):
    """Демо 8: Просмотр всех ответов в матче"""
    print("\n" + "=" * 60)
    print(f"ДЕМО 8: Результаты решения задач в матче {match_id}")
    print("=" * 60)

    result = await session.execute(
        select(MatchAnswer)
        .where(MatchAnswer.match_id == match_id)
        .order_by(MatchAnswer.user_id, MatchAnswer.task_id)
    )
    answers = result.scalars().all()

    if answers:
        print(f"\n✓ Найдено {len(answers)} ответов:\n")
        current_user = None
        for ans in answers:
            if current_user != ans.user_id:
                print(f"\n  [Игрок {ans.user_id}]")
                current_user = ans.user_id
            status = "✓ Правильно" if ans.is_correct else "✗ Неправильно"
            print(f"    Задача {ans.task_id}: {status}")
    else:
        print(f"\n⚠ Ответов не найдено")


async def main():
    """Запускает все демонстрации"""
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ QUERIES ДЛЯ PVP МАТЧЕЙ")
    print("=" * 60)

    try:
        async with async_session_maker() as session:
            # Запускаем все демо по очереди
            match_id, p1_id, p2_id = await demo_create_match(session)
            await demo_add_tasks(session, match_id)
            await demo_submit_answers(session, match_id, p1_id, p2_id)

            # Получаем task_id для демо повторной отправки
            result = await session.execute(
                select(MatchTask.task_id)
                .where(MatchTask.match_id == match_id)
                .limit(1)
            )
            task_id = result.scalar()
            if task_id:
                await demo_resubmit_answer(session, match_id, p1_id, task_id)

            await demo_find_active_matches(session, p1_id)
            await demo_match_answers_view(session, match_id)

            # Меняем статус на ACTIVE для демо поиска
            match = await session.get(Match, match_id)
            match.status = MatchStatus.ACTIVE
            await session.commit()

            await demo_find_active_matches(session, p1_id)
            await demo_finish_match(session, match_id, p1_id)
            await demo_match_history(session, p1_id)

        print("\n" + "=" * 60)
        print("✓ ВСЕ ДЕМОНСТРАЦИИ ЗАВЕРШЕНЫ")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠ Убедитесь, что PostgreSQL запущена!")
    print("   Команда: docker-compose up -d postgres")
    asyncio.run(main())
