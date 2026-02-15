# Olympiad Platform

Платформа для проведения математических олимпиад с PvP режимом и системой рейтинга.

## Технологии

- **Backend**: Python FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **Deployment**: Docker, Docker Compose

## Быстрый старт

### Локальная разработка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd olympiad_platform

# Запустить через Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

**Доступ:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Тестовый админ:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@gmail.com`

### Production

```bash
# С environment переменными
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

## Структура проекта

```
backend/          # FastAPI приложение
├── app/         # Основной код
│   ├── routers/ # API endpoints
│   ├── models/  # Database models
│   ├── schemas/ # Pydantic schemas
│   └── services/# Business logic
├── init_db.py   # Инициализация БД
└── Dockerfile   # Backend образ

frontend/        # Next.js приложение
├── app/         # Pages (App Router)
├── components/  # React компоненты
└── Dockerfile   # Frontend образ

data/tasks/      # Наборы задач (JSON)
```

## Features

- ✅ Регистрация и аутентификация
- ✅ Каталог задач по математике
- ✅ PvP режим (1v1 матчи)
- ✅ Система рейтинга ELO
- ✅ Таблица лидеров
- ✅ Админ-панель
- ✅ Real-time обновления (WebSocket)

## Автор

Andrew Uglov

## Лицензия

MIT
