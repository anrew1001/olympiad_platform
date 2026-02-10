/**
 * DifficultyBreakdown.tsx
 * Компонент для отображения статистики по уровням сложности
 * Горизонтальные progress bars с цветовой кодировкой
 */

"use client";

import { motion } from "motion/react";
import { DIFFICULTY_COLORS } from "@/lib/constants/tasks";
import type { DifficultyStats } from "@/lib/types/stats";

interface DifficultyBreakdownProps {
  byDifficulty: DifficultyStats[];
  loading?: boolean;
}

export function DifficultyBreakdown({ byDifficulty, loading }: DifficultyBreakdownProps) {
  // Sort by difficulty (1-5)
  const sortedByDifficulty = [...byDifficulty].sort((a, b) => a.difficulty - b.difficulty);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-2 w-32 bg-gray-700/30 animate-pulse rounded" />
            <div className="h-3 w-full bg-gray-700/20 animate-pulse rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  if (sortedByDifficulty.length === 0) {
    return (
      <div className="rounded-lg border border-gray-700/50 bg-gray-800/20 p-8 text-center">
        <p className="text-gray-400 font-mono text-sm">
          ПОКА НЕТ ПОПЫТОК ПО ЗАДАЧАМ
        </p>
        <p className="text-gray-500 font-mono text-xs mt-2">
          Начните решать задачи из каталога, чтобы увидеть статистику
        </p>
      </div>
    );
  }

  const containerVariants: any = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.4, ease: "easeOut" },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-5"
    >
      {sortedByDifficulty.map((item) => {
        const config = DIFFICULTY_COLORS[item.difficulty as keyof typeof DIFFICULTY_COLORS];
        const percentage = item.total_attempts > 0
          ? (item.solved / item.total_attempts) * 100
          : 0;

        return (
          <motion.div key={item.difficulty} variants={itemVariants} className="space-y-2">
            {/* Header: Label + Stats */}
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                {/* Difficulty code/icon */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="flex-shrink-0 w-8 h-8 flex items-center justify-center font-bold text-sm"
                  style={{
                    color: config.hex,
                    textShadow: `0 0 10px ${config.hex}`,
                  }}
                >
                  {config.code}
                </motion.div>

                {/* Label */}
                <div className="flex-shrink-0">
                  <p className="font-mono text-xs tracking-wider uppercase" style={{ color: config.hex }}>
                    {config.label}
                  </p>
                </div>
              </div>

              {/* Solved count */}
              <div className="flex-shrink-0 text-right">
                <p className="text-xs font-mono text-gray-400">
                  {item.solved} <span className="text-gray-500">/ {item.total_attempts}</span>
                </p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="relative h-3 bg-gray-800/50 overflow-hidden rounded-full border border-gray-700/30">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
                className="h-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${config.hex}80, ${config.hex})`,
                  boxShadow: `0 0 12px ${config.hex}60, inset 0 0 8px ${config.hex}30`,
                }}
              />
            </div>

            {/* Percentage text */}
            <div className="flex justify-end">
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-xs font-mono tracking-wide"
                style={{ color: config.hex }}
              >
                {percentage.toFixed(1)}%
              </motion.p>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
