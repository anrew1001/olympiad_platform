// WebSocket типы для PvP матчей

// === Base Types ===

export interface PlayerInfo {
  id: number;
  username: string;
  rating: number;
}

export interface MatchTask {
  task_id: number;
  order: number;
  title: string;
  text: string;
  difficulty: number;
  hints: string[];
}

// === Connection State ===

export type ConnectionState =
  | { status: 'disconnected'; error?: string }
  | { status: 'connecting' }
  | { status: 'connected'; latency: number }
  | { status: 'reconnecting'; attempt: number; nextRetryIn: number };

// === Server → Client Events (Discriminated Union) ===

export type ServerEvent =
  | PlayerJoinedEvent
  | MatchStartEvent
  | AnswerResultEvent
  | OpponentScoredEvent
  | MatchEndEvent
  | OpponentDisconnectedEvent
  | OpponentReconnectedEvent
  | DisconnectWarningEvent
  | ReconnectionSuccessEvent
  | ErrorEvent
  | PingEvent
  | PongEvent;

export interface PlayerJoinedEvent {
  type: 'player_joined';
  player: PlayerInfo;
}

export interface MatchStartEvent {
  type: 'match_start';
  tasks: MatchTask[];
}

export interface AnswerResultEvent {
  type: 'answer_result';
  task_id: number;
  is_correct: boolean;
  your_score: number;
}

export interface OpponentScoredEvent {
  type: 'opponent_scored';
  task_id: number;
  opponent_score: number;
}

export interface MatchEndEvent {
  type: 'match_end';
  reason: 'completion' | 'forfeit' | 'technical_error';
  winner_id: number | null;
  player1_rating_change: number;
  player1_new_rating: number;
  player2_rating_change: number;
  player2_new_rating: number;
  final_scores: {
    player1_score: number;
    player2_score: number;
  };
}

export interface OpponentDisconnectedEvent {
  type: 'opponent_disconnected';
  timestamp: string;
  reconnecting: true;
  timeout_seconds: number;
}

export interface OpponentReconnectedEvent {
  type: 'opponent_reconnected';
  timestamp: string;
}

export interface DisconnectWarningEvent {
  type: 'disconnect_warning';
  seconds_remaining: number;
  user_id: number;
}

export interface ReconnectionSuccessEvent {
  type: 'reconnection_success';
  your_score: number;
  opponent_score: number;
  time_elapsed: number;
  your_solved_tasks: number[];
  opponent_solved_tasks: number[];
  total_tasks: number;
  reconnection_count: number;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
  code:
    | 'INVALID_TASK'
    | 'INVALID_MESSAGE'
    | 'NOT_PARTICIPANT'
    | 'MATCH_NOT_ACTIVE'
    | 'PROCESSING_ERROR'
    | 'RATE_LIMITED'
    | 'STATE_SYNC_ERROR';
}

export interface PingEvent {
  type: 'ping';
  timestamp: number;
}

export interface PongEvent {
  type: 'pong';
  timestamp: number;
}

// === Client → Server Messages ===

export type ClientMessage = SubmitAnswerMessage | PongMessage;

export interface SubmitAnswerMessage {
  type: 'submit_answer';
  task_id: number;
  answer: string;
}

export interface PongMessage {
  type: 'pong';
  timestamp: number;
}

// === Match State ===

export interface MatchState {
  yourScore: number;
  opponentScore: number;
  yourSolvedTasks: Set<number>;
  opponentSolvedTasks: Set<number>;
  tasks: MatchTask[];
  timeElapsed: number;
  isFinished: boolean;
  result?: {
    outcome: 'victory' | 'defeat' | 'draw';
    reason: 'completion' | 'forfeit' | 'technical_error';
    ratingChange: number;
    newRating: number;
  };
}

// === Opponent Status ===

export interface OpponentStatus {
  isConnected: boolean;
  disconnectWarning?: {
    secondsRemaining: number;
  };
}

// === WebSocket Hook Options ===

export interface WebSocketOptions {
  onMessage?: (message: ServerEvent) => void;
  onConnectionStateChange?: (state: ConnectionState) => void;
  reconnectMaxAttempts?: number;
}
