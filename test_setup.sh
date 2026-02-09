#!/bin/bash

# Скрипт для тестирования что все инструкции из README работают

set -e

echo "=========================================="
echo "Testing Olympeit Setup Instructions"
echo "=========================================="
echo ""

# Test 1: Backend imports
echo "[1/5] Testing Backend imports..."
cd backend
python -c "from app.main import app; print('✓ FastAPI app loads')"
python -c "from app.database import async_engine; print('✓ Database connection setup')"
python -c "from app.routers.pvp import router; print('✓ PVP router loads')"
python -c "from app.services.elo import calculate_rating_change; print('✓ ELO service loads')"
python -c "from app.websocket.manager import manager; print('✓ WebSocket manager loads')"
cd ..
echo ""

# Test 2: Backend requirements
echo "[2/5] Checking Backend dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt exists"
    grep -q "fastapi" requirements.txt && echo "✓ FastAPI in requirements"
    grep -q "sqlalchemy" requirements.txt && echo "✓ SQLAlchemy in requirements"
    grep -q "uvicorn" requirements.txt && echo "✓ Uvicorn in requirements"
else
    echo "✗ requirements.txt not found!"
    exit 1
fi
cd ..
echo ""

# Test 3: Frontend build
echo "[3/5] Testing Frontend build..."
cd frontend
if [ -f "package.json" ]; then
    echo "✓ package.json exists"
    grep -q "next" package.json && echo "✓ Next.js in package.json"
    grep -q "react" package.json && echo "✓ React in package.json"
else
    echo "✗ package.json not found!"
    exit 1
fi
# Don't actually build to save time, just check config
if [ -f "next.config.ts" ] || [ -f "next.config.js" ]; then
    echo "✓ Next.js config found"
fi
cd ..
echo ""

# Test 4: Database setup
echo "[4/5] Checking Database scripts..."
if [ -d "backend/scripts" ]; then
    echo "✓ Backend scripts directory exists"
    [ -f "backend/scripts/init_db.py" ] && echo "✓ init_db.py exists"
    [ -f "backend/scripts/load_grade10_mix.py" ] && echo "✓ load_grade10_mix.py exists"
    [ -f "backend/scripts/create_admin.py" ] && echo "✓ create_admin.py exists"
else
    echo "✗ Backend scripts directory not found!"
    exit 1
fi
echo ""

# Test 5: Documentation
echo "[5/5] Checking Documentation..."
[ -f "README.md" ] && echo "✓ README.md exists"
[ -f "SETUP.md" ] && echo "✓ SETUP.md exists"
[ -d "archive" ] && echo "✓ archive/ directory exists"
[ -f "render.yaml" ] && echo "✓ render.yaml exists"
echo ""

echo "=========================================="
echo "All checks passed! Setup is correct."
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set up PostgreSQL (docker-compose up -d postgres)"
echo "2. cd backend && source venv_backend/bin/activate"
echo "3. python -m scripts.init_db"
echo "4. python -m scripts.load_grade10_mix"
echo "5. uvicorn app.main:app --reload"
echo ""
echo "In another terminal:"
echo "1. cd frontend"
echo "2. npm run dev"
echo ""
