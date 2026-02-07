/**
 * MatchHistoryList.tsx
 * Список матчей с пагинацией
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchMatchHistory } from "@/lib/api/matches";
import type { PaginatedMatchHistory, MatchHistoryFilters } from "@/lib/types/match";
import { MatchCard } from "./MatchCard";
import { MatchFilters } from "./MatchFilters";

interface MatchHistoryListProps {
  initialFilters?: MatchHistoryFilters;
  onMatchClick?: (matchId: number) => void;
}

export function MatchHistoryList({ onMatchClick }: MatchHistoryListProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [data, setData] = useState<PaginatedMatchHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Получить фильтры из URL параметров
  const filters: MatchHistoryFilters = {
    page: parseInt(searchParams.get("page") || "1"),
    per_page: parseInt(searchParams.get("per_page") || "10"),
    status: searchParams.get("status") || undefined,
    result: searchParams.get("result") || undefined,
    opponent_username: searchParams.get("opponent") || undefined,
    sort_by: searchParams.get("sort_by") || "finished_at",
    order: searchParams.get("order") || "desc",
  };

  // Загрузить данные при изменении фильтров
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchMatchHistory(filters);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ошибка при загрузке матчей");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [filters.page, filters.per_page, filters.status, filters.result, filters.opponent_username, filters.sort_by, filters.order]);

  const handleMatchClick = (matchId: number) => {
    if (onMatchClick) {
      onMatchClick(matchId);
    } else {
      router.push(`/matches/${matchId}`);
    }
  };

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`?${params.toString()}`);
  };

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4">
        <p className="text-red-700 font-medium">Ошибка</p>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Фильтры */}
      <MatchFilters />

      {/* Список матчей */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-24 bg-gray-200 rounded-lg animate-pulse"
            />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">Матчи не найдены</p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {data.items.map((match) => (
              <MatchCard
                key={match.match_id}
                match={match}
                onClick={() => handleMatchClick(match.match_id)}
              />
            ))}
          </div>

          {/* Пагинация */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between border-t pt-4">
              <p className="text-sm text-gray-600">
                Всего: {data.total} матчей (страница {data.page} из {data.pages})
              </p>

              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(data.page - 1)}
                  disabled={data.page === 1}
                  className="px-3 py-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 text-sm font-medium transition-colors"
                >
                  ← Предыдущая
                </button>

                <div className="flex items-center gap-1">
                  {[...Array(Math.min(5, data.pages))].map((_, i) => {
                    const pageNum = data.page > 3 ? data.page - 2 + i : i + 1;
                    if (pageNum > data.pages) return null;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                          pageNum === data.page
                            ? "bg-blue-500 text-white"
                            : "border border-gray-300 hover:bg-gray-50"
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => handlePageChange(data.page + 1)}
                  disabled={data.page === data.pages}
                  className="px-3 py-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 text-sm font-medium transition-colors"
                >
                  Следующая →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
