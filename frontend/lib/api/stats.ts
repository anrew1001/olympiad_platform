/**
 * API client для статистики решения задач
 * Получение данных о решении задач, попытках и достижениях
 */

import type { UserStatsResponse } from "@/lib/types/stats";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Получить хедеры авторизации с JWT токеном
 */
function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined"
    ? localStorage.getItem("access_token")
    : null;

  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

/**
 * Получить статистику решения задач текущего пользователя
 *
 * @throws Error если пользователь не авторизован (401) или произошла ошибка
 * @returns UserStatsResponse с полной статистикой
 */
export async function fetchUserStats(): Promise<UserStatsResponse> {
  const response = await fetch(
    `${API_BASE}/api/users/me/stats`,
    {
      headers: getAuthHeaders(),
      credentials: "include",
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      // Очистить некорректный токен и перенаправить на логин
      localStorage.removeItem("access_token");
      throw new Error("Требуется авторизация");
    }

    if (response.status === 403) {
      throw new Error("Доступ к статистике запрещён");
    }

    const errorData = await response.json().catch(() => ({}));
    const message = (errorData as any)?.detail || "Ошибка при загрузке статистики";
    throw new Error(message);
  }

  const data = await response.json();
  return data as UserStatsResponse;
}
