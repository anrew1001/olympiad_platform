# Multi-stage build для оптимизации размера image

# Stage 1: Builder - установка зависимостей
FROM python:3.11-slim as builder

WORKDIR /tmp

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости в /opt/venv
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - финальный image
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем virtualenv из builder
COPY --from=builder /opt/venv /opt/venv

# Копируем исходный код приложения
COPY . .

# Создаём non-root пользователя для безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /opt/venv

# Добавляем virtualenv в PATH
ENV PATH=/opt/venv/bin:$PATH
ENV VIRTUAL_ENV=/opt/venv
ENV PYTHONUNBUFFERED=1

USER appuser

# Health check для Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs')" || exit 1

# Expose порт
EXPOSE 8000

# Production команда с Gunicorn + Uvicorn Workers
# 4 workers на 4 ядрах, adjust в зависимости от ресурсов
CMD ["gunicorn", \
     "app.main:app", \
     "--workers=4", \
     "--worker-class=uvicorn.workers.UvicornWorker", \
     "--bind=0.0.0.0:8000", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "--log-level=info"]
