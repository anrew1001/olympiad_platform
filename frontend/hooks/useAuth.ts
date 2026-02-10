/**
 * Хук для доступа к контексту аутентификации
 * Вызывает ошибку при использовании вне AuthProvider
 */

'use client';

import { useContext } from 'react';
import { AuthContext } from '@/context/AuthContext';

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
