/**
 * API client для аутентификации
 * Обработка входа, получения текущего пользователя и управления токенами
 */

import type { LoginRequest, LoginResponse, UserResponse, FastAPIError } from '@/types/auth';
import { APIError } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Аутентифицировать пользователя и получить JWT токен
 *
 * POST /api/auth/login
 * Body: { email, password }
 * Returns: { access_token, token_type }
 * Throws: APIError при 401 (неверные данные) или сетевой ошибке
 */
export async function loginUser(credentials: LoginRequest): Promise<LoginResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData: FastAPIError = await response.json();

      // Backend возвращает "Неверный email или пароль" для 401
      if (response.status === 401) {
        throw new APIError(
          errorData.detail || 'Неверный email или пароль',
          401
        );
      }

      throw new APIError(
        errorData.detail || 'Ошибка при входе',
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError('Не удалось подключиться к серверу', 0);
  }
}

/**
 * Получить данные текущего пользователя по JWT токену
 *
 * GET /api/auth/me
 * Headers: { Authorization: Bearer <token> }
 * Returns: UserResponse
 * Throws: APIError при 401 (истекший/невалидный токен)
 */
export async function getCurrentUser(): Promise<UserResponse> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  if (!token) {
    throw new APIError('Токен отсутствует', 401);
  }

  try {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Токен истёк или невалиден - очистить localStorage
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        throw new APIError('Сессия истекла', 401);
      }

      const errorData: FastAPIError = await response.json();
      throw new APIError(
        errorData.detail || 'Ошибка при получении данных пользователя',
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError('Не удалось подключиться к серверу', 0);
  }
}
