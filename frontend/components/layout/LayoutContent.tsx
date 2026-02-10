'use client';

import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';

interface LayoutContentProps {
  children: React.ReactNode;
}

/**
 * Client-side wrapper для layout
 * Скрывает Navbar на full-screen страницах (login, register, match)
 */
export function LayoutContent({ children }: LayoutContentProps) {
  const pathname = usePathname();

  // Страницы где navbar не нужен (full-screen experience)
  const hideNavbar =
    pathname === '/login' ||
    pathname === '/register' ||
    pathname.startsWith('/pvp/match/');

  return (
    <>
      {!hideNavbar && <Navbar />}
      <div className={hideNavbar ? '' : 'pt-28'}>
        {children}
      </div>
    </>
  );
}
