/**
 * MatchFilters.tsx
 * Компонент для фильтрации и сортировки истории матчей
 */

"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export function MatchFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [opponentSearch, setOpponentSearch] = useState(
    searchParams.get("opponent") || ""
  );

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());

    if (value && value !== "all") {
      params.set(key, value);
    } else {
      params.delete(key);
    }

    // Reset to first page when changing filters
    params.set("page", "1");

    router.push(`?${params.toString()}`);
  };

  const handleOpponentSearch = (e: React.FocusEvent<HTMLInputElement>) => {
    if (e.target.value) {
      updateFilter("opponent", e.target.value);
    } else {
      updateFilter("opponent", "");
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {/* Статус */}
        <div className="flex flex-col gap-2">
          <label htmlFor="status" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Статус
          </label>
          <select
            id="status"
            value={searchParams.get("status") || "all"}
            onChange={(e) => updateFilter("status", e.target.value)}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white text-sm transition-colors hover:border-gray-400"
          >
            <option value="all">Все статусы</option>
            <option value="finished">Завершённые</option>
            <option value="active">Активные</option>
          </select>
        </div>

        {/* Результат */}
        <div className="flex flex-col gap-2">
          <label htmlFor="result" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Результат
          </label>
          <select
            id="result"
            value={searchParams.get("result") || "all"}
            onChange={(e) => updateFilter("result", e.target.value)}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white text-sm transition-colors hover:border-gray-400"
          >
            <option value="all">Все результаты</option>
            <option value="won">Победы</option>
            <option value="lost">Поражения</option>
            <option value="draw">Ничьи</option>
          </select>
        </div>

        {/* Поиск по сопернику */}
        <div className="flex flex-col gap-2">
          <label htmlFor="opponent" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Поиск соперника
          </label>
          <input
            id="opponent"
            type="text"
            placeholder="Имя соперника..."
            value={opponentSearch}
            onChange={(e) => setOpponentSearch(e.target.value)}
            onBlur={handleOpponentSearch}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleOpponentSearch(e as any);
              }
            }}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Сортировка */}
        <div className="flex flex-col gap-2">
          <label htmlFor="sort" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Сортировка
          </label>
          <select
            id="sort"
            value={searchParams.get("sort_by") || "finished_at"}
            onChange={(e) => updateFilter("sort_by", e.target.value)}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 dark:bg-gray-700 dark:text-white text-sm transition-colors hover:border-gray-400"
          >
            <option value="finished_at">По дате (новые)</option>
            <option value="rating_change">По рейтингу</option>
          </select>
        </div>
      </div>
    </div>
  );
}
