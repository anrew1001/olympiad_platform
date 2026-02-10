from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.utils.auth import verify_token


# Схема безопасности для извлечения Bearer токена из заголовка Authorization
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.

    Извлекает Bearer токен из заголовка Authorization, декодирует JWT,
    проверяет его валидность и возвращает объект пользователя из БД.

    Args:
        credentials: Bearer токен из заголовка (автоматически извлекается HTTPBearer)
        db: Асинхронная сессия БД (dependency injection)

    Returns:
        User: Объект пользователя из базы данных

    Raises:
        HTTPException 401: Если токен невалиден, истёк или пользователь не найден

    Примечание:
        Эта функция используется как dependency в защищённых эндпоинтах:
        @router.get("/protected")
        async def protected(current_user: User = Depends(get_current_user)):
            ...
    """
    # Извлекаем сам токен из credentials (credentials.credentials содержит строку токена)
    token = credentials.credentials

    # Декодируем и проверяем токен (verify_token выбросит HTTPException при ошибке)
    payload = verify_token(token)

    # Извлекаем user_id из payload (должен быть в поле "sub" согласно JWT стандарту)
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получаем пользователя из БД по ID (используем async/await паттерн)
    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        # Токен валидный, но пользователь был удалён из БД
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(required_role: UserRole):
    """
    Dependency factory для проверки роли пользователя.

    Создаёт dependency, которая проверяет, что текущий пользователь
    имеет требуемую роль. Это базовая функция для создания
    специализированных проверок ролей (get_admin_user, get_moderator_user, etc.)

    Args:
        required_role: Требуемая роль из UserRole enum

    Returns:
        Async функция-dependency, которую можно использовать с Depends()

    Примечание:
        Использование:
        @router.get("/admin")
        async def admin_only(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """

    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Внутренняя функция для проверки роли текущего пользователя.

        Args:
            current_user: Текущий авторизованный пользователь

        Returns:
            User: Пользователь, если роль совпадает

        Raises:
            HTTPException 403: Если у пользователя недостаточно прав
        """
        # Сравниваем роль пользователя с требуемой ролью
        if current_user.role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {required_role.value}",
            )
        return current_user

    return role_checker


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для проверки прав администратора.

    Проверяет, что текущий авторизованный пользователь имеет роль "admin".
    Это специализированная версия require_role(UserRole.ADMIN) для удобства.

    Args:
        current_user: Текущий авторизованный пользователь (из JWT токена)

    Returns:
        User: Объект пользователя с ролью admin

    Raises:
        HTTPException 401: Если пользователь не авторизован (обрабатывается в get_current_user)
        HTTPException 403: Если у пользователя нет прав администратора

    Примечание:
        Использование в роутере:
        @router.get("/admin/stats")
        async def admin_stats(admin: User = Depends(get_admin_user)):
            ...

        HTTP статусы:
        - 401 Unauthorized: проблемы с токеном (невалиден, истёк, пользователь удалён)
        - 403 Forbidden: токен валиден, но у пользователя нет прав администратора
    """
    # Проверяем роль пользователя
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль администратора",
        )

    return current_user
