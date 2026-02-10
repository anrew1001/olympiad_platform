from fastapi import APIRouter


# API роутер для health check
router = APIRouter(prefix="/api", tags=["health"])


# Простой health check endpoint
@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Проверка здоровья приложения (health check).

    Returns:
        Словарь с статусом приложения
    """
    return {"status": "ok"}
