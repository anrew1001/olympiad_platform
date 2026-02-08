'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { useMatchmaking } from '@/lib/hooks/useMatchmaking';
import { useAuth } from '@/lib/hooks/useAuth';
import { QueueAnimation } from '@/components/pvp/QueueAnimation';
import { QueueStatus } from '@/components/pvp/QueueStatus';
import { LoadingScreen } from '@/components/ui/LoadingScreen';

/**
 * Страница поиска матча
 * Flow: idle → searching → found → redirect /pvp/match/[id]
 */
export default function PvPQueuePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { status, matchId, error, find, cancel } = useMatchmaking();
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // === Auth Check ===

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?returnUrl=/pvp');
    }
  }, [isAuthenticated, authLoading, router]);

  // === Redirect on Match Found ===
  useEffect(() => {
    if (status === 'found' && matchId) {
      router.push(`/pvp/match/${matchId}`);
    }
  }, [status, matchId, router]);

  // === Elapsed Time Counter ===

  useEffect(() => {
    if (status !== 'searching') {
      setElapsedSeconds(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [status]);

  // === Loading or Auth Check State ===

  if (authLoading) {
    return <LoadingScreen text="ПРОВЕРКА АВТОРИЗАЦИИ..." />;
  }

  if (!isAuthenticated) {
    return null; // Will redirect in effect
  }

  return (
    <div className="min-h-screen bg-[#121212] relative overflow-hidden">
      {/* Animated grid background */}
      <motion.div
        className="fixed inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(90deg, #0066FF 1px, transparent 1px),
            linear-gradient(0deg, #0066FF 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
        animate={{ backgroundPosition: ['0% 0%', '100% 100%'] }}
        transition={{ duration: 20, repeat: Infinity, repeatType: 'reverse', ease: 'linear' }}
      />

      {/* Horizontal scan line */}
      <motion.div
        className="fixed left-0 right-0 h-[2px] z-40"
        style={{
          top: '50%',
          background: 'linear-gradient(90deg, transparent, #0066FF, transparent)',
          boxShadow: '0 0 20px rgba(0, 102, 255, 0.8)',
        }}
        animate={{ y: ['0%', '100vh'] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
      />

      {/* CRT scanlines overlay */}
      <div
        className="fixed inset-0 pointer-events-none z-50 opacity-[0.015]"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)',
        }}
      />

      {/* Main container */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 py-12 min-h-screen flex flex-col justify-center items-center">
        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1
            className="text-5xl md:text-6xl font-mono uppercase tracking-[0.1em] text-white mb-2"
            style={{
              textShadow: '0 0 30px rgba(0, 102, 255, 0.5)',
            }}
          >
            ⚔️ АРЕНА ПОИСКА
          </h1>
          <p className="text-sm font-mono text-[#0066FF] tracking-widest">НАЙДИ СОПЕРНИКА И ПОМЕРЬСЯ СИЛАМИ</p>
        </motion.div>

        {/* Main content */}
        <motion.div
          className="w-full max-w-2xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          {/* Idle state - Find button */}
          {status === 'idle' && !error && (
            <motion.div
              className="flex flex-col items-center gap-8"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <p className="text-center text-[#888] font-mono text-sm leading-relaxed max-w-md">
                Нажми кнопку ниже, чтобы начать поиск противника.
                <br />
                Система найдёт подходящего игрока в твоём рейтинговом диапазоне.
              </p>

              <motion.button
                onClick={find}
                className="group relative px-16 py-5 font-mono uppercase text-lg tracking-wider text-white border-2 border-[#0066FF] bg-[#0066FF]/10 overflow-hidden"
                style={{
                  clipPath:
                    'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px))',
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {/* Animated gradient background */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-[#0066FF] via-[#00d4ff] to-[#0066FF] opacity-0 group-hover:opacity-20"
                  animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                  style={{ backgroundSize: '200% 100%' }}
                />

                {/* Glow effect */}
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{
                    boxShadow: 'inset 0 0 20px rgba(0, 102, 255, 0.3)',
                  }}
                />

                <span className="relative z-10">НАЙТИ СОПЕРНИКА</span>
              </motion.button>

              {/* Decorative info */}
              <motion.div
                className="text-xs font-mono text-[#0066FF]/60 text-center space-y-1"
                animate={{ opacity: [0.4, 0.8, 0.4] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                <p>◇ СИСТЕМА ПОИСКА АКТИВНА ◇</p>
                <p>{'>'} Твой рейтинг: {user?.rating || 1200}</p>
              </motion.div>
            </motion.div>
          )}

          {/* Searching state */}
          {status === 'searching' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <QueueAnimation />
              <QueueStatus isSearching onCancel={cancel} elapsedSeconds={elapsedSeconds} />
            </motion.div>
          )}

          {/* Error state */}
          {error && (
            <motion.div
              className="text-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div
                className="relative border-2 border-[#ff3b30] bg-[#ff3b30]/5 p-6 mb-6"
                style={{
                  clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
                }}
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-[#ff3b30]" />
                <p className="text-[#ff3b30] font-mono text-sm pl-3">✗ {error}</p>
              </div>

              <motion.button
                onClick={() => {
                  find();
                }}
                className="px-8 py-3 font-mono text-sm uppercase text-white border border-[#0066FF] hover:bg-[#0066FF]/10 transition-all"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Попробовать снова
              </motion.button>
            </motion.div>
          )}
        </motion.div>

        {/* Footer info */}
        <motion.div
          className="absolute bottom-8 left-0 right-0 text-center text-xs font-mono text-[#444] pointer-events-none"
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          {'[СИСТЕМА ГОТОВА К ПОИСКУ]'}
        </motion.div>
      </div>
    </div>
  );
}
