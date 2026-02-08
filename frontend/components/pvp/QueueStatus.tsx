'use client';

import { motion } from 'motion/react';

interface QueueStatusProps {
  isSearching: boolean;
  elapsedSeconds?: number;
  onCancel: () => void;
}

/**
 * Компонент для отображения статуса поиска
 * Показывает текст статуса, время поиска и кнопку отмены
 */
export function QueueStatus({ isSearching, elapsedSeconds = 0, onCancel }: QueueStatusProps) {
  const statusTexts = {
    idle: 'ГОТОВИМСЯ К ПОИСКУ...',
    searching: 'ИНИЦИАЛИЗАЦИЯ ПОИСКА...',
  };

  const currentText = isSearching ? statusTexts.searching : statusTexts.idle;

  return (
    <motion.div
      className="flex flex-col items-center gap-8 mt-12"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      {/* Status text with typing effect */}
      <div className="text-center">
        <motion.h2
          className="text-2xl font-mono uppercase tracking-[0.2em] text-white mb-4"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          {currentText}
        </motion.h2>

        {/* Elapsed time */}
        {isSearching && (
          <motion.p
            className="text-sm font-mono text-[#06b6d4] tracking-wider"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            ВРЕМЯ ПОИСКА: {Math.floor(elapsedSeconds / 60)}:{String(elapsedSeconds % 60).padStart(2, '0')}
          </motion.p>
        )}
      </div>

      {/* Cancel button */}
      {isSearching && (
        <motion.button
          onClick={onCancel}
          className="group relative px-12 py-4 font-mono uppercase text-sm tracking-wider text-[#ff3b30] border-2 border-[#ff3b30] bg-[#ff3b30]/5 overflow-hidden transition-all duration-300"
          style={{
            clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {/* Hover background effect */}
          <motion.div
            className="absolute inset-0 bg-[#ff3b30]/20"
            initial={{ opacity: 0 }}
            whileHover={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          />

          <span className="relative z-10">ОТМЕНИТЬ ПОИСК</span>
        </motion.button>
      )}

      {/* Decorative text */}
      <motion.p
        className="text-xs font-mono text-[#444] tracking-widest mt-8"
        animate={{ opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        ▓ ОЖИДАНИЕ ОППОНЕНТА ▓
      </motion.p>
    </motion.div>
  );
}
