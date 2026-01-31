from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.utils.auth import hash_password, verify_password, create_access_token, verify_token


# API роутер для аутентификации и регистрации
router = APIRouter(prefix="/api/auth", tags=["auth"])

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


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с проверкой уникальности email и username"
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Регистрация нового пользователя на платформе.

    Args:
        user_data: Данные для создания пользователя (email, username, password)
        db: Асинхронная сессия БД (dependency injection)

    Returns:
        UserResponse: Созданный пользователь с id, email, username, rating, role, created_at

    Raises:
        HTTPException 400: Если email или username уже заняты
        HTTPException 422: Если данные не прошли валидацию (автоматически от Pydantic)
    """

    # Проверка уникальности email
    email_query = select(User).where(User.email == user_data.email)
    existing_email = await db.execute(email_query)
    if existing_email.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Проверка уникальности username
    username_query = select(User).where(User.username == user_data.username)
    existing_username = await db.execute(username_query)
    if existing_username.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Это имя пользователя уже занято"
        )

    # Хеширование пароля
    hashed_password = hash_password(user_data.password)

    # Создание нового пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        rating=1000,  # Стартовый рейтинг
        role="user"   # Роль по умолчанию
    )

    # Сохранение в БД
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или username уже существует"
        )

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентификация пользователя по email и паролю. Возвращает JWT токен для доступа к защищённым эндпоинтам."
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Аутентификация пользователя и получение JWT токена.

    Args:
        login_data: Email и пароль пользователя
        db: Асинхронная сессия БД

    Returns:
        TokenResponse: JWT access токен и тип токена (bearer)

    Raises:
        HTTPException 401: Если email или пароль неверны

    Примечание безопасности:
        ВАЖНО! Всегда возвращаем одно и то же сообщение об ошибке,
        независимо от того, что именно неверно - email или пароль.
        Это защищает от username enumeration attack (перебора существующих email).
    """
    # Ищем пользователя по email в БД
    query = select(User).where(User.email == login_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # КРИТИЧНО: Одинаковое сообщение для обоих случаев (защита от username enumeration)
    # НЕ раскрываем, существует ли пользователь с таким email или просто пароль неверный
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем пароль с помощью bcrypt (constant-time comparison)
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",  # То же самое сообщение!
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаём JWT токен с user_id в payload
    # ВАЖНО: В токене только user_id (в поле "sub"), никаких паролей или хешей!
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить текущего пользователя",
    description="Возвращает информацию о текущем авторизованном пользователе на основе JWT токена"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Получение данных текущего авторизованного пользователя.

    Args:
        current_user: Текущий пользователь (автоматически извлекается из JWT токена)

    Returns:
        UserResponse: Полные данные пользователя (id, username, email, rating, role, created_at)

    Raises:
        HTTPException 401: Если токен отсутствует, невалиден или истёк (обрабатывается в get_current_user)

    Примечание:
        Клиент должен передать токен в заголовке:
        Authorization: Bearer <access_token>

        Swagger UI автоматически добавит этот заголовок после нажатия кнопки "Authorize"
        и ввода токена, полученного от /login.
    """
    # get_current_user уже извлёк пользователя из БД на основе токена
    # Просто возвращаем его (FastAPI автоматически сериализует через UserResponse)
    return current_user
