"""
Скрипт для заполнения БД тестовыми задачами.

Использование:
    cd backend
    python seed_tasks.py
"""

import asyncio
import sys

from sqlalchemy import select

sys.path.insert(0, '.')

from app.database import async_session_maker, init_db
from app.models import Task


async def seed_tasks():
    """Наполнение БД тестовыми задачами"""

    # Инициализация БД (создание таблиц)
    await init_db()
    print("✓ База данных инициализирована")

    # Тестовые задачи
    tasks = [
        Task(
            subject="informatics",
            topic="algorithms",
            difficulty=2,
            title="Сортировка пузырьком",
            text="Реализуйте алгоритм сортировки пузырьком для массива целых чисел. Функция должна принимать массив и возвращать отсортированный массив.",
            answer="def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
            hints=["Используйте вложенный цикл", "Сравнивайте соседние элементы", "Меняйте местами если первый больше второго"]
        ),
        Task(
            subject="mathematics",
            topic="geometry",
            difficulty=1,
            title="Площадь треугольника",
            text="Найдите площадь треугольника со сторонами a=3, b=4, c=5. Используйте формулу Герона.",
            answer="6",
            hints=["Вычислите полупериметр s = (a+b+c)/2", "Используйте формулу S = sqrt(s*(s-a)*(s-b)*(s-c))", "Это прямоугольный треугольник, можно проверить через S = (a*b)/2"]
        ),
        Task(
            subject="informatics",
            topic="data_structures",
            difficulty=3,
            title="Реализация стека",
            text="Реализуйте структуру данных 'стек' с операциями push, pop, peek и isEmpty. Используйте список Python.",
            answer="class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        return self.items.pop()\n    def peek(self):\n        return self.items[-1]\n    def isEmpty(self):\n        return len(self.items) == 0",
            hints=["Стек работает по принципу LIFO (Last In First Out)", "Используйте методы append() и pop() для списка", "peek() возвращает последний элемент без удаления"]
        ),
        Task(
            subject="mathematics",
            topic="algebra",
            difficulty=2,
            title="Квадратное уравнение",
            text="Решите квадратное уравнение x² - 5x + 6 = 0. Найдите оба корня.",
            answer="x1 = 2, x2 = 3",
            hints=["Используйте формулу дискриминанта D = b² - 4ac", "x = (-b ± √D) / 2a", "Проверьте ответ подстановкой"]
        ),
        Task(
            subject="informatics",
            topic="algorithms",
            difficulty=4,
            title="Бинарный поиск",
            text="Реализуйте алгоритм бинарного поиска для поиска элемента в отсортированном массиве. Функция должна возвращать индекс элемента или -1 если элемент не найден.",
            answer="def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
            hints=["Массив должен быть отсортирован", "Сравнивайте с элементом в середине", "Отбрасывайте половину массива на каждой итерации", "Сложность O(log n)"]
        ),
        Task(
            subject="mathematics",
            topic="combinatorics",
            difficulty=3,
            title="Число сочетаний",
            text="Вычислите количество способов выбрать 3 элемента из 5 (C(5,3)). Используйте формулу сочетаний.",
            answer="10",
            hints=["C(n,k) = n! / (k! * (n-k)!)", "C(5,3) = 5! / (3! * 2!)", "Можно упростить: C(5,3) = (5*4*3) / (3*2*1) = 60/6"]
        ),
        Task(
            subject="informatics",
            topic="graphs",
            difficulty=5,
            title="Алгоритм Дейкстры",
            text="Реализуйте алгоритм Дейкстры для поиска кратчайшего пути в взвешенном графе. Граф представлен списком смежности.",
            answer="import heapq\n\ndef dijkstra(graph, start):\n    distances = {node: float('inf') for node in graph}\n    distances[start] = 0\n    pq = [(0, start)]\n    \n    while pq:\n        current_dist, current_node = heapq.heappop(pq)\n        \n        if current_dist > distances[current_node]:\n            continue\n            \n        for neighbor, weight in graph[current_node]:\n            distance = current_dist + weight\n            if distance < distances[neighbor]:\n                distances[neighbor] = distance\n                heapq.heappush(pq, (distance, neighbor))\n    \n    return distances",
            hints=["Используйте приоритетную очередь (heap)", "Храните расстояния до всех вершин", "Обновляйте расстояния если нашли более короткий путь", "Не забудьте про инициализацию расстояния до стартовой вершины как 0"]
        ),
        Task(
            subject="mathematics",
            topic="number_theory",
            difficulty=2,
            title="НОД двух чисел",
            text="Найдите наибольший общий делитель (НОД) чисел 48 и 18. Используйте алгоритм Евклида.",
            answer="6",
            hints=["Алгоритм Евклида: НОД(a,b) = НОД(b, a mod b)", "НОД(48, 18) = НОД(18, 12) = НОД(12, 6) = НОД(6, 0) = 6", "Процесс продолжается пока остаток не станет 0"]
        ),
    ]

    async with async_session_maker() as session:
        # Проверка существующих задач
        result = await session.execute(select(Task))
        existing_tasks = result.scalars().all()

        if not existing_tasks:
            session.add_all(tasks)
            await session.commit()
            print(f"✓ Добавлено {len(tasks)} тестовых задач")

            # Вывод статистики
            for task in tasks:
                print(f"  - [{task.subject}/{task.topic}] {task.title} (сложность: {task.difficulty})")
        else:
            print(f"⚠ База уже содержит {len(existing_tasks)} задач. Очистите БД перед повторным запуском.")


if __name__ == "__main__":
    print("Запуск скрипта заполнения БД тестовыми задачами...\n")
    asyncio.run(seed_tasks())
    print("\n✓ Готово!")
