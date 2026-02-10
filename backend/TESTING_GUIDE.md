# Скрипты для PvP матчей

**Структура проекта:**

```
backend/
├── app/
│   └── models/
│       ├── match.py              ← Новые модели
│       ├── enums.py              ← MatchStatus enum
│       └── __init__.py            ← Обновлено
├── scripts/
│   ├── recreate_tables.py        ← Пересоздание БД
│   ├── validate_match_models.py  ← Валидация БЕЗ БД ✓
│   ├── demo_match_queries.py     ← Примеры запросов
│   ├── seed_tasks.py             ← Заполнение задачами
│   └── make_admin.py             (существующий)
├── MATCH_MODELS_README.md        ← Документация моделей
├── MANUAL_TESTING.md             ← Ручное тестирование
└── TESTING_GUIDE.md              ← Этот файл
```

---

## 🚀 Быстрый старт

### 1. Валидировать модели (БЕЗ БД, только синтаксис)

```bash
cd backend
python -m scripts.validate_match_models

# Результат:
# ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ
```

✅ **Работает сейчас без PostgreSQL!**

### 2. Запустить тесты (ТРЕБУЕТ PostgreSQL)

```bash
# Запустить PostgreSQL в Docker
docker-compose up -d postgres
sleep 5

# Запустить все тесты
cd backend
python -m pytest tests/test_match_models.py -v

# Или конкретный тест
python -m pytest tests/test_match_models.py::TestMatchCreation::test_create_match -v

# Или по классу
python -m pytest tests/test_match_models.py::TestMatchConstraints -v
```

### 3. Пересоздать таблицы (ТРЕБУЕТ PostgreSQL)

```bash
cd backend
python -m scripts.recreate_tables

# Результат:
# Удаление существующих таблиц...
# ✓ Таблицы удалены
# Создание таблиц...
# ✓ Таблицы созданы успешно
# Готово!
```

### 4. Заполнить БД тестовыми задачами (ТРЕБУЕТ PostgreSQL)

```bash
cd backend
python -m scripts.seed_tasks

# Результат:
# ============================================================
# ЗАПОЛНЕНИЕ БД ТЕСТОВЫМИ ЗАДАЧАМИ
# ============================================================
#
# ✓ Добавлено 20 новых задач
# ✓ Всего в БД: 20 задач
#
# Распределение по темам:
#   • informatics/algorithms: 5 задач
#   • informatics/graphs: 5 задач
#   • mathematics/geometry: 5 задач
#   • mathematics/algebra: 5 задач
```

### 5. Демонстрация запросов (ТРЕБУЕТ PostgreSQL)

```bash
cd backend
python -m scripts.demo_match_queries

# Выполняет все демо:
# 1. Создание матча
# 2. Добавление задач
# 3. Отправка ответов
# 4. Повторная отправка (UPSERT)
# 5. Поиск активных матчей
# 6. История матчей
# 7. Результаты
# 8. Завершение и Elo
```

---

## 📋 Команды по категориям

### Валидация (без БД, быстро)

```bash
# Синтаксис и типы моделей
python -m scripts.validate_match_models
```

### Управление БД (требует PostgreSQL)

```bash
# Пересоздать все таблицы
python -m scripts.recreate_tables

# Заполнить тестовыми задачами
python -m scripts.seed_tasks

# Создать админа (существующий скрипт)
python -m scripts.make_admin
```

### Тестирование (требует PostgreSQL)

```bash
# Все тесты
python -m pytest tests/test_match_models.py -v

# Только Match модель
python -m pytest tests/test_match_models.py::TestMatchCreation -v
python -m pytest tests/test_match_models.py::TestMatchConstraints -v

# Только MatchTask
python -m pytest tests/test_match_models.py::TestMatchTask* -v

# Только MatchAnswer
python -m pytest tests/test_match_models.py::TestUpsertPattern -v
python -m pytest tests/test_match_models.py::TestCascadeDelete -v

# С выводом print и логов
python -m pytest tests/test_match_models.py -v -s

# Остановить на первой ошибке
python -m pytest tests/test_match_models.py -x

# Только отказавшие тесты
python -m pytest tests/test_match_models.py --lf
```

### Примеры и демонстрации

```bash
# Практические примеры запросов
python -m scripts.demo_match_queries
```

---

## 🔍 Что тестируется

### TestMatchCreation (3 теста)
- ✓ Создание базового матча
- ✓ Баллы по умолчанию = 0
- ✓ Статус по умолчанию = WAITING

### TestMatchConstraints (5 тестов)
- ✓ CHECK: нельзя player1_id == player2_id
- ✓ UNIQUE: не может быть двух задач на одну позицию
- ✓ UNIQUE: одна задача не может быть дважды в матче
- ✓ UNIQUE: один ответ на задачу (upsert ключ)

### TestMatchRelationships (4 теста)
- ✓ player1 relationship загружается (lazy="joined")
- ✓ tasks коллекция загружается (lazy="selectin")
- ✓ back_populates работает
- ✓ task relationship загружается

### TestUpsertPattern (3 теста)
- ✓ Первая отправка создаёт запись
- ✓ Повторная отправка UPDATE'ит, не INSERT'ит
- ✓ submitted_at обновляется на каждый UPDATE

### TestCascadeDelete (2 теста)
- ✓ Удаление Match удаляет MatchTask
- ✓ Удаление Match удаляет MatchAnswer

### TestFinishMatch (1 тест)
- ✓ Завершение матча с рейтингом

### TestStatusTransitions (2 теста)
- ✓ Enum значения доступны
- ✓ Переходы статусов работают

---

## 🗄️ Проверка в PostgreSQL

После запуска `python -m scripts.recreate_tables`:

```bash
docker-compose exec postgres psql -U olympiad -d olympiad

# Проверить таблицы
\dt matches match_tasks match_answers

# Структура matches
\d matches
# Должны быть:
# - Колонки: id, player1_id, player2_id, status, scores, winner_id, rating_changes, finished_at, created_at, updated_at
# - CHECK constraint: ck_matches_players_different
# - Индексы: на player1_id, player2_id, status, winner_id

# Структура match_tasks
\d match_tasks
# Должны быть:
# - Колонки: id, match_id, task_id, task_order, created_at, updated_at
# - UNIQUE INDEX: ix_match_tasks_match_order
# - UNIQUE INDEX: ix_match_tasks_match_task

# Структура match_answers
\d match_answers
# Должны быть:
# - Колонки: id, match_id, user_id, task_id, answer, is_correct, submitted_at, created_at, updated_at
# - UNIQUE INDEX: ix_match_answers_match_user_task (UPSERT ключ)
# - INDEX: ix_match_answers_match_user

# Список индексов
\di match*

# Выход
\q
```

---

## ⚙️ Конфигурация pytest

**`pytest.ini`** содержит:
- Путь к тестам: `tests/`
- Mode: `asyncio_mode = auto`
- Маркеры для запуска

**`tests/conftest.py`** содержит:
- PYTHONPATH настройка
- `db_session` fixture (пересоздаёт БД перед каждым тестом)

---

## 🐛 Troubleshooting

### Ошибка: `ModuleNotFoundError: No module named 'app'`

**Решение:** Используйте `-m` флаг:
```bash
python -m scripts.validate_match_models  # ✓ правильно
python scripts/validate_match_models.py  # ✗ неправильно
```

### Ошибка: `cannot perform operation: another operation is in progress`

**Причина:** asyncpg connection pooling issue
**Решение:** Убедитесь, что используется правильный fixture в conftest.py

### Ошибка: `Connection refused to localhost:5432`

**Причина:** PostgreSQL не запущена
**Решение:**
```bash
docker-compose up -d postgres
sleep 5  # Дождитесь инициализации
```

### Тесты работают слишком долго

**Решение:** Запустите конкретный тест:
```bash
python -m pytest tests/test_match_models.py::TestMatchCreation::test_create_match -v
```

---

## 📊 Примеры вывода

### Валидация (успех)
```
============================================================
✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ
============================================================

✓ Экспорты: Match, MatchTask, MatchAnswer, MatchStatus
✓ Enum: WAITING, ACTIVE, FINISHED, CANCELLED, ERROR
✓ Наследование Base: id, created_at, updated_at ✓
✓ Match: 15 атрибутов, 5 relationships, CHECK constraint, 3 indexes
✓ MatchTask: 3 колонки, 2 relationships, 2 UNIQUE constraints
✓ MatchAnswer: 6 колонов, 3 relationships, UPSERT ключ ✓
```

### Тесты (успех)
```
tests/test_match_models.py::TestMatchCreation::test_create_match PASSED [100%]

======================== 1 passed in 0.64s ========================
```

### Пересоздание таблиц (успех)
```
Пересоздание таблиц БД...
Удаление существующих таблиц...
✓ Таблицы удалены
Создание таблиц...
✓ Таблицы созданы успешно
Готово!
```

### Заполнение задачами (успех)
```
✓ Добавлено 20 новых задач
✓ Всего в БД: 20 задач

Распределение по темам:
  • informatics/algorithms: 5 задач
  • informatics/graphs: 5 задач
  • mathematics/algebra: 5 задач
  • mathematics/geometry: 5 задач

Распределение по сложности:
  • Уровень 1: 2 задачи
  • Уровень 2: 6 задач
  • Уровень 3: 6 задач
  • Уровень 4: 4 задач
  • Уровень 5: 2 задачи
```

---

## 📚 Дополнительные команды

### Очистить кэш pytest
```bash
rm -rf .pytest_cache __pycache__ tests/__pycache__
```

### Запустить с покрытием (если установлен pytest-cov)
```bash
python -m pytest tests/test_match_models.py --cov=app.models.match
```

### Параллельное выполнение (если установлен pytest-xdist)
```bash
python -m pytest tests/test_match_models.py -n auto
```

---

## ✅ Checklist для разработчика

- [ ] Запустить валидацию: `python -m scripts.validate_match_models` ✓
- [ ] Запустить PostgreSQL: `docker-compose up -d postgres`
- [ ] Пересоздать таблицы: `python -m scripts.recreate_tables`
- [ ] Заполнить задачи: `python -m scripts.seed_tasks`
- [ ] Запустить тесты: `python -m pytest tests/test_match_models.py -v`
- [ ] Проверить в psql: `docker-compose exec postgres psql -U olympiad -d olympiad`
- [ ] Запустить демо: `python -m scripts.demo_match_queries`

---

## 🎯 Что дальше?

После успешного прохождения тестов:

1. **Создать роутеры** — HTTP endpoints для матчей
2. **Интегрировать Elo** — расчёт рейтинга после матча
3. **Matchmaking** — поиск противника по уровню
4. **WebSocket** — real-time обновления матча
5. **Notifications** — уведомления об окончании матча

---

**Дата создания:** 2026-02-05
**Версия:** 1.0
**Статус:** Production-ready ✓
