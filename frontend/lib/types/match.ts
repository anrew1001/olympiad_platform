/**
 * TypeScript types для PvP матчей истории
 * (зеркало Pydantic schemas из backend/app/schemas/match_history.py)
 */

export interface OpponentInfo {
  id: number;
  username: string;
  rating: number;
}

export interface MatchHistoryItem {
  match_id: number;
  status: string; // "finished" | "active" | "cancelled"
  result: "won" | "lost" | "draw" | null;
  opponent: OpponentInfo;
  my_score: number;
  opponent_score: number;
  my_rating_change: number | null;
  finished_at: string | null; // ISO datetime
  created_at: string; // ISO datetime
}

export interface PaginatedMatchHistory {
  items: MatchHistoryItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface TaskSolutionInfo {
  task_id: number;
  title: string;
  difficulty: number;
  order: number;
  solved_by_me: boolean;
  solved_by_opponent: boolean;
  my_answer_time: string | null;
  opponent_answer_time: string | null;
}

export interface MatchDetail {
  match_id: number;
  status: string;
  result: "won" | "lost" | "draw" | null;
  opponent: OpponentInfo;
  my_score: number;
  opponent_score: number;
  my_rating_change: number | null;
  tasks: TaskSolutionInfo[];
  finished_at: string | null;
  created_at: string;
}

export interface RatingHistoryPoint {
  match_id: number;
  rating: number;
  rating_change: number;
  created_at: string; // ISO datetime
}

export interface MatchStats {
  total_matches: number;
  won: number;
  lost: number;
  draw: number;
  win_rate: number; // 0-100
  rating_history: RatingHistoryPoint[];
}

export type MatchStatus = "finished" | "active" | "cancelled" | "waiting" | "error";
export type MatchResult = "won" | "lost" | "draw";

export interface MatchHistoryFilters {
  page?: number;
  per_page?: number;
  status?: string;
  result?: string;
  opponent_username?: string;
  sort_by?: string;
  order?: string;
}
