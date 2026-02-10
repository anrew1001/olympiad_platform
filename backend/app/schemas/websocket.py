"""Pydantic схемы для WebSocket событий в PvP матчах."""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# ВХОДЯЩИЕ СОБЫТИЯ (Клиент → Сервер)
# ============================================================================


class SubmitAnswerMessage(BaseModel):
    """Сообщение от клиента с ответом на задачу."""

    type: str = Field("submit_answer", description="Тип события")
    task_id: int = Field(..., description="ID задачи")
    answer: str = Field(..., description="Текст ответа")


class PongMessage(BaseModel):
    """Pong ответ на heartbeat ping."""

    type: str = Field("pong", description="Тип события")
    timestamp: int = Field(..., description="Timestamp из ping сообщения")


# ============================================================================
# ИСХОДЯЩИЕ СОБЫТИЯ (Сервер → Клиент)
# ============================================================================


class PlayerInfo(BaseModel):
    """Информация об игроке."""

    id: int = Field(..., description="ID пользователя")
    username: str = Field(..., description="Имя пользователя")
    rating: int = Field(..., description="Рейтинг")


class PlayerJoinedEvent(BaseModel):
    """Событие: второй игрок подключился."""

    type: str = Field("player_joined", description="Тип события")
    player: PlayerInfo = Field(..., description="Информация о подключившемся игроке")


class TaskInfo(BaseModel):
    """Информация о задаче в матче."""

    task_id: int = Field(..., description="ID задачи")
    order: int = Field(..., description="Порядок в матче (1-5)")
    title: str = Field(..., description="Название задачи")
    text: str = Field(..., description="Условие задачи")
    difficulty: int = Field(..., description="Сложность (1-5)")
    hints: List[str] = Field(default_factory=list, description="Подсказки")


class MatchStartEvent(BaseModel):
    """Событие: матч начался, оба игрока подключились."""

    type: str = Field("match_start", description="Тип события")
    tasks: List[TaskInfo] = Field(..., description="Список задач матча")


class AnswerResultEvent(BaseModel):
    """Событие: результат вашего ответа на задачу."""

    type: str = Field("answer_result", description="Тип события")
    task_id: int = Field(..., description="ID задачи")
    is_correct: bool = Field(..., description="Правильный ли ответ")
    your_score: int = Field(..., description="Обновлённый ваш счёт")


class OpponentScoredEvent(BaseModel):
    """Событие: соперник ответил правильно."""

    type: str = Field("opponent_scored", description="Тип события")
    task_id: int = Field(..., description="ID задачи, на которую ответил соперник")
    opponent_score: int = Field(..., description="Обновлённый счёт соперника")


class FinalScores(BaseModel):
    """Финальные счёты матча."""

    player1_score: int = Field(..., description="Счёт первого игрока")
    player2_score: int = Field(..., description="Счёт второго игрока")


class MatchEndEvent(BaseModel):
    """Событие: матч завершился."""

    type: str = Field("match_end", description="Тип события")
    reason: str = Field("completion", description="Причина завершения: completion | forfeit | technical_error")
    winner_id: Optional[int] = Field(None, description="ID победителя (None при ничье)")
    player1_rating_change: int = Field(..., description="Изменение рейтинга player1")
    player1_new_rating: int = Field(..., description="Новый рейтинг player1")
    player2_rating_change: int = Field(..., description="Изменение рейтинга player2")
    player2_new_rating: int = Field(..., description="Новый рейтинг player2")
    final_scores: FinalScores = Field(..., description="Финальные счёты")


class OpponentDisconnectedEvent(BaseModel):
    """Событие: соперник отключился."""

    type: str = Field("opponent_disconnected", description="Тип события")
    timestamp: str = Field(..., description="Время отключения (ISO format)")
    reconnecting: bool = Field(True, description="Может ли соперник переподключиться?")
    timeout_seconds: Optional[int] = Field(None, description="Секунды до форфейта (обычно 30)")


class OpponentReconnectedEvent(BaseModel):
    """Событие: соперник переподключился."""

    type: str = Field("opponent_reconnected", description="Тип события")
    timestamp: str = Field(..., description="Время переподключения (ISO format)")


class DisconnectWarningEvent(BaseModel):
    """Событие: предупреждение о скором форфейте соперника."""

    type: str = Field("disconnect_warning", description="Тип события")
    seconds_remaining: int = Field(..., description="Секунд до форфейта")
    user_id: int = Field(..., description="ID отключенного игрока")


class ReconnectionSuccessEvent(BaseModel):
    """Событие: вы успешно переподключились."""

    type: str = Field("reconnection_success", description="Тип события")
    your_score: int = Field(..., description="Ваш текущий счёт")
    opponent_score: int = Field(..., description="Счёт соперника")
    time_elapsed: int = Field(..., description="Секунды с начала матча")
    your_solved_tasks: List[int] = Field(
        default_factory=list,
        description="ID задач, которые вы решили"
    )
    opponent_solved_tasks: List[int] = Field(
        default_factory=list,
        description="ID задач, решенных соперником"
    )
    total_tasks: int = Field(5, description="Всего задач в матче")
    reconnection_count: int = Field(0, description="Количество переподключений")


class ErrorEvent(BaseModel):
    """Событие: ошибка при обработке сообщения."""

    type: str = Field("error", description="Тип события")
    message: str = Field(..., description="Описание ошибки")
    code: str = Field(..., description="Код ошибки (INVALID_TASK, INVALID_MESSAGE и т.д.)")


class PingEvent(BaseModel):
    """Событие: heartbeat ping от сервера."""

    type: str = Field("ping", description="Тип события")
    timestamp: int = Field(..., description="Текущий Unix timestamp")
