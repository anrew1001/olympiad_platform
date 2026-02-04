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

    # Конфигурация для загрузки из .env файла
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Глобальный экземпляр конфигурации
settings = Settings()
