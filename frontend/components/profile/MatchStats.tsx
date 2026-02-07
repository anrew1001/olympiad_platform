/**
 * MatchStats.tsx
 * Компонент для отображения статистики по матчам (W/L/D, win rate)
 */

"use client";

import type { MatchStats } from "@/lib/types/match";

interface MatchStatsProps {
  stats: MatchStats;
  loading?: boolean;
}

export function MatchStats({ stats, loading }: MatchStatsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  const winRatePercent = stats.win_rate;

  return (
    <div className="rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        Статистика матчей
      </h3>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        {/* Всего матчей */}
        <div className="rounded-lg bg-gray-50 dark:bg-gray-700 p-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Всего матчей</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {stats.total_matches}
          </p>
        </div>

        {/* Победы */}
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 p-4 text-center">
          <p className="text-sm text-green-600 dark:text-green-400">Победы</p>
          <p className="text-3xl font-bold text-green-700 dark:text-green-400">
            {stats.won}
          </p>
        </div>

        {/* Поражения */}
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-center">
          <p className="text-sm text-red-600 dark:text-red-400">Поражения</p>
          <p className="text-3xl font-bold text-red-700 dark:text-red-400">
            {stats.lost}
          </p>
        </div>

        {/* Ничьи */}
        <div className="rounded-lg bg-gray-100 dark:bg-gray-700 p-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Ничьи</p>
          <p className="text-3xl font-bold text-gray-700 dark:text-gray-300">
            {stats.draw}
          </p>
        </div>

        {/* Win Rate */}
        <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4 text-center">
          <p className="text-sm text-blue-600 dark:text-blue-400">Win Rate</p>
          <p className="text-3xl font-bold text-blue-700 dark:text-blue-400">
            {winRatePercent.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Progress bar для win rate */}
      {stats.total_matches > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Прогресс побед
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {stats.won} из {stats.total_matches}
            </p>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(winRatePercent, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
