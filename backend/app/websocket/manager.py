"""Connection Manager для управления WebSocket соединениями в PvP матчах."""

import asyncio
import logging
import time
from typing import Callable, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Управляет активными WebSocket соединениями для PvP матчей.

    Архитектура:
    - Rooms (комнаты) организованы по match_id
    - Каждая комната содержит набор игроков (user_id -> websocket)
    - Per-room asyncio.Lock для thread-safe операций
    - O(1) lookup для всех операций
    - Session tracking для восстановления соединения (reconnection)
    - Rate limiting для защиты от spam ответов
    """

    def __init__(self):
        """Инициализирует connection manager."""
        # Структура: {match_id: {user_id: websocket}}
        self._rooms: Dict[int, Dict[int, WebSocket]] = {}
        # Per-room locks для предотвращения race conditions
        self._locks: Dict[int, asyncio.Lock] = {}

        # Session tracking для reconnection
        # Структура: {match_id: {user_id: {'session_id': str, 'disconnect_task': Task|None}}}
        self._sessions: Dict[int, Dict[int, dict]] = {}

        # Rate limiting для answer submission
        # Структура: {match_id: {user_id: {'last_answer_time': float}}}
        self._rate_limits: Dict[int, Dict[int, dict]] = {}

    async def connect(
        self,
        match_id: int,
        user_id: int,
        websocket: WebSocket,
    ) -> None:
        """
        Добавляет игрока в комнату матча.

        Args:
            match_id: ID матча
            user_id: ID пользователя (игрока)
            websocket: WebSocket соединение

        Raises:
            ValueError: Если player уже в этой комнате
        """
        async with self._get_room_lock(match_id):
            # Убедиться что комната существует
            if match_id not in self._rooms:
                self._rooms[match_id] = {}

            # Проверить что пользователь ещё не в комнате
            if user_id in self._rooms[match_id]:
                raise ValueError(f"User {user_id} already connected to match {match_id}")

            # Добавить соединение
            self._rooms[match_id][user_id] = websocket
            logger.info(f"Player {user_id} connected to match {match_id}")

    async def disconnect(self, match_id: int, user_id: int) -> None:
        """
        Удаляет игрока из комнаты матча.

        Также очищает session tracking и rate limiting информацию.

        Args:
            match_id: ID матча
            user_id: ID пользователя
        """
        async with self._get_room_lock(match_id):
            if match_id in self._rooms and user_id in self._rooms[match_id]:
                del self._rooms[match_id][user_id]
                logger.info(f"Player {user_id} disconnected from match {match_id}")

                # Удалить комнату если она пуста
                if not self._rooms[match_id]:
                    del self._rooms[match_id]
                    if match_id in self._locks:
                        del self._locks[match_id]

                    # Очистить session и rate limit данные
                    if match_id in self._sessions:
                        del self._sessions[match_id]
                    if match_id in self._rate_limits:
                        del self._rate_limits[match_id]

    async def send_personal(
        self,
        match_id: int,
        user_id: int,
        message: dict,
    ) -> None:
        """
        Отправляет сообщение конкретному игроку.

        Args:
            match_id: ID матча
            user_id: ID получателя
            message: Словарь сообщения

        Returns:
            None
        """
        if match_id not in self._rooms or user_id not in self._rooms[match_id]:
            logger.warning(f"Player {user_id} not connected to match {match_id}")
            return

        websocket = self._rooms[match_id][user_id]
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to player {user_id}: {e}")
            # Автоматически отключить мёртвое соединение
            await self.disconnect(match_id, user_id)

    async def broadcast(
        self,
        match_id: int,
        message: dict,
        exclude: Optional[int] = None,
    ) -> None:
        """
        Отправляет сообщение всем игрокам в матче.

        Args:
            match_id: ID матча
            message: Словарь сообщения
            exclude: ID игрока, который не получит сообщение (опционально)
        """
        if match_id not in self._rooms:
            return

        # Сериализовать JSON один раз перед broadcast
        disconnected_players: list[int] = []

        async with self._get_room_lock(match_id):
            for user_id, websocket in self._rooms[match_id].items():
                # Пропустить исключённого игрока если указан
                if exclude and user_id == exclude:
                    continue

                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to player {user_id}: {e}")
                    disconnected_players.append(user_id)

        # Удалить мёртвые соединения (вне lock чтобы избежать deadlock)
        for user_id in disconnected_players:
            await self.disconnect(match_id, user_id)

    def get_opponent_id(
        self,
        match_id: int,
        user_id: int,
    ) -> Optional[int]:
        """
        Получает ID оппонента в матче.

        Args:
            match_id: ID матча
            user_id: ID текущего игрока

        Returns:
            ID оппонента или None если оппонент не подключён
        """
        if match_id not in self._rooms:
            return None

        players = list(self._rooms[match_id].keys())

        # В матче должно быть 2 игрока максимум
        for player_id in players:
            if player_id != user_id:
                return player_id

        return None

    def is_both_connected(self, match_id: int) -> bool:
        """
        Проверяет подключены ли оба игрока матча.

        Args:
            match_id: ID матча

        Returns:
            True если оба игрока в комнате, False иначе
        """
        if match_id not in self._rooms:
            return False

        return len(self._rooms[match_id]) == 2

    def get_match_players(self, match_id: int) -> Set[int]:
        """
        Получает множество ID подключённых игроков матча.

        Args:
            match_id: ID матча

        Returns:
            Множество user_id подключённых игроков
        """
        if match_id not in self._rooms:
            return set()

        return set(self._rooms[match_id].keys())

    def is_connected(self, match_id: int, user_id: int) -> bool:
        """
        Проверяет подключён ли конкретный игрок.

        Args:
            match_id: ID матча
            user_id: ID пользователя

        Returns:
            True если пользователь подключён, False иначе
        """
        return match_id in self._rooms and user_id in self._rooms[match_id]

    def _get_room_lock(self, match_id: int) -> asyncio.Lock:
        """
        Получает или создаёт lock для комнаты.

        Args:
            match_id: ID матча

        Returns:
            asyncio.Lock для этой комнаты
        """
        if match_id not in self._locks:
            self._locks[match_id] = asyncio.Lock()

        return self._locks[match_id]

    # ===== SESSION TRACKING METHODS (для reconnection) =====

    async def connect_with_session(
        self,
        match_id: int,
        user_id: int,
        websocket: WebSocket,
        session_id: str,
    ) -> bool:
        """
        Подключает игрока с отслеживанием сессии (для reconnection).

        Если игрок уже был подключен в этой сессии и отключился,
        отмена timeout таска для reconnection.

        Args:
            match_id: ID матча
            user_id: ID пользователя
            websocket: WebSocket соединение
            session_id: Уникальный ID сессии (от клиента)

        Returns:
            True если это переподключение (reconnection), False если новое подключение

        Raises:
            ValueError: Если игрок уже подключён
        """
        async with self._get_room_lock(match_id):
            # Инициализировать session dict если нет
            if match_id not in self._sessions:
                self._sessions[match_id] = {}

            # Проверить есть ли уже сессия для этого игрока
            if user_id in self._sessions[match_id]:
                existing_session = self._sessions[match_id][user_id]
                # Если есть disconnect_task, это переподключение
                if existing_session.get("disconnect_task"):
                    # Отменить timeout таск
                    existing_session["disconnect_task"].cancel()
                    existing_session["disconnect_task"] = None

                    # Отследить метрики переподключения
                    reconnection_count = existing_session.get("reconnection_count", 0) + 1
                    disconnect_duration = time.time() - existing_session.get("disconnect_time", time.time())

                    existing_session["reconnection_count"] = reconnection_count
                    existing_session["last_reconnect_time"] = time.time()

                    # Расширенное логирование
                    logger.info(
                        f"RECONNECTION: user={user_id}, match={match_id}, "
                        f"count={reconnection_count}, duration={disconnect_duration:.2f}s, "
                        f"session={session_id[:8]}..."
                    )

                    # Обновить websocket
                    self._rooms[match_id][user_id] = websocket
                    return True

            # Новое подключение
            if match_id not in self._rooms:
                self._rooms[match_id] = {}

            if user_id in self._rooms[match_id]:
                raise ValueError(f"User {user_id} already connected to match {match_id}")

            self._rooms[match_id][user_id] = websocket

            # Сохранить session info
            self._sessions[match_id][user_id] = {
                "session_id": session_id,
                "disconnect_task": None,
                "reconnection_count": 0,
                "connect_time": time.time(),
            }

            # Расширенное логирование
            logger.info(
                f"NEW CONNECTION: user={user_id}, match={match_id}, "
                f"session={session_id[:8]}..."
            )
            return False

    def cancel_disconnect_timer(self, match_id: int, user_id: int) -> bool:
        """
        Отменяет pending disconnect timeout task.

        Args:
            match_id: ID матча
            user_id: ID пользователя

        Returns:
            True если таск был отменён, False если его не было
        """
        if match_id not in self._sessions or user_id not in self._sessions[match_id]:
            return False

        session_info = self._sessions[match_id][user_id]
        if session_info.get("disconnect_task"):
            session_info["disconnect_task"].cancel()
            session_info["disconnect_task"] = None
            return True

        return False

    async def start_disconnect_timer(
        self,
        match_id: int,
        user_id: int,
        timeout_seconds: int,
        callback: Callable,
    ) -> None:
        """
        Запускает таймер на отключение с progressive warnings.

        Отправляет предупреждения соппоненту за N секунд до форфейта.
        Если за timeout_seconds игрок не переподключится, вызывает callback.

        Args:
            match_id: ID матча
            user_id: ID пользователя
            timeout_seconds: Секунды до timeout (обычно 30)
            callback: Async функция для вызова при timeout
        """
        if match_id not in self._sessions or user_id not in self._sessions[match_id]:
            logger.warning(f"No session for user {user_id} in match {match_id}")
            return

        # Отследить когда произошло отключение
        self._sessions[match_id][user_id]["disconnect_time"] = time.time()

        async def timeout_handler():
            try:
                from app.config import settings
                from app.schemas.websocket import DisconnectWarningEvent

                # Получить intervals для warnings из config
                warning_intervals = sorted(
                    [w for w in settings.DISCONNECT_WARNING_INTERVALS if w < timeout_seconds],
                    reverse=True
                )

                elapsed = 0
                for warning_time in warning_intervals:
                    # Спать до времени warning
                    sleep_duration = warning_time - elapsed
                    if sleep_duration > 0:
                        await asyncio.sleep(sleep_duration)
                        elapsed = warning_time

                        # Отправить warning соппоненту
                        opponent_id = self.get_opponent_id(match_id, user_id)
                        if opponent_id and self.is_connected(match_id, opponent_id):
                            remaining = timeout_seconds - elapsed
                            await self.send_personal(
                                match_id,
                                opponent_id,
                                DisconnectWarningEvent(
                                    seconds_remaining=remaining,
                                    user_id=user_id,
                                ).model_dump(),
                            )
                            logger.debug(
                                f"Sent disconnect warning to user {opponent_id}: "
                                f"{remaining}s remaining for user {user_id}"
                            )

                # Спать оставшееся время до timeout
                final_sleep = timeout_seconds - elapsed
                if final_sleep > 0:
                    await asyncio.sleep(final_sleep)

                logger.warning(f"Player {user_id} disconnect timeout in match {match_id}")
                await callback()

            except asyncio.CancelledError:
                logger.debug(f"Disconnect timer cancelled for player {user_id}")

        # Создать и сохранить таск
        task = asyncio.create_task(timeout_handler())
        self._sessions[match_id][user_id]["disconnect_task"] = task

    # ===== RATE LIMITING METHODS =====

    def check_rate_limit(self, match_id: int, user_id: int) -> tuple[bool, float]:
        """
        Проверяет rate limit для отправки ответа.

        Rate limit: Максимум 1 ответ в секунду на пользователя.

        Args:
            match_id: ID матча
            user_id: ID пользователя

        Returns:
            Кортеж (is_allowed, seconds_until_allowed)
            - is_allowed: True если можно отправить ответ
            - seconds_until_allowed: Сколько секунд ждать если не разрешено (0.0 если разрешено)
        """
        import time

        # Инициализировать rate limit dict если нет
        if match_id not in self._rate_limits:
            self._rate_limits[match_id] = {}

        current_time = time.time()

        if user_id not in self._rate_limits[match_id]:
            # Первый ответ
            self._rate_limits[match_id][user_id] = {"last_answer_time": current_time}
            return True, 0.0

        user_limit = self._rate_limits[match_id][user_id]
        time_since_last_answer = current_time - user_limit["last_answer_time"]

        if time_since_last_answer < 1.0:
            wait_time = 1.0 - time_since_last_answer
            logger.debug(
                f"Rate limit exceeded for user {user_id} in match {match_id}, "
                f"wait {wait_time:.2f}s"
            )
            return False, wait_time

        # Обновить last answer time
        user_limit["last_answer_time"] = current_time
        return True, 0.0

    def reset_rate_limit(self, match_id: int, user_id: int) -> None:
        """
        Сбрасывает rate limit для пользователя.

        Используется при отключении или завершении матча.

        Args:
            match_id: ID матча
            user_id: ID пользователя
        """
        if match_id in self._rate_limits and user_id in self._rate_limits[match_id]:
            del self._rate_limits[match_id][user_id]

    def get_reconnection_count(self, match_id: int, user_id: int) -> int:
        """
        Возвращает количество переподключений для игрока.

        Args:
            match_id: ID матча
            user_id: ID пользователя

        Returns:
            Количество переподключений (0 если нет переподключений)
        """
        if match_id in self._sessions and user_id in self._sessions[match_id]:
            return self._sessions[match_id][user_id].get("reconnection_count", 0)
        return 0

    def check_flapping(self, match_id: int, user_id: int) -> tuple[bool, int]:
        """
        Проверяет флаппинг (частые переподключения).

        Флаппинг - это когда игрок быстро отключается и переподключается,
        что может быть признаком нестабильного соединения или попытки зла употребить.
        Если обнаружен флаппинг, timeout сокращается на 50%.

        Args:
            match_id: ID матча
            user_id: ID пользователя

        Returns:
            Кортеж (is_flapping, penalty_seconds):
            - is_flapping: True если обнаружен флаппинг
            - penalty_seconds: На сколько секунд сократить timeout (0 если не флаппинг)
        """
        from app.config import settings

        if match_id not in self._sessions or user_id not in self._sessions[match_id]:
            return False, 0

        session_info = self._sessions[match_id][user_id]
        reconnection_count = session_info.get("reconnection_count", 0)

        # Проверить если переподключений >= max, это флаппинг
        if reconnection_count >= settings.FLAPPING_MAX_DISCONNECTS:
            # Вычислить штраф
            penalty_seconds = int(
                settings.DISCONNECT_TIMEOUT_SECONDS * settings.FLAPPING_PENALTY_MULTIPLIER
            )
            logger.warning(
                f"FLAPPING DETECTED: user={user_id}, match={match_id}, "
                f"count={reconnection_count}, penalty={penalty_seconds}s"
            )
            return True, penalty_seconds

        return False, 0

    def total_connections(self) -> int:
        """Возвращает общее количество активных соединений."""
        return sum(len(players) for players in self._rooms.values())

    def total_rooms(self) -> int:
        """Возвращает количество активных комнат (матчей)."""
        return len(self._rooms)


# Глобальный экземпляр ConnectionManager
manager = ConnectionManager()
