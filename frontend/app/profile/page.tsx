/**
 * /profile
 * Страница профиля пользователя с секциями статистики решения задач и PvP матчей
 * Включает статистику попыток, график рейтинга и историю боёв
 */

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { fetchMatchStats } from "@/lib/api/matches";
import { fetchUserStats } from "@/lib/api/stats";
import type { MatchStats } from "@/lib/types/match";
import type { UserStatsResponse } from "@/lib/types/stats";
import { MatchHistoryList } from "@/components/profile/MatchHistoryList";
import { MatchStats as MatchStatsComponent } from "@/components/profile/MatchStats";
import { RatingChart } from "@/components/profile/RatingChart";
import { TopicAnalysis } from "@/components/profile/TopicAnalysis";
import { TaskStatsOverview } from "@/components/profile/TaskStatsOverview";
import { DifficultyBreakdown } from "@/components/profile/DifficultyBreakdown";
import { RecentActivityList } from "@/components/profile/RecentActivityList";
import { AchievementsSection } from "@/components/profile/AchievementsSection";

export default function ProfilePage() {
  // Auth check
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  // PvP stats
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Task stats
  const [taskStats, setTaskStats] = useState<UserStatsResponse | null>(null);
  const [taskStatsLoading, setTaskStatsLoading] = useState(true);
  const [taskStatsError, setTaskStatsError] = useState<string | null>(null);

  // Редирект на /login если не авторизован
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Загрузить PvP статистику при загрузке страницы
  useEffect(() => {
    if (!isAuthenticated) return;

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
  }, [isAuthenticated]);

  // Загрузить Task статистику при загрузке страницы
  useEffect(() => {
    if (!isAuthenticated) return;

    const loadTaskStats = async () => {
      try {
        setTaskStatsLoading(true);
        setTaskStatsError(null);
        const result = await fetchUserStats();
        setTaskStats(result);
      } catch (err) {
        setTaskStatsError(
          err instanceof Error ? err.message : "Ошибка при загрузке статистики"
        );
      } finally {
        setTaskStatsLoading(false);
      }
    };

    loadTaskStats();
  }, [isAuthenticated]);

  // Показать loading пока проверяется auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-cyan-400 font-mono tracking-wider">ИНИЦИАЛИЗАЦИЯ...</div>
      </div>
    );
  }

  // Если не авторизован, ничего не рендерить (редирект сработает)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] py-12 relative overflow-hidden">
      {/* CRT scanline overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015] z-0"
        style={{
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4">
        {/* Заголовок */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold text-white mb-2 font-mono tracking-tight">
            ПРОФИЛЬ
          </h1>
          <p className="text-cyan-400 font-mono text-sm tracking-wider uppercase">
            Статистика решения задач и история боёв
          </p>
        </div>

        {/* СЕКЦИЯ 1: Task Stats */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-white mb-8 font-mono tracking-tight">
            СТАТИСТИКА РЕШЕНИЯ
          </h2>

          {/* Task Stats Error */}
          {taskStatsError && (
            <div className="mb-6 p-4 border-2 border-[#ff3b30] bg-[#ff3b30]/5 relative"
              style={{
                clipPath: "polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)",
              }}>
              <div className="absolute top-4 left-4 w-3 h-3 bg-[#ff3b30]"
                style={{ boxShadow: "0 0 10px #ff3b30" }} />
              <p className="text-[#ff3b30] font-mono text-sm pl-8">
                ⚠ {taskStatsError}
              </p>
            </div>
          )}

          {/* Overview metrics */}
          <div className="mb-10">
            <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-4">
              Общая статистика
            </h3>
            <TaskStatsOverview stats={taskStats} loading={taskStatsLoading} />
          </div>

          {/* Difficulty breakdown */}
          <div className="mb-10">
            <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-4">
              По уровням сложности
            </h3>
            <DifficultyBreakdown
              byDifficulty={taskStats?.by_difficulty || []}
              loading={taskStatsLoading}
            />
          </div>

          {/* Recent activity */}
          <div className="mb-10">
            <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-4">
              Последние попытки
            </h3>
            <RecentActivityList
              recentActivity={taskStats?.recent_activity || []}
              loading={taskStatsLoading}
            />
          </div>

          {/* Achievements */}
          <div className="mb-10">
            <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-4">
              Достижения
            </h3>
            <AchievementsSection
              achievements={taskStats?.achievements || []}
              loading={taskStatsLoading}
            />
          </div>
        </section>

        {/* СЕКЦИЯ 2: PvP Stats */}
        <section>
          <h2 className="text-3xl font-bold text-white mb-8 font-mono tracking-tight">
            PVP СТАТИСТИКА
          </h2>

          {/* Match Stats Error */}
          {statsError && (
            <div className="mb-6 p-4 border-2 border-[#ff3b30] bg-[#ff3b30]/5 relative"
              style={{
                clipPath: "polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)",
              }}>
              <div className="absolute top-4 left-4 w-3 h-3 bg-[#ff3b30]"
                style={{ boxShadow: "0 0 10px #ff3b30" }} />
              <p className="text-[#ff3b30] font-mono text-sm pl-8">
                ⚠ {statsError}
              </p>
            </div>
          )}

          {/* Match Stats */}
          <div className="mb-8">
            {stats && (
              <MatchStatsComponent stats={stats} loading={statsLoading} />
            )}
          </div>

          {/* Rating Chart */}
          {stats && stats.rating_history.length > 0 && (
            <div className="mb-8">
              <RatingChart data={stats.rating_history} />
            </div>
          )}

          {/* Topic Analysis */}
          {stats &&
            (stats.strongest_topics.length > 0 ||
              stats.weakest_topics.length > 0) && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-white mb-4 font-mono">
                  АНАЛИЗ ПО ТЕМАМ
                </h3>
                <TopicAnalysis
                  strongestTopics={stats.strongest_topics}
                  weakestTopics={stats.weakest_topics}
                  loading={statsLoading}
                />
              </div>
            )}

          {/* Match History */}
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-white mb-4 font-mono">
              ИСТОРИЯ МАТЧЕЙ
            </h3>
            <Suspense fallback={
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="h-24 bg-gray-800/30 rounded-lg animate-pulse border border-gray-700/30"
                  />
                ))}
              </div>
            }>
              <MatchHistoryList />
            </Suspense>
          </div>
        </section>
      </div>
    </div>
  );
}
