'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'motion/react';
import { Logo } from '@/components/ui/Logo';
import { getPublicStats, type PublicStats } from '@/lib/api/stats';
import { useAuth } from '@/hooks/useAuth';

/**
 * Landing Page - Главная страница платформы
 * Hero секция + Features + Live Stats + CTAs
 */
export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    // Загрузить публичную статистику
    getPublicStats()
      .then(setStats)
      .catch((err) => {
        // Fallback - показать placeholder
        setStats({
          total_tasks: 60,
          total_users: 0,
          total_matches: 0,
          active_matches: 0,
        });
      });
  }, []);

  return (
    <div className="min-h-screen bg-[#121212] relative">
      {/* Статичный grid background */}
      <div
        className="fixed inset-0 opacity-[0.02] z-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(90deg, #0066FF 1px, transparent 1px),
            linear-gradient(0deg, #0066FF 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Hero Section */}
      <section className="relative z-10 pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center space-y-12">
          {/* Logo + Brand */}
          <motion.div
            className="space-y-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex justify-center">
              <Logo size={160} animate className="text-[#0066FF]" />
            </div>

            <h1 className="text-5xl md:text-7xl font-mono font-bold text-white tracking-tight">
              ОЛИМПИАДНАЯ
              <br />
              ПЛАТФОРМА
            </h1>

            <p className="text-lg md:text-xl text-[#999] font-sora max-w-2xl mx-auto leading-relaxed">
              Соревнуйся в PvP матчах, решай задачи по информатике, математике и физике.
              Прокачай свой рейтинг и стань лучшим!
            </p>
          </motion.div>

          {/* CTAs */}
          <motion.div
            className="flex items-center justify-center gap-6 flex-wrap"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {isAuthenticated ? (
              <>
                <Link
                  href="/pvp"
                  className="px-8 py-4 text-sm font-mono font-bold text-white bg-[#0066FF] hover:bg-[#0080FF] transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
                    boxShadow: '0 0 20px rgba(0, 102, 255, 0.4)',
                  }}
                >
                  НАЙТИ МАТЧ
                </Link>
                <Link
                  href="/tasks"
                  className="px-8 py-4 text-sm font-mono font-bold text-white border border-[#0066FF] hover:bg-[#0066FF]/10 transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
                  }}
                >
                  ЗАДАЧИ
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/register"
                  className="px-8 py-4 text-sm font-mono font-bold text-white bg-[#0066FF] hover:bg-[#0080FF] transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
                    boxShadow: '0 0 20px rgba(0, 102, 255, 0.4)',
                  }}
                >
                  НАЧАТЬ
                </Link>
                <Link
                  href="/login"
                  className="px-8 py-4 text-sm font-mono font-bold text-white border border-[#0066FF] hover:bg-[#0066FF]/10 transition-all"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
                  }}
                >
                  ВОЙТИ
                </Link>
              </>
            )}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            {/* Feature 1: Tasks */}
            <motion.div
              className="p-8 bg-[#121212] border border-[#0066FF]/20 hover:border-[#0066FF]/40 transition-all"
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-xl font-mono font-bold text-white mb-3">
                ЗАДАЧИ
              </h3>
              <p className="text-sm text-[#999] font-sora leading-relaxed">
                60+ задач по информатике, математике и физике. Разные уровни сложности - от базовых до олимпиадных.
              </p>
            </motion.div>

            {/* Feature 2: PvP */}
            <motion.div
              className="p-8 bg-[#121212] border border-[#0066FF]/20 hover:border-[#0066FF]/40 transition-all"
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-4xl mb-4">⚔️</div>
              <h3 className="text-xl font-mono font-bold text-white mb-3">
                PVP МАТЧИ
              </h3>
              <p className="text-sm text-[#999] font-sora leading-relaxed">
                Real-time соревнования 1 на 1. Быстрый матчмейкинг по рейтингу. Решай задачи быстрее соперника!
              </p>
            </motion.div>

            {/* Feature 3: Rating */}
            <motion.div
              className="p-8 bg-[#121212] border border-[#0066FF]/20 hover:border-[#0066FF]/40 transition-all"
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-4xl mb-4">🏆</div>
              <h3 className="text-xl font-mono font-bold text-white mb-3">
                РЕЙТИНГ
              </h3>
              <p className="text-sm text-[#999] font-sora leading-relaxed">
                ELO система рейтинга. Побеждай в матчах, прокачивай скилл и поднимайся в лидерборде.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      {stats && (
        <section className="relative z-10 py-20 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl font-mono font-bold text-white mb-3">
                СТАТИСТИКА ПЛАТФОРМЫ
              </h2>
              <p className="text-sm text-[#999] font-sora">
                В реальном времени
              </p>
            </motion.div>

            <motion.div
              className="grid grid-cols-2 md:grid-cols-4 gap-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              {[
                { label: 'ЗАДАЧ', value: stats.total_tasks },
                { label: 'ПОЛЬЗОВАТЕЛЕЙ', value: stats.total_users },
                { label: 'МАТЧЕЙ', value: stats.total_matches },
                { label: 'АКТИВНО', value: stats.active_matches },
              ].map((stat, i) => (
                <motion.div
                  key={stat.label}
                  className="p-6 bg-[#121212] border border-[#0066FF]/20 text-center"
                  whileHover={{ borderColor: 'rgba(0, 102, 255, 0.4)' }}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className="text-4xl font-mono font-bold text-[#0066FF] mb-2">
                    {stat.value}
                  </div>
                  <div className="text-xs font-mono text-[#999] tracking-wider">
                    {stat.label}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="relative z-10 py-12 px-6 border-t border-[#0066FF]/10">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-xs font-mono text-[#666]">
            © 2026 OLYMPIET
          </p>
        </div>
      </footer>
    </div>
  );
}
