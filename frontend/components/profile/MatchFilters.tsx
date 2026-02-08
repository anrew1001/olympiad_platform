/**
 * MatchFilters.tsx
 * Компонент для фильтрации и сортировки истории матчей
 * Cyberpunk стиль с неоновыми акцентами
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

  const selectClassName = "bg-[#1a1a1a] border border-[#333] px-3 py-2 text-white text-xs font-mono transition-all hover:border-[#0066FF] focus:outline-none focus:border-[#0066FF]";
  const inputClassName = "bg-[#1a1a1a] border border-[#333] px-3 py-2 text-white text-xs font-mono transition-all hover:border-[#0066FF] focus:outline-none focus:border-[#0066FF] placeholder:text-gray-600";
  const labelClassName = "text-[10px] font-mono tracking-widest uppercase text-[#0066FF]";

  return (
    <div
      className="relative p-4 border border-[#0066FF]/30 bg-[#0a0f1a]"
      style={{
        clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
      }}
    >
      {/* Corner bracket */}
      <div
        className="absolute top-0 right-0 w-3 h-3 bg-[#0066FF]"
        style={{ boxShadow: '0 0 10px #0066FF' }}
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {/* Статус */}
        <div className="flex flex-col gap-2">
          <label htmlFor="status" className={labelClassName}>
            Статус
          </label>
          <select
            id="status"
            value={searchParams.get("status") || "all"}
            onChange={(e) => updateFilter("status", e.target.value)}
            className={selectClassName}
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          >
            <option value="all">Все статусы</option>
            <option value="finished">Завершённые</option>
            <option value="active">Активные</option>
          </select>
        </div>

        {/* Результат */}
        <div className="flex flex-col gap-2">
          <label htmlFor="result" className={labelClassName}>
            Результат
          </label>
          <select
            id="result"
            value={searchParams.get("result") || "all"}
            onChange={(e) => updateFilter("result", e.target.value)}
            className={selectClassName}
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          >
            <option value="all">Все результаты</option>
            <option value="won">Победы</option>
            <option value="lost">Поражения</option>
            <option value="draw">Ничьи</option>
          </select>
        </div>

        {/* Поиск по сопернику */}
        <div className="flex flex-col gap-2">
          <label htmlFor="opponent" className={labelClassName}>
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
            className={inputClassName}
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          />
        </div>

        {/* Сортировка */}
        <div className="flex flex-col gap-2">
          <label htmlFor="sort" className={labelClassName}>
            Сортировка
          </label>
          <select
            id="sort"
            value={searchParams.get("sort_by") || "finished_at"}
            onChange={(e) => updateFilter("sort_by", e.target.value)}
            className={selectClassName}
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          >
            <option value="finished_at">По дате (новые)</option>
            <option value="rating_change">По рейтингу</option>
          </select>
        </div>
      </div>
    </div>
  );
}
