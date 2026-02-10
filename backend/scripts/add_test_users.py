"""
Скрипт для добавления тестовых пользователей для тестирования PvP matchmaking.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузить переменные окружения из .env файла
load_dotenv(Path(__file__).parent.parent / ".env")

# Добавляем parent directory в path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.database import async_session_maker
from app.models.user import User
from app.utils.auth import hash_password

async def add_test_users():
    """Добавляет 5 тестовых пользователей с разными рейтингами."""
    async with async_session_maker() as session:
        # Определяем тестовых пользователей
        test_users = [
            {
                "username": "player1",
                "email": "player1@test.com",
                "password": "password123",
                "rating": 1200,
            },
            {
                "username": "player2",
                "email": "player2@test.com",
                "password": "password123",
                "rating": 1250,
            },
            {
                "username": "player3",
                "email": "player3@test.com",
                "password": "password123",
                "rating": 1180,
            },
            {
                "username": "player4",
                "email": "player4@test.com",
                "password": "password123",
                "rating": 1300,
            },
            {
                "username": "player5",
                "email": "player5@test.com",
                "password": "password123",
                "rating": 1100,
            },
        ]

        for user_data in test_users:
            # Проверяем что пользователь не существует
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"✓ {user_data['username']} уже существует (rating={existing_user.rating})")
                continue

            # Создаём нового пользователя
            hashed_password = hash_password(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                rating=user_data["rating"],
            )
            session.add(user)
            print(f"+ {user_data['username']} добавлен (rating={user_data['rating']})")

        await session.commit()
        print("\n✅ Все пользователи добавлены!")

if __name__ == "__main__":
    asyncio.run(add_test_users())
