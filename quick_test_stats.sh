#!/bin/bash

# ============================================================================
# quick_test_stats.sh - Быстрый тест нового endpoint
# ============================================================================
# Использование:
#   1. Получить токен пользователя из панели администратора или логина
#   2. export USER_TOKEN="ваш_jwt_токен"
#   3. ./quick_test_stats.sh
# ============================================================================

API_URL="${API_URL:-http://localhost:8000}"
TOKEN="${USER_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "❌ Ошибка: Переменная USER_TOKEN не установлена"
    echo ""
    echo "Пожалуйста, получите JWT токен и установите переменную:"
    echo "  export USER_TOKEN='ваш_jwt_токен_здесь'"
    echo ""
    echo "Токен можно получить через логин:"
    echo "  curl -X POST http://localhost:8000/api/auth/login \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"username\": \"your_username\", \"password\": \"your_password\"}'"
    echo ""
    exit 1
fi

echo "🔍 Тестирование новой статистики..."
echo ""
echo "API URL: $API_URL"
echo "Token: ${TOKEN:0:30}..."
echo ""

# ============================================================================
# Проверка доступности API
# ============================================================================

echo "📡 Проверка доступности API..."
if ! curl -s -f "$API_URL/docs" > /dev/null 2>&1; then
    echo "❌ API недоступен на $API_URL"
    exit 1
fi
echo "✅ API доступен"
echo ""

# ============================================================================
# Вызов endpoint статистики
# ============================================================================

echo "📊 Загрузка детальной статистики..."
echo ""

RESPONSE=$(curl -s -X GET "$API_URL/api/users/me/matches/stats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

# Проверить ошибки
if echo "$RESPONSE" | grep -q "401\|403\|Unauthorized"; then
    echo "❌ Ошибка авторизации (401/403)"
    echo "Токен может быть неправильным или истекшим"
    echo ""
    echo "Ответ:"
    echo "$RESPONSE"
    exit 1
fi

if echo "$RESPONSE" | grep -q "error"; then
    echo "❌ Ошибка API"
    echo "$RESPONSE"
    exit 1
fi

# ============================================================================
# Красивый вывод результатов
# ============================================================================

echo "✅ Статистика получена!"
echo ""
echo "════════════════════════════════════════════════════════════════"

# Проверить наличие jq и красиво вывести JSON
if command -v jq &> /dev/null; then
    echo "$RESPONSE" | jq '.'
else
    # Fallback на raw JSON
    echo "$RESPONSE"
fi

echo "════════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# Проверка критических полей
# ============================================================================

echo "🔍 Проверка новых полей..."
echo ""

if command -v jq &> /dev/null; then
    FIELDS=(
        "current_streak"
        "best_win_streak"
        "strongest_topics"
        "weakest_topics"
    )

    for field in "${FIELDS[@]}"; do
        VALUE=$(echo "$RESPONSE" | jq ".$field" 2>/dev/null || echo "NOT_FOUND")
        if [ "$VALUE" = "NOT_FOUND" ]; then
            echo "❌ Поле '$field' отсутствует"
        else
            echo "✅ '$field': $VALUE"
        fi
    done
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✨ Тестирование завершено!"
echo "════════════════════════════════════════════════════════════════"
echo ""
