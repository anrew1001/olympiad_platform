'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  ConnectionState,
  ServerEvent,
  MatchState,
  OpponentStatus,
  PlayerInfo,
  MatchTask,
} from '@/lib/types/websocket';
import { useWebSocket } from './useWebSocket';
import { RateLimitedQueue, getWebSocketUrl } from '@/lib/utils/websocket';

interface UseMatchWebSocketOptions {
  matchId: number;
  token: string;
  yourPlayerId: number;
  opponent: PlayerInfo | null;
  initialTasks: MatchTask[];
  isYouPlayer1: boolean; // чтобы правильно определить rating_change
  onMatchEnd?: (result: MatchEndData) => void;
  onAnswerResult?: (taskId: number, isCorrect: boolean) => void; // callback для UI feedback
}

export interface MatchEndData {
  outcome: 'victory' | 'defeat' | 'draw';
  reason: 'completion' | 'forfeit' | 'technical_error';
  ratingChange: number;
  newRating: number;
  finalScores: { player1_score: number; player2_score: number };
}

/**
 * WebSocket хук для управления PvP матчем
 * Обрабатывает: события, score updates, opponent tracking, rate limiting
 */
export function useMatchWebSocket({
  matchId,
  token,
  yourPlayerId,
  opponent,
  initialTasks,
  isYouPlayer1,
  onMatchEnd,
  onAnswerResult,
}: UseMatchWebSocketOptions) {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
  });

  const [matchState, setMatchState] = useState<MatchState>({
    yourScore: 0,
    opponentScore: 0,
    yourSolvedTasks: new Set(),
    opponentSolvedTasks: new Set(),
    tasks: initialTasks,
    timeElapsed: 0,
    isFinished: false,
  });

  const [opponentStatus, setOpponentStatus] = useState<OpponentStatus>({
    isConnected: opponent ? true : false,
  });

  // Отслеживать все отправленные ответы (не только правильные)
  const [submittedTasks, setSubmittedTasks] = useState<Set<number>>(new Set());

  const rateLimiterRef = useRef(new RateLimitedQueue(1000)); // 1/sec
  const timeIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // === WebSocket Hook ===
  // Не подключаемся пока нет токена (данные ещё не загружены)

  const wsUrl = token ? getWebSocketUrl(matchId, token) : null;
  const { state: wsState, sendMessage } = useWebSocket(wsUrl, {
    onConnectionStateChange: setConnectionState,
    onMessage: handleServerEvent,
  });

  // === Server Event Handler ===

  function handleServerEvent(event: ServerEvent) {
    switch (event.type) {
      case 'player_joined':
        setOpponentStatus({ isConnected: true });
        break;

      case 'match_start':
        setMatchState((prev) => ({ ...prev, tasks: event.tasks }));
        startTimeCounter();
        break;

      case 'answer_result':
        // Отметить задачу как отправленную (независимо от правильности)
        setSubmittedTasks((prev) => new Set([...prev, event.task_id]));

        // Reconcile optimistic update with server response
        setMatchState((prev) => ({
          ...prev,
          yourScore: event.your_score,
          yourSolvedTasks: event.is_correct
            ? new Set([...prev.yourSolvedTasks, event.task_id])
            : prev.yourSolvedTasks,
        }));

        // Вызываем callback для UI feedback (correct/incorrect иконка)
        onAnswerResult?.(event.task_id, event.is_correct);
        break;

      case 'opponent_scored':
        setMatchState((prev) => ({
          ...prev,
          opponentScore: event.opponent_score,
          opponentSolvedTasks: new Set([...prev.opponentSolvedTasks, event.task_id]),
        }));
        break;

      case 'match_end':
        handleMatchEnd(event);
        break;

      case 'opponent_disconnected':
        setOpponentStatus({
          isConnected: false,
          disconnectWarning: {
            secondsRemaining: event.timeout_seconds,
          },
        });
        startDisconnectCountdown(event.timeout_seconds);
        break;

      case 'opponent_reconnected':
        setOpponentStatus({ isConnected: true });
        break;

      case 'disconnect_warning':
        // Update countdown
        setOpponentStatus((prev) => ({
          ...prev,
          disconnectWarning: {
            secondsRemaining: event.seconds_remaining,
          },
        }));
        break;

      case 'reconnection_success':
        // Sync state from server
        setMatchState((prev) => ({
          ...prev,
          yourScore: event.your_score,
          opponentScore: event.opponent_score,
          timeElapsed: event.time_elapsed,
          yourSolvedTasks: new Set(event.your_solved_tasks),
          opponentSolvedTasks: new Set(event.opponent_solved_tasks),
        }));
        break;

      case 'error':
        // Handle specific error codes
        if (event.code === 'RATE_LIMITED') {
          // Rate limited
        }
        break;

      case 'ping':
        // Auto-respond with pong
        sendMessage({ type: 'pong', timestamp: event.timestamp });
        break;

      case 'pong':
        // Handled by base useWebSocket
        break;
    }
  }

  // === Match End Handler ===

  function handleMatchEnd(event: any) {
    // КРИТИЧНО: Используем isYouPlayer1 из props, а НЕ вычисляем через scores!
    // Вычисление через scores было багом - могло давать неправильный результат
    const yourRatingChange = isYouPlayer1
      ? event.player1_rating_change
      : event.player2_rating_change;
    const yourNewRating = isYouPlayer1
      ? event.player1_new_rating
      : event.player2_new_rating;

    const result: MatchEndData = {
      outcome:
        event.winner_id === yourPlayerId
          ? 'victory'
          : event.winner_id === null
            ? 'draw'
            : 'defeat',
      reason: event.reason,
      ratingChange: yourRatingChange,
      newRating: yourNewRating,
      finalScores: event.final_scores,
    };

    setMatchState((prev) => ({
      ...prev,
      isFinished: true,
      result: {
        outcome: result.outcome,
        reason: result.reason,
        ratingChange: result.ratingChange,
        newRating: result.newRating,
      },
    }));

    onMatchEnd?.(result);
  }

  // === Time Counter ===

  function startTimeCounter() {
    timeIntervalRef.current = setInterval(() => {
      setMatchState((prev) => ({
        ...prev,
        timeElapsed: prev.timeElapsed + 1,
      }));
    }, 1000);
  }

  // === Disconnect Countdown ===

  function startDisconnectCountdown(initialSeconds: number) {
    let secondsLeft = initialSeconds;

    const countdownInterval = setInterval(() => {
      secondsLeft -= 1;
      if (secondsLeft >= 0) {
        setOpponentStatus((prev) => ({
          ...prev,
          disconnectWarning: {
            secondsRemaining: secondsLeft,
          },
        }));
      } else {
        clearInterval(countdownInterval);
      }
    }, 1000);
  }

  // === Submit Answer ===

  const submitAnswer = useCallback(
    (taskId: number, answer: string) => {
      // Проверка submittedTasks убрана - разрешаем повторные попытки
      // Блокировка только на backend для правильных ответов

      if (!rateLimiterRef.current.canSend()) {
        return false;
      }

      if (matchState.isFinished) {
        return false;
      }

      if (wsState.status !== 'connected') {
        return false;
      }

      // Send to server
      sendMessage({
        type: 'submit_answer',
        task_id: taskId,
        answer,
      });

      return true;
    },
    [matchState.isFinished, wsState.status, sendMessage, submittedTasks]
  );

  // === Cleanup ===

  useEffect(() => {
    return () => {
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current);
      }
    };
  }, []);

  return {
    connectionState,
    matchState,
    opponentStatus,
    submitAnswer,
    canSubmit:
      wsState.status === 'connected' && rateLimiterRef.current.getWaitTime() <= 0 && !matchState.isFinished,
    isReady: wsState.status === 'connected',
    submittedTasks, // Expose submitted tasks для UI
  };
}
