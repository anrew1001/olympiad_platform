'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { ConnectionState, ServerEvent, ClientMessage, WebSocketOptions } from '@/lib/types/websocket';
import { calculateBackoff } from '@/lib/utils/websocket';

/**
 * Базовый WebSocket хук для PvP матчей
 * Управляет: подключение, переподключение, heartbeat, message handling
 *
 * КРИТИЧНО: Callbacks хранятся в refs чтобы избежать reconnect loop.
 * Без refs: onMessage меняется при каждом рендере → connect пересоздаётся →
 * useEffect перезапускается → WebSocket закрывается/открывается → бесконечный цикл.
 *
 * url=null означает "не подключаться" (ждём загрузки данных матча).
 */
export function useWebSocket(
  url: string | null,
  options: WebSocketOptions = {}
) {
  const { reconnectMaxAttempts = 20 } = options;

  const [state, setState] = useState<ConnectionState>({ status: 'disconnected' });
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const attemptRef = useRef(0);
  const unmountedRef = useRef(false);

  // === Stable Refs для callbacks (предотвращает reconnect loop) ===
  const onMessageRef = useRef(options.onMessage);
  const onStateChangeRef = useRef(options.onConnectionStateChange);

  useEffect(() => { onMessageRef.current = options.onMessage; }, [options.onMessage]);
  useEffect(() => { onStateChangeRef.current = options.onConnectionStateChange; }, [options.onConnectionStateChange]);

  // === Cleanup Timers ===

  const cleanupTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);


  // === Connection Setup ===

  const connect = useCallback(() => {
    if (!url || unmountedRef.current) return;
    if (wsRef.current) return;

    setState({ status: 'connecting' });
    onStateChangeRef.current?.({ status: 'connecting' });

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) { ws.close(); return; }

        setState({ status: 'connected', latency: 0 });
        onStateChangeRef.current?.({ status: 'connected', latency: 0 });
        attemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ServerEvent;
          onMessageRef.current?.(data);
        } catch (error) {
          // Failed to parse WebSocket message
        }
      };

      ws.onerror = () => {
        // WebSocket error occurred
      };

      ws.onclose = () => {
        wsRef.current = null;
        cleanupTimers();

        if (unmountedRef.current) {
          setState({ status: 'disconnected' });
          return;
        }

        if (attemptRef.current >= reconnectMaxAttempts) {
          const s: ConnectionState = {
            status: 'disconnected',
            error: 'Превышено максимальное количество попыток переподключения',
          };
          setState(s);
          onStateChangeRef.current?.(s);
          return;
        }

        const attempt = attemptRef.current++;
        const backoffMs = calculateBackoff(attempt);
        const nextRetryIn = Math.ceil(backoffMs / 1000);

        const s: ConnectionState = { status: 'reconnecting', attempt, nextRetryIn };
        setState(s);
        onStateChangeRef.current?.(s);

        reconnectTimeoutRef.current = setTimeout(() => {
          wsRef.current = null;
          connect();
        }, backoffMs);
      };
    } catch (error) {
      const s: ConnectionState = { status: 'disconnected', error: String(error) };
      setState(s);
      onStateChangeRef.current?.(s);
    }
  }, [url, reconnectMaxAttempts, cleanupTimers]);

  // === Send Message ===

  const sendMessage = useCallback((message: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // === Manual Reconnect ===

  const reconnect = useCallback(() => {
    cleanupTimers();
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    attemptRef.current = 0;
    connect();
  }, [connect, cleanupTimers]);

  // === Lifecycle: подключаемся только когда url не null ===

  useEffect(() => {
    unmountedRef.current = false;

    if (url) {
      connect();
    }

    return () => {
      unmountedRef.current = true;
      cleanupTimers();
      if (wsRef.current) {
        wsRef.current.onclose = null; // Предотвращаем auto-reconnect при unmount
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps
  // Только url! connect стабилен, callbacks через refs.

  return {
    state,
    sendMessage,
    reconnect,
    isConnected: state.status === 'connected',
  };
}
