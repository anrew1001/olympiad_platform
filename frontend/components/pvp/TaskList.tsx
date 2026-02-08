'use client';

import { motion, AnimatePresence } from 'motion/react';
import type { MatchTask } from '@/lib/types/websocket';
import { getDifficultyColor, getDifficultyLabel } from '@/lib/constants/tasks';

interface TaskListProps {
  tasks: MatchTask[];
  yourSolvedTasks: Set<number>;
  opponentSolvedCount: number; // Just count, не IDs
  selectedTaskId: number | null;
  onSelectTask: (id: number) => void;
}

/**
 * Список задач матча (левая колонка)
 * Показывает статусы, сложность, и позволяет выбирать задачу
 */
export function TaskList({
  tasks,
  yourSolvedTasks,
  opponentSolvedCount,
  selectedTaskId,
  onSelectTask,
}: TaskListProps) {
  const containerVariants: any = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.3, ease: 'easeOut' },
    },
  };

  return (
    <motion.div
      className="space-y-3"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <h3 className="text-xs font-mono uppercase tracking-wider text-[#0066FF] mb-4">
        {'▸'} ЗАДАЧИ
      </h3>

      <AnimatePresence mode="popLayout">
        {tasks.map((task, idx) => {
          const isSolved = yourSolvedTasks.has(task.task_id);
          const isSelected = selectedTaskId === task.task_id;
          const diffColor = getDifficultyColor(task.difficulty);
          const diffLabel = getDifficultyLabel(task.difficulty);

          return (
            <motion.button
              key={task.task_id}
              onClick={() => onSelectTask(task.task_id)}
              variants={itemVariants}
              whileHover={{ scale: 1.02, x: 6, backgroundColor: 'rgba(0, 102, 255, 0.08)' }}
              whileTap={{ scale: 0.98 }}
              className={`w-full text-left p-4 rounded transition-all duration-300 ${
                isSelected
                  ? 'border-2 border-[#0066FF] bg-[#0066FF]/15'
                  : 'border border-[#222] bg-transparent hover:border-[#0066FF]/40'
              }`}
              style={
                isSelected
                  ? {
                      boxShadow: '0 0 25px rgba(0, 102, 255, 0.4), inset 0 0 15px rgba(0, 102, 255, 0.08)',
                    }
                  : {}
              }
            >
              {/* Number badge + Status indicator */}
              <div className="flex items-start gap-3 mb-3">
                {/* Number badge */}
                <motion.div
                  className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-sm bg-[#0066FF]/20 border border-[#0066FF]/40 text-[#0066FF]"
                  animate={{ scale: isSelected ? 1.1 : 1 }}
                  transition={{ duration: 0.2 }}
                >
                  {task.order}
                </motion.div>

                {/* Title + Status */}
                <div className="flex-1 min-w-0 space-y-1">
                  <p className="text-sm font-mono font-bold text-white truncate">
                    {task.title}
                  </p>
                  <p className="text-xs font-mono text-[#666]">
                    {isSolved ? '✓ РЕШЕНА' : 'В ОЖИДАНИИ'}
                  </p>
                </div>

                {/* Solved indicator */}
                {isSolved && (
                  <motion.div
                    initial={{ scale: 0, rotate: -90 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                    className="flex-shrink-0 w-5 h-5 rounded-full bg-[#00ff88] flex items-center justify-center text-[#121212] font-bold text-xs"
                  >
                    ✓
                  </motion.div>
                )}
              </div>

              {/* Difficulty badge + Opponent indicator */}
              <div className="flex items-center justify-between gap-2 px-8">
                <span
                  className="text-xs font-mono px-2 py-1 rounded transition-all duration-300"
                  style={{
                    backgroundColor: isSelected ? `${diffColor}30` : `${diffColor}15`,
                    color: diffColor,
                    border: `1px solid ${diffColor}50`,
                    textShadow: isSelected ? `0 0 8px ${diffColor}80` : 'none',
                  }}
                >
                  {diffLabel}
                </span>

                {/* Opponent solved indicator */}
                {opponentSolvedCount > 0 && !isSolved && (
                  <motion.span
                    className="text-xs font-mono text-[#06b6d4] font-bold"
                    animate={{ opacity: [0.4, 1, 0.4], scale: [0.9, 1.1, 0.9] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                  >
                    ⊙ OPP
                  </motion.span>
                )}
              </div>
            </motion.button>
          );
        })}
      </AnimatePresence>

      {/* Progress indicator */}
      <motion.div
        className="mt-6 pt-6 border-t border-[#1a1a1a] space-y-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="text-xs font-mono text-[#666] space-y-1">
          <p>
            ◇ Решено:{' '}
            <span className="text-[#00ff88]">{yourSolvedTasks.size}</span>/{tasks.length}
          </p>
          <p>
            ⊙ Соперник:{' '}
            <span className="text-[#06b6d4]">{opponentSolvedCount}</span>/{tasks.length}
          </p>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2 bg-[#1a1a1a] rounded overflow-hidden mt-3">
          <motion.div
            className="h-full bg-gradient-to-r from-[#0066FF] to-[#00d4ff]"
            animate={{
              width: `${(yourSolvedTasks.size / tasks.length) * 100}%`,
            }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            style={{
              boxShadow: '0 0 10px rgba(0, 102, 255, 0.5)',
            }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}
