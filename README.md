# Olympeit - Платформа олимпиадного программирования

Real-time платформа для соревновательного программирования с PvP матчами, системой рейтинга ELO и асинхронной архитектурой.

## Описание

Olympeit — это веб-платформа для практики и соревнований по олимпиадному программированию для учеников старших классов.

### Основные возможности

- Матчи PvP в реальном времени с WebSocket коммуникацией
- Динамическая система рейтинга ELO с адаптивным matchmaking
- Каталог задач: 60+ задач (математика, информатика, физика)
- Автоматическое восстановление соединения с прогрессивными предупреждениями
- Глобальная таблица лидеров с детальной статистикой
- Аналитика по темам и уровню сложности

## Технологический стек

### Backend
- Python 3.12 с поддержкой async/await
- FastAPI - высокопроизводительный framework
- PostgreSQL 14+ - основная БД
- SQLAlchemy 2.0 - асинхронный ORM
- WebSockets - real-time коммуникация
- JWT - аутентификация
- Pydantic - валидация данных

### Frontend
- Next.js 15 (App Router) - React framework с SSR
- TypeScript - строгая типизация
- Tailwind CSS - стилизация
- WebSocket client - real-time communication
- Framer Motion - анимации

## Установка и запуск

### Требования
- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- Docker Desktop ([Скачать](https://www.docker.com/products/docker-desktop/)) - для запуска через контейнеры

### Быстрый старт

#### 1. Клонирование
```bash
git clone https://github.com/your-username/olympiad-platform.git
cd olympiad-platform
```

#### 2. Backend

```bash
cd backend

# Виртуальное окружение
python3.12 -m venv venv_backend
source venv_backend/bin/activate  # macOS/Linux
# или venv_backend\Scripts\activate  # Windows

# Зависимости
pip install -r requirements.txt

# Конфиг
cat > .env << EOL
DATABASE_URL=postgresql+asyncpg://olympiad:olympiad@localhost:5432/olympiad
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL

# PostgreSQL (в отдельном терминале)
docker-compose up -d postgres

# Инициализация БД
python -m scripts.init_db
python -m scripts.load_grade10_mix

# Админ (опционально)
python -m scripts.create_admin

# Сервер
uvicorn app.main:app --reload
```

Backend: http://localhost:8000
Docs: http://localhost:8000/docs

#### 3. Frontend

```bash
cd frontend

npm install

cat > .env.local << EOL
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOL

npm run dev
```

Frontend: http://localhost:3000

### Альтернатива: Запуск через Docker

Для тестирования или production деплоя используйте Docker контейнеры:

```bash
# Запуск всех сервисов
docker-compose up -d

# Инициализация БД
./docker-init.sh
```

После запуска:

- Backend: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:3000](http://localhost:3000)

**Полная документация:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

## Структура проекта

```
olympiad_platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI приложение
│   │   ├── database.py          # SQLAlchemy конфиг
│   │   ├── models/              # ORM модели
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Бизнес-логика
│   │   ├── schemas/             # Pydantic модели
│   │   ├── websocket/           # WebSocket handlers
│   │   └── utils/               # Утилиты
│   ├── scripts/                 # Инициализация БД
│   ├── tests/                   # Тесты
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js App Router
│   │   ├── page.tsx            # Главная
│   │   ├── login/              # Вход/Регистрация
│   │   ├── pvp/                # PvP матчи
│   │   ├── tasks/              # Каталог задач
│   │   ├── profile/            # Профиль
│   │   └── leaderboard/        # Лидербоард
│   ├── components/              # React компоненты
│   ├── lib/                     # Хуки и утилиты
│   └── package.json
├── archive/                     # Архивные файлы разработки
├── render.yaml                  # Конфиг для Render
├── docker-compose.yml           # Локальный PostgreSQL
├── Dockerfile.backend           # Backend контейнер
├── Dockerfile.frontend          # Frontend контейнер
├── SETUP.md                     # Детальная инструкция
└── README.md
```

## API Endpoints

### Аутентификация
```
POST   /api/auth/register        Регистрация
POST   /api/auth/login           Вход
GET    /api/auth/me              Текущий пользователь
```

### Задачи
```
GET    /api/tasks                Список задач
GET    /api/tasks/{id}           Детали задачи
```

### Matchmaking
```
POST   /api/pvp/find             Найти/создать матч
POST   /api/pvp/cancel/{id}      Отменить матч
GET    /api/pvp/match/{id}       Детали матча
```

### WebSocket
```
WS     /api/ws/pvp/{match_id}    Real-time матч
```

События сервера: player_joined, match_start, answer_result, match_end, opponent_disconnected, opponent_reconnected, disconnect_warning, reconnection_success

События клиента: submit_answer, pong

### Пользователи
```
GET    /api/users/leaderboard    Таблица лидеров
GET    /api/users/{id}/stats     Статистика пользователя
```

Полная документация: http://localhost:8000/docs

## Тестирование

### Backend тесты
```bash
cd backend
source venv_backend/bin/activate
pytest tests/ -v
```

### Frontend проверка
```bash
cd frontend
npm run lint              # ESLint
npm run type-check       # TypeScript
npm run build            # Production build
```

### Проверка инструкций
```bash
./test_setup.sh
```

## Архитектура

### WebSocket Reconnection
- Timeout: 30 секунд (настраивается)
- Прогрессивные предупреждения: 15s, 10s, 5s
- Flapping detection: >3 отключения в 60s → штраф 50%
- Полное восстановление состояния

### ELO Rating System
- K-factor: 32 (адаптивный в Phase 2)
- Формула: `new_rating = old_rating + K * (actual_score - expected_score)`
- Minimum rating: 100

### Database Patterns
- UPSERT для ответов - атомарность под нагрузкой
- SELECT FOR UPDATE - критические секции
- Per-message sessions - WebSocket
- Master-only writes - без конфликтов

## Деплой на Render

Включен render.yaml для автоматического деплоя.

### Checklist перед production
- Обновить CORS в backend/app/main.py
- Конфигурировать environment variables
- Оптимизировать PostgreSQL
- Включить HTTPS для WebSocket (WSS)
- Настроить логирование (Sentry, CloudWatch)
- Настроить бэкапы БД

### Environment Variables

Backend:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
DISCONNECT_TIMEOUT_SECONDS=30
FRONTEND_URL=https://your-frontend.com
```

Frontend:
```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

## Разработка

### Code Style
- Backend: Black, Ruff, mypy
- Frontend: ESLint + Prettier
- Комментарии: Русский язык
- Идентификаторы: Английский язык
- Commits: Conventional Commits

### Git Workflow
```bash
git checkout develop
git pull origin develop
git checkout -b feature/description
# ... изменения ...
git add .
git commit -m "feat: описание"
git push origin feature/description
# Pull Request на GitHub
```

## Известные ограничения

- Alembic миграции не настроены
- Dockerfile еще не подготовлены
- CI/CD pipeline не настроен
- Frontend unit тесты не реализованы
- Интернационализация (i18n) не реализована
- Сабмит кода ограничен числовыми ответами

## Поддержка

- Issues: https://github.com/your-username/olympiad-platform/issues
- Pull requests приветствуются

## Лицензия

MIT License - см LICENSE

