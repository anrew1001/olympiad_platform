/**
 * API клиент для таблицы лидеров
 */

import { LeaderboardResponse } from "@/lib/types/leaderboard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Получить headers с JWT токеном для авторизации
 */
function getAuthHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

/**
 * Получить таблицу лидеров
 * @param limit Количество записей для отображения (по умолчанию 50)
 * @throws Error если запрос не удался
 */
export async function fetchLeaderboard(
  limit: number = 50
): Promise<LeaderboardResponse> {
  const response = await fetch(
    `${API_BASE}/api/users/leaderboard?limit=${limit}`,
    { headers: getAuthHeaders() }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch leaderboard: ${response.statusText}`
    );
  }

  return response.json();
}
