'use client';

import { motion } from 'motion/react';

interface DisconnectWarningProps {
  secondsRemaining: number;
  opponentName: string;
}

/**
 * Предупреждение об отключении соперника
 * Показывает countdown до forfeit
 */
export function DisconnectWarning({ secondsRemaining, opponentName }: DisconnectWarningProps) {
  // Color changes based on time remaining
  const getColor = () => {
    if (secondsRemaining <= 5) return '#ff3b30'; // Red
    if (secondsRemaining <= 10) return '#f97316'; // Orange
    return '#eab308'; // Yellow
  };

  const getBgColor = () => {
    if (secondsRemaining <= 5) return '#ff3b30';
    if (secondsRemaining <= 10) return '#f97316';
    return '#eab308';
  };

  return (
    <motion.div
      className="relative max-w-4xl mx-auto px-6 py-1"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
    >
      <div
        className="relative border-l-4 px-4 py-3 text-sm font-mono"
        style={{
          backgroundColor: `${getBgColor()}15`,
          borderLeftColor: getColor(),
          color: getColor(),
        }}
      >
        {/* Decorative scan line effect */}
        <motion.div
          className="absolute inset-0 pointer-events-none"
          animate={{ scaleY: [0, 1, 0], opacity: [0, 0.3, 0] }}
          transition={{ duration: 1, repeat: Infinity }}
          style={{
            background: `linear-gradient(90deg, transparent, ${getColor()}40, transparent)`,
            transformOrigin: 'top',
          }}
        />

        <div className="relative z-10 flex items-center justify-between gap-4">
          <span>
            {opponentName} отключился · FORFEIT через{' '}
            <motion.span
              className="font-bold"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            >
              {secondsRemaining}
            </motion.span>
            s
          </span>

          {/* Animated countdown indicator */}
          <motion.div
            className="flex items-center gap-1"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.6, repeat: Infinity }}
          >
            {[...Array(Math.ceil(secondsRemaining / 5))].map((_, i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: getColor() }}
              />
            ))}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
