## 🐳 Docker команды для проекта

### Основные
- `docker-compose up -d` — поднять БД в фоне
- `docker-compose down` — остановить всё
- `docker-compose ps` — статус контейнеров
- `docker-compose logs postgres` — логи БД
- `docker-compose logs -f postgres` — логи БД в реальном времени
- `docker-compose restart postgres` — перезапуск БД

### Работа с БД (юзер: olympiad, пароль: olympiad, БД: olympiad)
- `docker-compose exec postgres psql -U olympiad -d olympiad` — войти в psql
- `docker-compose exec postgres psql -U olympiad -d olympiad -c "SELECT COUNT(*) FROM tasks;"` — быстрый SQL
- `docker-compose exec postgres psql -U olympiad -d olympiad -c "\dt"` — список таблиц
- `docker-compose exec postgres psql -U olympiad -d olympiad -c "SELECT id, title, difficulty FROM tasks;"` — посмотреть задачи
- `docker-compose exec postgres pg_dump -U olympiad olympiad > backup.sql` — бэкап БД

### Очистка (если накосячил)
- `docker-compose down -v` — удалить контейнеры + volumes (БД обнулится!)
- `docker system prune -a` — очистить весь Docker (осторожно, удалит ВСЁ!)
- `docker volume ls` — посмотреть volumes
- `docker volume rm olympiad_platform_postgres_data` — удалить volume БД

### Backend (из корня проекта)
- `cd backend && source venv/bin/activate` — активировать venv
- `python recreate_db.py` — пересоздать таблицы
- `python seed_tasks.py` — залить тестовые данные
- `uvicorn app.main:app --reload` — запустить сервер (hot reload)
- `uvicorn app.main:app --host 0.0.0.0 --port 8000` — запустить на всех интерфейсах
- `deactivate` — выйти из venv

### Frontend
- `cd frontend && npm run dev` — запустить Next.js dev сервер
- `npm run build` — собрать production
- `npm run start` — запустить production сервер

### Проверка API
- `curl http://localhost:8000/api/tasks` — список задач
- `curl http://localhost:8000/api/tasks/1` — одна задача
- `curl http://localhost:8000/api/tasks/1 | jq '.answer'` — проверить что answer скрыт (null)
- `open http://localhost:8000/docs` — Swagger UI (macOS)
- `curl http://localhost:8000/health` — health check

### Быстрый рестарт всего проекта
```bash
# Остановить всё
docker-compose down
pkill -f uvicorn  # убить backend если завис

# Поднять заново
docker-compose up -d
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

### Дебаг
- `docker-compose logs --tail=50 postgres` — последние 50 строк логов БД
- `docker-compose exec postgres pg_isready -U olympiad` — проверка что БД готова
- `netstat -an | grep 5432` — проверить что порт 5432 занят
- `netstat -an | grep 8000` — проверить что порт 8000 занят