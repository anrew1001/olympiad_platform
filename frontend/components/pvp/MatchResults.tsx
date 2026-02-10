'use client';

import { motion } from 'motion/react';
import Link from 'next/link';

interface MatchResultsProps {
  outcome: 'victory' | 'defeat' | 'draw';
  finalScores: { player1_score: number; player2_score: number };
  ratingChange: number;
  newRating: number;
  reason: 'completion' | 'forfeit' | 'technical_error';
}

/**
 * Экран результатов матча
 * Показывает: исход, счёт, изменение рейтинга
 */
export function MatchResults({
  outcome,
  finalScores,
  ratingChange,
  newRating,
  reason,
}: MatchResultsProps) {
  const isVictory = outcome === 'victory';
  const isDraw = outcome === 'draw';

  const getOutcomeText = () => {
    if (isVictory) return 'ПОБЕДА!';
    if (isDraw) return 'НИЧЬЯ!';
    return 'ПОРАЖЕНИЕ...';
  };

  const getOutcomeColor = () => {
    if (isVictory) return '#00ff88';
    if (isDraw) return '#eab308';
    return '#ff3b30';
  };

  const getRatingColor = () => {
    return ratingChange >= 0 ? '#00ff88' : '#ff3b30';
  };

  const containerVariants: any = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.2,
        staggerChildren: 0.15,
      },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: 'backOut' },
    },
  };

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#121212]/95 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Radial pulse background effect - DRAMATIC */}
      <motion.div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle, ${getOutcomeColor()}30 0%, ${getOutcomeColor()}10 30%, transparent 70%)`,
          width: '1000px',
          height: '1000px',
          top: '50%',
          left: '50%',
          marginTop: '-500px',
          marginLeft: '-500px',
        }}
        animate={{ scale: [0.8, 1.3, 0.8], opacity: [0.8, 0.3, 0.6] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Secondary pulse ring */}
      <motion.div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          border: `2px solid ${getOutcomeColor()}`,
          width: '600px',
          height: '600px',
          top: '50%',
          left: '50%',
          marginTop: '-300px',
          marginLeft: '-300px',
        }}
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.1, 0.3] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
      />

      {/* Main card */}
      <motion.div
        className="relative z-10 max-w-2xl w-full mx-4 p-12 text-center rounded border border-[#1a1a1a] bg-[#121212]/80 backdrop-blur"
        style={{
          clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px))',
          boxShadow: `0 0 40px ${getOutcomeColor()}40, inset 0 0 30px ${getOutcomeColor()}10`,
        }}
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
      >
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-8"
        >
          {/* Outcome text */}
          <motion.div variants={itemVariants} className="space-y-3">
            <h1
              className="text-5xl md:text-6xl font-mono uppercase font-bold tracking-wider"
              style={{
                color: getOutcomeColor(),
                textShadow: `0 0 30px ${getOutcomeColor()}80`,
              }}
            >
              {getOutcomeText()}
            </h1>
          </motion.div>

          {/* Score */}
          <motion.div variants={itemVariants} className="space-y-2">
            <p className="text-sm font-mono text-[#0066FF] uppercase tracking-widest">
              ФИНАЛЬНЫЙ СЧЁТ
            </p>
            <div className="flex justify-center items-baseline gap-6">
              <motion.span
                className="text-5xl font-mono font-bold text-white"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.8 }}
              >
                {finalScores.player1_score}
              </motion.span>
              <span className="text-3xl font-mono text-[#444]">—</span>
              <motion.span
                className="text-5xl font-mono font-bold text-white"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
              >
                {finalScores.player2_score}
              </motion.span>
            </div>
          </motion.div>

          {/* Rating change - DRAMATIC */}
          <motion.div variants={itemVariants} className="space-y-4 py-6 px-6 rounded border border-[#0066FF]/30 bg-[#0066FF]/5">
            <p className="text-sm font-mono text-[#0066FF] uppercase tracking-widest text-center">
              ИЗМЕНЕНИЕ РЕЙТИНГА
            </p>

            <div className="flex justify-center items-center gap-6">
              {/* Old rating */}
              <motion.div
                className="text-center"
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6, duration: 0.5 }}
              >
                <span className="text-4xl font-mono font-bold text-[#888] block">{newRating - ratingChange}</span>
                <span className="text-xs font-mono text-[#555] mt-2">ДО</span>
              </motion.div>

              {/* Arrow with animation */}
              <motion.div
                className="flex flex-col items-center gap-2"
                animate={{ x: [0, 15, 0] }}
                transition={{ duration: 1.5, delay: 0.7, repeat: Infinity }}
              >
                <motion.span
                  className="text-3xl font-mono text-[#0066FF]"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1.5, delay: 0.7, repeat: Infinity }}
                >
                  →
                </motion.span>
              </motion.div>

              {/* New rating */}
              <motion.div
                className="text-center"
                initial={{ opacity: 0, x: 30, scale: 0.5 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                transition={{ delay: 0.8, duration: 0.6, ease: 'backOut' }}
              >
                <motion.span
                  className="text-4xl font-mono font-bold block"
                  style={{
                    color: getRatingColor(),
                    textShadow: `0 0 20px ${getRatingColor()}80`,
                  }}
                  key={newRating}
                >
                  {newRating}
                </motion.span>
                <span className="text-xs font-mono text-[#555] mt-2">ПОСЛЕ</span>
              </motion.div>
            </div>

            {/* Rating delta badge */}
            <motion.div
              className="text-center"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1, duration: 0.5, type: 'spring' }}
            >
              <motion.span
                className="inline-block px-6 py-2 rounded text-lg font-mono font-bold"
                style={{
                  backgroundColor: `${getRatingColor()}20`,
                  color: getRatingColor(),
                  border: `2px solid ${getRatingColor()}`,
                  textShadow: `0 0 15px ${getRatingColor()}`,
                  boxShadow: `0 0 20px ${getRatingColor()}60`,
                }}
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1.2, delay: 1, repeat: Infinity }}
              >
                {ratingChange >= 0 ? '▲ +' : '▼ '}{Math.abs(ratingChange)}
              </motion.span>
            </motion.div>
          </motion.div>

          {/* Reason (if forfeit or error) */}
          {(reason === 'forfeit' || reason === 'technical_error') && (
            <motion.p variants={itemVariants} className="text-xs font-mono text-[#888]">
              {reason === 'forfeit' && 'Соперник отключился'}
              {reason === 'technical_error' && 'Техническая ошибка (рейтинг не изменился)'}
            </motion.p>
          )}

          {/* Buttons */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row gap-4 pt-4"
          >
            <Link
              href="/pvp"
              className="flex-1 group relative px-8 py-3 font-mono uppercase text-sm text-white border-2 border-[#0066FF] bg-[#0066FF]/10 overflow-hidden text-center"
              style={{
                clipPath: 'polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))',
              }}
            >
              <motion.div
                className="absolute inset-0 bg-[#0066FF]/20"
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 1 }}
              />
              <span className="relative z-10">ИГРАТЬ СНОВА</span>
            </Link>

            <Link
              href="/tasks"
              className="flex-1 group relative px-8 py-3 font-mono uppercase text-sm text-white border-2 border-[#0066FF]/50 bg-transparent overflow-hidden text-center hover:border-[#0066FF] transition-colors"
              style={{
                clipPath: 'polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))',
              }}
            >
              <span className="relative z-10">К ЗАДАЧАМ</span>
            </Link>
          </motion.div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
