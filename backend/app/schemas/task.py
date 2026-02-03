from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Схема для элемента в списке задач ===

class TaskInList(BaseModel):
    """
    Схема задачи для отображения в списке.

    Содержит только основную информацию без полного текста,
    ответа и подсказок (для компактности).
    """

    id: int
    subject: str = Field(..., description="Предмет (например, informatics)")
    topic: str = Field(..., description="Тема (например, algorithms)")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность от 1 до 5")
    title: str = Field(..., description="Краткое название задачи")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Схема для детальной информации о задаче ===

class TaskDetail(BaseModel):
    """
    Схема полной информации о задаче.

    Содержит текст условия и подсказки, но НЕ содержит
    правильный ответ (для защиты от читерства).
    """

    id: int
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность от 1 до 5")
    title: str = Field(..., description="Краткое название")
    text: str = Field(..., description="Полный текст условия задачи")
    hints: List[str] = Field(default=[], description="Список подсказок")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Схема для пагинированного списка задач ===

class PaginatedTaskResponse(BaseModel):
    """
    Схема ответа для списка задач с пагинацией.

    Содержит массив задач и метаинформацию для пагинации
    (total, page, per_page, pages).
    """

    items: List[TaskInList] = Field(..., description="Список задач на текущей странице")
    total: int = Field(..., description="Общее количество задач (с учетом фильтров)")
    page: int = Field(..., ge=1, description="Текущая страница")
    per_page: int = Field(..., ge=1, le=100, description="Количество задач на странице")
    pages: int = Field(..., ge=0, description="Общее количество страниц")

    @field_validator('per_page')
    @classmethod
    def validate_per_page_limit(cls, v: int) -> int:
        """Ограничение максимального размера страницы"""
        if v > 100:
            raise ValueError('per_page не может быть больше 100')
        return v


# === Схемы для проверки ответов пользователя ===

class TaskCheckRequest(BaseModel):
    """
    Схема запроса для проверки ответа пользователя.

    Содержит только ответ пользователя для проверки.
    """

    answer: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Ответ пользователя для проверки"
    )

    @field_validator('answer')
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        """Проверка, что ответ не состоит только из пробелов"""
        if not v.strip():
            raise ValueError('Ответ не может быть пустым')
        return v


class TaskCheckResponse(BaseModel):
    """
    Схема ответа на проверку задачи.

    Возвращает результат проверки: правильно/неправильно,
    сообщение и опционально правильный ответ (только при ошибке).
    """

    is_correct: bool = Field(..., description="Правильно ли решена задача")
    message: str = Field(..., description="Сообщение пользователю о результате")
    correct_answer: str | None = Field(
        None,
        description="Правильный ответ (возвращается только при неверном ответе)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_correct": True,
                    "message": "Верно!",
                    "correct_answer": None
                },
                {
                    "is_correct": False,
                    "message": "Неверно, попробуйте ещё раз",
                    "correct_answer": "42"
                }
            ]
        }
    )


# === Схемы для Admin CRUD операций ===

class TaskCreate(BaseModel):
    """
    Схема для создания новой задачи администратором.

    Включает все поля, в том числе правильный ответ (answer).
    Используется только админами для создания задач.
    """

    subject: str = Field(..., min_length=1, max_length=100, description="Предмет")
    topic: str = Field(..., min_length=1, max_length=100, description="Тема")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность от 1 до 5")
    title: str = Field(..., min_length=5, max_length=200, description="Название задачи")
    text: str = Field(..., min_length=10, description="Полный текст условия задачи")
    answer: str = Field(..., min_length=1, description="Правильный ответ")
    hints: List[str] = Field(default=[], description="Список подсказок")

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Валидация subject против белого списка"""
        allowed = ["informatics", "mathematics"]
        if v.lower() not in allowed:
            raise ValueError(f'subject должен быть одним из: {", ".join(allowed)}')
        return v.lower()

    @field_validator('title', 'text', 'answer')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Удаление лишних пробелов и проверка что не пусто"""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Поле не может быть пустым или состоять только из пробелов')
        return stripped

    @field_validator('hints')
    @classmethod
    def validate_hints(cls, v: List[str]) -> List[str]:
        """Очистка пустых подсказок"""
        return [hint.strip() for hint in v if hint.strip()]


class TaskUpdate(BaseModel):
    """
    Схема для обновления задачи администратором.

    Все поля Optional для поддержки частичного обновления (PATCH-like поведение).
    """

    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    topic: Optional[str] = Field(None, min_length=1, max_length=100)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    text: Optional[str] = Field(None, min_length=10)
    answer: Optional[str] = Field(None, min_length=1)
    hints: Optional[List[str]] = Field(None)

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: Optional[str]) -> Optional[str]:
        """Валидация subject (только если передано)"""
        if v is None:
            return v
        allowed = ["informatics", "mathematics"]
        if v.lower() not in allowed:
            raise ValueError(f'subject должен быть одним из: {", ".join(allowed)}')
        return v.lower()

    @field_validator('title', 'text', 'answer')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Удаление пробелов (только если передано)"""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError('Поле не может быть пустым')
        return stripped

    @field_validator('hints')
    @classmethod
    def validate_hints(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Очистка пустых подсказок (только если передано)"""
        if v is None:
            return v
        return [hint.strip() for hint in v if hint.strip()]


class TaskAdminResponse(BaseModel):
    """
    Схема полной информации о задаче для администратора.

    В отличие от TaskDetail, ВКЛЮЧАЕТ правильный ответ (answer).
    Используется ТОЛЬКО в админских эндпоинтах, защищённых get_admin_user.

    КРИТИЧНО: Эта схема содержит конфиденциальную информацию (answer).
    Никогда не использовать её в публичных API эндпоинтах!
    """

    id: int
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    difficulty: int = Field(..., ge=1, le=5, description="Сложность")
    title: str = Field(..., description="Название")
    text: str = Field(..., description="Текст условия")
    answer: str = Field(..., description="Правильный ответ (ADMIN ONLY)")
    hints: List[str] = Field(default=[], description="Подсказки")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "id": 1,
                "subject": "informatics",
                "topic": "algorithms",
                "difficulty": 3,
                "title": "Сортировка пузырьком",
                "text": "Реализуйте алгоритм сортировки пузырьком для массива целых чисел.",
                "answer": "bubble_sort",
                "hints": ["Используйте вложенные циклы", "Сравнивайте соседние элементы"],
                "created_at": "2024-01-24T10:00:00Z",
                "updated_at": "2024-01-24T10:00:00Z"
            }]
        }
    )


class AdminPaginatedTaskResponse(BaseModel):
    """
    Пагинированный список задач для администратора.

    Отличается от обычного PaginatedTaskResponse тем, что items содержат
    TaskAdminResponse (с answer) вместо TaskInList.
    """

    items: List[TaskAdminResponse] = Field(..., description="Список задач на текущей странице (с answer)")
    total: int = Field(..., ge=0, description="Общее количество задач")
    page: int = Field(..., ge=1, description="Текущая страница")
    per_page: int = Field(..., ge=1, le=100, description="Элементов на странице")
    pages: int = Field(..., ge=0, description="Общее количество страниц")
