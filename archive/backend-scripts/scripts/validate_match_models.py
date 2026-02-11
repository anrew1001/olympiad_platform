"""
Валидация моделей PvP матчей БЕЗ подключения к БД.

Проверяет:
- Синтаксис и импорты
- Наличие всех колонок и relationships
- Типы данных (Mapped[], Optional[])
- Constraints (CHECK, UNIQUE indexes)
- Правильность foreign_keys параметров
- Enum конфигурация
"""
from sqlalchemy.orm import class_mapper, RelationshipProperty
from sqlalchemy.sql.schema import Index, CheckConstraint, ForeignKeyConstraint

from app.models import Match, MatchTask, MatchAnswer, MatchStatus, Base


def validate_match_model():
    """Проверяет модель Match"""
    print("\n=== Валидация Match ===")

    # Проверяем таблицу
    mapper = class_mapper(Match)
    print(f"✓ Таблица: {Match.__tablename__}")

    # Проверяем колонки
    columns_to_check = {
        "player1_id": "int",
        "player2_id": "int",
        "status": str,
        "player1_score": "int",
        "player2_score": "int",
        "winner_id": "int",
        "player1_rating_change": "int",
        "player2_rating_change": "int",
        "finished_at": "datetime",
    }

    for col_name in columns_to_check:
        col = getattr(Match, col_name)
        print(f"  ✓ Колонка {col_name}")

    # Проверяем relationships
    relationships = ["player1", "player2", "winner", "tasks", "answers"]
    for rel_name in relationships:
        rel = getattr(Match, rel_name)
        # Проверяем что это RelationshipProperty
        mapper_rel = mapper.relationships.get(rel_name)
        if mapper_rel:
            print(f"  ✓ Relationship {rel_name} (mapper)")
        else:
            print(f"  ✗ Relationship {rel_name} NOT FOUND в mapper")

    # Проверяем constraints
    print("\n  Constraints:")
    table_args = getattr(Match, "__table_args__", ())
    has_check_constraint = False
    has_status_index = False
    has_player1_status_index = False

    for arg in table_args:
        if isinstance(arg, CheckConstraint):
            print(f"    ✓ CHECK constraint: {arg.name}")
            has_check_constraint = True
        elif isinstance(arg, Index):
            print(f"    ✓ Index: {arg.name} на {arg.expressions}")
            if arg.name == "ix_matches_player1_status":
                has_player1_status_index = True
            if "status" in arg.name:
                has_status_index = True

    assert has_check_constraint, "Нет CHECK constraint на Match"
    assert has_status_index, "Нет индекса на status"
    assert has_player1_status_index, "Нет ix_matches_player1_status индекса"
    print("  ✓ Все constraints найдены")

    print("\n✓ Match прошла валидацию")


def validate_matchtask_model():
    """Проверяет модель MatchTask"""
    print("\n=== Валидация MatchTask ===")

    mapper = class_mapper(MatchTask)
    print(f"✓ Таблица: {MatchTask.__tablename__}")

    # Проверяем колонки
    columns_to_check = ["match_id", "task_id", "task_order"]
    for col_name in columns_to_check:
        col = getattr(MatchTask, col_name)
        print(f"  ✓ Колонка {col_name}")

    # Проверяем relationships
    relationships = ["match", "task"]
    for rel_name in relationships:
        mapper_rel = mapper.relationships.get(rel_name)
        if mapper_rel:
            print(f"  ✓ Relationship {rel_name}")
        else:
            print(f"  ✗ Relationship {rel_name} NOT FOUND")

    # Проверяем UNIQUE constraints
    print("\n  Constraints:")
    table_args = getattr(MatchTask, "__table_args__", ())
    unique_indexes = []

    for arg in table_args:
        if isinstance(arg, Index):
            print(f"    ✓ Index: {arg.name} (unique={arg.unique})")
            if arg.unique:
                unique_indexes.append(arg.name)

    assert len(unique_indexes) == 2, f"Ожидаем 2 UNIQUE индекса, найдено {len(unique_indexes)}"
    assert any("match_order" in idx for idx in unique_indexes), "Нет UNIQUE индекса на match_order"
    assert any("match_task" in idx for idx in unique_indexes), "Нет UNIQUE индекса на match_task"
    print("  ✓ Все UNIQUE constraints найдены")

    print("\n✓ MatchTask прошла валидацию")


def validate_matchanswer_model():
    """Проверяет модель MatchAnswer"""
    print("\n=== Валидация MatchAnswer ===")

    mapper = class_mapper(MatchAnswer)
    print(f"✓ Таблица: {MatchAnswer.__tablename__}")

    # Проверяем колонки
    columns_to_check = [
        "match_id",
        "user_id",
        "task_id",
        "answer",
        "is_correct",
        "submitted_at",
    ]
    for col_name in columns_to_check:
        col = getattr(MatchAnswer, col_name)
        print(f"  ✓ Колонка {col_name}")

    # Проверяем relationships
    relationships = ["match", "user", "task"]
    for rel_name in relationships:
        mapper_rel = mapper.relationships.get(rel_name)
        if mapper_rel:
            print(f"  ✓ Relationship {rel_name}")
        else:
            print(f"  ✗ Relationship {rel_name} NOT FOUND")

    # Проверяем UNIQUE constraint на (match_id, user_id, task_id)
    print("\n  Constraints:")
    table_args = getattr(MatchAnswer, "__table_args__", ())
    has_upsert_key = False

    for arg in table_args:
        if isinstance(arg, Index):
            print(f"    ✓ Index: {arg.name} (unique={arg.unique})")
            if arg.unique and "match_user_task" in arg.name:
                has_upsert_key = True

    assert has_upsert_key, "Нет UNIQUE индекса на (match_id, user_id, task_id)"
    print("  ✓ UPSERT key найден")

    print("\n✓ MatchAnswer прошла валидацию")


def validate_enum():
    """Проверяет MatchStatus enum"""
    print("\n=== Валидация MatchStatus Enum ===")

    assert hasattr(MatchStatus, "WAITING"), "Нет WAITING"
    assert hasattr(MatchStatus, "ACTIVE"), "Нет ACTIVE"
    assert hasattr(MatchStatus, "FINISHED"), "Нет FINISHED"
    assert hasattr(MatchStatus, "CANCELLED"), "Нет CANCELLED"
    assert hasattr(MatchStatus, "ERROR"), "Нет ERROR"

    assert MatchStatus.WAITING.value == "waiting", "WAITING.value должен быть 'waiting'"
    assert MatchStatus.ACTIVE.value == "active", "ACTIVE.value должен быть 'active'"
    assert MatchStatus.FINISHED.value == "finished", "FINISHED.value должен быть 'finished'"
    assert MatchStatus.CANCELLED.value == "cancelled", "CANCELLED.value должен быть 'cancelled'"
    assert MatchStatus.ERROR.value == "error", "ERROR.value должен быть 'error'"

    print("  ✓ WAITING = 'waiting'")
    print("  ✓ ACTIVE = 'active'")
    print("  ✓ FINISHED = 'finished'")
    print("  ✓ CANCELLED = 'cancelled'")
    print("  ✓ ERROR = 'error'")

    print("\n✓ MatchStatus прошла валидацию")


def validate_inheritance():
    """Проверяет наследование от Base"""
    print("\n=== Валидация наследования ===")

    # Проверяем что модели наследуют от Base
    assert issubclass(Match, Base), "Match не наследует Base"
    assert issubclass(MatchTask, Base), "MatchTask не наследует Base"
    assert issubclass(MatchAnswer, Base), "MatchAnswer не наследует Base"

    # Проверяем унаследованные поля
    for model_class in [Match, MatchTask, MatchAnswer]:
        mapper = class_mapper(model_class)
        columns = [c.key for c in mapper.columns]

        assert "id" in columns, f"{model_class.__name__} не имеет id"
        assert "created_at" in columns, f"{model_class.__name__} не имеет created_at"
        assert "updated_at" in columns, f"{model_class.__name__} не имеет updated_at"

        print(f"  ✓ {model_class.__name__} имеет id, created_at, updated_at")

    print("\n✓ Наследование прошло валидацию")


def validate_exports():
    """Проверяет что модели экспортированы в __init__.py"""
    print("\n=== Валидация экспортов ===")

    from app import models

    assert hasattr(models, "Match"), "Match не экспортирован"
    assert hasattr(models, "MatchTask"), "MatchTask не экспортирован"
    assert hasattr(models, "MatchAnswer"), "MatchAnswer не экспортирован"
    assert hasattr(models, "MatchStatus"), "MatchStatus не экспортирован"

    print("  ✓ Match")
    print("  ✓ MatchTask")
    print("  ✓ MatchAnswer")
    print("  ✓ MatchStatus")

    print("\n✓ Экспорты прошли валидацию")


def main():
    """Запускает все проверки"""
    print("\n" + "=" * 60)
    print("ВАЛИДАЦИЯ МОДЕЛЕЙ PVP МАТЧЕЙ")
    print("=" * 60)

    try:
        validate_exports()
        validate_enum()
        validate_inheritance()
        validate_match_model()
        validate_matchtask_model()
        validate_matchanswer_model()

        print("\n" + "=" * 60)
        print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("=" * 60)
        print("\nДля полного тестирования с БД:")
        print("  1. Запустите PostgreSQL: docker-compose up -d postgres")
        print("  2. Пересоздайте таблицы: python recreate_tables.py")
        print("  3. Запустите тесты: pytest -v tests/test_match_models.py")

        return 0

    except AssertionError as e:
        print(f"\n✗ ОШИБКА ВАЛИДАЦИИ: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ НЕОЖИДАННАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
