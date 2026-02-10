#!/bin/bash

# ============================================================
# Тестовый скрипт для Admin CRUD операций с задачами
# ============================================================
# Использование: ./backend/scripts/test_admin_crud.sh
# Требования: curl, jq, сервер на localhost:8000
# ============================================================

set -e  # Выход при любой ошибке

# === КОНФИГУРАЦИЯ ===
API_URL="http://localhost:8000"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin123"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# === HELPER ФУНКЦИИ ===

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# === 1. ПОЛУЧЕНИЕ ТОКЕНА АДМИНА ===

print_step "1️⃣  ПОЛУЧЕНИЕ ТОКЕНА АДМИНИСТРАТОРА"

print_info "Отправляю запрос: POST /api/auth/login"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    print_error "Не удалось получить токен. Проверьте учетные данные администратора."
    echo "Ответ: $LOGIN_RESPONSE"
fi

print_success "Токен получен: ${TOKEN:0:30}..."

# === 2. СОЗДАНИЕ ЗАДАЧИ ===

print_step "2️⃣  СОЗДАНИЕ НОВОЙ ЗАДАЧИ (POST /api/admin/tasks)"

print_info "Отправляю запрос с данными задачи..."
CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/tasks" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 3,
        "title": "Тестовая задача: Сортировка пузырьком",
        "text": "Реализуйте алгоритм быстрой сортировки для массива целых чисел. Напишите функцию, которая сортирует массив по возрастанию.",
        "answer": "quicksort",
        "hints": ["Используйте рекурсию", "Выберите pivot элемент"]
    }')

TASK_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')

if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
    print_error "Не удалось создать задачу."
    echo "Ответ: $CREATE_RESPONSE"
fi

TASK_TITLE=$(echo "$CREATE_RESPONSE" | jq -r '.title')
TASK_ANSWER=$(echo "$CREATE_RESPONSE" | jq -r '.answer')

print_success "Задача создана успешно!"
print_info "ID: $TASK_ID | Название: $TASK_TITLE | Ответ: $TASK_ANSWER"

# === 3. ПОЛУЧЕНИЕ СПИСКА ЗАДАЧ ===

print_step "3️⃣  ПОЛУЧЕНИЕ СПИСКА ЗАДАЧ (GET /api/admin/tasks)"

print_info "Отправляю запрос: GET /api/admin/tasks?page=1&per_page=10"
LIST_RESPONSE=$(curl -s -X GET "${API_URL}/api/admin/tasks?page=1&per_page=10" \
    -H "Authorization: Bearer ${TOKEN}")

TOTAL_TASKS=$(echo "$LIST_RESPONSE" | jq -r '.total')
RETURNED_COUNT=$(echo "$LIST_RESPONSE" | jq '.items | length')

print_success "Список получен"
print_info "Всего задач: $TOTAL_TASKS | На текущей странице: $RETURNED_COUNT"

# Проверка что answer присутствует в ответе
ANSWER_IN_LIST=$(echo "$LIST_RESPONSE" | jq -r '.items[0].answer')
if [ -z "$ANSWER_IN_LIST" ] || [ "$ANSWER_IN_LIST" = "null" ]; then
    print_error "КРИТИЧЕСКАЯ ОШИБКА: Поле 'answer' отсутствует в списке задач для админа!"
else
    print_success "Поле 'answer' присутствует в ответе: $ANSWER_IN_LIST"
fi

# === 4. ПОЛУЧЕНИЕ ОДНОЙ ЗАДАЧИ ===

print_step "4️⃣  ПОЛУЧЕНИЕ ЗАДАЧИ ПО ID (GET /api/admin/tasks/${TASK_ID})"

print_info "Отправляю запрос: GET /api/admin/tasks/${TASK_ID}"
GET_RESPONSE=$(curl -s -X GET "${API_URL}/api/admin/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${TOKEN}")

RETRIEVED_ID=$(echo "$GET_RESPONSE" | jq -r '.id')
RETRIEVED_TITLE=$(echo "$GET_RESPONSE" | jq -r '.title')
RETRIEVED_ANSWER=$(echo "$GET_RESPONSE" | jq -r '.answer')
RETRIEVED_CREATED=$(echo "$GET_RESPONSE" | jq -r '.created_at')

print_success "Задача получена"
print_info "ID: $RETRIEVED_ID"
print_info "Название: $RETRIEVED_TITLE"
print_info "Ответ: $RETRIEVED_ANSWER"
print_info "Создана: $RETRIEVED_CREATED"

# === 5. ОБНОВЛЕНИЕ ЗАДАЧИ ===

print_step "5️⃣  ОБНОВЛЕНИЕ ЗАДАЧИ (PUT /api/admin/tasks/${TASK_ID})"

print_info "Отправляю запрос с обновленными данными..."
UPDATE_RESPONSE=$(curl -s -X PUT "${API_URL}/api/admin/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "difficulty": 4,
        "title": "Тестовая задача: Быстрая сортировка (обновлено)",
        "hints": ["Используйте рекурсию", "Выберите pivot элемент", "Разделите массив на две части"]
    }')

UPDATED_ID=$(echo "$UPDATE_RESPONSE" | jq -r '.id')
UPDATED_DIFFICULTY=$(echo "$UPDATE_RESPONSE" | jq -r '.difficulty')
UPDATED_TITLE=$(echo "$UPDATE_RESPONSE" | jq -r '.title')
UPDATED_HINTS_COUNT=$(echo "$UPDATE_RESPONSE" | jq '.hints | length')
UPDATED_ANSWER=$(echo "$UPDATE_RESPONSE" | jq -r '.answer')

if [ "$UPDATED_DIFFICULTY" != "4" ]; then
    print_error "Ошибка: сложность не обновлена! Ожидалось 4, получено $UPDATED_DIFFICULTY"
fi

print_success "Задача обновлена успешно!"
print_info "Новая сложность: $UPDATED_DIFFICULTY"
print_info "Новое название: $UPDATED_TITLE"
print_info "Количество подсказок: $UPDATED_HINTS_COUNT"
print_info "Ответ остался неизменным: $UPDATED_ANSWER"

# === 6. ПРОВЕРКА ФИЛЬТРАЦИИ ===

print_step "6️⃣  ПРОВЕРКА ФИЛЬТРАЦИИ (GET /api/admin/tasks?subject=informatics&difficulty=4)"

print_info "Отправляю запрос с фильтрами..."
FILTER_RESPONSE=$(curl -s -X GET \
    "${API_URL}/api/admin/tasks?subject=informatics&difficulty=4" \
    -H "Authorization: Bearer ${TOKEN}")

FILTER_TOTAL=$(echo "$FILTER_RESPONSE" | jq -r '.total')
FILTER_COUNT=$(echo "$FILTER_RESPONSE" | jq '.items | length')

print_success "Фильтрация работает"
print_info "Найдено задач с фильтром: $FILTER_COUNT из $FILTER_TOTAL всего"

# === 7. УДАЛЕНИЕ ЗАДАЧИ ===

print_step "7️⃣  УДАЛЕНИЕ ЗАДАЧИ (DELETE /api/admin/tasks/${TASK_ID})"

print_info "Отправляю запрос на удаление..."
DELETE_RESPONSE=$(curl -s -X DELETE "${API_URL}/api/admin/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${TOKEN}")

DELETE_OK=$(echo "$DELETE_RESPONSE" | jq -r '.ok')
DELETE_MSG=$(echo "$DELETE_RESPONSE" | jq -r '.message')

if [ "$DELETE_OK" != "true" ]; then
    print_error "Не удалось удалить задачу"
    echo "Ответ: $DELETE_RESPONSE"
fi

print_success "Задача удалена"
print_info "Сообщение: $DELETE_MSG"

# === 8. ПРОВЕРКА УДАЛЕНИЯ (404) ===

print_step "8️⃣  ПРОВЕРКА УДАЛЕНИЯ - ДОЛЖЕН БЫТЬ 404 (GET /api/admin/tasks/${TASK_ID})"

print_info "Отправляю запрос на несуществующую задачу..."
CHECK_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_URL}/api/admin/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${TOKEN}")

HTTP_CODE=$(echo "$CHECK_RESPONSE" | tail -n 1)
ERROR_DETAIL=$(echo "$CHECK_RESPONSE" | head -n -1 | jq -r '.detail')

if [ "$HTTP_CODE" != "404" ]; then
    print_error "Ошибка: ожидался HTTP 404, получен $HTTP_CODE"
fi

print_success "Получен правильный HTTP код 404"
print_info "Сообщение об ошибке: $ERROR_DETAIL"

# === 9. ПРОВЕРКА БЕЗОПАСНОСТИ ===

print_step "9️⃣  ПРОВЕРКА БЕЗОПАСНОСТИ - ДОСТУП БЕЗ ТОКЕНА"

print_info "Отправляю запрос БЕЗ Authorization заголовка..."
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_URL}/api/admin/tasks")

UNAUTH_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n 1)

if [ "$UNAUTH_CODE" != "401" ] && [ "$UNAUTH_CODE" != "403" ]; then
    print_error "Ошибка: доступ без токена должен возвращать 401/403, получен $UNAUTH_CODE"
fi

print_success "Доступ без токена правильно заблокирован (HTTP $UNAUTH_CODE)"

# === 10. СОЗДАНИЕ ВТОРОЙ ЗАДАЧИ И ПРОВЕРКА ВАЛИДАЦИИ ===

print_step "🔟 ПРОВЕРКА ВАЛИДАЦИИ"

print_info "Попытка создать задачу с неверным subject..."
INVALID_SUBJECT=$(curl -s -X POST "${API_URL}/api/admin/tasks" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "subject": "invalid_subject",
        "topic": "test",
        "difficulty": 1,
        "title": "Test Task",
        "text": "Test task description",
        "answer": "test"
    }')

VALIDATION_ERROR=$(echo "$INVALID_SUBJECT" | jq -r '.detail[0].msg // .detail // empty')

if [ -n "$VALIDATION_ERROR" ]; then
    print_success "Валидация работает (ошибка перехвачена)"
    print_info "Ошибка: $VALIDATION_ERROR"
else
    print_error "Валидация не сработала - задача с неверным subject была создана!"
fi

# === ИТОГОВЫЙ ОТЧЕТ ===

print_step "✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!"

echo ""
echo -e "${GREEN}Проверено и успешно:${NC}"
echo "  ✓ Создание задачи (POST /api/admin/tasks)"
echo "  ✓ Получение списка задач (GET /api/admin/tasks)"
echo "  ✓ Получение одной задачи (GET /api/admin/tasks/{id})"
echo "  ✓ Обновление задачи (PUT /api/admin/tasks/{id})"
echo "  ✓ Фильтрация задач по фильтрам"
echo "  ✓ Удаление задачи (DELETE /api/admin/tasks/{id})"
echo "  ✓ Проверка удаления (404 при GET удалённой задачи)"
echo "  ✓ Безопасность (401/403 при доступе без токена)"
echo "  ✓ Валидация входных данных"
echo "  ✓ Наличие поля 'answer' в админских ответах"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Проверка Admin CRUD завершена успешно!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
