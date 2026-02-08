// PvP API клиент
import { MatchTask, PlayerInfo } from '@/lib/types/websocket';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// === Response Types ===

export interface FindMatchResponse {
  match_id: number;
  status: 'waiting' | 'active';
  opponent?: {
    id: number;
    username: string;
    rating: number;
  };
}

export interface CancelSearchResponse {
  cancelled: boolean;
}

export interface MatchDetailResponse {
  match_id: number;
  status: string;
  player1: PlayerInfo;
  player2: PlayerInfo | null;
  player1_score: number;
  player2_score: number;
  match_tasks: MatchTask[];
  created_at: string;
}

// === API Functions ===

/**
 * POST /api/pvp/find
 * Начинает поиск соперника или присоединяется к ожидающему матчу
 */
export async function findMatch(): Promise<FindMatchResponse> {
  const res = await fetch(`${API_URL}/api/pvp/find`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    let errorMessage = 'Unknown error';

    // Читаем текст один раз, потом пытаемся распарсить как JSON
    const errorText = await res.text();
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.detail || errorData.message || errorText;
    } catch {
      errorMessage = errorText || `HTTP ${res.status} error`;
    }

    console.error('Find match error response:', {
      status: res.status,
      message: errorMessage,
    });

    if (res.status === 401) throw new Error('UNAUTHORIZED');
    if (res.status === 403) throw new Error('FORBIDDEN');
    if (res.status === 409) throw new Error(`CONFLICT: ${errorMessage}`);
    throw new Error(`Failed to find match: ${res.status} ${errorMessage}`);
  }

  return res.json();
}

/**
 * DELETE /api/pvp/find
 * Отменяет поиск (удаляет waiting матч)
 */
export async function cancelSearch(): Promise<CancelSearchResponse> {
  const res = await fetch(`${API_URL}/api/pvp/find`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    if (res.status === 401) throw new Error('UNAUTHORIZED');

    const errorText = await res.text();
    let errorMessage = 'Failed to cancel search';
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.detail || errorData.message || errorText;
    } catch {
      errorMessage = errorText || 'Failed to cancel search';
    }

    throw new Error(errorMessage);
  }

  return res.json();
}

/**
 * GET /api/pvp/match/{matchId}
 * Получает полную информацию о матче (задачи, игроки, счёт)
 * 403 если пользователь не участник матча
 */
export async function getMatch(matchId: number): Promise<MatchDetailResponse> {
  const res = await fetch(`${API_URL}/api/pvp/match/${matchId}`, {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    if (res.status === 401) throw new Error('UNAUTHORIZED');
    if (res.status === 403) throw new Error('NOT_PARTICIPANT');
    if (res.status === 404) throw new Error('MATCH_NOT_FOUND');

    const errorText = await res.text();
    let errorMessage = 'Failed to get match';
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.detail || errorData.message || errorText;
    } catch {
      errorMessage = errorText || 'Failed to get match';
    }

    throw new Error(errorMessage);
  }

  return res.json();
}
