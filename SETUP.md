# Olympiad Platform — Setup Guide

Привет! Это инструкция как начать работать в проекте.

## 1. Установи необходимое

### Python 3.12

**Windows:**
1. Открой https://www.python.org/downloads/
2. Нажми "Download Python 3.12.x"
3. Запусти установщик
4. **ВАЖНО:** Отметь "Add Python to PATH"
5. Нажми "Install Now"

**macOS/Linux:**

Уже должен быть установлен (проверь):

```bash
python3.12 --version
```

### VSCode

1. Открой https://code.visualstudio.com
2. Скачай для своей ОС
3. Установи

### Git

**Windows:**
1. https://git-scm.com/download/win
2. Скачай и установи (все по умолчанию ОК)

**macOS/Linux:**

```bash
git --version
```

### Расширения в VSCode

Открой VSCode → левая панель → Extensions

Установи:
- `Python` (Microsoft)
- `GitLens` (Eric Amodio)

## 2. Клонируй репозиторий

### Способ 1 (в VSCode - САМЫЙ ПРОСТОЙ)

1. Открой VSCode
2. Нажми: `Ctrl+Shift+P` (Windows/Linux) или `Cmd+Shift+P` (Mac)
3. Напиши: `Git: Clone`
4. Вставь ссылку:

```
https://github.com/andrewUG/olympiad-platform.git
```

5. Выбери папку где сохранить (Documents/Projects)
6. Нажми "Open folder"

### Способ 2 (через терминал)

**Windows:**

```bash
cd Documents
git clone https://github.com/andrewUG/olympiad-platform.git
cd olympiad-platform
```

**macOS/Linux:**

```bash
cd ~
git clone https://github.com/andrewUG/olympiad-platform.git
cd olympiad-platform
```

Потом в VSCode: `File → Open Folder` → выбери olympiad-platform

## 3. Backend Setup (Python окружение)

Открой терминал в VSCode: `Terminal → New Terminal` или `Ctrl+J`

### Шаг 1: Переходим в папку backend

```bash
cd backend
```

### Шаг 2: Создаём виртуальное окружение

**Windows:**

```bash
python -m venv venv_backend
```

**macOS (Apple Silicon M1/M2/M3):**

```bash
/opt/homebrew/bin/python3.12 -m venv venv_backend
```

**macOS (Intel) / Linux:**

```bash
python3.12 -m venv venv_backend
```

### Шаг 3: Активируешь окружение

**Windows (PowerShell):**

```bash
venv_backend\Scripts\Activate.ps1
```

**Windows (CMD):**

```bash
venv_backend\Scripts\activate.bat
```

**macOS/Linux:**

```bash
source venv_backend/bin/activate
```

Если правильно - в начале строки появится `(venv_backend)`:

```
(venv_backend) user@computer olympiad_platform %
```

### Шаг 4: Устанавливаешь зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Это займёт 2-3 минуты.

Проверь что установилось:

```bash
python -c "import fastapi; print('OK')"
```

Если видишь `OK` - всё хорошо!

## 4. Запусти backend

Убедись что окружение активировано! (в начале должно быть `(venv_backend)`)

```bash
uvicorn app.main:app --reload
```

Вывод должен быть:

```
Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

Открой браузер → http://localhost:8000/docs

Если видишь красивый синий интерфейс → **всё работает!**

**НЕ ЗАКРЫВАЙ этот терминал!** Оставь его запущенным.

## 5. Git workflow (как работать)

### Шаг 1: Переходим на develop ветку

Открой новый терминал (`Ctrl+J`):

```bash
git checkout develop
git pull origin develop
```

### Шаг 2: Создаём свою ветку

```bash
git checkout -b feature/твоё-имя
```

Примеры хороших имён:
- `feature/auth-endpoints` (авторизация)
- `feature/practice-api` (решение задач)
- `feature/websocket-handler` (WebSocket)
- `feature/frontend-setup` (Next.js)

### Шаг 3: Работаешь!

Редактируй файлы в VSCode, сохраняй (`Ctrl+S`)

### Шаг 4: Коммитишь

```bash
git add .
git commit -m "feat: описание что сделал"
```

Примеры:
```bash
git commit -m "feat: создал POST /api/auth/register"
git commit -m "fix: исправил валидацию email"
```

### Шаг 5: Пушишь на GitHub

```bash
git push origin feature/твоё-имя
```

### Шаг 6: Создаёшь Pull Request

1. Открой GitHub репо в браузере
2. Вверху появится кнопка **"Compare & pull request"**
3. Нажми её
4. Напиши описание
5. Нажми **"Create Pull Request"**

Потом Андрей проверит код и одобрит!

## 6. Если что-то не работает

### "python: command not found"

**Windows:**

Переустанови Python, убедись что отмечен "Add Python to PATH"

**macOS/Linux:**

```bash
/opt/homebrew/bin/python3.12 --version
```

### "ModuleNotFoundError: No module named 'fastapi'"

Активируй виртуальное окружение!

**Windows:**
```bash
venv_backend\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv_backend/bin/activate
```

### "Порт 8000 занят"

**Windows (PowerShell):**

```bash
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force
```

**macOS/Linux:**

```bash
lsof -i :8000
kill -9 [PID]
```

Потом заново запусти: `uvicorn app.main:app --reload`

### "Не вижу файлы в VSCode"

`File → Open Folder` → выбери папку `olympiad-platform`

### "Git говорит fatal: not a git repository"

Убедись что открыл правильную папку в VSCode (olympiad-platform)

## 7. Каждый день перед началом

```bash
git checkout develop
git pull origin develop
git checkout feature/твоё-имя
```

И работаешь.

## 8. Твоя задача

Спроси у Андрея какую ветку делать:

- `feature/auth-endpoints` - регистрация и вход
- `feature/practice-api` - API для решения задач
- `feature/websocket-pvp` - PvP режим (real-time)
- `feature/frontend` - Next.js и UI

## 9. Checklist перед началом

```
[ ] Установил Python 3.12
[ ] Установил VSCode
[ ] Установил расширения (Python, GitLens)
[ ] Клонировал репо
[ ] Создал вирт. окружение (venv)
[ ] Активировал окружение ((venv_backend) в строке)
[ ] Установил зависимости (pip install)
[ ] Запустил backend (uvicorn)
[ ] Открывается http://localhost:8000/docs
[ ] Создал feature ветку
[ ] Знаю как коммитить
[ ] Знаю как пушить
```

Когда всё готово → ты готов! 🚀

---

Вопросы? Напиши в чат!