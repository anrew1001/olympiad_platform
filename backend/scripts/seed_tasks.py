"""
Скрипт для заполнения БД тестовыми задачами.

Создаёт задачи разных уровней сложности по разным темам.
Используется для подготовки data для разработки и тестирования.

Запуск:
    cd backend
    python -m scripts.seed_tasks
"""
import asyncio
from app.database import async_session_maker
from app.models import Task


# Задачи по темам и сложности
TASKS_DATA = [
    # Informatics — Algorithms
    {
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 1,
        "title": "Сумма двух чисел",
        "text": "Напишите функцию, которая возвращает сумму двух чисел.",
        "answer": "def sum(a, b): return a + b",
        "hints": ["Используйте оператор +"],
    },
    {
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 2,
        "title": "Поиск максимума",
        "text": "Найдите максимум в массиве без использования встроенных функций.",
        "answer": "max_val = arr[0]; for x in arr: max_val = x if x > max_val else max_val",
        "hints": ["Используйте цикл", "Сравните каждый элемент"],
    },
    {
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 3,
        "title": "Сортировка массива",
        "text": "Отсортируйте массив чисел по возрастанию. Какая сложность вашего алгоритма?",
        "answer": "O(n log n) с quicksort или mergesort",
        "hints": ["Думайте о сложности", "Quicksort или mergesort оптимальны"],
    },
    {
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 4,
        "title": "Динамическое программирование",
        "text": "Решите задачу о рюкзаке (knapsack) методом динамического программирования.",
        "answer": "DP с таблицей [n+1][W+1], время O(nW), память O(nW)",
        "hints": ["Используйте таблицу для мемоизации", "dp[i][w] = макс стоимость с i предметами"],
    },
    {
        "subject": "informatics",
        "topic": "algorithms",
        "difficulty": 5,
        "title": "NP-complete редукция",
        "text": "Докажите, что задача X сводится к задаче Y за полиномиальное время.",
        "answer": "Редукция от 3-SAT или от другой NP-complete задачи",
        "hints": ["Построить редукцию за полиномиальное время", "Доказать корректность"],
    },
    # Informatics — Graphs
    {
        "subject": "informatics",
        "topic": "graphs",
        "difficulty": 2,
        "title": "DFS обход",
        "text": "Реализуйте DFS (поиск в глубину) для графа.",
        "answer": "Рекурсивная функция с посещением вершин и соседей",
        "hints": ["Используйте стек или рекурсию", "Отмечайте посещённые вершины"],
    },
    {
        "subject": "informatics",
        "topic": "graphs",
        "difficulty": 3,
        "title": "BFS и кратчайший путь",
        "text": "Найдите кратчайший путь от вершины A к вершине B в невзвешенном графе.",
        "answer": "BFS, расстояние = количество рёбер до B",
        "hints": ["BFS гарантирует кратчайший путь", "Используйте очередь"],
    },
    {
        "subject": "informatics",
        "topic": "graphs",
        "difficulty": 4,
        "title": "Dijkstra алгоритм",
        "text": "Найдите кратчайший путь в взвешенном графе с положительными весами.",
        "answer": "Dijkstra с приоритетной очередью, O((V+E) log V)",
        "hints": ["Используйте приоритетную очередь", "Расслабляйте рёбра"],
    },
    {
        "subject": "informatics",
        "topic": "graphs",
        "difficulty": 5,
        "title": "Максимальный поток",
        "text": "Найдите максимальный поток в сети Ford-Fulkerson алгоритмом.",
        "answer": "Ford-Fulkerson с DFS или BFS, сложность O(E * max_flow)",
        "hints": ["Используйте остаточную сеть", "Находите пути пока они существуют"],
    },
    # Mathematics — Geometry
    {
        "subject": "mathematics",
        "topic": "geometry",
        "difficulty": 1,
        "title": "Площадь прямоугольника",
        "text": "Найдите площадь прямоугольника со сторонами a и b.",
        "answer": "S = a * b",
        "hints": ["Перемножьте стороны"],
    },
    {
        "subject": "mathematics",
        "topic": "geometry",
        "difficulty": 2,
        "title": "Площадь треугольника",
        "text": "Найдите площадь треугольника с основанием a и высотой h.",
        "answer": "S = (a * h) / 2",
        "hints": ["Используйте формулу для площади треугольника"],
    },
    {
        "subject": "mathematics",
        "topic": "geometry",
        "difficulty": 3,
        "title": "Теорема косинусов",
        "text": "Найдите третью сторону треугольника, если известны две стороны и угол между ними.",
        "answer": "c² = a² + b² - 2ab*cos(C), c = √(a² + b² - 2ab*cos(C))",
        "hints": ["Применить теорему косинусов", "cos(C) дан в радианах или градусах?"],
    },
    {
        "subject": "mathematics",
        "topic": "geometry",
        "difficulty": 4,
        "title": "Пересечение линий",
        "text": "Найдите точку пересечения двух линий в 2D пространстве.",
        "answer": "Решить систему уравнений: a1*x + b1*y = c1, a2*x + b2*y = c2",
        "hints": ["Используйте метод подстановки или Крамера", "Проверьте параллельность"],
    },
    {
        "subject": "mathematics",
        "topic": "geometry",
        "difficulty": 5,
        "title": "Выпуклая оболочка",
        "text": "Найдите выпуклую оболочку набора точек в 2D. Алгоритм Грэхема.",
        "answer": "Сортировка по полярному углу + стек, O(n log n)",
        "hints": ["Graham scan", "Используйте cross product для проверки поворота"],
    },
    # Mathematics — Algebra
    {
        "subject": "mathematics",
        "topic": "algebra",
        "difficulty": 1,
        "title": "Решение линейного уравнения",
        "text": "Решите уравнение: 2x + 3 = 7",
        "answer": "x = 2",
        "hints": ["Перенесите константы в одну сторону", "Разделите на коэффициент"],
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "difficulty": 2,
        "title": "Квадратное уравнение",
        "text": "Решите квадратное уравнение: x² - 5x + 6 = 0",
        "answer": "x = 2 или x = 3 (D = 25 - 24 = 1, x = (5±1)/2)",
        "hints": ["Используйте формулу корней", "Проверьте дискриминант"],
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "difficulty": 3,
        "title": "Система линейных уравнений",
        "text": "Решите систему: 2x + y = 5, x - y = 1",
        "answer": "x = 2, y = 1",
        "hints": ["Используйте метод подстановки или сложения", "Проверьте решение"],
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "difficulty": 4,
        "title": "Матричные операции",
        "text": "Найдите обратную матрицу для матрицы [[1, 2], [3, 4]].",
        "answer": "A⁻¹ = [[−2, 1], [1.5, −0.5]], det(A) = −2",
        "hints": ["Используйте формулу обратной матрицы", "det(A) ≠ 0"],
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "difficulty": 5,
        "title": "Диагонализация матрицы",
        "text": "Диагонализируйте матрицу. Найдите собственные значения и собственные векторы.",
        "answer": "Решить det(A - λI) = 0 для λ, затем (A - λI)v = 0 для v",
        "hints": ["Найти характеристический полином", "Для каждого λ найти собственный вектор"],
    },
]


async def seed_tasks():
    """Создаёт тестовые задачи в БД"""
    async with async_session_maker() as session:
        print(f"\n{'='*60}")
        print("ЗАПОЛНЕНИЕ БД ТЕСТОВЫМИ ЗАДАЧАМИ")
        print(f"{'='*60}\n")

        # Проверяем сколько задач уже есть
        from sqlalchemy import select, func

        result = await session.execute(select(func.count(Task.id)))
        existing_count = result.scalar() or 0

        if existing_count > 0:
            print(f"⚠ В БД уже есть {existing_count} задач.")
            print("   Добавляем новые задачи (не удаляем старые)...\n")

        # Добавляем задачи
        created = 0
        for task_data in TASKS_DATA:
            task = Task(**task_data)
            session.add(task)
            created += 1

        await session.commit()

        print(f"✓ Добавлено {created} новых задач")
        print(f"✓ Всего в БД: {existing_count + created} задач")

        # Группируем по темам
        print(f"\nРаспределение по темам:")
        from itertools import groupby

        by_topic = {}
        for data in TASKS_DATA:
            key = f"{data['subject']}/{data['topic']}"
            by_topic[key] = by_topic.get(key, 0) + 1

        for topic, count in sorted(by_topic.items()):
            print(f"  • {topic}: {count} задач")

        # Распределение по сложности
        print(f"\nРаспределение по сложности:")
        by_difficulty = {}
        for data in TASKS_DATA:
            diff = data["difficulty"]
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

        for diff in sorted(by_difficulty.keys()):
            count = by_difficulty[diff]
            print(f"  • Уровень {diff}: {count} задач")

        print(f"\n{'='*60}")
        print("✓ УСПЕШНО")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("⚠ Убедитесь, что PostgreSQL запущена!")
    print("   Команда: docker-compose up -d postgres\n")
    asyncio.run(seed_tasks())
