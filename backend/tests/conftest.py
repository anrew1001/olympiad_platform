"""Pytest конфигурация и fixtures для тестирования."""

import asyncio
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.task import Task
from app.models.match import Match, MatchTask, MatchAnswer
from app.models.enums import MatchStatus


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture
async def async_db_engine():
    """Создаёт in-memory SQLite для тестов."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session_maker(async_db_engine):
    """Создаёт AsyncSession factory."""
    return async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(async_session_maker):
    """Создаёт новую БД сессию для каждого теста."""
    async with async_session_maker() as session:
        yield session


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
async def test_users(db_session):
    """Создаёт двух тестовых пользователей."""
    user1 = User(
        id=1,
        username="player1",
        email="player1@test.com",
        password_hash="hash1",
        rating=1000,
    )
    user2 = User(
        id=2,
        username="player2",
        email="player2@test.com",
        password_hash="hash2",
        rating=1000,
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    return [user1, user2]


@pytest.fixture
async def test_tasks(db_session):
    """Создаёт 5 тестовых задач для матча."""
    tasks = []
    for i in range(1, 6):
        task = Task(
            id=i,
            title=f"Task {i}",
            description=f"Description {i}",
            input_format="",
            output_format="",
            time_limit=1000,
            memory_limit=256,
            difficulty=2,  # Medium difficulty
            test_cases=[],
        )
        db_session.add(task)
        tasks.append(task)

    await db_session.commit()
    return tasks


@pytest.fixture
async def test_match(db_session, test_users, test_tasks):
    """Создаёт тестовый матч между двумя игроками."""
    match = Match(
        id=1,
        player1_id=test_users[0].id,
        player2_id=test_users[1].id,
        status=MatchStatus.ACTIVE,
        created_at=datetime.utcnow(),
        player1_score=0,
        player2_score=0,
    )
    db_session.add(match)
    await db_session.flush()

    # Добавить все задачи в матч
    for task in test_tasks:
        match_task = MatchTask(
            match_id=match.id,
            task_id=task.id,
        )
        db_session.add(match_task)

    await db_session.commit()
    return match


# ============================================================================
# NOTE: event_loop fixture removed - pytest-asyncio handles it automatically
# with asyncio_mode=auto in pytest.ini
# ============================================================================


# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture
async def equal_rating_users(db_session):
    """Два игрока с одинаковыми рейтингами (1000)."""
    user1 = User(
        id=101,
        username="equal1",
        email="equal1@test.com",
        password_hash="hash",
        rating=1000,
    )
    user2 = User(
        id=102,
        username="equal2",
        email="equal2@test.com",
        password_hash="hash",
        rating=1000,
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    return [user1, user2]


@pytest.fixture
async def skill_gap_users(db_session):
    """Два игрока с большим перевесом рейтинга (200 разница)."""
    strong = User(
        id=201,
        username="strong",
        email="strong@test.com",
        password_hash="hash",
        rating=1200,
    )
    weak = User(
        id=202,
        username="weak",
        email="weak@test.com",
        password_hash="hash",
        rating=1000,
    )
    db_session.add_all([strong, weak])
    await db_session.commit()
    return [strong, weak]


@pytest.fixture
async def extreme_rating_users(db_session):
    """Два игрока с экстремальной разницей рейтинга (800+)."""
    master = User(
        id=301,
        username="master",
        email="master@test.com",
        password_hash="hash",
        rating=2000,
    )
    novice = User(
        id=302,
        username="novice",
        email="novice@test.com",
        password_hash="hash",
        rating=800,
    )
    db_session.add_all([master, novice])
    await db_session.commit()
    return [master, novice]
