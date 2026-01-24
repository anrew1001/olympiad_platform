from passlib.context import CryptContext


# Конфигурация для хеширования паролей используя bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хеширует открытый пароль используя bcrypt алгоритм.

    Args:
        password: Открытый пароль в виде строки

    Returns:
        Хешированный пароль в виде строки
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие открытого пароля хешированному паролю.

    Args:
        plain_password: Открытый пароль для проверки
        hashed_password: Хешированный пароль для сравнения

    Returns:
        True если пароли совпадают, False в противном случае
    """
    return pwd_context.verify(plain_password, hashed_password)
