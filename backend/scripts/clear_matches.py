"""
Скрипт для очистки всех активных/waiting матчей
Использование: python -m scripts.clear_matches
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, delete, func
from app.database import async_engine, async_session_maker
from app.models.match import Match, MatchTask, MatchAnswer
from app.models.enums import MatchStatus


async def clear_all_matches():
    """Очистить все матчи и связанные данные"""

    async with async_session_maker() as session:
        print("=" * 60)
        print("ОЧИСТКА ВСЕХ МАТЧЕЙ")
        print("=" * 60)
        print()

        # Получить статистику ДО очистки
        result = await session.execute(
            select(Match.status, func.count(Match.id))
            .group_by(Match.status)
        )
        stats_before = result.all()

        print("📊 Текущее состояние:")
        total = 0
        for status, count in stats_before:
            print(f"   {status.value}: {count}")
            total += count
        print(f"   ВСЕГО: {total}")
        print()

        if total == 0:
            print("✅ Нет матчей для очистки")
            return

        # Подтверждение
        print("⚠️  ЭТО УДАЛИТ ВСЕ МАТЧИ!")
        confirm = input("Продолжить? (yes/no): ")

        if confirm.lower() != 'yes':
            print("❌ Отменено")
            return

        print()
        print("🗑️  Удаление данных...")

        # 1. Удалить ответы на матчи
        result = await session.execute(delete(MatchAnswer))
        deleted_answers = result.rowcount
        print(f"   ✓ Удалено ответов: {deleted_answers}")

        # 2. Удалить задачи матчей
        result = await session.execute(delete(MatchTask))
        deleted_tasks = result.rowcount
        print(f"   ✓ Удалено задач: {deleted_tasks}")

        # 3. Удалить сами матчи
        result = await session.execute(delete(Match))
        deleted_matches = result.rowcount
        print(f"   ✓ Удалено матчей: {deleted_matches}")

        await session.commit()

        print()
        print("✅ ВСЕ МАТЧИ ОЧИЩЕНЫ!")
        print()
        print("💡 WebSocket соединения будут автоматически закрыты при попытке подключения")


async def main():
    """Main entry point"""
    try:
        await clear_all_matches()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
