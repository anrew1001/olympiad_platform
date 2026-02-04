import logging

from fastapi import FastAPI, Request

from app.database import init_db
from app.routers import health_router


# Логирование
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Olympiad Platform API",
    description="API для олимпиадной платформы",
    version="1.0.0",
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Middleware для добавления заголовков безопасности в каждый ответ.
    Защищает от XSS, Clickjacking и других распространенных атак.
    """
    response = await call_next(request)
    # Ограничивает источники контента только собственным доменом
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none';"
    )
    # Запрещает встраивание сайта во фреймы (защита от Clickjacking)
    response.headers["X-Frame-Options"] = "DENY"
    # Предотвращает MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Активирует фильтр XSS в старых браузерах
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Принудительное использование HTTPS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


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
