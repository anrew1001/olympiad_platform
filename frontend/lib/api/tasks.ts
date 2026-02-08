/**
 * API клиент для тактической системы миссий
 */

import type { PaginatedTaskResponse, TaskFilters, TaskDetail } from "@/lib/types/task";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Получить заголовки с JWT токеном
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
 * Получить список миссий с фильтрацией
 *
 * GET /api/tasks
 */
export async function fetchTasks(
  filters: TaskFilters = {}
): Promise<PaginatedTaskResponse> {
  const params = new URLSearchParams();

  if (filters.subject) params.set("subject", filters.subject);
  if (filters.difficulty) params.set("difficulty", String(filters.difficulty));
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));

  const queryString = params.toString();
  const url = `${API_BASE}/api/tasks${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Ошибка при загрузке миссий: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Получить детальную информацию о миссии
 *
 * GET /api/tasks/{id}
 */
export async function fetchTaskDetail(taskId: number): Promise<TaskDetail> {
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Миссия не найдена");
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Ошибка при загрузке миссии: ${response.statusText}`
    );
  }

  return response.json();
}
