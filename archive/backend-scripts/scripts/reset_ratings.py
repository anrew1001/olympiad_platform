"""
Скрипт для сброса рейтингов всех пользователей на начальное значение 1500
Использование: python -m scripts.reset_ratings
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.database import async_engine, async_session_maker
from app.models.user import User


async def reset_all_ratings():
    """Сбросить рейтинги всех пользователей на 1500"""

    async with async_session_maker() as session:
        print("=" * 60)
        print("СБРОС РЕЙТИНГОВ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
        print("=" * 60)
        print()

        # Получить статистику ДО
        result = await session.execute(
            select(User.username, User.rating).order_by(User.rating.desc())
        )
        users_before = result.all()

        print("📊 Текущие рейтинги:")
        for username, rating in users_before[:10]:  # Показать топ-10
            print(f"   {username}: {rating}")
        if len(users_before) > 10:
            print(f"   ... и ещё {len(users_before) - 10} пользователей")
        print()

        if not users_before:
            print("✅ Нет пользователей для сброса")
            return

        # Подтверждение
        print("⚠️  ЭТО СБРОСИТ ВСЕ РЕЙТИНГИ НА 1500!")
        confirm = input("Продолжить? (yes/no): ")

        if confirm.lower() != 'yes':
            print("❌ Отменено")
            return

        print()
        print("🔄 Сброс рейтингов...")

        # Обновить все рейтинги на 1500
        result = await session.execute(
            update(User).values(rating=1500)
        )
        updated_count = result.rowcount

        await session.commit()

        print(f"   ✓ Обновлено пользователей: {updated_count}")
        print()
        print("✅ ВСЕ РЕЙТИНГИ СБРОШЕНЫ НА 1500!")
        print()

        # Показать результат
        result = await session.execute(
            select(User.username, User.rating).order_by(User.username)
        )
        users_after = result.all()

        print("📊 Рейтинги после сброса:")
        for username, rating in users_after[:10]:
            print(f"   {username}: {rating}")
        if len(users_after) > 10:
            print(f"   ... и ещё {len(users_after) - 10} пользователей")


async def main():
    """Main entry point"""
    try:
        await reset_all_ratings()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
