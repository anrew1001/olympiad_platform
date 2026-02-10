import logging
import os
import sys
import json
from pathlib import Path

# print("===== DEBUG: main.py loading =====", file=sys.stderr)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, delete

from app.database import init_db, async_session_maker
from app.models import Task
from app.routers import health_router, auth_router, tasks_router, users_router, admin_router, matches_router, pvp_router
from app.websocket.pvp import router as websocket_router
from app.routers.stats import router as stats_router

# print("===== DEBUG: imports done =====", file=sys.stderr)

# Логирование
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
# print("===== DEBUG: creating FastAPI app =====", file=sys.stderr)
app = FastAPI(
    title="Olympiad Platform API",
    description="API для олимпиадной платформы",
    version="1.0.0",
    default_response_class=JSONResponse,
)
# print("===== DEBUG: FastAPI app created =====", file=sys.stderr)


# Конфигурация CORS
# КРИТИЧЕСКИ ВАЖНО: CORS middleware должен быть ПЕРВЫМ (перед всеми другими)
if os.getenv("ENVIRONMENT") == "production":
    cors_origins = [
        "https://your-production-domain.com",  # TODO: заменить на реальный домен
    ]
else:
    # Development: разрешить localhost
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


# Logging middleware для отладки CORS
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирует запросы и ответы для отладки CORS проблем."""
    print(f"🔵 Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        print(f"🟢 Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"🔴 Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def load_tasks_from_json() -> None:
    """Загружает задачи из JSON файла если БД пуста. Использует титл как уникальный ключ."""
    try:
        async with async_session_maker() as session:
            # Проверяем нужна ли загрузка - если все 60 уникальных задач уже есть, пропускаем
            result = await session.execute(select(func.count(Task.title.distinct())))
            unique_count = result.scalar() or 0

            if unique_count >= 60:
                # Если есть дубли, удаляем их
                if unique_count > 60:
                    # Удаляем дубли - оставляем только первую копию каждого заголовка
                    await session.execute("""
                        DELETE FROM tasks WHERE id NOT IN (
                            SELECT MIN(id) FROM tasks GROUP BY title
                        )
                    """)
                    await session.commit()
                    logger.info(f"✓ Удалены дубли, осталось 60 задач")
                return

            # Ищем JSON файл в /app/data/tasks/grade10_mix.json
            json_path = Path(__file__).parent.parent / "data" / "tasks" / "grade10_mix.json"

            if not json_path.exists():
                logger.warning(f"⚠ Файл задач не найден: {json_path}")
                return

            # Загружаем JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)

            # Добавляем все задачи
            tasks = []
            for task_data in tasks_data:
                task = Task(
                    subject=task_data.get("subject"),
                    topic=task_data.get("topic"),
                    difficulty=task_data.get("difficulty"),
                    title=task_data.get("title"),
                    text=task_data.get("text"),
                    answer=task_data.get("answer"),
                    hints=task_data.get("hints", [])
                )
                tasks.append(task)

            session.add_all(tasks)
            await session.commit()
            logger.info(f"✓ Загружено {len(tasks)} задач из {json_path.name}")

            # Сразу же удаляем дубли если они появились от параллельных workers
            result = await session.execute(select(func.count(Task.id)))
            total = result.scalar() or 0
            if total > 60:
                # Получаем все задачи и находим дубли
                result = await session.execute(select(Task).order_by(Task.title, Task.id))
                all_tasks = result.scalars().all()

                titles_seen = set()
                ids_to_delete = []
                for task in all_tasks:
                    if task.title in titles_seen:
                        ids_to_delete.append(task.id)
                    else:
                        titles_seen.add(task.title)

                if ids_to_delete:
                    await session.execute(delete(Task).where(Task.id.in_(ids_to_delete)))
                    await session.commit()
                    logger.info(f"✓ Удалены {len(ids_to_delete)} дубли от параллельных workers")

    except Exception as e:
        logger.warning(f"⚠ Ошибка загрузки задач из JSON: {e}")


# Event handler при старте приложения
@app.on_event("startup")
async def startup_event() -> None:
    """
    Инициализирует базу данных при старте приложения.
    Создает все необходимые таблицы и загружает задачи из JSON.
    Ошибки подключения логируются, приложение продолжает работу.
    """
    try:
        await init_db()
        logger.info("✓ База данных инициализирована успешно")
    except ConnectionRefusedError:
        logger.warning("⚠ PostgreSQL недоступен. Проверьте подключение.")
        return
    except Exception as e:
        # Игнорируем ошибки вроде duplicate key при параллельной инициализации
        if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("✓ База данных уже инициализирована")
        else:
            logger.warning(f"⚠ Ошибка инициализации БД: {e}")

    # Задачи загружаются init_db.py перед стартом, поэтому здесь не нужно


# Подключение роутеров к приложению
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(matches_router)
app.include_router(pvp_router)
app.include_router(stats_router)
app.include_router(websocket_router)
