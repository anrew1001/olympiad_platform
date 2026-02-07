/**
 * /profile
 * Страница профиля пользователя с секцией истории PvP матчей
 * Включает список матчей, статистику и график рейтинга
 */

"use client";

import { useState, useEffect, Suspense } from "react";
import { fetchMatchStats } from "@/lib/api/matches";
import type { MatchStats } from "@/lib/types/match";
import { MatchHistoryList } from "@/components/profile/MatchHistoryList";
import { MatchStats as MatchStatsComponent } from "@/components/profile/MatchStats";
import { RatingChart } from "@/components/profile/RatingChart";
import { TopicAnalysis } from "@/components/profile/TopicAnalysis";

export default function ProfilePage() {
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Загрузить статистику при загрузке страницы
  useEffect(() => {
    const loadStats = async () => {
      try {
        setStatsLoading(true);
        setStatsError(null);
        const result = await fetchMatchStats();
        setStats(result);
      } catch (err) {
        setStatsError(
          err instanceof Error ? err.message : "Ошибка при загрузке статистики"
        );
      } finally {
        setStatsLoading(false);
      }
    };

    loadStats();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black py-12">
      <div className="max-w-6xl mx-auto px-4">
        {/* Заголовок */}
        <div className="mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Ваш профиль
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            История PvP матчей и статистика
          </p>
        </div>

        {/* Статистика */}
        <div className="mb-8">
          {statsError && (
            <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 p-4 mb-4">
              <p className="text-red-700 dark:text-red-400">
                Ошибка загрузки статистики: {statsError}
              </p>
            </div>
          )}
          {stats && (
            <MatchStatsComponent stats={stats} loading={statsLoading} />
          )}
        </div>

        {/* График рейтинга */}
        {stats && stats.rating_history.length > 0 && (
          <div className="mb-8">
            <RatingChart data={stats.rating_history} />
          </div>
        )}

        {/* Анализ по темам */}
        {stats &&
          (stats.strongest_topics.length > 0 ||
            stats.weakest_topics.length > 0) && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Анализ по темам
              </h2>
              <TopicAnalysis
                strongestTopics={stats.strongest_topics}
                weakestTopics={stats.weakest_topics}
                loading={statsLoading}
              />
            </div>
          )}

        {/* История матчей */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            История матчей
          </h2>
          <Suspense fallback={
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-24 bg-gray-200 rounded-lg animate-pulse"
                />
              ))}
            </div>
          }>
            <MatchHistoryList />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
