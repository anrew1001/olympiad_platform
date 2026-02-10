/**
 * Tactical Mission Parameters Control
 * Панель управления параметрами миссии (фильтры)
 */

"use client";

import { motion } from "motion/react";
import { useRouter, useSearchParams } from "next/navigation";
import { SUBJECT_OPTIONS, DIFFICULTY_OPTIONS } from "@/lib/constants/tasks";

export function TaskFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentSubject = searchParams.get("subject") || "";
  const currentDifficulty = searchParams.get("difficulty") || "";

  /**
   * Обновить параметр фильтра в URL
   */
  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());

    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }

    // Сброс на первую страницу при изменении фильтров
    params.set("page", "1");

    router.push(`/tasks?${params.toString()}`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      {/* HUD container */}
      <div
        className="relative p-6 border border-[#0066FF]/30 bg-black/60 backdrop-blur-md"
        style={{
          clipPath: "polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)",
          boxShadow: "0 0 20px rgba(0,102,255,0.1), inset 0 0 30px rgba(0,102,255,0.03)",
        }}
      >
        {/* Top corner notch with glow */}
        <div
          className="absolute top-0 right-0 w-4 h-4"
          style={{
            borderTop: "2px solid #0066FF",
            borderRight: "2px solid #0066FF",
            boxShadow: "0 0 8px #0066FF",
          }}
        />

        {/* Scanning line animation */}
        <motion.div
          animate={{
            x: ["-100%", "100%"],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute top-0 left-0 w-1/4 h-full opacity-10"
          style={{
            background: "linear-gradient(90deg, transparent, #0066FF, transparent)",
          }}
        />

        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-[#00ff88]" style={{ boxShadow: "0 0 6px #00ff88" }} />
            <div className="w-2 h-2 bg-[#00ff88]/50" />
            <div className="w-2 h-2 bg-[#00ff88]/20" />
          </div>
          <h2 className="text-sm font-mono tracking-[0.2em] text-gray-400 uppercase">
            ФИЛЬТРЫ ЗАДАНИЙ
          </h2>
        </div>

        {/* Filters grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
          {/* Subject filter */}
          <div className="space-y-3">
            <label
              htmlFor="subject-filter"
              className="block text-[10px] font-mono tracking-[0.25em] text-cyan-400 uppercase"
            >
              ▸ ПРЕДМЕТ
            </label>
            <div className="relative">
              <select
                id="subject-filter"
                value={currentSubject}
                onChange={(e) => updateFilter("subject", e.target.value)}
                className={`
                  w-full h-12 px-4 pr-10
                  bg-black/80 border border-gray-700
                  text-white text-sm font-mono tracking-wide
                  appearance-none cursor-pointer
                  transition-all duration-200
                  focus:outline-none focus:border-[#0066FF] focus:ring-2 focus:ring-[#0066FF]/30
                  hover:border-gray-600
                `}
                style={{
                  clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
                }}
              >
                {SUBJECT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>

              {/* Custom arrow */}
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
                  <path d="M1 1L6 6L11 1" stroke="#0066FF" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
              </div>

              {/* Charging line indicator */}
              <motion.div
                key={currentSubject}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.3 }}
                className="absolute bottom-0 left-0 h-[2px] bg-[#0066FF] origin-left"
                style={{ width: currentSubject ? "100%" : "0%" }}
              />
            </div>
          </div>

          {/* Difficulty filter */}
          <div className="space-y-3">
            <label
              htmlFor="difficulty-filter"
              className="block text-[10px] font-mono tracking-[0.25em] text-cyan-400 uppercase"
            >
              ▸ СЛОЖНОСТЬ
            </label>
            <div className="relative">
              <select
                id="difficulty-filter"
                value={currentDifficulty}
                onChange={(e) => updateFilter("difficulty", e.target.value)}
                className={`
                  w-full h-12 px-4 pr-10
                  bg-black/80 border border-gray-700
                  text-white text-sm font-mono tracking-wide
                  appearance-none cursor-pointer
                  transition-all duration-200
                  focus:outline-none focus:border-[#0066FF] focus:ring-2 focus:ring-[#0066FF]/30
                  hover:border-gray-600
                `}
                style={{
                  clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
                }}
              >
                {DIFFICULTY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>

              {/* Custom arrow */}
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
                  <path d="M1 1L6 6L11 1" stroke="#0066FF" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
              </div>

              {/* Charging line indicator */}
              <motion.div
                key={currentDifficulty}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.3 }}
                className="absolute bottom-0 left-0 h-[2px] bg-[#0066FF] origin-left"
                style={{ width: currentDifficulty ? "100%" : "0%" }}
              />
            </div>
          </div>
        </div>

        {/* Active filters indicator */}
        {(currentSubject || currentDifficulty) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-4 pt-4 border-t border-gray-800"
          >
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-1.5 h-1.5 bg-[#00ff88]"
                style={{ boxShadow: "0 0 6px #00ff88" }}
              />
              <span className="text-xs font-mono text-gray-500 tracking-wider">
                ФИЛЬТРЫ АКТИВНЫ
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Bottom edge glow */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[1px]"
        style={{
          background: "linear-gradient(90deg, transparent, #0066FF, transparent)",
          boxShadow: "0 0 10px #0066FF",
        }}
      />
    </motion.div>
  );
}
