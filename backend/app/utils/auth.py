import bcrypt
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

from app.config import settings


def hash_password(password: str) -> str:
    """
    Хеширует открытый пароль используя bcrypt алгоритм.

    Args:
        password: Открытый пароль в виде строки

    Returns:
        Хешированный пароль в виде строки
    """
    # Конвертируем пароль в байты
    password_bytes = password.encode('utf-8')

    # Генерируем соль
    salt = bcrypt.gensalt()

    # Хешируем пароль
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Возвращаем как строку
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие открытого пароля хешированному паролю.

    Args:
        plain_password: Открытый пароль для проверки
        hashed_password: Хешированный пароль для сравнения

    Returns:
        True если пароли совпадают, False в противном случае
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT access токен с заданными данными и временем жизни.

    Args:
        data: Словарь с данными для payload (обычно {"sub": user_id})
        expires_delta: Время жизни токена. Если None, используется значение из конфига

    Returns:
        Закодированный JWT токен в виде строки

    Примечание:
        JWT payload содержит только user_id в поле "sub" и время истечения "exp".
        Никогда не включайте пароли, хеши паролей или другие чувствительные данные!
        Токен подписывается с использованием SECRET_KEY из конфигурации.
    """
    to_encode = data.copy()

    # Определяем время истечения токена (используем UTC для consistency)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
        )

    # Добавляем exp claim в payload (JWT автоматически проверит при декодировании)
    to_encode.update({"exp": expire})

    # Кодируем и подписываем токен с использованием HMAC-SHA256
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Проверяет и декодирует JWT токен.

    Args:
        token: JWT токен для проверки

    Returns:
        Декодированный payload токена (обычно содержит {"sub": user_id, "exp": ...})

    Raises:
        HTTPException 401: Если токен истек, невалиден или подпись не совпадает

    Примечание:
        Функция автоматически проверяет:
        - Срок действия токена (exp claim)
        - Подпись токена (signature verification)
        - Формат токена (JWT structure)

        В случае любой ошибки возвращается 401 Unauthorized с заголовком
        WWW-Authenticate: Bearer согласно спецификации OAuth2.
    """
    try:
        # Декодируем токен с проверкой подписи и срока действия
        # jwt.decode автоматически проверит exp claim
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except ExpiredSignatureError:
        # Токен истек (exp claim в прошлом)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        # Любая другая ошибка JWT:
        # - Невалидная подпись (token был изменен)
        # - Неверный формат токена
        # - Отсутствуют обязательные claims
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )
