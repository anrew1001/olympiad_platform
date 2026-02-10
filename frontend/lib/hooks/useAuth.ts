'use client';

import { useContext } from 'react';
import { AuthContext } from '@/context/AuthContext';

/**
 * Hook для доступа к контексту аутентификации
 * Использует AuthContext из context/AuthContext.tsx
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
