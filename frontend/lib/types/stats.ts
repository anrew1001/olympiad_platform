/**
 * TypeScript types для статистики решения задач
 * Зеркало Pydantic schemas из backend/app/schemas/stats.py
 */

export interface DifficultyStats {
  difficulty: number; // 1-5
  solved: number;
  total_attempts: number;
}

export interface RecentActivityItem {
  task_id: number;
  task_title: string;
  task_difficulty: number; // 1-5
  is_correct: boolean;
  created_at: string; // ISO datetime
}

export interface AchievementItem {
  type: string; // "first_solve", "solved_10", etc.
  title: string;
  description: string;
  unlocked_at: string; // ISO datetime
}

export interface UserStatsResponse {
  // Общая статистика
  total_attempts: number;
  correct_attempts: number;
  accuracy: number; // 0-100
  unique_solved: number;

  // По сложности
  by_difficulty: DifficultyStats[];

  // Недавняя активность (макс 10)
  recent_activity: RecentActivityItem[];

  // Достижения
  achievements: AchievementItem[];
}
