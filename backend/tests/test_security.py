import os

# Устанавливаем фиктивные переменные окружения для тестов
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_HOURS"] = "1"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

@pytest.fixture
def client():
    # Патчим init_db, чтобы тесты не требовали реального подключения к базе данных
    with patch("app.main.init_db", return_value=None):
        with TestClient(app) as c:
            yield c

def test_security_headers(client):
    """
    Тест проверяет наличие обязательных заголовков безопасности в ответе API.
    """
    response = client.get("/api/health")
    assert response.status_code == 200

    # Проверка заголовков безопасности
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
