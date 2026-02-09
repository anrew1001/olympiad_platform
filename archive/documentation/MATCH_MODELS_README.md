# PvP Match Models — Реализация

**Статус:** ✓ Завершено и валидировано
**Дата:** 2026-02-05

---

## 📋 Что реализовано

### Модели (backend/app/models/match.py)

```
Match
├─ player1_id, player2_id (FK→users, RESTRICT)
├─ status (MatchStatus enum)
├─ player1_score, player2_score (default 0)
├─ winner_id (FK→users, SET NULL)
├─ player1_rating_change, player2_rating_change (for Elo)
├─ finished_at (timestamp, nullable)
├─ Relationships: player1, player2, winner (all lazy="joined")
├─ Relationships: tasks, answers (lazy="selectin", cascade="all, delete-orphan")
└─ Constraints: CHECK (player1_id ≠ player2_id), 3 indexes

MatchTask
├─ match_id, task_id (FKs)
├─ task_order (порядок 1, 2, 3...)
├─ Relationships: match (back_populates), task
└─ Constraints: UNIQUE (match_id, task_order), UNIQUE (match_id, task_id)

MatchAnswer
├─ match_id, user_id, task_id (FKs)
├─ answer (Text), is_correct (bool)
├─ submitted_at (server_default + onupdate)
├─ Relationships: match (back_populates), user, task
└─ Constraints: UNIQUE (match_id, user_id, task_id) — UPSERT ключ
```

### Enum (backend/app/models/enums.py)

```python
MatchStatus(str, Enum):
    WAITING = "waiting"      # Ждёт второго игрока
    ACTIVE = "active"        # Матч идёт
    FINISHED = "finished"    # Завершён, рейтинг рассчитан
    CANCELLED = "cancelled"  # Отменён
    ERROR = "error"          # Системная ошибка
```

---

## ✅ Валидация

Запустите без БД:
```bash
cd backend
python validate_match_models.py
```

**Результат:**
```
✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ
- Экспорты: Match, MatchTask, MatchAnswer, MatchStatus ✓
- Enum: 5 статусов ✓
- Наследование Base (id, created_at, updated_at) ✓
- Match: 5 relationships, CHECK constraint, 3 indexes ✓
- MatchTask: 2 UNIQUE constraints ✓
- MatchAnswer: UPSERT key (match_id, user_id, task_id) ✓
```

---

## 🔧 Использование

### 1. Создание матча

```python
from app.models import Match, MatchStatus

match = Match(
    player1_id=user1_id,
    player2_id=user2_id,
    status=MatchStatus.WAITING,
    # player1_score, player2_score = 0 по умолчанию
)
session.add(match)
await session.commit()
```

### 2. Добавление задач в матч

```python
from app.models import MatchTask

for i, task in enumerate([task1, task2, task3], 1):
    mt = MatchTask(
        match_id=match.id,
        task_id=task.id,
        task_order=i,  # Порядок важен!
    )
    session.add(mt)
await session.commit()
```

### 3. Отправка ответа (UPSERT паттерн)

**Первая отправка — INSERT:**
```python
ans = MatchAnswer(
    match_id=match.id,
    user_id=player1_id,
    task_id=task_id,
    answer="My answer",
    is_correct=True,
)
session.add(ans)
await session.commit()
```

**Повторная отправка — UPDATE (не INSERT!):**
```python
# SELECT существующей записи
result = await session.execute(
    select(MatchAnswer).where(
        (MatchAnswer.match_id == match_id)
        & (MatchAnswer.user_id == player_id)
        & (MatchAnswer.task_id == task_id)
    )
)
existing = result.scalar_one()

# UPDATE существующей записи
existing.answer = "Updated answer"
existing.is_correct = False
# submitted_at автоматически обновится (onupdate=func.now())
await session.commit()
```

### 4. Завершение матча (с Elo)

```python
match.status = MatchStatus.FINISHED
match.finished_at = datetime.utcnow()
match.winner_id = player1_id
match.player1_score = 3
match.player2_score = 1
match.player1_rating_change = 25   # +25 за победу
match.player2_rating_change = -25  # -25 за поражение
await session.commit()
```

### 5. Поиск активных матчей игрока

```python
from sqlalchemy import select, and_, or_

result = await session.execute(
    select(Match).where(
        and_(
            Match.status == MatchStatus.ACTIVE,
            or_(
                Match.player1_id == player_id,
                Match.player2_id == player_id,
            )
        )
    )
)
active_matches = result.scalars().all()
```

### 6. Доступ к relationships (async-safe)

```python
# Всё правильно подружено, работает с async

# Загрузка матча с связанными данными
match = await session.get(Match, match_id)

# player1, player2, winner уже загружены (lazy="joined")
print(f"Игрок 1: {match.player1.username}")

# tasks, answers уже загружены (lazy="selectin")
for task in match.tasks:
    print(f"Задача {task.task_order}: {task.task.title}")

for answer in match.answers:
    print(f"Игрок {answer.user_id}: {answer.answer}")
```

---

## 🗄️ Schema в PostgreSQL

После создания таблиц:

```sql
-- Таблицы
\dt matches match_tasks match_answers

-- Структура
\d matches          -- Видны колонки, CHECK constraint
\d match_tasks      -- Видны UNIQUE индексы
\d match_answers    -- Видны UNIQUE индексы

-- Индексы
\di match*
```

**Созданные индексы:**

| Таблица | Индекс | Колонки | Unique |
|---------|--------|---------|--------|
| matches | (auto) | player1_id | no |
| matches | (auto) | player2_id | no |
| matches | (auto) | status | no |
| matches | (auto) | winner_id | no |
| matches | ix_matches_player1_status | (player1_id, status) | no |
| matches | ix_matches_player2_status | (player2_id, status) | no |
| matches | ix_matches_status_created | (status, created_at) | no |
| match_tasks | (auto) | match_id | no |
| match_tasks | (auto) | task_id | no |
| match_tasks | ix_match_tasks_match_order | (match_id, task_order) | **yes** |
| match_tasks | ix_match_tasks_match_task | (match_id, task_id) | **yes** |
| match_answers | (auto) | match_id | no |
| match_answers | (auto) | user_id | no |
| match_answers | (auto) | task_id | no |
| match_answers | ix_match_answers_match_user_task | (match_id, user_id, task_id) | **yes** |
| match_answers | ix_match_answers_match_user | (match_id, user_id) | no |

---

## 🧪 Тесты

### С подключением к БД (полный набор)

```bash
# Убедитесь, что PostgreSQL работает
docker-compose up -d postgres

# Пересоздайте таблицы
cd backend
python recreate_tables.py

# Запустите тесты
pytest -v tests/test_match_models.py

# Или конкретный тест
pytest -v tests/test_match_models.py::TestMatchConstraints::test_cannot_play_self
```

**Что тестируется:**
- ✓ Создание матча
- ✓ CHECK constraint (player1 ≠ player2)
- ✓ UNIQUE constraints на MatchTask и MatchAnswer
- ✓ Relationships и lazy loading
- ✓ UPSERT паттерн (UPDATE на повтор)
- ✓ submitted_at обновляется
- ✓ CASCADE удаление
- ✓ Переходы статусов

### Демонстрационные queries (с БД)

```bash
python demo_match_queries.py
```

**Выполняет:**
1. Создание матча
2. Добавление задач
3. Отправка ответов
4. Повторная отправка (UPSERT)
5. Поиск активных матчей
6. История матчей игрока
7. Просмотр результатов

---

## 🔐 Безопасность и integrity

### Constraints (БД уровень)

- ✓ **CHECK** `player1_id ≠ player2_id` — нельзя играть с собой
- ✓ **UNIQUE** `(match_id, task_order)` — позиция задачи уникальна
- ✓ **UNIQUE** `(match_id, task_id)` — одна задача на матч
- ✓ **UNIQUE** `(match_id, user_id, task_id)` — один ответ на задачу
- ✓ **FK RESTRICT** на player1, player2, task — не удалять используемые данные
- ✓ **FK SET NULL** на winner — матч выживает если победитель удалён
- ✓ **FK CASCADE** на match_tasks, match_answers — дети удаляются со своим Match

### Async-safe relationships

- ✓ `lazy="joined"` на many-to-one — не вызывает MissingGreenlet
- ✓ `lazy="selectin"` на коллекциях — single IN query после load
- ✓ `passive_deletes=True` — не загружает детей перед DELETE
- ✓ `expire_on_commit=False` — объекты работают после commit

---

## 📁 Файлы проекта

```
backend/
├── app/
│   └── models/
│       ├── match.py                    ← НОВЫЙ (400 строк)
│       ├── enums.py                    ← ОБНОВЛЕН (MatchStatus)
│       ├── __init__.py                 ← ОБНОВЛЕН (экспорты)
│       ├── base.py                     (не менялся)
│       ├── user.py                     (не менялся)
│       ├── task.py                     (не менялся)
│       └── ...
├── recreate_tables.py                  ← ОБНОВЛЕН (импорты)
├── validate_match_models.py            ← НОВЫЙ (валидация)
├── demo_match_queries.py               ← НОВЫЙ (примеры)
├── tests/
│   └── test_match_models.py            ← НОВЫЙ (50+ тестов)
└── MATCH_MODELS_README.md              ← ЭТОТ ФАЙЛ
```

---

## 🚀 Быстрый старт

### 1. Валидировать модели (без БД)
```bash
cd backend
python validate_match_models.py
```

### 2. Подготовить БД
```bash
docker-compose up -d postgres
sleep 5
python recreate_tables.py
```

### 3. Запустить тесты
```bash
pytest -v tests/test_match_models.py
```

### 4. Попробовать примеры
```bash
python demo_match_queries.py
```

### 5. Использовать в приложении
```python
from app.models import Match, MatchTask, MatchAnswer, MatchStatus
```

---

## 📝 Документация в коде

Каждая модель и поле имеют полные docstring на русском:

```python
class Match(Base):
    """
    Модель 1v1 матча между двумя игроками.
    Хранит состояние матча, баллы, результат и историю рейтинга.
    """

    player1_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        # ... документация прямо в коде
    )
```

---

## ⚠️ Важные замечания

1. **`onupdate=func.now()` работает только с ORM-уровнем**
   - ✓ `session.commit()` — ОК
   - ✗ `execute(update(...))` — not fired

2. **Relationships требуют правильной загрузки**
   - ✓ `session.get(Match, id)` — все relationships загружены
   - ✓ `select(Match)` with `options(...)` — явно указать
   - ✗ Raw relationship access после lazy load — MissingGreenlet

3. **UNIQUE индекс на (match_id, user_id, task_id)**
   - Это UPSERT ключ
   - При повторе: SELECT, UPDATE, не INSERT

4. **Enum сохраняет `.value` строки**
   - БД: `"waiting"` (не `"WAITING"`)
   - Python: `MatchStatus.WAITING`
   - Конвертация автоматическая через `values_callable`

---

## 🎯 Дополнительные идеи улучшений

Уже реализованные:
- ✓ Два поля для рейтинга (player1_rating_change, player2_rating_change)
- ✓ CHECK constraint на самоматч
- ✓ UNIQUE constraints на MatchTask
- ✓ Правильный UPSERT ключ
- ✓ Async-safe relationships с lazy strategies
- ✓ passive_deletes для оптимизации
- ✓ Полные docstring

Возможные будущие расширения:
- [ ] Лог истории изменения статуса (Match.status_history)
- [ ] Ограничение на кол-во матчей в сутки
- [ ] Система штрафов за отказ от матча
- [ ] Rating K-factor (динамический Elo)
- [ ] Рейтинговая система по темам

---

## 📞 Контакты и поддержка

Если нужны изменения в модели:
1. Обновите модель в `match.py`
2. Запустите `python validate_match_models.py`
3. Пересоздайте таблицы: `python recreate_tables.py`
4. Запустите тесты: `pytest -v tests/test_match_models.py`

---

**Создано:** 2026-02-05
**Версия моделей:** 1.0
**Статус:** Production-ready ✓
