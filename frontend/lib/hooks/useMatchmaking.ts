'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { findMatch, cancelSearch, getMatch } from '@/lib/api/pvp';

type MatchmakingStatus = 'idle' | 'searching' | 'found' | 'error';

/**
 * Hook для управления поиском матча
 * Обрабатывает: поиск, polling статуса, отмену, переход на матч
 */
export function useMatchmaking() {
  const [status, setStatus] = useState<MatchmakingStatus>('idle');
  const [matchId, setMatchId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRetryingRef = useRef(false);

  // === Find Match ===

  const doFind = useCallback(async (isRetry = false) => {
    try {
      const response = await findMatch();
      setMatchId(response.match_id);

      if (response.status === 'active') {
        // Соперник сразу найден
        setStatus('found');
      } else {
        // Ждём соперника (status === 'waiting')
        // Начинаем polling
        setStatus('searching');
        startPolling(response.match_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';

      // Если конфликт (уже есть матч), пробуем отменить и повторить
      if (errorMessage.includes('CONFLICT') && !isRetry) {
        isRetryingRef.current = true;
        try {
          await cancelSearch();
          // Повторяем поиск матча после небольшой задержки
          setTimeout(() => doFind(true), 300);
          return;
        } catch (cancelErr) {
          const cancelMessage = cancelErr instanceof Error ? cancelErr.message : 'Unknown error';
          setError(`Не удалось отменить поиск: ${cancelMessage}`);
          setStatus('error');
          isRetryingRef.current = false;
          return;
        }
      }

      setError(errorMessage);
      setStatus('error');
      isRetryingRef.current = false;
    }
  }, []); // startPolling не нужен в deps т.к. он стабильный

  const find = useCallback(async () => {
    setStatus('searching');
    setError(null);
    isRetryingRef.current = false;
    await doFind(false);
  }, [doFind]);

  // === Cancel Search ===

  const cancel = useCallback(async () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    try {
      await cancelSearch();
      setStatus('idle');
      setMatchId(null);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    }
  }, []);

  // === Polling ===

  const startPolling = useCallback((id: number) => {
    // Простой polling каждые 2 сек для проверки статуса матча
    // Если opponent присоединился, вернёт status='active'
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await getMatch(id);

        if (response.status === 'active') {
          // Соперник найден!
          setStatus('found');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        // Polling error
      }
    }, 2000);
  }, []);

  // === Cleanup ===

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return {
    status,
    matchId,
    error,
    find,
    cancel,
  };
}
