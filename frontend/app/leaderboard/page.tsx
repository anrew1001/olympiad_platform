"use client";

import { useState, useEffect } from "react";
import { fetchLeaderboard } from "@/lib/api/leaderboard";
import { LeaderboardResponse } from "@/lib/types/leaderboard";
import LeaderboardTable from "@/components/leaderboard/LeaderboardTable";

export default function LeaderboardPage() {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadLeaderboard() {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchLeaderboard(limit);
        setData(result);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Неизвестная ошибка";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    }

    loadLeaderboard();
  }, [limit]);

  function handleShowMore() {
    setLimit((prev) => prev + 50);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#121212]">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-6 text-white">Таблица лидеров</h1>
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#121212]">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-6 text-white">Таблица лидеров</h1>
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#121212]">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Таблица лидеров</h1>
        <p className="text-gray-400 mb-6">
          Всего в рейтинге: <span className="font-semibold">{data.total_users}</span> игроков
        </p>

        <LeaderboardTable
          entries={data.entries}
          currentUserEntry={data.current_user_entry}
        />

        {/* "Показать ещё" кнопка */}
        {data.entries.length < data.total_users && (
          <div className="mt-6 text-center">
            <button
              onClick={handleShowMore}
              className={`
                px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold
                rounded-lg transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-black
              `}
            >
              Показать ещё +50
            </button>
          </div>
        )}

        {/* Информационное сообщение если всё загружено */}
        {data.entries.length >= data.total_users && data.total_users > 0 && (
          <div className="mt-6 text-center">
            <p className="text-gray-500 text-sm">Вы просмотрели всех игроков рейтинга</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Компонент скелетона для загрузки
 */
function LoadingSkeleton() {
  return (
    <div className="w-full bg-black rounded-lg overflow-hidden border border-gray-800 animate-pulse">
      {/* Заголовок */}
      <div className="grid grid-cols-12 gap-4 bg-gray-900 p-4 border-b border-gray-800">
        <div className="col-span-1 h-4 bg-gray-700 rounded"></div>
        <div className="col-span-4 h-4 bg-gray-700 rounded"></div>
        <div className="col-span-2 h-4 bg-gray-700 rounded"></div>
        <div className="col-span-2 h-4 bg-gray-700 rounded"></div>
        <div className="col-span-3 h-4 bg-gray-700 rounded"></div>
      </div>

      {/* Строки */}
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="grid grid-cols-12 gap-4 p-4 border-b border-gray-800"
        >
          <div className="col-span-1 h-6 bg-gray-800 rounded"></div>
          <div className="col-span-4 h-6 bg-gray-800 rounded"></div>
          <div className="col-span-2 h-6 bg-gray-800 rounded"></div>
          <div className="col-span-2 h-6 bg-gray-800 rounded"></div>
          <div className="col-span-3 h-6 bg-gray-800 rounded"></div>
        </div>
      ))}
    </div>
  );
}

/**
 * Компонент сообщения об ошибке
 */
function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
      <p className="text-red-400 font-semibold">Ошибка загрузки рейтинга</p>
      <p className="text-red-300 text-sm mt-1">{message}</p>
    </div>
  );
}
