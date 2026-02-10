/**
 * MatchStats.tsx
 * Компонент для отображения статистики по матчам (W/L/D, win rate, серии побед)
 * Cyberpunk стиль с угловыми срезами и неоновыми акцентами
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
      <div className="grid grid-cols-2 gap-4 md:grid-cols-7">
        {[...Array(7)].map((_, i) => (
          <div
            key={i}
            className="h-24 bg-[#1a1a1a] border border-[#333] animate-pulse"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
            }}
          />
        ))}
      </div>
    );
  }

  const winRatePercent = stats.win_rate;

  const statCards = [
    {
      label: 'ВСЕГО МАТЧЕЙ',
      value: stats.total_matches,
      color: '#666',
      bgColor: '#1a1a1a',
    },
    {
      label: 'ПОБЕДЫ',
      value: stats.won,
      color: '#00ff88',
      bgColor: '#001a0f',
    },
    {
      label: 'ПОРАЖЕНИЯ',
      value: stats.lost,
      color: '#ff3b30',
      bgColor: '#1a0a0a',
    },
    {
      label: 'НИЧЬИ',
      value: stats.draw,
      color: '#999',
      bgColor: '#1a1a1a',
    },
    {
      label: 'WIN RATE',
      value: `${winRatePercent.toFixed(1)}%`,
      color: '#0066FF',
      bgColor: '#0a0f1a',
    },
  ];

  // Текущая серия
  const streakColor = stats.current_streak > 0 ? '#00ff88' : stats.current_streak < 0 ? '#ff3b30' : '#666';
  const streakBg = stats.current_streak > 0 ? '#001a0f' : stats.current_streak < 0 ? '#1a0a0a' : '#1a1a1a';
  const streakText = stats.current_streak > 0
    ? `${stats.current_streak} ${pluralize(stats.current_streak, "победа", "победы", "побед")} подряд`
    : stats.current_streak < 0
    ? `${Math.abs(stats.current_streak)} ${pluralize(Math.abs(stats.current_streak), "поражение", "поражения", "поражений")} подряд`
    : "Нет серии";

  return (
    <div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-7 mb-6">
        {/* Основные статы */}
        {statCards.map((card, idx) => (
          <div
            key={idx}
            className="relative p-4 border transition-all hover:brightness-110"
            style={{
              backgroundColor: card.bgColor,
              borderColor: card.color + '40',
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
            }}
          >
            {/* Corner bracket */}
            <div
              className="absolute top-0 right-0 w-2 h-2"
              style={{
                backgroundColor: card.color,
                boxShadow: `0 0 8px ${card.color}`,
              }}
            />

            <p className="text-[10px] font-mono tracking-wider mb-2 uppercase" style={{ color: card.color }}>
              {card.label}
            </p>
            <p className="text-3xl font-bold font-mono" style={{ color: card.color }}>
              {card.value}
            </p>
          </div>
        ))}

        {/* Текущая серия */}
        <div
          className="relative p-4 border transition-all hover:brightness-110"
          style={{
            backgroundColor: streakBg,
            borderColor: streakColor + '40',
            clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
          }}
        >
          <div
            className="absolute top-0 right-0 w-2 h-2"
            style={{
              backgroundColor: streakColor,
              boxShadow: `0 0 8px ${streakColor}`,
            }}
          />

          <p className="text-[10px] font-mono tracking-wider mb-2 uppercase" style={{ color: streakColor }}>
            СЕРИЯ
          </p>
          <p className="text-3xl font-bold font-mono" style={{ color: streakColor }}>
            {stats.current_streak > 0 && "+"}
            {stats.current_streak}
          </p>
          <p className="text-[9px] font-mono mt-1" style={{ color: streakColor + 'aa' }}>
            {streakText}
          </p>
        </div>

        {/* Лучшая серия */}
        <div
          className="relative p-4 border transition-all hover:brightness-110"
          style={{
            backgroundColor: '#0f0a1a',
            borderColor: '#9966ff40',
            clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
          }}
        >
          <div
            className="absolute top-0 right-0 w-2 h-2"
            style={{
              backgroundColor: '#9966ff',
              boxShadow: '0 0 8px #9966ff',
            }}
          />

          <p className="text-[10px] font-mono tracking-wider mb-2 uppercase text-[#9966ff]">
            ЛУЧШАЯ
          </p>
          <p className="text-3xl font-bold font-mono text-[#9966ff]">
            {stats.best_win_streak}
          </p>
          <p className="text-[9px] font-mono mt-1 text-[#9966ffaa]">
            {stats.best_win_streak > 0
              ? `${stats.best_win_streak} ${pluralize(stats.best_win_streak, "победа", "победы", "побед")} подряд`
              : "Нет побед"}
          </p>
        </div>
      </div>

      {/* Progress bar для win rate */}
      {stats.total_matches > 0 && (
        <div
          className="relative p-4 border border-[#0066FF]/20 bg-[#0a0f1a]"
          style={{
            clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-mono tracking-wider uppercase text-[#0066FF]">
              ПРОГРЕСС ПОБЕД
            </p>
            <p className="text-xs font-mono text-gray-400">
              {stats.won} из {stats.total_matches}
            </p>
          </div>

          {/* Progress bar */}
          <div className="relative w-full h-2 bg-[#1a1a1a] border border-[#333] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#00ff88] to-[#0066FF] transition-all duration-500"
              style={{
                width: `${Math.min(winRatePercent, 100)}%`,
                boxShadow: '0 0 10px rgba(0, 255, 136, 0.5)',
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function pluralize(
  count: number,
  one: string,
  few: string,
  many: string
): string {
  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}
