'use client';

import { motion } from 'motion/react';
import type { PlayerInfo } from '@/lib/types/websocket';

interface MatchHeaderProps {
  player1: PlayerInfo & { isYou: boolean };
  player2: PlayerInfo & { isYou: boolean };
  score1: number;
  score2: number;
  timeElapsed: number;
  opponentDisconnected?: { secondsRemaining: number };
  onForfeit?: () => void;
  matchFinished?: boolean;
}

/**
 * Header матча: информация об игроках, счёт, таймер
 * Layout: Player1 (левая) | Score (центр) | Player2 (правая)
 */
export function MatchHeader({
  player1,
  player2,
  score1,
  score2,
  timeElapsed,
  opponentDisconnected,
  onForfeit,
  matchFinished = false,
}: MatchHeaderProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <motion.header
      className="relative bg-[#121212] border-b border-[#0066FF]/30 overflow-hidden"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Decorative line */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#0066FF] to-transparent"
        style={{ boxShadow: '0 0 10px rgba(0, 102, 255, 0.5)' }}
      />

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-3 gap-8 items-start">
          {/* Player 1 (Left) */}
          <motion.div
            className={`text-left space-y-3 px-4 py-4 rounded border ${
              player1.isYou
                ? 'border-[#a855f7]/60 bg-[#a855f7]/5'
                : 'border-transparent hover:border-[#0066FF]/30'
            } transition-all`}
            whileHover={{ scale: 1.02, backgroundColor: 'rgba(0, 102, 255, 0.05)' }}
          >
            <p className="text-xs font-mono text-[#0066FF] uppercase tracking-widest">
              {player1.isYou ? '▸ ВЫ' : '◇ СОПЕРНИК'}
            </p>
            <p className="text-lg font-mono font-bold text-white">{player1.username}</p>
            <p className="text-xs font-mono text-[#0066FF] font-semibold">★ {player1.rating}</p>
          </motion.div>

          {/* Center - Score & Timer */}
          <div className="text-center space-y-4">
            {/* Score - Enhanced Visual */}
            <motion.div
              className="relative py-4"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              <div className="flex justify-center items-baseline gap-4">
                {/* Left score */}
                <motion.div
                  className="text-center"
                  key={`score1-${score1}`}
                  initial={{ scale: 1.3, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                >
                  <motion.span
                    className="text-6xl font-mono font-bold block"
                    style={{
                      color: '#0066FF',
                      textShadow: '0 0 30px rgba(0, 102, 255, 0.9), 0 0 60px rgba(0, 102, 255, 0.4)',
                    }}
                  >
                    {score1}
                  </motion.span>
                </motion.div>

                {/* Divider */}
                <motion.div
                  className="flex flex-col items-center gap-1"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className="w-1 h-6 bg-[#0066FF]/40 rounded-full" />
                  <span className="text-xl font-mono text-[#0066FF]/60">—</span>
                  <div className="w-1 h-6 bg-[#0066FF]/40 rounded-full" />
                </motion.div>

                {/* Right score */}
                <motion.div
                  className="text-center"
                  key={`score2-${score2}`}
                  initial={{ scale: 1.3, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                >
                  <motion.span
                    className="text-6xl font-mono font-bold block"
                    style={{
                      color: '#0066FF',
                      textShadow: '0 0 30px rgba(0, 102, 255, 0.9), 0 0 60px rgba(0, 102, 255, 0.4)',
                    }}
                  >
                    {score2}
                  </motion.span>
                </motion.div>
              </div>
            </motion.div>

            {/* Timer */}
            <motion.div
              className={`text-3xl font-mono font-bold tracking-wider py-2 px-4 rounded ${
                timeElapsed > 3600
                  ? 'bg-[#ff3b30]/10 text-[#ff3b30]'
                  : timeElapsed > 1800
                    ? 'bg-[#f97316]/10 text-[#f97316]'
                    : 'bg-[#00ff88]/5 text-[#00ff88]'
              }`}
              style={{
                textShadow:
                  timeElapsed > 3600
                    ? '0 0 20px rgba(255, 59, 48, 0.6)'
                    : timeElapsed > 1800
                      ? '0 0 15px rgba(249, 115, 22, 0.4)'
                      : '0 0 15px rgba(0, 255, 136, 0.3)',
              }}
              animate={timeElapsed > 3600 ? { scale: [1, 1.06, 1] } : {}}
              transition={{ duration: 0.8, repeat: timeElapsed > 3600 ? Infinity : 0 }}
            >
              {formatTime(timeElapsed)}
            </motion.div>

            {/* Disconnect warning badge */}
            {opponentDisconnected && (
              <motion.div
                className="inline-block px-4 py-2 text-xs font-mono bg-[#ff3b30]/20 border border-[#ff3b30] text-[#ff3b30] rounded"
                animate={{ opacity: [0.5, 1, 0.5], scale: [0.95, 1.02, 0.95] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              >
                ⚠ FORFEIT через {opponentDisconnected.secondsRemaining}s
              </motion.div>
            )}

            {/* Forfeit Button */}
            {!matchFinished && onForfeit && (
              <button
                onClick={() => {
                  if (confirm('Вы уверены что хотите сдаться?')) {
                    onForfeit();
                  }
                }}
                className="px-4 py-2 text-xs font-mono bg-[#1a0a0a] border border-[#ff3b30]/40 text-[#ff3b30] hover:border-[#ff3b30] hover:bg-[#ff3b30]/10 transition-all"
                style={{
                  clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                }}
              >
                СДАТЬСЯ
              </button>
            )}
          </div>

          {/* Player 2 (Right) */}
          <motion.div
            className={`text-right space-y-3 px-4 py-4 rounded border ${
              player2.isYou
                ? 'border-[#a855f7]/60 bg-[#a855f7]/5'
                : 'border-transparent hover:border-[#0066FF]/30'
            } transition-all`}
            whileHover={{ scale: 1.02, backgroundColor: 'rgba(0, 102, 255, 0.05)' }}
          >
            <p className="text-xs font-mono text-[#0066FF] uppercase tracking-widest">
              {player2.isYou ? '▸ ВЫ' : '◇ СОПЕРНИК'}
            </p>
            <p className="text-lg font-mono font-bold text-white">{player2.username}</p>
            <p className="text-xs font-mono text-[#0066FF] font-semibold">★ {player2.rating}</p>
          </motion.div>
        </div>
      </div>

      {/* Bottom decorative line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#00d4ff] to-transparent"
        style={{ boxShadow: '0 0 10px rgba(0, 212, 255, 0.3)' }}
      />
    </motion.header>
  );
}
