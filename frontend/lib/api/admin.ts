/**
 * API client для админ панели
 * Требует JWT токен с ролью admin
 */

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

// ============================================================================
// ТИПЫ
// ============================================================================

export interface AdminStats {
  total_users: number;
  total_tasks: number;
  total_attempts: number;
  total_correct_attempts: number;
  platform_accuracy: number;
  active_users_today: number;
}

export interface TaskCreate {
  subject: string;
  topic: string;
  difficulty: number;
  title: string;
  text: string;
  answer: string;
  hints?: string[] | null;
}

export interface TaskUpdate {
  subject?: string;
  topic?: string;
  difficulty?: number;
  title?: string;
  text?: string;
  answer?: string;
  hints?: string[] | null;
}

export interface TaskAdmin {
  id: number;
  subject: string;
  topic: string;
  difficulty: number;
  title: string;
  text: string;
  answer: string; // ВАЖНО: админ видит ответ
  hints: string[] | null;
  created_at: string;
  updated_at: string | null;
}

export interface AdminPaginatedTasks {
  items: TaskAdmin[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// ============================================================================
// API ФУНКЦИИ
// ============================================================================

/**
 * Получить статистику платформы (только для админов)
 */
export async function getAdminStats(): Promise<AdminStats> {
  const response = await fetch(`${API_BASE}/api/admin/stats`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("Доступ запрещён: требуется роль администратора");
    }
    throw new Error("Ошибка при загрузке статистики");
  }

  return response.json();
}

/**
 * Получить список задач (админ версия с ответами)
 */
export async function getAdminTasks(params?: {
  subject?: string;
  topic?: string;
  difficulty?: number;
  page?: number;
  per_page?: number;
}): Promise<AdminPaginatedTasks> {
  const query = new URLSearchParams();

  if (params?.subject) query.set("subject", params.subject);
  if (params?.topic) query.set("topic", params.topic);
  if (params?.difficulty) query.set("difficulty", String(params.difficulty));
  if (params?.page) query.set("page", String(params.page));
  if (params?.per_page) query.set("per_page", String(params.per_page));

  const url = `${API_BASE}/api/admin/tasks${query.toString() ? `?${query}` : ""}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("Доступ запрещён");
    }
    throw new Error("Ошибка при загрузке задач");
  }

  return response.json();
}

/**
 * Получить задачу по ID (админ версия с ответом)
 */
export async function getAdminTask(taskId: number): Promise<TaskAdmin> {
  const response = await fetch(`${API_BASE}/api/admin/tasks/${taskId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Задача не найдена");
    }
    if (response.status === 403) {
      throw new Error("Доступ запрещён");
    }
    throw new Error("Ошибка при загрузке задачи");
  }

  return response.json();
}

/**
 * Создать новую задачу
 */
export async function createTask(data: TaskCreate): Promise<TaskAdmin> {
  const response = await fetch(`${API_BASE}/api/admin/tasks`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка при создании задачи");
  }

  return response.json();
}

/**
 * Обновить задачу
 */
export async function updateTask(taskId: number, data: TaskUpdate): Promise<TaskAdmin> {
  const response = await fetch(`${API_BASE}/api/admin/tasks/${taskId}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка при обновлении задачи");
  }

  return response.json();
}

/**
 * Удалить задачу
 */
export async function deleteTask(taskId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/admin/tasks/${taskId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка при удалении задачи");
  }
}
