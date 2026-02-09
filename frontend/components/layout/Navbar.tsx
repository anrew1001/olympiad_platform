'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'motion/react';
import { Logo } from '../ui/Logo';
import { useAuth } from '@/lib/hooks/useAuth';

/**
 * Глобальный Navbar - fixed top
 * Показывает: Logo + навигация + auth state
 */
export function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  const navLinks = [
    { href: '/tasks', label: 'ЗАДАЧИ' },
    { href: '/pvp', label: 'PVP МАТЧ' },
    { href: '/leaderboard', label: 'ЛИДЕРБОРД' },
    { href: '/profile', label: 'ПРОФИЛЬ' },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/');

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 h-28 bg-[#121212]/95 backdrop-blur-sm border-b border-[#0066FF]/20"
      initial={{ y: -112 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Left: Logo + Brand */}
        <Link href="/" className="flex items-center gap-5 group">
          <motion.div
            whileHover={{ rotate: 180 }}
            transition={{ duration: 0.6 }}
          >
            <Logo size={80} className="text-[#0066FF] group-hover:text-[#0080FF] transition-colors" />
          </motion.div>
          <span className="font-mono text-3xl font-bold text-white tracking-wider">
            OLYMPIET
          </span>
        </Link>

        {/* Center: Navigation */}
        <div className="flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="relative group"
            >
              <span
                className={`
                  text-sm font-mono font-semibold tracking-wider transition-colors
                  ${isActive(link.href) ? 'text-[#0066FF]' : 'text-[#999] hover:text-white'}
                `}
              >
                {link.label}
              </span>

              {/* Active indicator */}
              {isActive(link.href) && (
                <motion.div
                  layoutId="navbar-active"
                  className="absolute -bottom-1 left-0 right-0 h-[2px] bg-[#0066FF]"
                  style={{
                    boxShadow: '0 0 8px rgba(0, 102, 255, 0.6)',
                  }}
                  transition={{ duration: 0.3 }}
                />
              )}
            </Link>
          ))}
        </div>

        {/* Right: Auth */}
        <div className="flex items-center gap-5">
          {isAuthenticated && user ? (
            <>
              {/* User badge (не кликабельный - профиль в навигации) */}
              <div className="flex items-center gap-3 px-4 py-2 rounded border border-[#0066FF]/30">
                <span className="text-sm font-mono text-white font-semibold">
                  {user.username}
                </span>
                <span className="text-sm font-mono text-[#0066FF] font-bold">
                  ★ {user.rating}
                </span>
              </div>

              {/* Logout */}
              <button
                onClick={logout}
                className="text-sm font-mono font-semibold text-[#999] hover:text-[#ff3b30] transition-colors"
              >
                ВЫХОД
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="px-6 py-3 text-sm font-mono font-bold text-white border border-[#0066FF] hover:bg-[#0066FF]/10 transition-all"
              style={{
                clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
              }}
            >
              ВОЙТИ
            </Link>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
