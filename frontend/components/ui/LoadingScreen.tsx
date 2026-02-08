'use client';

import { motion } from 'motion/react';
import { Logo } from './Logo';

interface LoadingScreenProps {
  text?: string;
}

/**
 * Полноэкранный loading screen с анимированным логотипом
 * Props:
 * - text: кастомный текст (default: "ЗАГРУЗКА...")
 */
export function LoadingScreen({ text = 'ЗАГРУЗКА...' }: LoadingScreenProps) {
  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center relative overflow-hidden">
      {/* Статичный grid background */}
      <div
        className="fixed inset-0 opacity-[0.02] z-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(90deg, #0066FF 1px, transparent 1px),
            linear-gradient(0deg, #0066FF 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Content */}
      <motion.div
        className="relative z-10 text-center space-y-8"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Анимированный логотип */}
        <div className="flex justify-center">
          <Logo size={120} animate className="text-[#0066FF]" />
        </div>

        {/* Текст */}
        <motion.p
          className="text-sm font-mono text-[#0066FF] uppercase tracking-widest"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          {text}
        </motion.p>

        {/* Прогресс бар (косметический) */}
        <div className="w-64 h-1 bg-[#1a1a1a] rounded-full overflow-hidden mx-auto">
          <motion.div
            className="h-full bg-gradient-to-r from-[#0066FF]/50 via-[#0066FF] to-[#0066FF]/50 rounded-full"
            animate={{
              x: ['-100%', '100%'],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'linear',
            }}
            style={{ width: '50%' }}
          />
        </div>
      </motion.div>
    </div>
  );
}
