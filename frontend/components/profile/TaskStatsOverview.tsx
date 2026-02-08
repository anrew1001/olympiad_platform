/**
 * TaskStatsOverview.tsx
 * Компонент для отображения общей статистики решения задач (4 metric cards)
 * Cyberpunk HUD стиль с corner brackets и glow effects
 */

"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { UserStatsResponse } from "@/lib/types/stats";

interface TaskStatsOverviewProps {
  stats: UserStatsResponse | null;
  loading?: boolean;
}

/**
 * Animated number counter (0 → final value)
 */
function AnimatedNumber({ value, duration = 0.8 }: { value: number; duration?: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const increment = value / (duration * 60); // 60 FPS
    const interval = setInterval(() => {
      start += increment;
      if (start >= value) {
        setCount(value);
        clearInterval(interval);
      } else {
        setCount(Math.floor(start));
      }
    }, 1000 / 60);

    return () => clearInterval(interval);
  }, [value, duration]);

  return <span>{count}</span>;
}

/**
 * Tactical corner brackets for cyberpunk aesthetic
 */
function TacticalCorners({ color = "#0066FF" }: { color?: string }) {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Top-left */}
      <motion.div
        animate={{ opacity: [0.3, 0.8, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity }}
        className="absolute top-0 left-0 w-4 h-4"
        style={{
          borderTop: `2px solid ${color}`,
          borderLeft: `2px solid ${color}`,
        }}
      />
      {/* Top-right */}
      <motion.div
        animate={{ opacity: [0.3, 0.8, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
        className="absolute top-0 right-0 w-4 h-4"
        style={{
          borderTop: `2px solid ${color}`,
          borderRight: `2px solid ${color}`,
        }}
      />
      {/* Bottom-left */}
      <motion.div
        animate={{ opacity: [0.3, 0.8, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 }}
        className="absolute bottom-0 left-0 w-4 h-4"
        style={{
          borderBottom: `2px solid ${color}`,
          borderLeft: `2px solid ${color}`,
        }}
      />
      {/* Bottom-right */}
      <motion.div
        animate={{ opacity: [0.3, 0.8, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity, delay: 0.9 }}
        className="absolute bottom-0 right-0 w-4 h-4"
        style={{
          borderBottom: `2px solid ${color}`,
          borderRight: `2px solid ${color}`,
        }}
      />
    </div>
  );
}

/**
 * Metric card component with cyberpunk styling
 */
function MetricCard({
  label,
  value,
  unit = "",
  color = "#0066FF",
  gradient = false,
  isLoading = false,
  isProminent = false,
  index = 0,
}: {
  label: string;
  value: number | string;
  unit?: string;
  color?: string;
  gradient?: boolean;
  isLoading?: boolean;
  isProminent?: boolean;
  index?: number;
}) {
  const isNumeric = typeof value === "number";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5 }}
      className="relative group"
    >
      <div
        className="relative p-6 h-full border-2 overflow-hidden"
        style={{
          borderColor: `${color}40`,
          background: gradient
            ? `linear-gradient(135deg, ${color}15, ${color}05)`
            : `${color}08`,
          clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))",
        }}
      >
        {/* Hover glow effect */}
        <motion.div
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 0.15 }}
          transition={{ duration: 0.3 }}
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `radial-gradient(circle at 50% 50%, ${color}40 0%, transparent 70%)`,
          }}
        />

        {/* Tactical corner brackets */}
        <TacticalCorners color={color} />

        {/* Content */}
        <div className="relative z-10 text-center">
          {/* Label */}
          <p className="text-xs font-mono tracking-widest uppercase mb-3" style={{ color: `${color}80` }}>
            {label}
          </p>

          {/* Value */}
          {isLoading ? (
            <div className="h-10 bg-gray-700/30 animate-pulse rounded mb-2" />
          ) : (
            <p
              className={`font-bold font-mono mb-1 transition-all ${
                isProminent
                  ? "text-4xl"
                  : "text-3xl"
              }`}
              style={{ color }}
            >
              {isNumeric ? <AnimatedNumber value={value as number} /> : value}
              {unit && <span className="text-sm ml-1">{unit}</span>}
            </p>
          )}

          {/* Accent line */}
          <motion.div
            className="h-[2px] w-8 mx-auto"
            style={{
              background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
            }}
          />
        </div>
      </div>
    </motion.div>
  );
}

export function TaskStatsOverview({ stats, loading }: TaskStatsOverviewProps) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-32 bg-gray-800/30 rounded-lg animate-pulse border border-gray-700/30"
            style={{
              clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))",
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Attempts */}
      <MetricCard
        index={0}
        label="Всего попыток"
        value={stats.total_attempts}
        color="#6B7280"
        isLoading={loading}
      />

      {/* Correct Attempts */}
      <MetricCard
        index={1}
        label="Правильные ответы"
        value={stats.correct_attempts}
        color="#00ff88"
        isLoading={loading}
      />

      {/* Accuracy (PROMINENT) */}
      <MetricCard
        index={2}
        label="Точность"
        value={stats.accuracy.toFixed(1)}
        unit="%"
        color="#0066FF"
        gradient
        isProminent
        isLoading={loading}
      />

      {/* Unique Solved */}
      <MetricCard
        index={3}
        label="Уникальных решено"
        value={stats.unique_solved}
        color="#06b6d4"
        isLoading={loading}
      />
    </div>
  );
}
