/**
 * RecentActivityList.tsx
 * Компонент для отображения списка последних 10 попыток решения задач
 * С кликабельными ссылками на страницы задач и результатами
 */

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";
import { DIFFICULTY_COLORS } from "@/lib/constants/tasks";
import type { RecentActivityItem } from "@/lib/types/stats";

interface RecentActivityListProps {
  recentActivity: RecentActivityItem[];
  loading?: boolean;
}

/**
 * Relative timestamp formatter
 */
function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return formatDistanceToNow(date, { addSuffix: true, locale: ru });
  } catch {
    return "недавно";
  }
}

/**
 * Result indicator (check or cross)
 */
function ResultBadge({ isCorrect }: { isCorrect: boolean }) {
  return isCorrect ? (
    <div className="flex items-center gap-1.5 px-2 py-1 bg-[#00ff88]/10 border border-[#00ff88]/30 rounded">
      <span className="text-sm font-bold" style={{ color: "#00ff88", textShadow: "0 0 6px #00ff88" }}>
        ✓
      </span>
      <span className="text-xs font-mono tracking-wide" style={{ color: "#00ff88" }}>
        ВЕРНО
      </span>
    </div>
  ) : (
    <div className="flex items-center gap-1.5 px-2 py-1 bg-[#ff3b30]/10 border border-[#ff3b30]/30 rounded">
      <span className="text-sm font-bold" style={{ color: "#ff3b30", textShadow: "0 0 6px #ff3b30" }}>
        ✕
      </span>
      <span className="text-xs font-mono tracking-wide" style={{ color: "#ff3b30" }}>
        НЕВЕРНО
      </span>
    </div>
  );
}

export function RecentActivityList({ recentActivity, loading }: RecentActivityListProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="h-16 bg-gray-800/30 rounded-lg animate-pulse border border-gray-700/30"
            style={{
              clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
            }}
          />
        ))}
      </div>
    );
  }

  if (recentActivity.length === 0) {
    return (
      <div className="rounded-lg border border-gray-700/50 bg-gray-800/20 p-8 text-center">
        <p className="text-gray-400 font-mono text-sm">
          ЕЩЕ НЕТ РЕШЁННЫХ ЗАДАЧ
        </p>
        <p className="text-gray-500 font-mono text-xs mt-2 mb-4">
          Начните решать задачи из каталога
        </p>
        <Link
          href="/tasks"
          className="inline-block px-4 py-2 border border-[#0066FF]/50 text-[#0066FF] font-mono text-xs tracking-wider uppercase hover:bg-[#0066FF]/10 transition-colors"
          style={{
            clipPath: "polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))",
          }}
        >
          ОТКРЫТЬ КАТАЛОГ
        </Link>
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.35, ease: "easeOut" },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      {recentActivity.map((item, idx) => {
        const config = DIFFICULTY_COLORS[item.task_difficulty as keyof typeof DIFFICULTY_COLORS];

        return (
          <motion.div key={`${item.task_id}-${idx}`} variants={itemVariants}>
            <Link href={`/tasks/${item.task_id}`}>
              <div
                className="group p-4 border-2 border-gray-700/40 bg-gray-800/20 hover:border-[#0066FF]/60 transition-all duration-300 hover:bg-gray-800/40 cursor-pointer overflow-hidden relative"
                style={{
                  clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
                }}
              >
                {/* Hover glow */}
                <motion.div
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 0.1 }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background: "radial-gradient(circle at 100% 0%, #0066FF40 0%, transparent 60%)",
                  }}
                />

                {/* Content */}
                <div className="relative z-10 flex items-center justify-between gap-4 flex-wrap">
                  {/* Task title + difficulty */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-mono truncate group-hover:text-[#00d4ff] transition-colors">
                      {item.task_title}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      {/* Difficulty badge */}
                      <div
                        className="px-2 py-1 text-xs font-mono font-bold border"
                        style={{
                          color: config.hex,
                          borderColor: `${config.hex}60`,
                          backgroundColor: `${config.hex}15`,
                          textShadow: `0 0 4px ${config.hex}`,
                          clipPath: "polygon(0 0, calc(100% - 3px) 0, 100% 3px, 100% 100%, 3px 100%, 0 calc(100% - 3px))",
                        }}
                      >
                        {config.code} {config.label}
                      </div>

                      {/* Timestamp */}
                      <p className="text-xs text-gray-500 font-mono">
                        {formatTimestamp(item.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Result badge */}
                  <div className="flex-shrink-0">
                    <ResultBadge isCorrect={item.is_correct} />
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
