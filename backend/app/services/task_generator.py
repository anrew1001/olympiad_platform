"""
Сервис генерации вариаций задач на основе шаблонов.

Поддерживает замену числовых параметров и вычисление ответов.
Для соответствия требованиям ТЗ по генерации вариаций задач.
"""

import logging
import random
import re
from typing import Any

logger = logging.getLogger(__name__)


class TaskGenerator:
    """
    Генератор вариаций задач через параметрическую замену.

    Поддерживаемые шаблоны:
    - {{param_name|min:max}} - случайное целое число от min до max
    - {{param_name|min:max:step}} - число с шагом step
    - {{eval:expression}} - вычисление выражения (для answer)

    Пример шаблона:
    {
        "subject": "математика",
        "topic": "алгебра",
        "difficulty": 2,
        "title": "Линейное уравнение",
        "text": "Решите уравнение: {{a|1:10}}x + {{b|1:20}} = {{c|20:50}}",
        "answer": "{{eval:(c-b)/a}}",
        "hints": ["Перенесите {{b}} в правую часть"]
    }
    """

    @staticmethod
    def generate_variation(template: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
        """
        Генерирует вариацию задачи из шаблона.

        Args:
            template: Шаблон задачи с параметрами {{param|min:max}}
            seed: Сид для воспроизводимости (опционально)

        Returns:
            Словарь с конкретными значениями вместо шаблонов

        Raises:
            ValueError: Если шаблон некорректен
        """

        if seed is not None:
            random.seed(seed)

        # Хранилище значений параметров
        params: dict[str, float] = {}

        def replace_param(match: re.Match) -> str:
            """Заменяет {{param|min:max}} на случайное число"""
            full_match = match.group(0)
            content = match.group(1)

            # Обработка eval: выражений
            if content.startswith("eval:"):
                expression = content[5:]
                try:
                    # Безопасное вычисление с доступом только к params
                    result = eval(expression, {"__builtins__": {}}, params)
                    # Округляем до 2 знаков для float, целое для int
                    if isinstance(result, float):
                        return str(round(result, 2))
                    return str(int(result))
                except Exception as e:
                    logger.error(f"Failed to eval '{expression}': {e}")
                    raise ValueError(f"Ошибка вычисления: {expression}")

            # Обработка параметров param|min:max
            parts = content.split("|")
            if len(parts) != 2:
                logger.warning(f"Invalid template syntax: {full_match}")
                return full_match

            param_name = parts[0].strip()
            range_parts = parts[1].split(":")

            if len(range_parts) == 2:
                # {{param|min:max}} - целое число
                try:
                    min_val = int(range_parts[0])
                    max_val = int(range_parts[1])
                    value = random.randint(min_val, max_val)
                    params[param_name] = value
                    return str(value)
                except ValueError:
                    logger.error(f"Invalid range: {parts[1]}")
                    raise ValueError(f"Некорректный диапазон: {parts[1]}")

            elif len(range_parts) == 3:
                # {{param|min:max:step}} - число с шагом
                try:
                    min_val = float(range_parts[0])
                    max_val = float(range_parts[1])
                    step = float(range_parts[2])

                    # Генерируем список значений с шагом
                    values = []
                    current = min_val
                    while current <= max_val:
                        values.append(current)
                        current += step

                    if not values:
                        raise ValueError("Пустой диапазон с шагом")

                    value = random.choice(values)
                    params[param_name] = value

                    # Если step целый и значения целые - возвращаем int
                    if step == int(step) and value == int(value):
                        return str(int(value))
                    return str(round(value, 2))

                except ValueError as e:
                    logger.error(f"Invalid range with step: {parts[1]}: {e}")
                    raise ValueError(f"Некорректный диапазон с шагом: {parts[1]}")

            return full_match

        # Паттерн для поиска {{...}}
        pattern = re.compile(r"\{\{([^}]+)\}\}")

        # Создаём копию шаблона
        result = template.copy()

        # Обрабатываем каждое поле
        for key, value in result.items():
            if isinstance(value, str):
                # Заменяем шаблоны в строках
                result[key] = pattern.sub(replace_param, value)

            elif isinstance(value, list):
                # Обрабатываем списки (hints)
                result[key] = [
                    pattern.sub(replace_param, item) if isinstance(item, str) else item
                    for item in value
                ]

        logger.info(f"Generated variation with params: {params}")
        return result

    @staticmethod
    def validate_template(template: dict[str, Any]) -> bool:
        """
        Проверяет корректность шаблона задачи.

        Args:
            template: Шаблон для валидации

        Returns:
            True если шаблон корректен, иначе False
        """

        required_fields = ["subject", "topic", "difficulty", "title", "text", "answer"]

        # Проверяем наличие обязательных полей
        for field in required_fields:
            if field not in template:
                logger.error(f"Missing required field: {field}")
                return False

        # Проверяем типы
        if not isinstance(template["difficulty"], int) or not (1 <= template["difficulty"] <= 5):
            logger.error(f"Invalid difficulty: {template['difficulty']}")
            return False

        # Проверяем что есть хотя бы один параметр или eval
        pattern = re.compile(r"\{\{([^}]+)\}\}")
        has_templates = False

        for key in ["text", "answer"]:
            if pattern.search(str(template.get(key, ""))):
                has_templates = True
                break

        if not has_templates:
            logger.warning("Template has no parameters - will generate identical copies")

        return True

    @staticmethod
    def generate_multiple(template: dict[str, Any], count: int = 5) -> list[dict[str, Any]]:
        """
        Генерирует несколько вариаций одной задачи.

        Args:
            template: Шаблон задачи
            count: Количество вариаций

        Returns:
            Список вариаций задач
        """

        if not TaskGenerator.validate_template(template):
            raise ValueError("Некорректный шаблон задачи")

        variations = []
        for i in range(count):
            variation = TaskGenerator.generate_variation(template, seed=None)
            variations.append(variation)

        return variations


# Примеры шаблонов для тестирования
EXAMPLE_TEMPLATES = [
    {
        "subject": "математика",
        "topic": "алгебра",
        "difficulty": 2,
        "title": "Линейное уравнение",
        "text": "Решите уравнение: {{a|2:10}}x + {{b|5:20}} = {{c|25:60}}",
        "answer": "{{eval:(c-b)/a}}",
        "hints": [
            "Перенесите {{b}} в правую часть",
            "Разделите обе части на {{a}}",
        ],
    },
    {
        "subject": "математика",
        "topic": "геометрия",
        "difficulty": 3,
        "title": "Площадь прямоугольника",
        "text": "Найдите площадь прямоугольника со сторонами {{a|5:15}} см и {{b|8:20}} см.",
        "answer": "{{eval:a*b}}",
        "hints": ["Площадь прямоугольника = длина × ширина"],
    },
    {
        "subject": "физика",
        "topic": "кинематика",
        "difficulty": 3,
        "title": "Равномерное движение",
        "text": "Автомобиль едет со скоростью {{v|40:100:10}} км/ч. Какое расстояние он проедет за {{t|2:5}} часа?",
        "answer": "{{eval:v*t}}",
        "hints": ["Расстояние = скорость × время"],
    },
]


if __name__ == "__main__":
    # Тестирование генератора
    print("=== ТЕСТИРОВАНИЕ ГЕНЕРАТОРА ЗАДАЧ ===\n")

    for idx, template in enumerate(EXAMPLE_TEMPLATES, 1):
        print(f"Шаблон {idx}: {template['title']}")
        print(f"Оригинал: {template['text']}")

        # Генерируем 3 вариации
        variations = TaskGenerator.generate_multiple(template, count=3)

        for i, var in enumerate(variations, 1):
            print(f"\nВариация {i}:")
            print(f"  Текст: {var['text']}")
            print(f"  Ответ: {var['answer']}")

        print("\n" + "=" * 60 + "\n")
