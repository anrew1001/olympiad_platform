import type { RegisterRequest, UserResponse, FastAPIError } from '@/types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export async function registerUser(data: RegisterRequest): Promise<UserResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData: FastAPIError = await response.json();

      // Обработка ошибок FastAPI
      if (typeof errorData.detail === 'string') {
        throw new APIError(errorData.detail, response.status);
      } else if (Array.isArray(errorData.detail)) {
        // Pydantic validation errors
        const messages = errorData.detail.map(err => err.msg).join(', ');
        throw new APIError(messages, response.status, errorData.detail);
      }

      throw new APIError('Произошла ошибка при регистрации', response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError('Не удалось подключиться к серверу', 0);
  }
}
