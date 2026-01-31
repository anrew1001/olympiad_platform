import logging

from fastapi import FastAPI

from app.database import init_db
from app.routers import health_router, auth_router


# Логирование
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Olympiad Platform API",
    description="API для олимпиадной платформы",
    version="1.0.0",
)


# Event handler при старте приложения
@app.on_event("startup")
async def startup_event() -> None:
    """
    Инициализирует базу данных при старте приложения.
    Создает все необходимые таблицы.
    Ошибки подключения логируются, приложение продолжает работу.
    """
    try:
        await init_db()
        logger.info("✓ База данных инициализирована успешно")
    except ConnectionRefusedError:
        logger.warning("⚠ PostgreSQL недоступен на localhost:5432. Проверьте подключение.")
    except Exception as e:
        logger.warning(f"⚠ Ошибка инициализации БД: {e}")


# Подключение роутеров к приложению
app.include_router(health_router)
app.include_router(auth_router)
