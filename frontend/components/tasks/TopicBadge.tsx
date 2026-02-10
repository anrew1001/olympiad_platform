/**
 * Mission Category Tag
 * Тактический тег категории миссии
 */

"use client";

import { motion } from "motion/react";
import { TOPIC_LABELS } from "@/lib/constants/tasks";

interface TopicBadgeProps {
  topic: string;
}

export function TopicBadge({ topic }: TopicBadgeProps) {
  const label = TOPIC_LABELS[topic] || topic.toUpperCase();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative inline-flex items-center gap-1.5 px-2 py-1 font-mono text-xs"
      style={{
        background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)",
        border: "1px solid rgba(255,255,255,0.1)",
        clipPath: "polygon(3px 0, 100% 0, 100% calc(100% - 3px), calc(100% - 3px) 100%, 0 100%, 0 3px)",
      }}
    >
      {/* Holographic shimmer */}
      <motion.div
        animate={{
          x: ["-100%", "100%"],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute inset-0 w-1/3"
        style={{
          background: "linear-gradient(90deg, transparent, rgba(0,102,255,0.1), transparent)",
        }}
      />

      {/* Category icon */}
      <div className="w-1 h-1 bg-cyan-400 relative z-10" style={{ boxShadow: "0 0 4px #06b6d4" }} />

      {/* Label */}
      <span className="text-gray-400 relative z-10 tracking-wider">{label}</span>
    </motion.div>
  );
}
