'use client';

import { motion } from 'motion/react';

/**
 * Radar sweep анимация для экрана поиска матча
 * 3 концентрических кольца + вращающаяся луч
 */
export function QueueAnimation() {
  return (
    <div className="flex justify-center items-center py-20">
      <div className="relative w-80 h-80">
        {/* Background grid effect */}
        <div className="absolute inset-0 rounded-full border border-[#0066FF]/20" />

        {/* Outer rings (pulsing) */}
        <motion.div
          className="absolute inset-0 rounded-full border border-[#0066FF]/40"
          animate={{ scale: [0.8, 1.2], opacity: [0.8, 0.3] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
        />

        <motion.div
          className="absolute inset-8 rounded-full border border-[#00d4ff]/40"
          animate={{ scale: [0.85, 1.15], opacity: [0.7, 0.2] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
        />

        <motion.div
          className="absolute inset-16 rounded-full border border-[#0066FF]/40"
          animate={{ scale: [0.9, 1.1], opacity: [0.6, 0.15] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut', delay: 0.6 }}
        />

        {/* Rotating sweep line */}
        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          style={{
            background: 'conic-gradient(from 0deg, #0066FF 0deg, transparent 90deg)',
            opacity: 0.6,
          }}
        />

        {/* Center dot */}
        <motion.div
          className="absolute top-1/2 left-1/2 w-4 h-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#0066FF]"
          animate={{ scale: [1, 1.5, 1], opacity: [1, 0.8, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            boxShadow: '0 0 20px rgba(0, 102, 255, 0.8), 0 0 40px rgba(0, 102, 255, 0.4)',
          }}
        />

        {/* Corner brackets */}
        <div className="absolute -inset-6 pointer-events-none">
          {/* Top-left */}
          <motion.div
            className="absolute top-0 left-0 w-6 h-6 border-l-2 border-t-2 border-[#0066FF]"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          {/* Top-right */}
          <motion.div
            className="absolute top-0 right-0 w-6 h-6 border-r-2 border-t-2 border-[#0066FF]"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
          />
          {/* Bottom-left */}
          <motion.div
            className="absolute bottom-0 left-0 w-6 h-6 border-l-2 border-b-2 border-[#0066FF]"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, delay: 1 }}
          />
          {/* Bottom-right */}
          <motion.div
            className="absolute bottom-0 right-0 w-6 h-6 border-r-2 border-b-2 border-[#0066FF]"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, delay: 1.5 }}
          />
        </div>

        {/* Data stream particles (optional) */}
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute left-1/2 -translate-x-1/2 w-1 h-20 rounded-full"
              style={{
                background: 'linear-gradient(180deg, transparent, #06b6d4, transparent)',
                filter: 'blur(1px)',
              }}
              animate={{
                y: ['-20%', '120%'],
                opacity: [0, 0.4, 0],
              }}
              transition={{
                duration: 3 + i * 0.5,
                repeat: Infinity,
                ease: 'linear',
                delay: i * 1,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
