/**
 * MatchHistoryList.tsx
 * Список матчей с пагинацией
 * Cyberpunk стиль с неоновыми акцентами
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
      <div
        className="relative p-4 border border-[#ff3b30] bg-[#1a0a0a]"
        style={{
          clipPath: 'polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)',
        }}
      >
        <div
          className="absolute top-2 left-2 w-2 h-2 bg-[#ff3b30]"
          style={{ boxShadow: '0 0 8px #ff3b30' }}
        />
        <p className="text-xs font-mono tracking-wider uppercase text-[#ff3b30] mb-1">
          ОШИБКА
        </p>
        <p className="text-sm font-mono text-[#ff3b30aa]">{error}</p>
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
              className="h-24 bg-[#1a1a1a] border border-[#333] animate-pulse"
              style={{
                clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
              }}
            />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 font-mono text-sm tracking-wider">МАТЧИ НЕ НАЙДЕНЫ</p>
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
            <div className="flex items-center justify-between border-t border-[#333] pt-4">
              <p className="text-xs font-mono text-gray-600">
                Всего: {data.total} матчей (страница {data.page} из {data.pages})
              </p>

              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(data.page - 1)}
                  disabled={data.page === 1}
                  className="px-3 py-2 border border-[#333] bg-[#1a1a1a] disabled:opacity-30 disabled:cursor-not-allowed hover:border-[#0066FF] hover:bg-[#0a0f1a] text-xs font-mono text-white transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                  }}
                >
                  ← ПРЕД
                </button>

                <div className="flex items-center gap-1">
                  {[...Array(Math.min(5, data.pages))].map((_, i) => {
                    const pageNum = data.page > 3 ? data.page - 2 + i : i + 1;
                    if (pageNum > data.pages) return null;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`w-10 h-10 text-xs font-mono font-bold transition-all ${
                          pageNum === data.page
                            ? "bg-[#0066FF] text-white border-[#0066FF]"
                            : "bg-[#1a1a1a] text-gray-400 border-[#333] hover:border-[#0066FF] hover:bg-[#0a0f1a]"
                        }`}
                        style={{
                          border: '1px solid',
                          clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                          boxShadow: pageNum === data.page ? '0 0 10px rgba(0, 102, 255, 0.5)' : 'none',
                        }}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => handlePageChange(data.page + 1)}
                  disabled={data.page === data.pages}
                  className="px-3 py-2 border border-[#333] bg-[#1a1a1a] disabled:opacity-30 disabled:cursor-not-allowed hover:border-[#0066FF] hover:bg-[#0a0f1a] text-xs font-mono text-white transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                  }}
                >
                  СЛЕД →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
