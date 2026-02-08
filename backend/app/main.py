import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.database import init_db
from app.routers import health_router, auth_router, tasks_router, users_router, admin_router, matches_router, pvp_router
from app.websocket.pvp import router as websocket_router
from app.routers.stats import router as stats_router


# Логирование
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Olympiad Platform API",
    description="API для олимпиадной платформы",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)


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
    logger.info(f"🔵 Request: {request.method} {request.url.path}")
    logger.info(f"   Origin: {request.headers.get('Origin', 'NO ORIGIN HEADER')}")
    logger.info(f"   Headers: {dict(request.headers)}")

    try:
        response = await call_next(request)
        logger.info(f"🟢 Response status: {response.status_code}")
        logger.info(f"   CORS header: {response.headers.get('access-control-allow-origin', 'NO CORS HEADER')}")
        logger.info(f"   All response headers: {dict(response.headers)}")
        return response
    except Exception as e:
        logger.error(f"🔴 Exception in request handler: {e}", exc_info=True)
        raise


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
app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(matches_router)
app.include_router(pvp_router)
app.include_router(stats_router)
app.include_router(websocket_router)
