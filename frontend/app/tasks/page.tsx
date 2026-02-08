/**
 * Tactical Mission Briefing System
 * Главная страница каталога миссий с HUD-интерфейсом
 */

"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { fetchTasks } from "@/lib/api/tasks";
import type { PaginatedTaskResponse, TaskFilters } from "@/lib/types/task";
import { TaskFilters as TaskFiltersComponent } from "@/components/tasks/TaskFilters";
import { TaskGrid } from "@/components/tasks/TaskGrid";
import { TaskPagination } from "@/components/tasks/TaskPagination";

/**
 * Детерминированные позиции частиц для избежания hydration mismatch
 */
const PARTICLE_POSITIONS = [
  { left: "5%", x1: "8%", x2: "12%", height: "95px", duration: 14, delay: 0 },
  { left: "12%", x1: "10%", x2: "15%", height: "110px", duration: 16, delay: 0.5 },
  { left: "18%", x1: "20%", x2: "18%", height: "85px", duration: 13, delay: 1 },
  { left: "25%", x1: "27%", x2: "23%", height: "105px", duration: 15, delay: 1.5 },
  { left: "32%", x1: "35%", x2: "30%", height: "78px", duration: 12, delay: 2 },
  { left: "40%", x1: "42%", x2: "38%", height: "98px", duration: 17, delay: 0.3 },
  { left: "48%", x1: "50%", x2: "46%", height: "88px", duration: 14, delay: 0.8 },
  { left: "55%", x1: "58%", x2: "52%", height: "115px", duration: 18, delay: 1.3 },
  { left: "63%", x1: "65%", x2: "61%", height: "72px", duration: 13, delay: 1.8 },
  { left: "70%", x1: "72%", x2: "68%", height: "102px", duration: 15, delay: 2.3 },
  { left: "78%", x1: "80%", x2: "76%", height: "91px", duration: 16, delay: 0.2 },
  { left: "85%", x1: "87%", x2: "83%", height: "107px", duration: 14, delay: 0.7 },
  { left: "92%", x1: "94%", x2: "90%", height: "80px", duration: 15, delay: 1.2 },
  { left: "8%", x1: "10%", x2: "6%", height: "96px", duration: 17, delay: 3 },
  { left: "60%", x1: "62%", x2: "58%", height: "104px", duration: 16, delay: 2.5 },
];

export default function TacticalMissionBriefing() {
  const searchParams = useSearchParams();

  const [data, setData] = useState<PaginatedTaskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Извлечь параметры миссии из URL
  const filters: TaskFilters = {
    subject: searchParams.get("subject") || undefined,
    difficulty: searchParams.get("difficulty")
      ? parseInt(searchParams.get("difficulty")!)
      : undefined,
    page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : 1,
    per_page: 20,
  };

  // Загрузить миссии при изменении параметров
  useEffect(() => {
    const loadMissions = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchTasks(filters);
        setData(result);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Неизвестная системная ошибка";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadMissions();
  }, [filters.subject, filters.difficulty, filters.page]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Tactical grid background */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none">
        <motion.div
          animate={{
            backgroundPosition: ["0% 0%", "100% 100%"],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "linear",
          }}
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #0066FF 1px, transparent 1px),
              linear-gradient(0deg, #0066FF 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* Horizontal scan line */}
      <motion.div
        animate={{
          y: ["0%", "100%"],
          opacity: [0, 0.2, 0],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "linear",
        }}
        className="fixed left-0 right-0 h-[3px] pointer-events-none"
        style={{
          background: "linear-gradient(90deg, transparent, #0066FF, transparent)",
          boxShadow: "0 0 20px rgba(0, 102, 255, 0.8)",
        }}
      />

      {/* Data stream particles - Deterministic positions to avoid hydration mismatch */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {PARTICLE_POSITIONS.map((pos, i) => (
          <motion.div
            key={`particle-${i}`}
            animate={{
              y: ["-10%", "110%"],
              x: [pos.x1, pos.x2],
              opacity: [0, 0.3, 0],
            }}
            transition={{
              duration: pos.duration,
              repeat: Infinity,
              delay: pos.delay,
              ease: "linear",
            }}
            className="absolute w-px"
            style={{
              left: pos.left,
              background: "linear-gradient(180deg, transparent, #06b6d4, transparent)",
              height: pos.height,
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <div className="relative z-10 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Tactical header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <div className="flex items-start gap-6">
            {/* Status indicator */}
            <div className="flex flex-col gap-2 pt-2">
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-3 h-3 bg-[#00ff88]"
                style={{ boxShadow: "0 0 10px #00ff88" }}
              />
              <div className="w-3 h-px bg-gray-700" />
              <div className="w-3 h-px bg-gray-700" />
              <div className="w-3 h-px bg-gray-700" />
            </div>

            <div className="flex-1 space-y-3">
              {/* System label */}
              <div className="flex items-center gap-3">
                <div className="h-px w-12 bg-[#0066FF]" style={{ boxShadow: "0 0 6px #0066FF" }} />
                <span className="text-xs font-mono tracking-[0.3em] text-cyan-500 uppercase">
                  СИСТЕМА КАТАЛОГА
                </span>
              </div>

              {/* Main title */}
              <h1
                className="text-5xl md:text-6xl font-bold text-white tracking-tight"
                style={{
                  fontFamily: "Sora, sans-serif",
                  textShadow: "0 0 30px rgba(0, 102, 255, 0.3)",
                }}
              >
                КАТАЛОГ ЗАДАНИЙ
              </h1>

              {/* Subtitle */}
              <p className="text-sm font-mono text-gray-500 tracking-wide max-w-2xl">
                ВЫБЕРИ ЗАДАНИЕ И ПРОКАЧАЙ СВОИ НАВЫКИ // УРОВЕНЬ СЛОЖНОСТИ ОТМЕЧЕН
              </p>
            </div>

            {/* Mission count display */}
            {data && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 }}
                className="hidden lg:block relative"
              >
                <div
                  className="px-6 py-4 border border-[#0066FF]/30 bg-black/60 backdrop-blur-sm"
                  style={{
                    clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%)",
                  }}
                >
                  <div className="text-center space-y-1">
                    <div className="text-xs font-mono text-gray-500 tracking-wider">
                      ВСЕГО ЗАДАНИЙ
                    </div>
                    <div
                      className="text-3xl font-bold font-mono text-[#0066FF]"
                      style={{ textShadow: "0 0 20px #0066FF" }}
                    >
                      {data.total}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Mission parameters (filters) */}
        <div className="mb-8">
          <TaskFiltersComponent />
        </div>

        {/* Error alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 overflow-hidden"
            >
              <div
                className="relative p-6 border-2 border-[#ff3b30] bg-[#ff3b30]/5 backdrop-blur-sm"
                style={{
                  clipPath: "polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)",
                }}
              >
                {/* Alert indicator */}
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="absolute top-4 left-4 w-3 h-3 bg-[#ff3b30]"
                  style={{ boxShadow: "0 0 10px #ff3b30" }}
                />

                <div className="pl-8">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-mono tracking-[0.2em] text-[#ff3b30] uppercase">
                      ⚠ СИСТЕМНАЯ ОШИБКА
                    </span>
                  </div>
                  <p className="text-sm font-mono text-red-300">{error}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mission grid */}
        <div className="mb-12">
          <TaskGrid tasks={data?.items || []} loading={loading} />
        </div>

        {/* Grid navigation (pagination) */}
        {data && data.pages > 1 && (
          <TaskPagination
            currentPage={data.page}
            totalPages={data.pages}
            totalItems={data.total}
          />
        )}

        {/* Footer system info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-16 pt-8 border-t border-gray-900"
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#00ff88]" style={{ boxShadow: "0 0 4px #00ff88" }} />
              <span className="tracking-wider">СИСТЕМА ОНЛАЙН</span>
            </div>
            <div className="tracking-wider">
              OLYMPEIT CATALOG v2.0.0
            </div>
          </div>
        </motion.div>
      </div>

      {/* CRT scanline overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015]"
        style={{
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)",
        }}
      />
    </div>
  );
}
