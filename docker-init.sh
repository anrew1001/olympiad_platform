#!/bin/bash

# Скрипт для инициализации БД в Docker контейнере

set -e

echo "=========================================="
echo "Olympeit Docker Initialization"
echo "=========================================="
echo ""

# Ждём пока PostgreSQL будет готов
echo "[1/4] Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec olympiad_postgres pg_isready -U olympiad > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 1
done

# Инициализируем БД
echo "[2/4] Initializing database..."
docker exec olympiad_backend python -m scripts.init_db
echo "✓ Database initialized"

# Загружаем задачи
echo "[3/4] Loading problems..."
docker exec olympiad_backend python -m scripts.load_grade10_mix
echo "✓ Problems loaded"

# Создаём админа
echo "[4/4] Creating admin account..."
docker exec olympiad_backend python -m scripts.create_admin
echo "✓ Admin created (username: admin, password: admin123)"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "API:      http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
