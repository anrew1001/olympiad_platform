"""Connection Manager для управления WebSocket соединениями в PvP матчах."""

import asyncio
import logging
from typing import Dict, Optional, Set

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
    """

    def __init__(self):
        """Инициализирует connection manager."""
        # Структура: {match_id: {user_id: websocket}}
        self._rooms: Dict[int, Dict[int, WebSocket]] = {}
        # Per-room locks для предотвращения race conditions
        self._locks: Dict[int, asyncio.Lock] = {}

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

    def total_connections(self) -> int:
        """Возвращает общее количество активных соединений."""
        return sum(len(players) for players in self._rooms.values())

    def total_rooms(self) -> int:
        """Возвращает количество активных комнат (матчей)."""
        return len(self._rooms)


# Глобальный экземпляр ConnectionManager
manager = ConnectionManager()
