/**
 * API client functions для работы с историей PvP матчей
 * Использует native fetch API (без React Query для минимализма)
 */

import type {
  PaginatedMatchHistory,
  MatchDetail,
  MatchStats,
  MatchHistoryFilters,
} from "@/lib/types/match";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Получить Authorization header с JWT токеном
 */
function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

/**
 * Получить историю PvP матчей с поддержкой фильтров, сортировки и пагинации
 *
 * @param params - объект с параметрами запроса
 * @returns список матчей с информацией о пагинации
 */
export async function fetchMatchHistory(
  params: MatchHistoryFilters
): Promise<PaginatedMatchHistory> {
  const query = new URLSearchParams(
    Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => [k, String(v)])
  ).toString();

  const url = `${API_BASE}/api/users/me/matches${query ? `?${query}` : ""}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка при загрузке истории матчей");
  }

  return response.json();
}

/**
 * Получить детали конкретного матча (задачи, результаты решений, времена ответов)
 *
 * @param matchId - ID матча
 * @returns полная информация о матче
 */
export async function fetchMatchDetail(matchId: number): Promise<MatchDetail> {
  const response = await fetch(
    `${API_BASE}/api/users/me/matches/${matchId}`,
    {
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 404) {
      throw new Error("Матч не найден");
    }
    if (response.status === 403) {
      throw new Error("У вас нет доступа к этому матчу");
    }
    throw new Error(error.detail || "Ошибка при загрузке деталей матча");
  }

  return response.json();
}

/**
 * Получить статистику по матчам и историю рейтинга
 *
 * @returns статистика (W/L/D count, win rate, история рейтинга за последние 50 матчей)
 */
export async function fetchMatchStats(): Promise<MatchStats> {
  const response = await fetch(
    `${API_BASE}/api/users/me/matches/stats`,
    {
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка при загрузке статистики матчей");
  }

  return response.json();
}

/**
 * Helper функция для форматирования URL параметров
 */
export function buildQueryParams(filters: MatchHistoryFilters): string {
  const params = new URLSearchParams();

  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.status && filters.status !== "all") params.set("status", filters.status);
  if (filters.result && filters.result !== "all") params.set("result", filters.result);
  if (filters.opponent_username) params.set("opponent_username", filters.opponent_username);
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.order) params.set("order", filters.order);

  return params.toString();
}
