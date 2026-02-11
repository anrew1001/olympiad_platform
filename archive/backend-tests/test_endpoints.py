"""
Скрипт для проверки корректности регистрации эндпоинтов.

Использование:
    python test_endpoints.py
"""

import sys
sys.path.insert(0, '.')

from app.main import app


def test_endpoints_registered():
    """Проверка что эндпоинты зарегистрированы корректно"""

    print("Проверка зарегистрированных эндпоинтов:\n")

    # Получаем все маршруты
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method != 'HEAD':  # Игнорируем HEAD методы
                    routes.append({
                        'method': method,
                        'path': route.path,
                        'name': route.name
                    })

    # Группируем по префиксам
    tasks_routes = [r for r in routes if r['path'].startswith('/api/tasks')]
    auth_routes = [r for r in routes if r['path'].startswith('/api/auth')]
    health_routes = [r for r in routes if r['path'].startswith('/api/health')]

    # Проверка эндпоинтов для tasks
    print("📋 Tasks API:")
    expected_tasks = [
        ('GET', '/api/tasks', 'get_tasks'),
        ('GET', '/api/tasks/{task_id}', 'get_task'),
    ]

    for method, path, name in expected_tasks:
        found = any(r['method'] == method and r['path'] == path and r['name'] == name for r in tasks_routes)
        status = "✓" if found else "✗"
        print(f"  {status} {method:6} {path:30} ({name})")

    # Проверка схем
    print("\n📦 Pydantic схемы:")
    try:
        from app.schemas.task import TaskInList, TaskDetail, PaginatedTaskResponse
        print("  ✓ TaskInList")
        print("  ✓ TaskDetail")
        print("  ✓ PaginatedTaskResponse")

        # Проверка что answer не в схемах
        task_in_list_fields = TaskInList.model_fields.keys()
        task_detail_fields = TaskDetail.model_fields.keys()

        if 'answer' not in task_in_list_fields:
            print("  ✓ TaskInList НЕ содержит поле 'answer' (КРИТИЧНО!)")
        else:
            print("  ✗ ОШИБКА: TaskInList содержит поле 'answer'!")

        if 'answer' not in task_detail_fields:
            print("  ✓ TaskDetail НЕ содержит поле 'answer' (КРИТИЧНО!)")
        else:
            print("  ✗ ОШИБКА: TaskDetail содержит поле 'answer'!")

    except ImportError as e:
        print(f"  ✗ Ошибка импорта схем: {e}")

    # Проверка модели
    print("\n💾 Модель Task:")
    try:
        from app.models import Task
        print("  ✓ Task модель импортирована")

        # Проверка полей
        expected_fields = ['subject', 'topic', 'difficulty', 'title', 'text', 'answer', 'hints']
        for field in expected_fields:
            if hasattr(Task, field):
                print(f"  ✓ Поле '{field}' присутствует")
            else:
                print(f"  ✗ Поле '{field}' отсутствует!")

    except ImportError as e:
        print(f"  ✗ Ошибка импорта модели: {e}")

    # Общая статистика
    print(f"\n📊 Статистика:")
    print(f"  Всего эндпоинтов: {len(routes)}")
    print(f"  - Tasks API: {len(tasks_routes)}")
    print(f"  - Auth API: {len(auth_routes)}")
    print(f"  - Health API: {len(health_routes)}")

    print("\n✓ Проверка завершена!")


if __name__ == "__main__":
    test_endpoints_registered()
