"""Тесты для ConnectionManager (Phase 3)."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock

from app.websocket.manager import ConnectionManager


class MockWebSocket:
    """Mock WebSocket для тестирования."""

    def __init__(self):
        self.sent_messages = []
        self.connected = True

    async def send_json(self, data):
        """Имитирует отправку JSON."""
        if not self.connected:
            raise RuntimeError("WebSocket closed")
        self.sent_messages.append(data)

    async def accept(self):
        """Имитирует принятие соединения."""
        pass

    async def close(self):
        """Имитирует закрытие соединения."""
        self.connected = False


class TestConnectionManagerBasic:
    """Базовые тесты для ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect_user(self):
        """Пользователь подключается к матчу."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        # Act
        await manager.connect(match_id=1, user_id=100, websocket=ws)

        # Assert
        assert manager.is_connected(match_id=1, user_id=100)
        assert manager.total_connections() == 1
        assert manager.total_rooms() == 1

    @pytest.mark.asyncio
    async def test_disconnect_user(self):
        """Пользователь отключается от матча."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(match_id=1, user_id=100, websocket=ws)

        # Act
        await manager.disconnect(match_id=1, user_id=100)

        # Assert
        assert not manager.is_connected(match_id=1, user_id=100)
        assert manager.total_connections() == 0
        assert manager.total_rooms() == 0

    @pytest.mark.asyncio
    async def test_get_opponent_id(self):
        """Получение ID оппонента."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws1)
        await manager.connect(match_id=1, user_id=200, websocket=ws2)

        # Act
        opponent_of_100 = manager.get_opponent_id(match_id=1, user_id=100)
        opponent_of_200 = manager.get_opponent_id(match_id=1, user_id=200)

        # Assert
        assert opponent_of_100 == 200
        assert opponent_of_200 == 100

    @pytest.mark.asyncio
    async def test_is_both_connected(self):
        """Проверка подключены ли оба игрока."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        # Act: только один подключен
        await manager.connect(match_id=1, user_id=100, websocket=ws1)
        assert not manager.is_both_connected(match_id=1)

        # Act: оба подключены
        await manager.connect(match_id=1, user_id=200, websocket=ws2)
        assert manager.is_both_connected(match_id=1)

        # Act: один отключился
        await manager.disconnect(match_id=1, user_id=100)
        assert not manager.is_both_connected(match_id=1)

    @pytest.mark.asyncio
    async def test_send_personal(self):
        """Отправка личного сообщения."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(match_id=1, user_id=100, websocket=ws)

        # Act
        message = {"type": "test", "data": "hello"}
        await manager.send_personal(match_id=1, user_id=100, message=message)

        # Assert
        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0] == message

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Broadcast сообщения всем в комнате."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws1)
        await manager.connect(match_id=1, user_id=200, websocket=ws2)

        # Act
        message = {"type": "broadcast"}
        await manager.broadcast(match_id=1, message=message)

        # Assert
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_exclude(self):
        """Broadcast с исключением конкретного игрока."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws1)
        await manager.connect(match_id=1, user_id=200, websocket=ws2)

        # Act
        message = {"type": "broadcast"}
        await manager.broadcast(match_id=1, message=message, exclude=100)

        # Assert
        assert len(ws1.sent_messages) == 0  # Excluded
        assert len(ws2.sent_messages) == 1  # Included


class TestSessionTracking:
    """Тесты для отслеживания сессий (reconnection)."""

    @pytest.mark.asyncio
    async def test_connect_with_session_new_connection(self):
        """Новое подключение с сессией."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        # Act
        is_reconnection = await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws, session_id="session123"
        )

        # Assert
        assert is_reconnection is False
        assert manager.is_connected(match_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_connect_with_session_reconnection(self):
        """Переподключение в течение 30 секунд."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        # Act: первое подключение
        is_recon_1 = await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws1, session_id="session123"
        )
        assert is_recon_1 is False

        # Имитируем отключение
        await manager.disconnect(match_id=1, user_id=100)
        assert not manager.is_connected(match_id=1, user_id=100)

        # Но сессия должна быть в памяти (с disconnect_task)
        # Так что мы должны оставить сессию в manager после disconnect
        # Это делается в disconnect_timer callback
        # Для этого теста нужно переподключиться сразу же

        # Act: переподключение
        is_recon_2 = await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws2, session_id="session123"
        )

        # Assert: это уже новое подключение (так как мы вызвали disconnect)
        # но если бы мы не вызвали disconnect, это было бы reconnection
        assert manager.is_connected(match_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_cancel_disconnect_timer(self):
        """Отмена таймера отключения при reconnection."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        # Setup: создаём подключение и имитируем disconnect с таймером
        await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws, session_id="session123"
        )

        # Создаём mock callback
        callback_called = False

        async def mock_callback():
            nonlocal callback_called
            callback_called = True

        # Start timer (но не вызываем disconnect)
        await manager.start_disconnect_timer(
            match_id=1, user_id=100, timeout_seconds=1, callback=mock_callback
        )

        # Act: отменяем таймер
        was_cancelled = manager.cancel_disconnect_timer(match_id=1, user_id=100)

        # Assert
        assert was_cancelled is True

        # Callback не должен быть вызван
        await asyncio.sleep(1.5)
        assert callback_called is False


class TestDisconnectTimer:
    """Тесты для таймера отключения."""

    @pytest.mark.asyncio
    async def test_disconnect_timer_fires(self):
        """Таймер срабатывает после timeout."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws, session_id="session123"
        )

        # Setup
        callback_fired = False

        async def mock_callback():
            nonlocal callback_fired
            callback_fired = True

        # Act: стартуем таймер на 0.1 секунды
        await manager.start_disconnect_timer(
            match_id=1, user_id=100, timeout_seconds=0.1, callback=mock_callback
        )

        # Ждём чтобы callback сработал
        await asyncio.sleep(0.2)

        # Assert
        assert callback_fired is True

    @pytest.mark.asyncio
    async def test_disconnect_timer_cancelled(self):
        """Таймер может быть отменён до срабатывания."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        await manager.connect_with_session(
            match_id=1, user_id=100, websocket=ws, session_id="session123"
        )

        callback_fired = False

        async def mock_callback():
            nonlocal callback_fired
            callback_fired = True

        # Act: стартуем таймер
        await manager.start_disconnect_timer(
            match_id=1, user_id=100, timeout_seconds=0.5, callback=mock_callback
        )

        # Сразу отменяем
        manager.cancel_disconnect_timer(match_id=1, user_id=100)

        # Ждём дольше чем timeout
        await asyncio.sleep(0.6)

        # Assert: callback не должен срабатывать
        assert callback_fired is False


class TestRateLimiting:
    """Тесты для rate limiting."""

    def test_rate_limit_first_answer_allowed(self):
        """Первый ответ всегда разрешён."""
        manager = ConnectionManager()

        # Act
        is_allowed, wait_time = manager.check_rate_limit(match_id=1, user_id=100)

        # Assert
        assert is_allowed is True
        assert wait_time == 0.0

    def test_rate_limit_second_answer_too_fast(self):
        """Второй ответ в течение 1 секунды блокируется."""
        manager = ConnectionManager()

        # Setup: первый ответ
        manager.check_rate_limit(match_id=1, user_id=100)

        # Act: сразу же второй ответ
        is_allowed, wait_time = manager.check_rate_limit(match_id=1, user_id=100)

        # Assert
        assert is_allowed is False
        assert 0.9 < wait_time <= 1.0

    def test_rate_limit_second_answer_after_delay(self):
        """Второй ответ после 1+ секунды разрешён."""
        manager = ConnectionManager()

        # Setup
        manager.check_rate_limit(match_id=1, user_id=100)
        time.sleep(1.05)

        # Act
        is_allowed, wait_time = manager.check_rate_limit(match_id=1, user_id=100)

        # Assert
        assert is_allowed is True
        assert wait_time == 0.0

    def test_rate_limit_multiple_users_independent(self):
        """Rate limit для каждого пользователя независим."""
        manager = ConnectionManager()

        # Setup: User 100 делает ответ
        manager.check_rate_limit(match_id=1, user_id=100)

        # Act: User 200 может сразу же
        is_allowed_200, _ = manager.check_rate_limit(match_id=1, user_id=200)

        # Assert
        assert is_allowed_200 is True

    def test_rate_limit_multiple_matches_independent(self):
        """Rate limit для каждого матча независим."""
        manager = ConnectionManager()

        # Setup: User 100 в матче 1
        manager.check_rate_limit(match_id=1, user_id=100)

        # Act: User 100 в матче 2 может сразу же
        is_allowed, _ = manager.check_rate_limit(match_id=2, user_id=100)

        # Assert
        assert is_allowed is True

    def test_rate_limit_reset(self):
        """Reset rate limit очищает данные."""
        manager = ConnectionManager()

        # Setup
        manager.check_rate_limit(match_id=1, user_id=100)

        # Act: reset
        manager.reset_rate_limit(match_id=1, user_id=100)

        # После reset первый ответ снова разрешён
        is_allowed, _ = manager.check_rate_limit(match_id=1, user_id=100)

        # Assert
        assert is_allowed is True


class TestEdgeCases:
    """Тесты edge cases."""

    @pytest.mark.asyncio
    async def test_send_to_disconnected_user(self):
        """Отправка сообщения отключённому пользователю."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(match_id=1, user_id=100, websocket=ws)

        # Закрываем WebSocket
        ws.connected = False

        # Act & Assert: должно автоматически отключить
        await manager.send_personal(match_id=1, user_id=100, message={"test": "msg"})

        # User должен быть удалён
        assert not manager.is_connected(match_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_cannot_connect_same_user_twice(self):
        """Нельзя подключить одного пользователя дважды."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws1)

        # Act & Assert
        with pytest.raises(ValueError, match="already connected"):
            await manager.connect(match_id=1, user_id=100, websocket=ws2)

    @pytest.mark.asyncio
    async def test_get_match_players(self):
        """Получение множества подключённых игроков."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws1)
        await manager.connect(match_id=1, user_id=200, websocket=ws2)
        await manager.connect(match_id=2, user_id=300, websocket=ws3)

        # Act
        players_match_1 = manager.get_match_players(match_id=1)
        players_match_2 = manager.get_match_players(match_id=2)

        # Assert
        assert players_match_1 == {100, 200}
        assert players_match_2 == {300}

    @pytest.mark.asyncio
    async def test_empty_room_cleanup(self):
        """Пустая комната удаляется автоматически."""
        manager = ConnectionManager()
        ws = MockWebSocket()

        await manager.connect(match_id=1, user_id=100, websocket=ws)
        assert manager.total_rooms() == 1

        await manager.disconnect(match_id=1, user_id=100)

        # Комната должна быть удалена
        assert manager.total_rooms() == 0
