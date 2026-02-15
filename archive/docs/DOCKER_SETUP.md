# Docker Setup для Olympiad Platform

## Структура Docker Files

```
backend/
├── Dockerfile           # Production Dockerfile с Gunicorn
└── .dockerignore       # Exclude ненужные файлы

frontend/
├── Dockerfile          # Production Dockerfile (Next.js multi-stage)
└── .dockerignore       # Exclude ненужные файлы

docker-compose.prod.yml # Production окружение (БД + Backend + Frontend)
docker-compose.local.yml # Development окружение с hot-reload
docker-compose.yml      # Development (исходный файл для локальной разработки)
```

## Быстрый старт

### 1. Local Development (с hot-reload)

```bash
# Запустить всё в Docker
docker-compose -f docker-compose.local.yml up -d

# Проверить логи
docker-compose -f docker-compose.local.yml logs -f

# Остановить
docker-compose -f docker-compose.local.yml down
```

**Доступ:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 2. Production Build & Run

```bash
# 1. Создать production images (если не готовы)
docker build -t olympiad-backend:latest ./backend
docker build -t olympiad-frontend:latest ./frontend

# 2. Скопировать и отредактировать production env
cp .env.production .env.production.local
# Отредактируй переменные окружения (пароли, SECRET_KEY и т.д.)

# 3. Запустить production окружение
docker-compose -f docker-compose.prod.yml up -d

# 4. Проверить статус
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Docker Image Details

### Backend Image
- **Base:** `python:3.11-slim`
- **Framework:** FastAPI + Gunicorn
- **Workers:** 4 Uvicorn workers (можешь изменить в Dockerfile)
- **Port:** 8000
- **Size:** ~371MB compressed
- **Health Check:** HTTP GET на /docs каждые 30s

### Frontend Image
- **Base:** `node:20-alpine` (production)
- **Framework:** Next.js
- **Build:** Multi-stage (builder + runtime)
- **Port:** 3000
- **Size:** ~1.06GB compressed
- **Health Check:** HTTP GET на localhost:3000 каждые 30s

## Возможные проблемы и решения

### 1. Port already in use
```bash
# Найти что занимает порт
lsof -i :8000
lsof -i :3000

# Освободить или переопределить в docker-compose
```

### 2. PostgreSQL не инициализируется
```bash
# Очистить volume
docker volume rm olympiad_platform_postgres_data

# Перезапустить
docker-compose up -d
```

### 3. Frontend image слишком большой
Frontend image содержит полный build Next.js. Можешь оптимизировать:
- Удалить dev dependencies из production image
- Использовать serverless deployment (Vercel, Netlify)

### 4. Backend не может подключиться к БД
```bash
# Проверить network
docker network inspect olympiad_platform_default

# Проверить БД в контейнере
docker exec olympiad_postgres psql -U olympiad -d olympiad -c "SELECT 1"
```

## Network & Services

```
┌─────────────────────────────────┐
│   olympiad_platform_default     │
├─────────────────────────────────┤
│ postgres:5432 ←─────────┐       │
│                         │       │
│ backend:8000 ←──────────┤       │
│                         │       │
│ frontend:3000 ←─────────┘       │
└─────────────────────────────────┘
```

- Все контейнеры в одной network
- Internal DNS: `postgres`, `backend`, `frontend`
- Frontend → Backend через `http://backend:8000` (внутри)
- Внешний доступ через host ports

## Production Deployment Checklist

- [ ] Отредактировать `SECRET_KEY` в `.env.production`
- [ ] Установить сильный пароль для PostgreSQL
- [ ] Использовать https (nginx proxy, Let's Encrypt)
- [ ] Настроить backup для `postgres_data` volume
- [ ] Настроить logging (ELK, Datadog)
- [ ] Настроить monitoring (Prometheus, Grafana)
- [ ] Настроить CI/CD pipeline (GitHub Actions)
- [ ] Настроить resource limits для контейнеров
- [ ] Использовать external DB вместо контейнера для production

## Скрипты полезные

```bash
# Посмотреть что в контейнере
docker exec olympiad_backend ls -la /app

# Зайти в контейнер
docker exec -it olympiad_backend bash
docker exec -it olympiad_postgres psql -U olympiad

# Посмотреть логи конкретного сервиса
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Перестроить image
docker-compose build --no-cache

# Удалить всё (volumes + networks + containers)
docker-compose down -v
```

## Optimization Tips

### Backend
- Увеличить `workers` в gunicorn если высокая нагрузка
- Настроить pool size в SQLAlchemy
- Использовать Redis для кеширования
- Включить gzip compression

### Frontend
- Output file tracing уже встроен (минимизирует размер)
- Edge functions на Vercel для быстрой доставки
- Image optimization автоматический

## Полезные ссылки

- [FastAPI + Docker Best Practices](https://fastapi.tiangolo.com/deployment/docker/)
- [Next.js Docker Guide](https://nextjs.org/docs/deployment)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
