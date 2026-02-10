/**
 * Глобальный контекст аутентификации
 * Управляет состоянием пользователя и JWT токеном на уровне приложения
 */

'use client';

import {
  createContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { getCurrentUser } from '@/lib/api/auth';
import type { AuthContextType, UserResponse } from '@/types/auth';

// Создать контекст с undefined по умолчанию (вызовет ошибку при использовании вне провайдера)
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Начать с загрузки

  /**
   * Инициализировать состояние аутентификации при монтировании
   * Проверить localStorage на наличие токена → получить данные пользователя
   */
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Токен невалиден/истёк - getCurrentUser уже очистил localStorage
        console.error('Auth init failed:', error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  /**
   * Вход: Сохранить токен → получить данные пользователя → обновить состояние
   */
  const login = async (token: string): Promise<void> => {
    localStorage.setItem('access_token', token);

    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      // Не удалось получить пользователя после входа - очистить токен
      localStorage.removeItem('access_token');
      throw error;
    }
  };

  /**
   * Выход: Очистить токен + состояние пользователя
   */
  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  /**
   * Обновить данные пользователя (например, после обновления профиля)
   */
  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      // Токен истёк во время сеанса - выйти
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
