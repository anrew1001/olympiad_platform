#!/usr/bin/env python3
"""
Скрипт для назначения роли администратора пользователю.

Использование:
    python scripts/make_admin.py                    # Интерактивный режим
    python scripts/make_admin.py user@example.com   # Прямое назначение по email

Требования:
    - Запускать из директории backend/ проекта
    - PostgreSQL должен быть доступен
    - .env файл должен содержать DATABASE_URL

Безопасность:
    - Запрашивает подтверждение перед изменением роли
    - Логирует все операции в stdout и файл admin_actions.log
    - Проверяет существование пользователя перед изменением
"""

import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import User
from app.models.enums import UserRole


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler("admin_actions.log", encoding="utf-8"),  # Вывод в файл
    ],
)
logger = logging.getLogger(__name__)


async def make_admin(email: str, db: AsyncSession) -> bool:
    """
    Назначает роль администратора пользователю по email.

    Args:
        email: Email пользователя для назначения роли admin
        db: Асинхронная сессия БД

    Returns:
        True если роль успешно назначена, False в случае ошибки
    """

    # 1. Поиск пользователя по email
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        logger.error(f"Пользователь с email '{email}' не найден")
        return False

    # 2. Проверка текущей роли
    if user.role == UserRole.ADMIN.value:
        logger.warning(
            f"Пользователь {user.username} (id={user.id}) "
            f"уже имеет роль администратора"
        )
        print(f"\nℹ️  Пользователь '{user.username}' уже является администратором")
        return True

    # 3. Вывод информации о пользователе
    print("\n" + "=" * 60)
    print("Информация о пользователе:")
    print("=" * 60)
    print(f"ID:           {user.id}")
    print(f"Username:     {user.username}")
    print(f"Email:        {user.email}")
    print(f"Текущая роль: {user.role}")
    print(f"Рейтинг:      {user.rating}")
    print(f"Создан:       {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 4. Запрос подтверждения
    confirmation = (
        input(
            f"\n⚠️  Вы уверены, что хотите назначить роль администратора "
            f"пользователю '{user.username}'? (yes/no): "
        )
        .strip()
        .lower()
    )

    if confirmation not in ["yes", "y", "да"]:
        logger.info("Операция отменена пользователем")
        print("\n❌ Операция отменена")
        return False

    # 5. Назначение роли admin
    old_role = user.role
    user.role = UserRole.ADMIN.value

    try:
        await db.commit()
        await db.refresh(user)

        # 6. Логирование успешной операции
        logger.info(
            f"ADMIN ROLE ASSIGNED: user_id={user.id}, "
            f"username={user.username}, email={user.email}, "
            f"old_role={old_role}, new_role={user.role}, "
            f"timestamp={datetime.utcnow().isoformat()}"
        )

        print(
            f"\n✅ Роль администратора успешно назначена пользователю '{user.username}'"
        )
        print(f"Пользователь теперь имеет доступ к /api/admin/* endpoints")
        return True

    except Exception as e:
        await db.rollback()
        logger.error(
            f"Ошибка при назначении роли администратора: {e}",
            exc_info=True,
        )
        print(f"\n❌ Ошибка при назначении роли: {e}")
        return False


async def main():
    """
    Главная функция скрипта.

    Поддерживает два режима:
    1. Интерактивный: запрос email через input()
    2. CLI аргумент: email передаётся как аргумент командной строки
    """

    print("\n" + "=" * 60)
    print("Скрипт назначения роли администратора")
    print("=" * 60)

    # Определение email пользователя
    if len(sys.argv) > 1:
        # Email передан как CLI аргумент
        email = sys.argv[1].strip()
        print(f"\nИспользуется email из аргумента: {email}")
    else:
        # Интерактивный режим: запрос email
        email = input("\nВведите email пользователя: ").strip()

    # Валидация email (базовая)
    if not email or "@" not in email:
        logger.error(f"Невалидный email: '{email}'")
        print("\n❌ Ошибка: Невалидный email адрес")
        sys.exit(1)

    # Создание сессии БД и выполнение операции
    async with async_session_maker() as db:
        try:
            success = await make_admin(email, db)
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            print(f"\n❌ Критическая ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Запуск асинхронной main функции
    asyncio.run(main())
