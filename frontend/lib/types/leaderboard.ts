/**
 * Типы для таблицы лидеров
 */

export interface LeaderboardEntry {
  /** Место в рейтинге (1 = лучший) */
  position: number;
  /** ID пользователя */
  user_id: number;
  /** Имя пользователя */
  username: string;
  /** Рейтинг игрока */
  rating: number;
  /** Количество завершённых матчей */
  matches_played: number;
  /** Количество побед */
  wins: number;
  /** Процент побед (0-100) */
  win_rate: number;
  /** Это текущий авторизованный пользователь */
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  /** Список записей таблицы лидеров (отсортирован по рейтингу) */
  entries: LeaderboardEntry[];
  /** Общее количество пользователей в рейтинге */
  total_users: number;
  /** Запись текущего пользователя (если не входит в топ N) */
  current_user_entry: LeaderboardEntry | null;
}
