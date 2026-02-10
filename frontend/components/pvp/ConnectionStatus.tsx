'use client';

import { motion } from 'motion/react';
import type { ConnectionState } from '@/lib/types/websocket';

interface ConnectionStatusProps {
  state: ConnectionState;
}

/**
 * Индикатор подключения (top-right corner)
 * Показывает статус WebSocket и информацию о reconnection
 */
export function ConnectionStatus({ state }: ConnectionStatusProps) {
  const getColor = () => {
    switch (state.status) {
      case 'connected':
        return '#00ff88';
      case 'connecting':
        return '#eab308';
      case 'reconnecting':
        return '#f97316';
      case 'disconnected':
        return '#ff3b30';
      default:
        return '#666';
    }
  };

  const getLabel = () => {
    switch (state.status) {
      case 'connected':
        return `● Connected (${state.latency}ms)`;
      case 'connecting':
        return '⟳ Connecting...';
      case 'reconnecting':
        return `⟳ Reconnecting in ${state.nextRetryIn}s... (attempt ${state.attempt})`;
      case 'disconnected':
        return state.error ? `✗ ${state.error}` : '✗ Disconnected';
      default:
        return '';
    }
  };

  return (
    <motion.div
      className="fixed top-6 right-6 z-50"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div
        className="px-4 py-2 rounded text-xs font-mono bg-[#121212] border border-[#1a1a1a]"
        style={{
          color: getColor(),
          boxShadow: `0 0 10px ${getColor()}33`,
        }}
      >
        {/* Animated indicator dot */}
        {(state.status === 'connected' || state.status === 'connecting' || state.status === 'reconnecting') && (
          <motion.span
            className="inline-block w-2 h-2 rounded-full mr-2"
            style={{ backgroundColor: getColor() }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}

        {getLabel()}
      </div>

      {/* Countdown for reconnecting */}
      {state.status === 'reconnecting' && (
        <motion.div
          className="mt-2 text-xs font-mono text-[#f97316] text-right"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          Попытка {state.attempt}...
        </motion.div>
      )}
    </motion.div>
  );
}
