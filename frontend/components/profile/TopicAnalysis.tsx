/**
 * TopicAnalysis.tsx
 * Компонент для отображения анализа сильных и слабых тем пользователя
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
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
      </div>
    );
  }

  // Если нет данных по темам
  if (strongestTopics.length === 0 && weakestTopics.length === 0) {
    return (
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-8 text-center">
        <p className="text-gray-600 dark:text-gray-400">
          Недостаточно данных для анализа тем
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
          Решите минимум 3 задачи по одной теме для отображения статистики
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Сильные темы */}
      <TopicColumn
        title="Сильные темы"
        subtitle="Топ-3 по проценту правильных ответов"
        topics={strongestTopics}
        colorScheme="green"
        emptyMessage="Нет данных"
      />

      {/* Слабые темы */}
      <TopicColumn
        title="Слабые темы"
        subtitle="Требуют дополнительной практики"
        topics={weakestTopics}
        colorScheme="red"
        emptyMessage="Нет данных"
      />
    </div>
  );
}

interface TopicColumnProps {
  title: string;
  subtitle: string;
  topics: TopicStats[];
  colorScheme: "green" | "red";
  emptyMessage: string;
}

function TopicColumn({
  title,
  subtitle,
  topics,
  colorScheme,
  emptyMessage,
}: TopicColumnProps) {
  const colors = {
    green: {
      bg: "bg-green-50 dark:bg-green-900/20",
      border: "border-green-200 dark:border-green-700",
      text: "text-green-700 dark:text-green-400",
      progressBg: "bg-green-100 dark:bg-green-800/30",
      progressBar: "bg-gradient-to-r from-green-400 to-green-600",
    },
    red: {
      bg: "bg-red-50 dark:bg-red-900/20",
      border: "border-red-200 dark:border-red-700",
      text: "text-red-700 dark:text-red-400",
      progressBg: "bg-red-100 dark:bg-red-800/30",
      progressBar: "bg-gradient-to-r from-red-400 to-red-600",
    },
  };

  const color = colors[colorScheme];

  return (
    <div className={`rounded-lg ${color.bg} border ${color.border} p-6`}>
      <h4 className={`text-lg font-semibold ${color.text} mb-1`}>
        {title}
      </h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{subtitle}</p>

      {topics.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-500 text-center py-8">
          {emptyMessage}
        </p>
      ) : (
        <div className="space-y-4">
          {topics.map((topic, index) => (
            <div key={topic.topic}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-bold ${color.text}`}>
                    #{index + 1}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {formatTopicName(topic.topic)}
                  </span>
                </div>
                <span className={`text-sm font-semibold ${color.text}`}>
                  {topic.success_rate.toFixed(1)}%
                </span>
              </div>

              {/* Progress bar */}
              <div
                className={`w-full ${color.progressBg} rounded-full h-2.5 overflow-hidden`}
              >
                <div
                  className={`h-full ${color.progressBar} rounded-full transition-all duration-300`}
                  style={{ width: `${topic.success_rate}%` }}
                />
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
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
