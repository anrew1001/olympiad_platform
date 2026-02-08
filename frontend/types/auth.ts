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

// Схемы для входа в систему
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}

// Состояние аутентификации
export interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Тип контекста аутентификации
export interface AuthContextType extends AuthState {
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}
