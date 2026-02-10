/**
 * Task Card
 * Карточка задания с HUD-элементами
 */

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Task } from "@/lib/types/task";
import { DifficultyBadge } from "./DifficultyBadge";
import { TopicBadge } from "./TopicBadge";
import { SUBJECT_LABELS, DIFFICULTY_COLORS } from "@/lib/constants/tasks";

interface TaskCardProps {
  task: Task;
  onClick?: (taskId: number) => void;
  index?: number; // Для stagger animation
}

export function TaskCard({ task, onClick, index = 0 }: TaskCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const config = DIFFICULTY_COLORS[task.difficulty as keyof typeof DIFFICULTY_COLORS];

  const handleClick = () => {
    if (onClick) onClick(task.id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.05,
        duration: 0.4,
        ease: [0.22, 1, 0.36, 1],
      }}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      tabIndex={0}
      role="button"
      aria-label={`Развернуть миссию: ${task.title}`}
      className={`
        group relative cursor-pointer
        bg-black/40 backdrop-blur-sm
        border transition-all duration-300
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0066FF]
      `}
      style={{
        borderColor: isHovered ? config.hex : "rgba(255,255,255,0.1)",
        clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
        boxShadow: isHovered ? `0 0 30px ${config.hex}40, inset 0 0 30px ${config.hex}10` : "none",
      }}
    >
      {/* Tactical corner brackets (тактические скобки) */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top-left */}
        <motion.div
          animate={{
            opacity: isHovered ? [0.3, 1, 0.3] : 0.3,
          }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="absolute top-0 left-0 w-4 h-4"
          style={{
            borderTop: `2px solid ${config.hex}`,
            borderLeft: `2px solid ${config.hex}`,
          }}
        />
        {/* Top-right */}
        <motion.div
          animate={{
            opacity: isHovered ? [0.3, 1, 0.3] : 0.3,
          }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
          className="absolute top-0 right-0 w-4 h-4"
          style={{
            borderTop: `2px solid ${config.hex}`,
            borderRight: `2px solid ${config.hex}`,
          }}
        />
        {/* Bottom-left */}
        <motion.div
          animate={{
            opacity: isHovered ? [0.3, 1, 0.3] : 0.3,
          }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 }}
          className="absolute bottom-0 left-0 w-4 h-4"
          style={{
            borderBottom: `2px solid ${config.hex}`,
            borderLeft: `2px solid ${config.hex}`,
          }}
        />
        {/* Bottom-right */}
        <motion.div
          animate={{
            opacity: isHovered ? [0.3, 1, 0.3] : 0.3,
          }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.9 }}
          className="absolute bottom-0 right-0 w-4 h-4"
          style={{
            borderBottom: `2px solid ${config.hex}`,
            borderRight: `2px solid ${config.hex}`,
          }}
        />
      </div>

      {/* Scanning effect on hover */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ scaleY: 0, opacity: 0 }}
            animate={{ scaleY: 1, opacity: 0.1 }}
            exit={{ scaleY: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0"
            style={{
              background: `linear-gradient(180deg, transparent 0%, ${config.hex} 50%, transparent 100%)`,
              transformOrigin: "top",
            }}
          />
        )}
      </AnimatePresence>

      {/* Content */}
      <div className="relative z-10 p-6 space-y-4">
        {/* Mission header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-1">
            {/* Subject tag */}
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-[#0066FF]" style={{ boxShadow: "0 0 6px #0066FF" }} />
              <span className="text-[10px] text-gray-500 font-mono tracking-[0.2em] uppercase">
                {SUBJECT_LABELS[task.subject]}
              </span>
            </div>

            {/* Task ID */}
            <div className="font-mono text-xs text-cyan-400">
              ЗАДАНИЕ #{task.id.toString().padStart(4, "0")}
            </div>
          </div>

          {/* Difficulty badge */}
          <DifficultyBadge difficulty={task.difficulty} compact />
        </div>

        {/* Task title */}
        <h3
          className={`
            text-lg font-semibold leading-tight
            transition-colors duration-300
            ${isHovered ? config.text : "text-white"}
          `}
          style={{
            fontFamily: "Sora, sans-serif",
            textShadow: isHovered ? `0 0 10px ${config.hex}` : "none",
          }}
        >
          {task.title}
        </h3>

        {/* Task category */}
        <div className="flex items-center justify-between gap-3">
          <TopicBadge topic={task.topic} />

          {/* Open button indicator */}
          <motion.div
            animate={{
              opacity: isHovered ? [0.5, 1, 0.5] : 0.3,
            }}
            transition={{ duration: 1, repeat: Infinity }}
            className="flex items-center gap-1.5 text-xs font-mono text-gray-600 group-hover:text-[#0066FF] transition-colors"
          >
            <span className="tracking-wider">ОТКРЫТЬ</span>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path
                d="M2 6H10M10 6L6 2M10 6L6 10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
          </motion.div>
        </div>
      </div>

      {/* Holographic glow layer */}
      <motion.div
        animate={{
          opacity: isHovered ? 0.15 : 0,
        }}
        transition={{ duration: 0.3 }}
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 50% 50%, ${config.hex}40 0%, transparent 70%)`,
        }}
      />

      {/* Energy pulse on hover */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1.2, opacity: 0 }}
            exit={{ scale: 1.4, opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="absolute inset-0 pointer-events-none"
            style={{
              border: `1px solid ${config.hex}`,
              clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
            }}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
