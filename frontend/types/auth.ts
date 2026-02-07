// Схемы для регистрации (соответствуют backend UserCreate)
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Схема ответа от backend (соответствует UserResponse)
export interface UserResponse {
  id: number;
  username: string;
  email: string;
  rating: number;
  role: string;
  created_at: string;
}

// Ошибка от FastAPI (стандартный формат)
export interface FastAPIError {
  detail: string | Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}
