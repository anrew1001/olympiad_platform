/**
 * Tactical Mission Grid with Skeleton Loaders
 * Тактическая сетка миссий со сканирующими загрузчиками
 */

"use client";

import { motion, AnimatePresence } from "motion/react";
import { useRouter } from "next/navigation";
import { Task } from "@/lib/types/task";
import { TaskCard } from "./TaskCard";

interface TaskGridProps {
  tasks: Task[];
  loading?: boolean;
}

export function TaskGrid({ tasks, loading = false }: TaskGridProps) {
  const router = useRouter();

  const handleTaskClick = (taskId: number) => {
    router.push(`/tasks/${taskId}`);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <TacticalSkeleton key={i} index={i} />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return <EmptyMissionState />;
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {tasks.map((task, index) => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={handleTaskClick}
            index={index}
          />
        ))}
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * Tactical Skeleton Loader with Scanning Effect
 */
function TacticalSkeleton({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="relative bg-black/40 backdrop-blur-sm border border-gray-800 p-6"
      style={{
        clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
      }}
    >
      {/* Scanning animation */}
      <motion.div
        animate={{
          y: ["-100%", "200%"],
          opacity: [0, 0.3, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "linear",
          delay: index * 0.2,
        }}
        className="absolute inset-0 w-full h-8"
        style={{
          background: "linear-gradient(180deg, transparent, #0066FF, transparent)",
        }}
      />

      {/* Content skeleton */}
      <div className="space-y-4 relative z-10">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="space-y-2">
            <div className="h-2 w-24 bg-gray-800 animate-pulse" />
            <div className="h-3 w-32 bg-gray-700 animate-pulse" />
          </div>
          <div className="h-7 w-24 bg-gray-800 animate-pulse" />
        </div>

        {/* Title */}
        <div className="space-y-2">
          <div className="h-5 w-full bg-gray-700 animate-pulse" />
          <div className="h-5 w-3/4 bg-gray-800 animate-pulse" />
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center">
          <div className="h-6 w-28 bg-gray-800 animate-pulse" />
          <div className="h-4 w-20 bg-gray-900 animate-pulse" />
        </div>
      </div>

      {/* Corner brackets */}
      <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-gray-700" />
      <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-gray-700" />
      <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-gray-700" />
      <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-gray-700" />
    </motion.div>
  );
}

/**
 * Empty Mission State (No Results)
 */
function EmptyMissionState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center py-24 px-4"
    >
      {/* Holographic icon */}
      <motion.div
        animate={{
          rotateY: [0, 360],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "linear",
        }}
        className="mb-8 relative"
      >
        <div
          className="w-20 h-20 border-2 border-[#0066FF] flex items-center justify-center"
          style={{
            clipPath: "polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)",
            boxShadow: "0 0 30px rgba(0,102,255,0.5), inset 0 0 20px rgba(0,102,255,0.2)",
          }}
        >
          <span className="text-4xl">📡</span>
        </div>

        {/* Scanning rings */}
        <motion.div
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.5, 0, 0.5],
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute inset-0 border-2 border-[#0066FF] rounded-full"
        />
      </motion.div>

      {/* Message */}
      <div className="text-center space-y-3">
        <h3 className="text-xl font-semibold text-white font-mono tracking-wider">
          МИССИИ НЕ ОБНАРУЖЕНЫ
        </h3>
        <p className="text-sm text-gray-400 max-w-md font-mono">
          Измените параметры поиска или очистите фильтры для отображения доступных заданий
        </p>

        {/* Data stream effect */}
        <motion.div
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="flex justify-center gap-1 mt-6"
        >
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              animate={{
                height: ["4px", "12px", "4px"],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.1,
              }}
              className="w-1 bg-cyan-500"
              style={{ boxShadow: "0 0 4px #06b6d4" }}
            />
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
}
