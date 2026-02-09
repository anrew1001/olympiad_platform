#!/bin/bash

##############################################################################
# Комплексная проверка PvP matchmaking системы
#
# Этот скрипт выполняет:
# 1. Синтаксис проверку Python кода
# 2. Пересоздание БД таблиц
# 3. Заливку тестовых данных
# 4. Все curl-тесты для 3 игроков
# 5. Вывод итогов (PASS/FAIL)
##############################################################################

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Переменные
BACKEND_DIR="/Users/andrewUG/VS_code/olympiad_platform/backend"
API_URL="http://localhost:8000"
TESTS_PASSED=0
TESTS_FAILED=0

##############################################################################
# Utility functions
##############################################################################

log_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

check_server() {
    if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${RED}✗ Server не отвечает на http://localhost:8000/api/health${NC}"
        echo -e "${RED}  Пожалуйста, запустите: uvicorn app.main:app --reload${NC}"
        exit 1
    fi
}

##############################################################################
# PHASE 1: Подготовка
##############################################################################

log_header "PHASE 1: Проверка синтаксиса Python"

cd "$BACKEND_DIR"
# venv уже может быть активирован в текущей оболочке, проверяем только наличие python
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python не найден. Активируй venv: source venv/bin/activate${NC}"
    exit 1
fi

# Синтаксис проверка новых файлов
if python -m py_compile app/services/matching.py 2>&1 | grep -q "SyntaxError"; then
    log_fail "services/matching.py содержит синтаксические ошибки"
    python -m py_compile app/services/matching.py
    exit 1
else
    log_pass "services/matching.py синтаксис OK"
fi

if python -m py_compile app/schemas/match.py 2>&1 | grep -q "SyntaxError"; then
    log_fail "schemas/match.py содержит синтаксические ошибки"
    python -m py_compile app/schemas/match.py
    exit 1
else
    log_pass "schemas/match.py синтаксис OK"
fi

if python -m py_compile app/routers/pvp.py 2>&1 | grep -q "SyntaxError"; then
    log_fail "routers/pvp.py содержит синтаксические ошибки"
    python -m py_compile app/routers/pvp.py
    exit 1
else
    log_pass "routers/pvp.py синтаксис OK"
fi

##############################################################################
# PHASE 2: Пересоздание БД
##############################################################################

log_header "PHASE 2: Пересоздание БД таблиц (из-за изменения schema)"

if python -m scripts.recreate_tables > /dev/null 2>&1; then
    log_pass "Таблицы пересоздана"
else
    log_fail "Ошибка пересоздания таблиц"
    python -m scripts.recreate_tables 2>&1 | head -20
    exit 1
fi

##############################################################################
# PHASE 3: Заливка тестовых данных
##############################################################################

log_header "PHASE 3: Заливка тестовых данных"

if python -m scripts.seed_tasks > /dev/null 2>&1; then
    log_pass "Задачи залиты в БД"
else
    log_fail "Ошибка при заливке задач"
    python -m scripts.seed_tasks 2>&1 | head -20
    exit 1
fi

##############################################################################
# PHASE 4: Проверка сервера
##############################################################################

log_header "PHASE 4: Проверка доступности сервера"

check_server
log_pass "API сервер доступен"

##############################################################################
# PHASE 5: API Tests
##############################################################################

log_header "PHASE 5: API тесты"

log_info "Регистрация игроков..."

# Регистрация игрока A
REGISTER_A=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"playerA_test","email":"a_test@test.com","password":"test123"}')

if echo "$REGISTER_A" | jq -e '.access_token' > /dev/null 2>&1; then
    log_pass "Игрок A зарегистрирован"
else
    log_fail "Регистрация игрока A"
    echo "$REGISTER_A" | jq '.'
fi

# Регистрация игрока B
REGISTER_B=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"playerB_test","email":"b_test@test.com","password":"test123"}')

if echo "$REGISTER_B" | jq -e '.access_token' > /dev/null 2>&1; then
    log_pass "Игрок B зарегистрирован"
else
    log_fail "Регистрация игрока B"
    echo "$REGISTER_B" | jq '.'
fi

# Регистрация игрока C
REGISTER_C=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"playerC_test","email":"c_test@test.com","password":"test123"}')

if echo "$REGISTER_C" | jq -e '.access_token' > /dev/null 2>&1; then
    log_pass "Игрок C зарегистрирован"
else
    log_fail "Регистрация игрока C"
fi

log_info "Логин и получение токенов..."

# Логин A
TOKEN_A=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"a_test@test.com","password":"test123"}' | jq -r '.access_token')

if [ ! -z "$TOKEN_A" ] && [ "$TOKEN_A" != "null" ]; then
    log_pass "Токен A получен"
else
    log_fail "Получение токена A"
    exit 1
fi

# Логин B
TOKEN_B=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"b_test@test.com","password":"test123"}' | jq -r '.access_token')

if [ ! -z "$TOKEN_B" ] && [ "$TOKEN_B" != "null" ]; then
    log_pass "Токен B получен"
else
    log_fail "Получение токена B"
fi

# Логин C
TOKEN_C=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"c_test@test.com","password":"test123"}' | jq -r '.access_token')

if [ ! -z "$TOKEN_C" ] && [ "$TOKEN_C" != "null" ]; then
    log_pass "Токен C получен"
else
    log_fail "Получение токена C"
fi

##############################################################################
# TEST 1: POST /api/pvp/find для A → waiting
##############################################################################

log_info "TEST 1: Игрок A ищет матч (должен создать waiting)"

FIND_A=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

MATCH_ID=$(echo "$FIND_A" | jq -r '.match_id')
STATUS_A=$(echo "$FIND_A" | jq -r '.status')
OPPONENT_A=$(echo "$FIND_A" | jq -r '.opponent')

if [ "$STATUS_A" = "waiting" ] && [ "$OPPONENT_A" = "null" ] && [ ! -z "$MATCH_ID" ] && [ "$MATCH_ID" != "null" ]; then
    log_pass "A создал waiting матч (match_id=$MATCH_ID, opponent=null)"
else
    log_fail "POST /api/pvp/find для A: expected waiting + null opponent, got status=$STATUS_A, opponent=$OPPONENT_A"
fi

##############################################################################
# TEST 2: POST /api/pvp/find для B → active + присоединение
##############################################################################

log_info "TEST 2: Игрок B ищет матч (должен присоединиться к A)"

FIND_B=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json")

MATCH_ID_B=$(echo "$FIND_B" | jq -r '.match_id')
STATUS_B=$(echo "$FIND_B" | jq -r '.status')
OPPONENT_B=$(echo "$FIND_B" | jq -r '.opponent.username')

if [ "$STATUS_B" = "active" ] && [ "$OPPONENT_B" = "playerA_test" ] && [ "$MATCH_ID_B" = "$MATCH_ID" ]; then
    log_pass "B присоединился к матчу A (match_id=$MATCH_ID_B, status=active, opponent=A)"
else
    log_fail "POST /api/pvp/find для B: expected active + opponent=playerA_test, got status=$STATUS_B, opponent=$OPPONENT_B"
fi

##############################################################################
# TEST 3: GET /api/pvp/match/{match_id} с проверкой що answer НЕ в ответе
##############################################################################

log_info "TEST 3: GET /api/pvp/match/$MATCH_ID (проверка что answer НЕ в ответе)"

MATCH_DETAIL=$(curl -s -X GET "$API_URL/api/pvp/match/$MATCH_ID" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

PLAYER1=$(echo "$MATCH_DETAIL" | jq -r '.player1.username')
PLAYER2=$(echo "$MATCH_DETAIL" | jq -r '.player2.username')
TASK_COUNT=$(echo "$MATCH_DETAIL" | jq '.match_tasks | length')
HAS_ANSWER=$(echo "$MATCH_DETAIL" | jq '.match_tasks[0] | has("answer")')

if [ "$PLAYER1" = "playerA_test" ] && [ "$PLAYER2" = "playerB_test" ]; then
    log_pass "Матч детали загружены (player1=A, player2=B)"
else
    log_fail "Матч детали: player1=$PLAYER1, player2=$PLAYER2"
fi

if [ "$TASK_COUNT" = "5" ]; then
    log_pass "Матч содержит 5 задач"
else
    log_fail "Матч содержит $TASK_COUNT задач, ожидалось 5"
fi

if [ "$HAS_ANSWER" = "false" ]; then
    log_pass "SECURITY OK: поле 'answer' НЕ в ответе"
else
    log_fail "SECURITY ISSUE: поле 'answer' найдено в ответе"
fi

##############################################################################
# TEST 4: Защита от дубля — A снова ищет матч → 409
##############################################################################

log_info "TEST 4: Игрок A пытается найти еще один матч (должен получить 409)"

FIND_A_DUP=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

if [ "$STATUS_CODE" = "409" ]; then
    log_pass "POST /api/pvp/find повторно для A вернул 409 Conflict"
else
    log_fail "POST /api/pvp/find повторно для A вернул $STATUS_CODE, ожидалось 409"
fi

##############################################################################
# TEST 5: Поиск матча для C → создает новый waiting
##############################################################################

log_info "TEST 5: Игрок C ищет матч (должен создать новый waiting)"

FIND_C=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")

MATCH_ID_C=$(echo "$FIND_C" | jq -r '.match_id')
STATUS_C=$(echo "$FIND_C" | jq -r '.status')
OPPONENT_C=$(echo "$FIND_C" | jq -r '.opponent')

if [ "$STATUS_C" = "waiting" ] && [ "$OPPONENT_C" = "null" ] && [ ! -z "$MATCH_ID_C" ] && [ "$MATCH_ID_C" != "$MATCH_ID" ]; then
    log_pass "C создал новый waiting матч (match_id=$MATCH_ID_C ≠ $MATCH_ID)"
else
    log_fail "POST /api/pvp/find для C: expected new waiting match, got status=$STATUS_C"
fi

##############################################################################
# TEST 6: Отмена поиска — DELETE /api/pvp/find для C
##############################################################################

log_info "TEST 6: Игрок C отменяет поиск (DELETE /api/pvp/find)"

CANCEL_C=$(curl -s -X DELETE "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")

CANCELLED=$(echo "$CANCEL_C" | jq -r '.cancelled')

if [ "$CANCELLED" = "true" ]; then
    log_pass "DELETE /api/pvp/find для C вернул cancelled=true"
else
    log_fail "DELETE /api/pvp/find для C: expected cancelled=true, got $CANCELLED"
fi

##############################################################################
# TEST 7: Контроль доступа — C не может видеть матч A+B
##############################################################################

log_info "TEST 7: Контроль доступа — C пытается получить матч A+B (должен получить 403)"

STATUS_CODE_403=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/api/pvp/match/$MATCH_ID" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")

if [ "$STATUS_CODE_403" = "403" ]; then
    log_pass "GET /api/pvp/match/$MATCH_ID для non-participant вернул 403 Forbidden"
else
    log_fail "GET /api/pvp/match/$MATCH_ID для C вернул $STATUS_CODE_403, ожидалось 403"
fi

##############################################################################
# SUMMARY
##############################################################################

log_header "ИТОГИ ТЕСТИРОВАНИЯ"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))

echo -e "${GREEN}✓ Пройдено: $TESTS_PASSED/$TOTAL${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}✗ Ошибок: $TESTS_FAILED/$TOTAL${NC}"
else
    echo -e "${GREEN}✗ Ошибок: 0${NC}"
fi

echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! PvP Matchmaking работает!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ❌ ЕСТЬ ОШИБКИ. Смотри выше подробности.${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 1
fi
