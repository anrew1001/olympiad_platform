/**
 * /matches/[id]
 * Страница деталей конкретного матча
 * Показывает задачи, результаты решений, времена ответов
 */

"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchMatchDetail } from "@/lib/api/matches";
import type { MatchDetail } from "@/lib/types/match";
import { format } from "date-fns";
import { ru } from "date-fns/locale";

export default function MatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const matchId = parseInt(params.id as string);

  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMatch = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchMatchDetail(matchId);
        setMatch(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ошибка при загрузке матча");
      } finally {
        setLoading(false);
      }
    };

    loadMatch();
  }, [matchId]);

  const isWon = match?.result === "won";
  const isDraw = match?.result === "draw";

  const resultColor = isWon
    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700"
    : isDraw
      ? "bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600"
      : "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700";

  const resultTextColor = isWon
    ? "text-green-700 dark:text-green-400"
    : isDraw
      ? "text-gray-700 dark:text-gray-400"
      : "text-red-700 dark:text-red-400";

  const resultLabel = isWon ? "Победа" : isDraw ? "Ничья" : "Поражение";

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-black py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="space-y-6">
            <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-24 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-black py-12">
        <div className="max-w-4xl mx-auto px-4">
          <button
            onClick={() => router.back()}
            className="mb-6 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm font-medium transition-colors"
          >
            ← Вернуться
          </button>
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 p-6">
            <p className="text-red-700 dark:text-red-400 font-medium">Ошибка</p>
            <p className="text-red-600 dark:text-red-400 text-sm mt-2">
              {error || "Матч не найден"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Кнопка назад */}
        <button
          onClick={() => router.back()}
          className="mb-6 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm font-medium transition-colors"
        >
          ← Вернуться
        </button>

        {/* Заголовок и основная информация */}
        <div className={`rounded-lg border ${resultColor} p-6 mb-8`}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Матч с {match.opponent.username}
              </h1>
              <p className={`inline-block rounded px-3 py-1 text-sm font-semibold ${resultTextColor}`}>
                {resultLabel}
              </p>
              <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
                {format(new Date(match.created_at), "dd MMMM yyyy, HH:mm", {
                  locale: ru,
                })}
              </p>
            </div>

            <div className="text-right">
              <div className="text-4xl font-bold text-gray-900 dark:text-white">
                {match.my_score} : {match.opponent_score}
              </div>
              {match.my_rating_change !== null && (
                <p className={`text-2xl font-bold mt-2 ${
                  match.my_rating_change > 0
                    ? "text-green-600"
                    : match.my_rating_change < 0
                      ? "text-red-600"
                      : "text-gray-600"
                }`}>
                  {match.my_rating_change > 0 ? "+" : ""}
                  {match.my_rating_change} рейтинг
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Информация о сопернике */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Информация о сопернике
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">
                {match.opponent.username}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">ID: {match.opponent.id}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600 dark:text-gray-400">Рейтинг</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {match.opponent.rating}
              </p>
            </div>
          </div>
        </div>

        {/* Задачи и результаты */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Задачи ({match.tasks.length})
          </h2>

          {match.tasks.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">Нет данных о задачах</p>
          ) : (
            <div className="space-y-4">
              {match.tasks.map((task) => (
                <div
                  key={task.task_id}
                  className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {task.order}. {task.title}
                        </span>
                        <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">
                          Сложность: {task.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex-1 min-w-[150px]">
                      <p className="text-gray-600 dark:text-gray-400 mb-1">Вы</p>
                      <div className={`rounded px-3 py-2 ${
                        task.solved_by_me
                          ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
                      }`}>
                        <p className="font-medium">{task.solved_by_me ? "✓ Решено" : "✗ Не решено"}</p>
                        {task.my_answer_time && (
                          <p className="text-xs mt-1 opacity-80">
                            {format(new Date(task.my_answer_time), "HH:mm:ss")}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex-1 min-w-[150px]">
                      <p className="text-gray-600 dark:text-gray-400 mb-1">Соперник</p>
                      <div className={`rounded px-3 py-2 ${
                        task.solved_by_opponent
                          ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
                      }`}>
                        <p className="font-medium">
                          {task.solved_by_opponent ? "✓ Решено" : "✗ Не решено"}
                        </p>
                        {task.opponent_answer_time && (
                          <p className="text-xs mt-1 opacity-80">
                            {format(new Date(task.opponent_answer_time), "HH:mm:ss")}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
