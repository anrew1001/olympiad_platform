"""WebSocket роутер для real-time PvP матчей."""

import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.match import Match, MatchTask
from app.models.user import User
from app.models.enums import MatchStatus
from app.utils.auth import verify_token
from app.services.match_logic import (
    process_answer,
    check_match_completion,
    finalize_match,
    finalize_match_forfeit,
    handle_technical_error,
    get_match_state,
    activate_match,
)
from app.config import settings
from app.websocket.manager import manager
from app.schemas.websocket import (
    SubmitAnswerMessage,
    PongMessage,
    PlayerJoinedEvent,
    MatchStartEvent,
    AnswerResultEvent,
    OpponentScoredEvent,
    MatchEndEvent,
    OpponentDisconnectedEvent,
    OpponentReconnectedEvent,
    DisconnectWarningEvent,
    ReconnectionSuccessEvent,
    ErrorEvent,
    PingEvent,
    TaskInfo,
    PlayerInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pvp", tags=["pvp-websocket"])

# Heartbeat settings
HEARTBEAT_INTERVAL = 30  # секунды
HEARTBEAT_TIMEOUT = 30  # секунды
# DISCONNECT_TIMEOUT загружается из config.DISCONNECT_TIMEOUT_SECONDS


# ============================================================================
# JWT AUTHENTICATION
# ============================================================================


async def authenticate_websocket(
    websocket: WebSocket,
    token: str,
    session: AsyncSession,
) -> User:
    """
    Аутентифицирует WebSocket соединение через JWT токен.

    Args:
        websocket: WebSocket соединение
        token: JWT токен из query параметра
        session: AsyncSession для БД операций

    Returns:
        User объект если успешно

    Raises:
        WebSocketException: Если токен невалиден или user не найден
    """
    try:
        # Verify JWT токен
        payload = verify_token(token)
        user_id = int(payload.get("sub"))

        # Загрузить пользователя из БД
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User {user_id} from token not found in DB")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="User not found",
            )
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        logger.info(f"WebSocket authenticated for user {user_id}")
        return user

    except WebSocketException:
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication failed",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def send_error(
    websocket: WebSocket,
    message: str,
    code: str,
) -> None:
    """
    Отправляет error event клиенту.

    Args:
        websocket: WebSocket соединение
        message: Текст ошибки
        code: Код ошибки
    """
    try:
        event = ErrorEvent(message=message, code=code)
        await websocket.send_json(event.model_dump())
    except Exception as e:
        logger.debug(f"Could not send error to client: {e}")


async def load_match_with_tasks(
    match_id: int,
    session: AsyncSession,
) -> tuple[Match | None, list[TaskInfo]]:
    """
    Загружает матч и преобразует задачи в TaskInfo.

    Args:
        match_id: ID матча
        session: AsyncSession для БД операций

    Returns:
        Кортеж (Match, List[TaskInfo]) или (None, []) если матч не найден
    """
    result = await session.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(joinedload(Match.tasks))
    )
    match = result.unique().scalar_one_or_none()

    if not match:
        return None, []

    # Преобразовать MatchTask в TaskInfo
    tasks_info = []
    for match_task in match.tasks:
        # Загрузить задачу (она загружается через lazy="joined" в MatchTask)
        task = match_task.task
        tasks_info.append(
            TaskInfo(
                task_id=task.id,
                order=match_task.task_order,
                title=task.title,
                text=task.text,
                difficulty=task.difficulty,
                hints=task.hints or [],
            )
        )

    # Отсортировать по order
    tasks_info.sort(key=lambda t: t.order)

    return match, tasks_info


async def cleanup_orphaned_match(
    match_id: int,
    user_id: int,
    session: AsyncSession,
) -> bool:
    """
    Cleans up orphaned WAITING match when creator disconnects.

    Only deletes matches that are:
    - Status: WAITING
    - player1_id == user_id (disconnecting user created it)
    - player2_id IS NULL (no one joined)

    Args:
        match_id: ID of the match
        user_id: ID of user who disconnected
        session: AsyncSession for DB operations

    Returns:
        True if match was cleaned up, False otherwise
    """
    try:
        # Lock and load match
        result = await session.execute(
            select(Match)
            .where(Match.id == match_id)
            .options(
                noload(Match.player1),
                noload(Match.player2),
                noload(Match.winner),
                noload(Match.tasks),
                noload(Match.answers),
            )
            .with_for_update()
        )
        match = result.scalar_one_or_none()

        if not match:
            logger.debug(f"Match {match_id} not found for cleanup")
            return False

        # Only cleanup WAITING matches where user is player1 and player2 never joined
        if (
            match.status == MatchStatus.WAITING
            and match.player1_id == user_id
            and match.player2_id is None
        ):
            # Delete the match
            await session.delete(match)  # AsyncSession.delete() IS async!
            await session.commit()
            logger.info(
                f"Cleaned up orphaned WAITING match {match_id} "
                f"after player1 {user_id} disconnected before anyone joined"
            )
            return True

        logger.debug(
            f"Match {match_id} not cleaned: status={match.status.value}, "
            f"player1={match.player1_id}, player2={match.player2_id}"
        )
        return False

    except Exception as e:
        logger.error(f"Error cleaning up orphaned match {match_id}: {e}", exc_info=True)
        await session.rollback()
        return False


async def handle_message(
    match_id: int,
    user_id: int,
    message: dict,
) -> None:
    """
    Обработчик входящих сообщений от клиента.

    Args:
        match_id: ID матча
        user_id: ID пользователя
        message: Словарь сообщения
    """
    message_type = message.get("type")

    if message_type == "pong":
        # Heartbeat response -- ничего не делаем
        logger.debug(f"Received pong from user {user_id}")
        return

    elif message_type == "submit_answer":
        task_id = message.get("task_id")
        answer = message.get("answer")

        logger.info(f"[ANSWER] User {user_id} submitted answer for task {task_id}: '{answer}' (type={type(answer).__name__}, len={len(str(answer)) if answer is not None else 0})")

        if not task_id or answer is None:
            await manager.send_personal(
                match_id,
                user_id,
                ErrorEvent(
                    message="Missing task_id or answer",
                    code="INVALID_MESSAGE",
                ).model_dump(),
            )
            return

        # CHECK RATE LIMIT: Max 1 answer per second per user
        is_allowed, wait_time = manager.check_rate_limit(match_id, user_id)
        if not is_allowed:
            await manager.send_personal(
                match_id,
                user_id,
                ErrorEvent(
                    message=f"Rate limited. Wait {wait_time:.1f}s before next answer",
                    code="RATE_LIMITED",
                ).model_dump(),
            )
            return

        # Обработать ответ в новой БД сессии
        async with async_session_maker() as session:
            try:
                # Проверить что матч всё ещё active
                result = await session.execute(
                    select(Match).where(Match.id == match_id)
                )
                match = result.scalar_one_or_none()

                if not match:
                    await manager.send_personal(
                        match_id,
                        user_id,
                        ErrorEvent(
                            message="Match not found",
                            code="MATCH_NOT_FOUND",
                        ).model_dump(),
                    )
                    return

                # Allow WAITING (waiting for both players) and ACTIVE (both connected) statuses
                if match.status not in (MatchStatus.WAITING, MatchStatus.ACTIVE):
                    await manager.send_personal(
                        match_id,
                        user_id,
                        ErrorEvent(
                            message="Match is not available",
                            code="MATCH_NOT_AVAILABLE",
                        ).model_dump(),
                    )
                    return

                # Проверить что user участник матча
                if user_id not in (match.player1_id, match.player2_id):
                    await manager.send_personal(
                        match_id,
                        user_id,
                        ErrorEvent(
                            message="User not a participant",
                            code="NOT_PARTICIPANT",
                        ).model_dump(),
                    )
                    return

                # Проверить что task_id принадлежит этому матчу
                result_task = await session.execute(
                    select(MatchTask).where(
                        (MatchTask.match_id == match_id) &
                        (MatchTask.task_id == task_id)
                    )
                )
                match_task = result_task.scalar_one_or_none()

                if not match_task:
                    await manager.send_personal(
                        match_id,
                        user_id,
                        ErrorEvent(
                            message=f"Task {task_id} not in this match",
                            code="INVALID_TASK",
                        ).model_dump(),
                    )
                    return

                # Процесс ответа
                is_correct, new_score = await process_answer(
                    match_id, user_id, task_id, answer, session
                )

                # КРИТИЧНО: Коммитим ответ СРАЗУ чтобы он не потерялся
                # если дальше будет ошибка в check_match_completion или finalize_match
                await session.commit()
                logger.debug(f"Answer committed for user {user_id} on task {task_id}")

                # Отправить результат игроку
                await manager.send_personal(
                    match_id,
                    user_id,
                    AnswerResultEvent(
                        task_id=task_id,
                        is_correct=is_correct,
                        your_score=new_score,
                    ).model_dump(),
                )

                # Если ответ правильный -- уведомить соперника
                if is_correct:
                    opponent_id = manager.get_opponent_id(match_id, user_id)
                    if opponent_id:
                        await manager.send_personal(
                            match_id,
                            opponent_id,
                            OpponentScoredEvent(
                                task_id=task_id,
                                opponent_score=new_score,
                            ).model_dump(),
                        )

                # Проверить завершён ли матч (в новой транзакции)
                is_complete = await check_match_completion(match_id, session)
                logger.info(f"Match {match_id} completion check after answer: is_complete={is_complete}")

                if is_complete:
                    # Финализировать матч
                    result_data = await finalize_match(match_id, session, reason="completion")
                    await session.commit()

                    # Отправить match_end обоим игрокам
                    await manager.broadcast(
                        match_id,
                        MatchEndEvent(
                            reason="completion",
                            winner_id=result_data["winner_id"],
                            player1_rating_change=result_data["player1_rating_change"],
                            player1_new_rating=result_data["player1_new_rating"],
                            player2_rating_change=result_data["player2_rating_change"],
                            player2_new_rating=result_data["player2_new_rating"],
                            final_scores={
                                "player1_score": result_data["final_scores"]["player1_score"],
                                "player2_score": result_data["final_scores"]["player2_score"],
                            },
                        ).model_dump(),
                    )

                    logger.info(f"Match {match_id} finished normally")

            except ValueError as e:
                logger.error(f"Error processing answer: {e}")
                await manager.send_personal(
                    match_id,
                    user_id,
                    ErrorEvent(
                        message=str(e),
                        code="PROCESSING_ERROR",
                    ).model_dump(),
                )
            except Exception as e:
                logger.error(f"Unexpected error processing answer: {e}", exc_info=True)
                await manager.send_personal(
                    match_id,
                    user_id,
                    ErrorEvent(
                        message="Internal server error",
                        code="INTERNAL_ERROR",
                    ).model_dump(),
                )

    else:
        # Unknown message type
        await manager.send_personal(
            match_id,
            user_id,
            ErrorEvent(
                message=f"Unknown message type: {message_type}",
                code="UNKNOWN_TYPE",
            ).model_dump(),
        )


async def heartbeat_task(
    match_id: int,
    user_id: int,
    last_pong: dict,  # Словарь для передачи по ссылке
) -> None:
    """
    Background task для отправки heartbeat ping.

    Args:
        match_id: ID матча
        user_id: ID пользователя
        last_pong: Словарь с временем последнего pong
    """
    while manager.is_connected(match_id, user_id):
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

            # Проверить timeout
            if time.time() - last_pong["time"] > HEARTBEAT_TIMEOUT:
                logger.warning(f"Heartbeat timeout for user {user_id} in match {match_id}")
                # WebSocket будет закрыт в основном loop через try/except
                break

            # Отправить ping
            await manager.send_personal(
                match_id,
                user_id,
                PingEvent(timestamp=int(time.time())).model_dump(),
            )

        except Exception as e:
            logger.debug(f"Heartbeat task error: {e}")
            break


# ============================================================================
# MAIN WEBSOCKET ENDPOINT
# ============================================================================


@router.websocket("/ws/{match_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    match_id: int,
    token: str = Query(...),
) -> None:
    """
    WebSocket endpoint для PvP матчей.

    URL: ws://localhost:8000/api/pvp/ws/{match_id}?token={jwt_token}

    Flow:
    1. Accept connection
    2. Authenticate user via JWT token
    3. Verify match exists and user is participant
    4. Register in ConnectionManager
    5. Send player_joined event if opponent connected
    6. If both connected -> send match_start
    7. Enter message loop
    8. On disconnect -> cleanup
    """

    user: User | None = None
    match: Match | None = None
    last_pong = {"time": time.time()}
    heartbeat = None

    try:
        # 1. Accept connection before auth (allows sending error message)
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for match {match_id}")

        # 2. Authenticate user
        async with async_session_maker() as session:
            user = await authenticate_websocket(websocket, token, session)

        if not user:
            return

        # 3. Verify match and user participation
        async with async_session_maker() as session:
            result = await session.execute(
                select(Match)
                .where(Match.id == match_id)
                .options(
                    joinedload(Match.player1),
                    joinedload(Match.player2),
                    joinedload(Match.tasks),
                )
            )
            match = result.unique().scalar_one_or_none()

        if not match:
            await send_error(websocket, "Match not found", "MATCH_NOT_FOUND")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Проверить что user участник
        if user.id not in (match.player1_id, match.player2_id):
            await send_error(websocket, "User not a participant", "NOT_PARTICIPANT")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Проверить что матч в состоянии WAITING или ACTIVE (но не ERROR/FINISHED)
        # WAITING = ожидаем второго игрока
        # ACTIVE = оба подключены или один переподключился
        if match.status not in (MatchStatus.WAITING, MatchStatus.ACTIVE):
            await send_error(websocket, "Match is not available", "MATCH_NOT_AVAILABLE")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 4. Register in ConnectionManager with session tracking
        try:
            session_id = secrets.token_urlsafe(32)  # Generate secure session ID
            is_reconnection = await manager.connect_with_session(
                match_id, user.id, websocket, session_id
            )
        except ValueError as e:
            await send_error(websocket, str(e), "CONNECTION_ERROR")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # If reconnection, notify opponent and send current scores
        if is_reconnection:
            logger.info(f"User {user.id} reconnected to match {match_id}")
            opponent_id = manager.get_opponent_id(match_id, user.id)

            if opponent_id:
                # Notify opponent of reconnection
                await manager.send_personal(
                    match_id,
                    opponent_id,
                    OpponentReconnectedEvent(
                        timestamp=datetime.utcnow().isoformat()
                    ).model_dump(),
                )

                # Get complete match state for full reconnection sync
                async with async_session_maker() as session:
                    try:
                        match_state = await get_match_state(match_id, session)

                        # Determine which player is reconnecting
                        is_player1 = (user.id == match_state["player1_id"])

                        your_score = match_state["player1_score"] if is_player1 else match_state["player2_score"]
                        opponent_score = match_state["player2_score"] if is_player1 else match_state["player1_score"]
                        your_solved = match_state["player1_solved_tasks"] if is_player1 else match_state["player2_solved_tasks"]
                        opponent_solved = match_state["player2_solved_tasks"] if is_player1 else match_state["player1_solved_tasks"]

                        # Get reconnection count from manager
                        reconnection_count = manager.get_reconnection_count(match_id, user.id)

                        await manager.send_personal(
                            match_id,
                            user.id,
                            ReconnectionSuccessEvent(
                                your_score=your_score,
                                opponent_score=opponent_score,
                                time_elapsed=match_state["time_elapsed"],
                                your_solved_tasks=your_solved,
                                opponent_solved_tasks=opponent_solved,
                                total_tasks=match_state["total_tasks"],
                                reconnection_count=reconnection_count,
                            ).model_dump(),
                        )
                        logger.debug(
                            f"Reconnection success event sent to user {user.id}: "
                            f"your_score={your_score}, opponent_score={opponent_score}, "
                            f"solved={len(your_solved)}/{match_state['total_tasks']}"
                        )
                    except Exception as e:
                        logger.error(f"Error sending reconnection_success: {e}")
                        await manager.send_personal(
                            match_id,
                            user.id,
                            ErrorEvent(
                                message="Failed to sync match state",
                                code="STATE_SYNC_ERROR"
                            ).model_dump(),
                        )

        # 5. Send player_joined if opponent connected
        opponent_id = manager.get_opponent_id(match_id, user.id)
        if opponent_id:
            # Opponent already connected
            opponent_info = None
            if opponent_id == match.player1_id:
                opponent_info = PlayerInfo(
                    id=match.player1.id,
                    username=match.player1.username,
                    rating=match.player1.rating,
                )
            else:
                opponent_info = PlayerInfo(
                    id=match.player2.id,
                    username=match.player2.username,
                    rating=match.player2.rating,
                )

            # Send to opponent: you joined
            if opponent_info:
                current_player = (
                    match.player2 if opponent_id == match.player1_id else match.player1
                )
                await manager.send_personal(
                    match_id,
                    opponent_id,
                    PlayerJoinedEvent(
                        player=PlayerInfo(
                            id=current_player.id,
                            username=current_player.username,
                            rating=current_player.rating,
                        )
                    ).model_dump(),
                )

        # 6. If both connected -> activate match and send match_start to both
        if manager.is_both_connected(match_id):
            # Load tasks and activate match
            async with async_session_maker() as session:
                try:
                    # Load tasks
                    _, tasks_info = await load_match_with_tasks(match_id, session)

                    # Activate match (WAITING -> ACTIVE)
                    await activate_match(match_id, session)
                    await session.commit()
                except Exception as e:
                    logger.error(f"Error activating match {match_id}: {e}")
                    await session.rollback()
                    raise

            match_start_event = MatchStartEvent(tasks=tasks_info)

            await manager.broadcast(
                match_id,
                match_start_event.model_dump(),
            )

            logger.info(f"Match {match_id} started (both players connected)")

        # 7. Start heartbeat task
        heartbeat = asyncio.create_task(heartbeat_task(match_id, user.id, last_pong))

        # 8. Enter message loop
        while True:
            raw_data = await websocket.receive_text()
            message = json.loads(raw_data)

            # Update last_pong on any message (resets timeout)
            if message.get("type") == "pong":
                last_pong["time"] = time.time()

            # Handle message
            await handle_message(match_id, user.id, message)

    except WebSocketDisconnect:
        logger.info(f"User {user.id if user else 'unknown'} disconnected from match {match_id}")

    except WebSocketException:
        logger.warning(f"WebSocket exception for match {match_id}")

    except Exception as e:
        logger.error(f"WebSocket error in match {match_id}: {e}", exc_info=True)

    finally:
        # Cancel heartbeat task
        if heartbeat:
            heartbeat.cancel()
            try:
                await heartbeat
            except asyncio.CancelledError:
                pass

        # Cleanup
        if user:
            if match:
                opponent_id = manager.get_opponent_id(match_id, user.id)

                # Opponent никогда не подключался - cleanup WebSocket and orphaned match
                if opponent_id is None:
                    logger.info(
                        f"User {user.id} disconnected from match {match_id}, "
                        f"opponent never connected - attempting orphaned match cleanup"
                    )
                    manager.disconnect(match_id, user.id)

                    # Cleanup orphaned WAITING match from database
                    # Используем глобальный импорт async_session_maker (строка 14)
                    async with async_session_maker() as session:
                        try:
                            was_cleaned = await cleanup_orphaned_match(
                                match_id, user.id, session
                            )
                            if was_cleaned:
                                logger.info(
                                    f"Successfully cleaned up orphaned match {match_id} "
                                    f"for user {user.id}"
                                )
                            else:
                                logger.debug(
                                    f"No cleanup needed for match {match_id} "
                                    f"(may have been joined or already cleaned)"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error during orphaned match cleanup for match {match_id}: {e}",
                                exc_info=True
                            )

                # Opponent подключался - проверяем всё ли ещё подключён
                elif manager.is_connected(match_id, opponent_id):
                    # Case: Only this player disconnected - start timeout for reconnection
                    # Check for flapping and apply penalty if detected
                    is_flapping, penalty = manager.check_flapping(match_id, user.id)

                    # Adjust timeout if flapping detected
                    timeout = settings.DISCONNECT_TIMEOUT_SECONDS - penalty

                    logger.info(
                        f"User {user.id} disconnected from match {match_id}, "
                        f"opponent {opponent_id} still connected. Starting {timeout}s timeout "
                        f"(flapping={is_flapping}, original={settings.DISCONNECT_TIMEOUT_SECONDS}s)"
                    )

                    # Define timeout callback for technical error (no rating change per spec)
                    async def disconnect_timeout_callback():
                        async with async_session_maker() as session:
                            try:
                                logger.warning(
                                    f"Disconnect timeout expired for user {user.id} in match {match_id}. "
                                    f"Finalizing as technical_error (no rating change per spec)."
                                )
                                await handle_technical_error(
                                    match_id,
                                    session,
                                    f"Player {user.id} disconnected and failed to reconnect within timeout"
                                )
                                await session.commit()

                                # Send match_end to remaining player with no rating changes
                                await manager.send_personal(
                                    match_id,
                                    opponent_id,
                                    MatchEndEvent(
                                        reason="technical_error",
                                        winner_id=None,
                                        player1_rating_change=0,
                                        player1_new_rating=0,
                                        player2_rating_change=0,
                                        player2_new_rating=0,
                                        final_scores={
                                            "player1_score": 0,
                                            "player2_score": 0,
                                        },
                                    ).model_dump(),
                                )

                                logger.info(f"Technical error in match {match_id}: no rating changes applied")
                            except Exception as e:
                                logger.error(f"Error in disconnect timeout: {e}")

                    # Start timer with adjusted timeout
                    await manager.start_disconnect_timer(
                        match_id,
                        user.id,
                        timeout,
                        disconnect_timeout_callback,
                    )

                    # Notify opponent of disconnection with timeout info
                    await manager.send_personal(
                        match_id,
                        opponent_id,
                        OpponentDisconnectedEvent(
                            timestamp=datetime.utcnow().isoformat(),
                            reconnecting=True,
                            timeout_seconds=timeout,
                        ).model_dump(),
                    )
                    logger.info(
                        f"Notified opponent {opponent_id} of user {user.id} disconnect "
                        f"(reconnecting: True, timeout: {timeout}s, flapping_penalty={penalty}s)"
                    )

                    # Log flapping penalty if applied
                    if is_flapping:
                        logger.warning(
                            f"Flapping penalty applied to user {user.id}: "
                            f"timeout reduced from {settings.DISCONNECT_TIMEOUT_SECONDS}s to {timeout}s"
                        )

                # Case: Opponent тоже отключился (оба offline) - technical error
                else:
                    logger.warning(f"Both players disconnected from match {match_id}")
                    manager.disconnect(match_id, user.id)
                    async with async_session_maker() as session:
                        try:
                            await handle_technical_error(
                                match_id, session,
                                "Both players disconnected"
                            )
                            await session.commit()
                        except Exception as e:
                            logger.error(f"Error handling technical error for match {match_id}: {e}")

            # Disconnect from ConnectionManager (если ещё не отключён)
            if manager.is_connected(match_id, user.id):
                await manager.disconnect(match_id, user.id)
            logger.info(f"Cleaned up user {user.id} from match {match_id}")
