/**
 * TopicAnalysis.tsx
 * Компонент для отображения анализа сильных и слабых тем пользователя
 * Cyberpunk стиль с неоновыми акцентами
 */

"use client";

import type { TopicStats } from "@/lib/types/match";

interface TopicAnalysisProps {
  strongestTopics: TopicStats[];
  weakestTopics: TopicStats[];
  loading?: boolean;
}

export function TopicAnalysis({
  strongestTopics,
  weakestTopics,
  loading,
}: TopicAnalysisProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div
          className="h-64 bg-[#1a1a1a] border border-[#333] animate-pulse"
          style={{
            clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
          }}
        />
        <div
          className="h-64 bg-[#1a1a1a] border border-[#333] animate-pulse"
          style={{
            clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
          }}
        />
      </div>
    );
  }

  // Если нет данных по темам
  if (strongestTopics.length === 0 && weakestTopics.length === 0) {
    return (
      <div
        className="relative p-8 border border-[#333] bg-[#1a1a1a] text-center"
        style={{
          clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
        }}
      >
        <p className="text-gray-500 font-mono text-sm tracking-wider">
          НЕДОСТАТОЧНО ДАННЫХ ДЛЯ АНАЛИЗА
        </p>
        <p className="text-xs text-gray-600 font-mono mt-2">
          Решите минимум 3 задачи по одной теме
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Сильные темы */}
      <TopicColumn
        title="СИЛЬНЫЕ ТЕМЫ"
        subtitle="Топ-3 по проценту правильных ответов"
        topics={strongestTopics}
        accentColor="#00ff88"
        borderColor="#00ff8840"
        bgColor="#001a0f"
        emptyMessage="Нет данных"
      />

      {/* Слабые темы */}
      <TopicColumn
        title="СЛАБЫЕ ТЕМЫ"
        subtitle="Требуют дополнительной практики"
        topics={weakestTopics}
        accentColor="#ff3b30"
        borderColor="#ff3b3040"
        bgColor="#1a0a0a"
        emptyMessage="Нет данных"
      />
    </div>
  );
}

interface TopicColumnProps {
  title: string;
  subtitle: string;
  topics: TopicStats[];
  accentColor: string;
  borderColor: string;
  bgColor: string;
  emptyMessage: string;
}

function TopicColumn({
  title,
  subtitle,
  topics,
  accentColor,
  borderColor,
  bgColor,
  emptyMessage,
}: TopicColumnProps) {
  return (
    <div
      className="relative p-6 border"
      style={{
        backgroundColor: bgColor,
        borderColor: borderColor,
        clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
      }}
    >
      {/* Corner bracket */}
      <div
        className="absolute top-0 right-0 w-3 h-3"
        style={{
          backgroundColor: accentColor,
          boxShadow: `0 0 10px ${accentColor}`,
        }}
      />

      <h4 className="text-sm font-mono tracking-widest uppercase mb-1" style={{ color: accentColor }}>
        {title}
      </h4>
      <p className="text-xs font-mono text-gray-500 mb-6">{subtitle}</p>

      {topics.length === 0 ? (
        <p className="text-gray-600 font-mono text-xs text-center py-8">
          {emptyMessage}
        </p>
      ) : (
        <div className="space-y-5">
          {topics.map((topic, index) => (
            <div key={topic.topic}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold font-mono" style={{ color: accentColor }}>
                    #{index + 1}
                  </span>
                  <span className="font-mono text-sm text-white">
                    {formatTopicName(topic.topic)}
                  </span>
                </div>
                <span className="text-sm font-bold font-mono" style={{ color: accentColor }}>
                  {topic.success_rate.toFixed(1)}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="relative w-full bg-[#1a1a1a] border border-[#333] h-2 overflow-hidden">
                <div
                  className="h-full transition-all duration-500"
                  style={{
                    width: `${topic.success_rate}%`,
                    backgroundColor: accentColor,
                    boxShadow: `0 0 8px ${accentColor}`,
                  }}
                />
              </div>

              <p className="text-[10px] font-mono text-gray-600 mt-1">
                {topic.attempts}{" "}
                {pluralize(topic.attempts, "попытка", "попытки", "попыток")}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Форматирование названия темы (например, "dynamic_programming" → "Dynamic Programming")
function formatTopicName(topic: string): string {
  return topic
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
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
