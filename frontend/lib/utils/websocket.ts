// WebSocket утилиты

/**
 * Вычисляет exponential backoff с jitter
 * Возвращает количество миллисекунд до следующей попытки
 * 1s → 2s → 4s → 8s → ... → max 30s
 * + jitter ±20% для предотвращения thundering herd
 */
export function calculateBackoff(attempt: number): number {
  const baseDelay = 1000; // 1 second
  const maxDelay = 30000; // 30 seconds
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  // Jitter: ±20%
  const jitter = delay * (0.8 + Math.random() * 0.4);
  return Math.floor(jitter);
}

/**
 * Rate limiter для клиентской стороны (1 action/sec)
 * Используется для защиты от spam ответов
 */
export class RateLimitedQueue {
  private lastSendTime = 0;
  private readonly minInterval: number;

  constructor(intervalMs: number = 1000) {
    this.minInterval = intervalMs;
  }

  /**
   * Проверяет можно ли отправить сообщение
   * Если да - обновляет lastSendTime и возвращает true
   */
  canSend(): boolean {
    const now = Date.now();
    const timeSinceLast = now - this.lastSendTime;
    if (timeSinceLast >= this.minInterval) {
      this.lastSendTime = now;
      return true;
    }
    return false;
  }

  /**
   * Возвращает количество миллисекунд до следующего разрешённого отправления
   */
  getWaitTime(): number {
    const now = Date.now();
    const timeSinceLast = now - this.lastSendTime;
    return Math.max(0, this.minInterval - timeSinceLast);
  }

  /**
   * Сбрасывает лимит (для тестирования)
   */
  reset(): void {
    this.lastSendTime = 0;
  }
}

/**
 * Формирует WebSocket URL для подключения к матчу
 */
export function getWebSocketUrl(matchId: number, token: string): string {
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = process.env.NEXT_PUBLIC_WS_HOST || 'localhost:8000';
  return `${protocol}//${host}/api/pvp/ws/${matchId}?token=${token}`;
}

/**
 * Type guard для проверки если event имеет конкретный тип
 */
export function isServerEvent<T extends { type: string }>(event: any, type: T['type']): event is T {
  return event && typeof event === 'object' && event.type === type;
}
