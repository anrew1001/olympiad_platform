from datetime import datetime
from typing import List

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
