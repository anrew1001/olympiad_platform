/**
 * Difficulty Level Badge
 * Интерактивный индикатор уровня сложности задания
 */

"use client";

import { motion } from "motion/react";
import { DIFFICULTY_COLORS } from "@/lib/constants/tasks";

interface DifficultyBadgeProps {
  difficulty: number; // 1-5
  compact?: boolean;
}

export function DifficultyBadge({ difficulty, compact = false }: DifficultyBadgeProps) {
  const config = DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS];

  if (!config) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        relative inline-flex items-center gap-2.5 px-3 py-2
        border ${config.border} ${config.bg}
        font-mono text-xs tracking-wide
      `}
      style={{
        clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)",
      }}
    >
      {/* Animated scan line */}
      <motion.div
        animate={{
          scaleY: [0, 1, 0],
          opacity: [0, 0.25, 0],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "linear",
        }}
        className={`absolute inset-0 ${config.bg}`}
        style={{ transformOrigin: "top" }}
      />

      {/* Pixel progress bar (пиксельная шкала сложности) */}
      <div className="flex gap-1 relative z-10">
        {Array.from({ length: 5 }).map((_, i) => (
          <motion.div
            key={i}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: i * 0.08, duration: 0.25 }}
            className="relative w-2 h-4 rounded-sm"
            style={{
              background: i < difficulty ? config.hex : "#2d3748",
              boxShadow: i < difficulty ? `0 0 6px ${config.hex}, inset 0 0 2px ${config.hex}` : "none",
              transformOrigin: "bottom",
              border: `1px solid ${i < difficulty ? config.hex : "#4a5568"}`,
            }}
          >
            {/* Glow pulse for filled bars */}
            {i < difficulty && (
              <motion.div
                animate={{
                  boxShadow: [
                    `0 0 4px ${config.hex}`,
                    `0 0 8px ${config.hex}`,
                    `0 0 4px ${config.hex}`,
                  ],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.1,
                }}
                className="absolute inset-0 rounded-sm"
              />
            )}
          </motion.div>
        ))}
      </div>

      {/* Level icon + name */}
      {!compact && (
        <motion.div
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity }}
          className={`${config.text} relative z-10 font-bold flex items-center gap-1.5`}
        >
          <span className="text-sm">{config.code}</span>
          <span className="text-[10px] hidden sm:inline">{config.label}</span>
        </motion.div>
      )}

      {/* Corner accent */}
      <div
        className="absolute top-0 right-0 w-1 h-1"
        style={{
          backgroundColor: config.hex,
          boxShadow: `0 0 4px ${config.hex}`,
        }}
      />
    </motion.div>
  );
}
