'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { findMatch, cancelSearch } from '@/lib/api/pvp';

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
        // Начинаем polling через POST /api/pvp/find каждые 3 сек
        setStatus('searching');
        startPolling();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Find match error:', err, errorMessage);

      // 409 CONFLICT означает активный матч (уже играется)
      if (errorMessage.includes('CONFLICT') && !isRetry) {
        console.log('Active match exists, canceling and retrying...');
        isRetryingRef.current = true;
        try {
          await cancelSearch();
          setTimeout(() => doFind(true), 300);
          return;
        } catch (cancelErr) {
          const cancelMessage = cancelErr instanceof Error ? cancelErr.message : 'Unknown error';
          console.error('Failed to cancel:', cancelMessage);
        }
      }

      setError(errorMessage);
      setStatus('error');
      isRetryingRef.current = false;
    }
  }, []);

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

  const startPolling = useCallback(() => {
    // Polling каждые 3 сек через POST /api/pvp/find
    // Это позволяет серверу повторно искать соперника при каждом poll
    // и решает race condition когда оба игрока создали WAITING матчи одновременно
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await findMatch();
        console.log(`[Polling] Match ${response.match_id} status: ${response.status}`);

        setMatchId(response.match_id);

        if (response.status === 'active') {
          // Соперник найден!
          console.log(`[Polling] Match ${response.match_id} is active! Transitioning to found.`);
          setStatus('found');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        console.debug('Polling error:', err);
      }
    }, 3000);
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
