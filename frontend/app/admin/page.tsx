/**
 * /admin
 * Админ панель - статистика платформы
 * Требует роль admin
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getAdminStats, type AdminStats } from "@/lib/api/admin";
import { LoadingScreen } from "@/components/ui/LoadingScreen";

export default function AdminPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Редирект если не админ
  useEffect(() => {
    if (!authLoading && (!isAuthenticated || user?.role !== "admin")) {
      router.push("/");
    }
  }, [isAuthenticated, user, authLoading, router]);

  // Загрузить статистику
  useEffect(() => {
    if (!isAuthenticated || user?.role !== "admin") return;

    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getAdminStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [isAuthenticated, user]);

  if (authLoading || loading) {
    return <LoadingScreen text="ПРОВЕРКА ДОСТУПА..." />;
  }

  if (!isAuthenticated || user?.role !== "admin") {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#121212] py-12 relative overflow-hidden">
      {/* Scanline overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015] z-0"
        style={{
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4">
        {/* Заголовок */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold text-white mb-2 font-mono tracking-tight">
            АДМИН ПАНЕЛЬ
          </h1>
          <p className="text-[#0066FF] font-mono text-sm tracking-wider uppercase">
            Статистика платформы и управление
          </p>
        </div>

        {/* Ошибка */}
        {error && (
          <div
            className="relative mb-6 p-4 border border-[#ff3b30] bg-[#1a0a0a]"
            style={{
              clipPath: 'polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)',
            }}
          >
            <div
              className="absolute top-2 left-2 w-2 h-2 bg-[#ff3b30]"
              style={{ boxShadow: '0 0 8px #ff3b30' }}
            />
            <p className="text-xs font-mono tracking-wider uppercase text-[#ff3b30] mb-1">
              ОШИБКА
            </p>
            <p className="text-sm font-mono text-[#ff3b30aa]">{error}</p>
          </div>
        )}

        {/* Статистика */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {/* Total Users */}
            <StatCard
              label="ПОЛЬЗОВАТЕЛЕЙ"
              value={stats.total_users}
              sublabel="Всего зарегистрировано"
              color="#0066FF"
            />

            {/* Total Tasks */}
            <StatCard
              label="ЗАДАЧ"
              value={stats.total_tasks}
              sublabel="В базе данных"
              color="#00ff88"
            />

            {/* Total Attempts */}
            <StatCard
              label="ПОПЫТОК"
              value={stats.total_attempts}
              sublabel="Всего решений"
              color="#9966ff"
            />

            {/* Correct Attempts */}
            <StatCard
              label="ПРАВИЛЬНЫХ"
              value={stats.total_correct_attempts}
              sublabel="Успешных попыток"
              color="#00ff88"
            />

            {/* Platform Accuracy */}
            <StatCard
              label="ТОЧНОСТЬ"
              value={`${stats.platform_accuracy.toFixed(1)}%`}
              sublabel="Средняя точность платформы"
              color="#0066FF"
            />

            {/* Active Today */}
            <StatCard
              label="АКТИВНЫХ"
              value={stats.active_users_today}
              sublabel="Пользователей сегодня"
              color="#ffcc00"
            />
          </div>
        )}

        {/* Управление */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Управление задачами */}
          <Link href="/admin/tasks">
            <div
              className="relative p-8 border border-[#0066FF]/30 bg-[#0a0f1a] hover:border-[#0066FF]/60 transition-all cursor-pointer group"
              style={{
                clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
              }}
            >
              <div
                className="absolute top-0 right-0 w-3 h-3 bg-[#0066FF] group-hover:shadow-[0_0_15px_#0066FF] transition-all"
                style={{ boxShadow: '0 0 10px #0066FF' }}
              />

              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-mono font-bold text-white mb-3 uppercase">
                УПРАВЛЕНИЕ ЗАДАЧАМИ
              </h3>
              <p className="text-sm text-gray-400 font-mono leading-relaxed">
                Создание, редактирование и удаление задач. Полный CRUD функционал.
              </p>
            </div>
          </Link>

          {/* Placeholder для будущих фич */}
          <div
            className="relative p-8 border border-[#333] bg-[#1a1a1a] opacity-50"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
            }}
          >
            <div className="text-4xl mb-4">👥</div>
            <h3 className="text-xl font-mono font-bold text-gray-600 mb-3 uppercase">
              УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
            </h3>
            <p className="text-sm text-gray-600 font-mono leading-relaxed">
              Скоро будет доступно...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// StatCard Component
// ============================================================================

interface StatCardProps {
  label: string;
  value: number | string;
  sublabel: string;
  color: string;
}

function StatCard({ label, value, sublabel, color }: StatCardProps) {
  return (
    <div
      className="relative p-6 border bg-[#0a0f1a] transition-all hover:brightness-110"
      style={{
        borderColor: `${color}40`,
        clipPath: 'polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))',
      }}
    >
      <div
        className="absolute top-0 right-0 w-2.5 h-2.5"
        style={{
          backgroundColor: color,
          boxShadow: `0 0 10px ${color}`,
        }}
      />

      <p className="text-xs font-mono tracking-widest mb-2 uppercase" style={{ color }}>
        {label}
      </p>
      <p className="text-4xl font-bold font-mono mb-1" style={{ color }}>
        {value}
      </p>
      <p className="text-[10px] font-mono text-gray-600 uppercase tracking-wider">
        {sublabel}
      </p>
    </div>
  );
}
