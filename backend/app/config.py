from pydantic_settings import BaseSettings, SettingsConfigDict


# Конфигурация приложения, загружаемая из переменных окружения
class Settings(BaseSettings):
    """Основные настройки приложения"""

    # URL подключения к базе данных PostgreSQL с asyncpg драйвером
    DATABASE_URL: str

    # Секретный ключ для JWT токенов
    SECRET_KEY: str

    # Алгоритм для JWT подписания
    ALGORITHM: str

    # Время жизни access токена в часах
    ACCESS_TOKEN_EXPIRE_HOURS: int

    # Настройки пула подключений к PostgreSQL
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 10

    # WebSocket reconnection settings
    DISCONNECT_TIMEOUT_SECONDS: int = 30  # Grace period before forfeit
    DISCONNECT_WARNING_INTERVALS: list[int] = [15, 10, 5]  # Warning times (seconds remaining)
    FLAPPING_WINDOW_SECONDS: int = 60  # Time window to track disconnects
    FLAPPING_MAX_DISCONNECTS: int = 3  # Max disconnects before penalty
    FLAPPING_PENALTY_MULTIPLIER: float = 0.5  # Reduce timeout by 50% if flapping

    # Конфигурация для загрузки из environment variables
    # .env файл используется локально, в Docker используются env vars из docker-compose.yml
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )


# Глобальный экземпляр конфигурации
settings = Settings()
