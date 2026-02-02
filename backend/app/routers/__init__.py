from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router
from app.routers.admin import router as admin_router

__all__ = ["health_router", "auth_router", "tasks_router", "users_router", "admin_router"]
