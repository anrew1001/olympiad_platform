"""
Скрипт для создания админ аккаунта
Использование: python -m scripts.create_admin
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_engine, async_session_maker
from app.models.user import User
from app.utils.auth import hash_password


async def create_admin_user():
    """Создать админ пользователя"""

    async with async_session_maker() as session:
        # Проверить существует ли уже админ
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("❌ Пользователь 'admin' уже существует!")
            print(f"   ID: {existing_admin.id}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")

            # Обновить роль если не admin
            if existing_admin.role != "admin":
                existing_admin.role = "admin"
                await session.commit()
                print("✅ Роль обновлена на 'admin'")
            return

        # Создать нового админа
        admin = User(
            username="admin",
            email="admin@gmail.com",
            hashed_password=hash_password("admin123"),  # Пароль: admin123
            role="admin",
            rating=1500,
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("✅ Админ пользователь создан!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@gmail.com")
        print(f"   ID: {admin.id}")
        print("")
        print("⚠️  ВАЖНО: Смените пароль после первого входа!")


async def main():
    """Main entry point"""
    print("=" * 50)
    print("СОЗДАНИЕ АДМИН АККАУНТА")
    print("=" * 50)
    print("")

    try:
        await create_admin_user()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
