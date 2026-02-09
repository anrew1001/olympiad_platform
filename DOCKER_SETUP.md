# Docker Setup - Полное тестирование приложения

Это руководство для полного тестирования приложения в Docker контейнерах.

## Быстрый старт (с Docker)

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/olympiad-platform.git
cd olympiad-platform
```

### 2. Запуск контейнеров

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL (порт 5432)
- Backend FastAPI (порт 8000)
- Frontend Next.js (порт 3000)

### 3. Инициализация БД

```bash
chmod +x docker-init.sh
./docker-init.sh
```

Это создаст:
- Таблицы в БД
- 60 задач
- Админ аккаунт (username: admin, password: admin123)

### 4. Проверить что работает

```bash
# Backend API
curl http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

## Команды для управления контейнерами

### Просмотр логов

```bash
# Все контейнеры
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend

# Только БД
docker-compose logs -f postgres
```

### Остановка

```bash
docker-compose down
```

### Перезапуск

```bash
docker-compose restart
```

### Удалить всё (включая данные БД)

```bash
docker-compose down -v
```

## Доступ к контейнерам

### Bash в backend контейнере

```bash
docker exec -it olympiad_backend bash
```

### Python REPL в backend

```bash
docker exec -it olympiad_backend python
```

### SQL доступ к БД

```bash
docker exec -it olympiad_postgres psql -U olympiad -d olympiad
```

### Npm/Node в frontend контейнере

```bash
docker exec -it olympiad_frontend npm --version
```

## Отладка

### Проверить статус контейнеров

```bash
docker-compose ps
```

### Проверить сетевое взаимодействие

```bash
# Из backend → PostgreSQL
docker exec olympiad_backend python -c "
import asyncio
from app.database import async_engine
async def test():
    async with async_engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('✓ Database connection works')
asyncio.run(test())
"

# Из frontend → Backend
docker exec olympiad_frontend curl http://backend:8000/docs
```

### Проверить переменные окружения

```bash
docker exec olympiad_backend env | grep DATABASE_URL
docker exec olympiad_frontend env | grep NEXT_PUBLIC_API_URL
```

## Тестирование функционала

### 1. Регистрация

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. Вход

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. Получить список задач

```bash
curl http://localhost:8000/api/tasks
```

## Когда нужна переинициализация

### Полный reset (удалить всё и начать заново)

```bash
docker-compose down -v
docker-compose up -d
./docker-init.sh
```

### Просто удалить данные БД (оставить контейнеры)

```bash
docker volume rm olympiad_postgres_data
docker-compose restart postgres
./docker-init.sh
```

## Production vs Development

### Development (текущая конфиг)

```yaml
- Hot reload включён (volumes с исходным кодом)
- DEBUG режим
- SECRET_KEY = dev-secret-key (МЕНЯЕТСЯ в production!)
```

### Production (для Render)

- Используй render.yaml
- SECRET_KEY генерируется автоматически
- DATABASE_URL из managed PostgreSQL
- Контейнеры собираются один раз (без hot reload)

## Troubleshooting

### Порты уже заняты

```bash
# Найти какой процесс использует порт
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Либо измени порты в docker-compose.yml:
# ports:
#   - "8001:8000"  # Backend на 8001
#   - "3001:3000"  # Frontend на 3001
```

### Контейнеры не поднимаются

```bash
# Проверь логи
docker-compose logs

# Убедись что Docker запущен
docker ps

# Перебuild контейнеры
docker-compose build --no-cache
docker-compose up -d
```

### WebSocket не работает

Когда используешь Docker, убедись что:
- Backend поднялся полностью (check health: http://localhost:8000/docs)
- NEXT_PUBLIC_WS_URL указывает на правильный адрес (http://backend:8000 внутри контейнера)

### БД не инициализируется

```bash
# Проверь что PostgreSQL готов
docker exec olympiad_postgres pg_isready -U olympiad

# Запусти init вручную
docker exec olympiad_backend python -m scripts.init_db
docker exec olympiad_backend python -m scripts.load_grade10_mix
```

## Next Steps

1. Когда всё работает локально в Docker → готово для production
2. Используй `render.yaml` для деплоя на Render
3. Всё остальное (HTTPS, backups, monitoring) настраивается на Render dashboard
