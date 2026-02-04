import asyncio
from passlib.context import CryptContext


# Конфигурация для хеширования паролей используя bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    """
    Хеширует открытый пароль используя bcrypt алгоритм.
    Выполняется в отдельном потоке, чтобы не блокировать event loop.

    Args:
        password: Открытый пароль в виде строки

    Returns:
        Хешированный пароль в виде строки
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие открытого пароля хешированному паролю.
    Выполняется в отдельном потоке, чтобы не блокировать event loop.

    Args:
        plain_password: Открытый пароль для проверки
        hashed_password: Хешированный пароль для сравнения

    Returns:
        True если пароли совпадают, False в противном случае
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.verify, plain_password, hashed_password)
