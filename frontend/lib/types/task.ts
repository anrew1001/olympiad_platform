/**
 * Типы для работы с задачами (Tactical Mission System)
 */

export interface Task {
  id: number;
  subject: string;        // "informatics" | "mathematics"
  topic: string;          // "algorithms", "graphs", etc.
  difficulty: number;     // 1-5 (threat level)
  title: string;
  created_at: string;
}

export interface TaskDetail extends Task {
  text: string;
  hints: string[];
  updated_at: string;
}

export interface PaginatedTaskResponse {
  items: Task[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface TaskFilters {
  subject?: string;
  difficulty?: number;
  page?: number;
  per_page?: number;
}

/**
 * Запрос на проверку ответа к заданию
 */
export interface TaskCheckRequest {
  answer: string;
}

/**
 * Ответ от API при проверке ответа на задание
 */
export interface TaskCheckResponse {
  is_correct: boolean;
  message: string;
  correct_answer: string | null; // null если ответ правильный
}
