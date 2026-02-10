#!/bin/bash
# Быстрая проверка API — предполагает что БД и сервер уже запущены

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
PASS=0
FAIL=0

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

log_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Проверка сервера
log_header "Проверка доступности сервера"
if curl -s http://localhost:8000/api/health | jq . > /dev/null 2>&1; then
    log_pass "API сервер доступен"
else
    echo -e "${RED}Ошибка: API недоступен на $API_URL${NC}"
    echo -e "${RED}Запустите: uvicorn app.main:app --reload${NC}"
    exit 1
fi

log_header "Регистрация игроков"

# A
curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"a_qtest","email":"a_q@test.com","password":"test123"}' > /dev/null
log_pass "Игрок A зарегистрирован"

# B
curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"b_qtest","email":"b_q@test.com","password":"test123"}' > /dev/null
log_pass "Игрок B зарегистрирован"

# C
curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"c_qtest","email":"c_q@test.com","password":"test123"}' > /dev/null
log_pass "Игрок C зарегистрирован"

log_header "Получение токенов"

TOKEN_A=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"a_q@test.com","password":"test123"}' | jq -r '.access_token')
[ ! -z "$TOKEN_A" ] && [ "$TOKEN_A" != "null" ] && log_pass "Токен A" || log_fail "Токен A"

TOKEN_B=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"b_q@test.com","password":"test123"}' | jq -r '.access_token')
[ ! -z "$TOKEN_B" ] && [ "$TOKEN_B" != "null" ] && log_pass "Токен B" || log_fail "Токен B"

TOKEN_C=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"c_q@test.com","password":"test123"}' | jq -r '.access_token')
[ ! -z "$TOKEN_C" ] && [ "$TOKEN_C" != "null" ] && log_pass "Токен C" || log_fail "Токен C"

log_header "TEST 1: A создает waiting матч"

FIND_A=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

MATCH_ID=$(echo "$FIND_A" | jq -r '.match_id')
STATUS=$(echo "$FIND_A" | jq -r '.status')
OPPONENT=$(echo "$FIND_A" | jq -r '.opponent')

[ "$STATUS" = "waiting" ] && [ "$OPPONENT" = "null" ] && log_pass "A: waiting матч (id=$MATCH_ID)" || log_fail "A: ожидалось waiting + null opponent, получено status=$STATUS, opponent=$OPPONENT"

log_header "TEST 2: B присоединяется к матчу A"

FIND_B=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json")

STATUS_B=$(echo "$FIND_B" | jq -r '.status')
MATCH_ID_B=$(echo "$FIND_B" | jq -r '.match_id')
OPPONENT_B=$(echo "$FIND_B" | jq -r '.opponent.username')

[ "$STATUS_B" = "active" ] && [ "$MATCH_ID_B" = "$MATCH_ID" ] && [ "$OPPONENT_B" = "a_qtest" ] && \
    log_pass "B: присоединился (match_id=$MATCH_ID, status=active)" || \
    log_fail "B: ожидалось active + match_id=$MATCH_ID + opponent=a_qtest, получено status=$STATUS_B, id=$MATCH_ID_B, opp=$OPPONENT_B"

log_header "TEST 3: GET матч детали + проверка нет answer"

DETAIL=$(curl -s -X GET "$API_URL/api/pvp/match/$MATCH_ID" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")

P1=$(echo "$DETAIL" | jq -r '.player1.username')
P2=$(echo "$DETAIL" | jq -r '.player2.username')
TASK_COUNT=$(echo "$DETAIL" | jq '.match_tasks | length')
HAS_ANSWER=$(echo "$DETAIL" | jq '.match_tasks[0] | has("answer")')

[ "$P1" = "a_qtest" ] && log_pass "player1 = A" || log_fail "player1 = $P1"
[ "$P2" = "b_qtest" ] && log_pass "player2 = B" || log_fail "player2 = $P2"
[ "$TASK_COUNT" = "5" ] && log_pass "5 задач в матче" || log_fail "$TASK_COUNT задач (ожидалось 5)"
[ "$HAS_ANSWER" = "false" ] && log_pass "SECURITY: answer НЕ в ответе" || log_fail "SECURITY: answer присутствует!"

log_header "TEST 4: Защита от дубля — A повторно (409)"

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json")
[ "$STATUS_CODE" = "409" ] && log_pass "A повторно: 409 Conflict" || log_fail "A повторно: код $STATUS_CODE (ожидалось 409)"

log_header "TEST 5: C создает новый waiting матч"

FIND_C=$(curl -s -X POST "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")

STATUS_C=$(echo "$FIND_C" | jq -r '.status')
MATCH_ID_C=$(echo "$FIND_C" | jq -r '.match_id')

[ "$STATUS_C" = "waiting" ] && [ "$MATCH_ID_C" != "$MATCH_ID" ] && \
    log_pass "C: новый waiting матч (id=$MATCH_ID_C)" || \
    log_fail "C: status=$STATUS_C, id=$MATCH_ID_C (ожидалось новый waiting)"

log_header "TEST 6: DELETE /find для C (отмена поиска)"

CANCEL=$(curl -s -X DELETE "$API_URL/api/pvp/find" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")

CANCELLED=$(echo "$CANCEL" | jq -r '.cancelled')
[ "$CANCELLED" = "true" ] && log_pass "C: отмена поиска (cancelled=true)" || log_fail "C: cancelled=$CANCELLED (ожидалось true)"

log_header "TEST 7: Контроль доступа — C не видит матч A+B (403)"

STATUS_CODE_403=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/api/pvp/match/$MATCH_ID" \
  -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json")
[ "$STATUS_CODE_403" = "403" ] && log_pass "C: 403 при доступе к чужому матчу" || log_fail "C: код $STATUS_CODE_403 (ожидалось 403)"

log_header "ИТОГИ"

TOTAL=$((PASS + FAIL))
echo -e "${GREEN}✓ Пройдено: $PASS/$TOTAL${NC}"
[ $FAIL -gt 0 ] && echo -e "${RED}✗ Ошибок: $FAIL${NC}" || echo -e "${GREEN}✗ Ошибок: 0${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 0
else
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ❌ ЕСТЬ ОШИБКИ${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 1
fi
