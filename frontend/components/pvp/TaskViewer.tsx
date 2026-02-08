'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import type { MatchTask } from '@/lib/types/websocket';
import { getDifficultyColor, getDifficultyLabel } from '@/lib/constants/tasks';

interface TaskViewerProps {
  task: MatchTask | null;
  onSubmit: (answer: string) => void;
  submissionStatus?: 'submitting' | 'correct' | 'incorrect';
  disabled: boolean;
}

/**
 * Просмотр задачи и форма для ответа (правая колонка)
 */
export function TaskViewer({
  task,
  onSubmit,
  submissionStatus,
  disabled,
}: TaskViewerProps) {
  const [answer, setAnswer] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset answer when task changes
  useEffect(() => {
    setAnswer('');
  }, [task?.task_id]);

  const handleSubmit = () => {
    if (answer.trim() && !disabled) {
      onSubmit(answer.trim());
      setAnswer('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !disabled && answer.trim()) {
      handleSubmit();
    }
  };

  if (!task) {
    return (
      <motion.div
        className="flex items-center justify-center h-[500px] rounded border-2 border-[#1a1a1a]"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <p className="text-sm font-mono text-[#666] text-center">
          Выбери задачу слева для начала
        </p>
      </motion.div>
    );
  }

  const diffColor = getDifficultyColor(task.difficulty);
  const diffLabel = getDifficultyLabel(task.difficulty);

  return (
    <motion.div
      className="space-y-6 p-8 rounded border border-[#0066FF]/10 bg-[#121212] max-h-[800px] overflow-y-auto"
      style={{
        boxShadow: '0 0 5px rgba(0, 102, 255, 0.05)',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      key={task.task_id}
    >
      {/* Task header */}
      <motion.div
        className="space-y-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-mono font-bold text-white mb-2">
              ▸ ЗАДАЧА #{task.order}
            </h3>
            <p className="text-sm text-[#ccc] font-sora">{task.title}</p>
          </div>
        </div>

        {/* Metadata badges */}
        <div className="flex items-center gap-3 flex-wrap">
          <span
            className="text-xs font-mono px-3 py-1 rounded"
            style={{
              backgroundColor: `${diffColor}20`,
              color: diffColor,
              border: `1px solid ${diffColor}40`,
            }}
          >
            {diffLabel}
          </span>
        </div>

        {/* Divider */}
        <div className="pt-3 border-t border-[#1a1a1a]" />
      </motion.div>

      {/* Task text */}
      <motion.div
        className="space-y-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
      >
        <div
          className="text-base leading-loose text-[#e5e5e5] font-sora whitespace-pre-wrap break-words px-2"
          style={{ maxHeight: '400px', overflowY: 'auto', lineHeight: '1.8' }}
        >
          {task.text}
        </div>

        {/* Hints */}
        {task.hints && task.hints.length > 0 && (
          <motion.div
            className="mt-6 pt-6 border-t border-[#1a1a1a]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <p className="text-xs font-mono text-[#0066FF] uppercase tracking-wider mb-3">
              ▸ ПОДСКАЗКИ
            </p>
            <ul className="space-y-2">
              {task.hints.map((hint, idx) => (
                <motion.li
                  key={idx}
                  className="text-xs text-[#888] font-sora pl-3 border-l-2 border-[#0066FF]/40"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + idx * 0.05 }}
                >
                  {hint}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        )}
      </motion.div>

      {/* Answer form */}
      <motion.div
        className="space-y-3 pt-6 border-t border-[#1a1a1a]"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
      >
        <p className="text-xs font-mono text-[#0066FF] uppercase tracking-wider">
          ▸ ВАШ ОТВЕТ
        </p>

        {/* Input field - INTENSE FOCUS */}
        <div className="relative space-y-2">
          <motion.div
            className="relative"
            animate={{
              boxShadow: isFocused
                ? '0 0 15px rgba(0, 102, 255, 0.2)'
                : '0 0 0px rgba(0, 102, 255, 0)',
            }}
            transition={{ duration: 0.3 }}
          >
            <input
              ref={inputRef}
              type="text"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyDown={handleKeyDown}
              disabled={disabled || submissionStatus === 'submitting'}
              placeholder="Введите ответ..."
              className="w-full h-16 bg-[#121212]/60 border-2 px-5 text-white placeholder-[#555] font-mono text-base outline-none transition-all duration-300"
              style={{
                borderColor: isFocused ? '#0066FF' : '#333',
                backdropFilter: 'blur(4px)',
              }}
            />

            {/* Animated border glow - приглушённый */}
            <motion.div
              className="absolute inset-0 pointer-events-none rounded"
              animate={{
                boxShadow: isFocused
                  ? '0 0 10px rgba(0, 102, 255, 0.3)'
                  : '0 0 0px rgba(0, 102, 255, 0)',
              }}
              transition={{ duration: 0.3 }}
            />
          </motion.div>

          {/* Charging indicator - Enhanced */}
          <AnimatePresence>
            {isFocused && (
              <motion.div
                initial={{ scaleX: 0, opacity: 0 }}
                animate={{ scaleX: 1, opacity: 1 }}
                exit={{ scaleX: 0, opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="h-1 bg-gradient-to-r from-transparent via-[#0066FF] to-transparent origin-left rounded-full"
                style={{
                  boxShadow: '0 0 8px rgba(0, 102, 255, 0.5)',
                }}
              />
            )}
          </AnimatePresence>

          {/* Character count hint */}
          {isFocused && answer && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs font-mono text-[#0066FF]/60 text-right"
            >
              {answer.length} символов · Enter для отправки
            </motion.p>
          )}
        </div>

        {/* Submit button + feedback - DRAMATIC */}
        <div className="flex items-center gap-3 pt-2">
          <motion.button
            onClick={handleSubmit}
            disabled={disabled || !answer.trim() || submissionStatus === 'submitting'}
            className="flex-1 group relative px-6 py-4 font-mono uppercase text-sm font-bold text-white border-2 border-[#0066FF] bg-[#0066FF]/20 overflow-hidden disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
              boxShadow: !disabled && submissionStatus !== 'submitting'
                ? '0 0 20px rgba(0, 102, 255, 0.4)'
                : 'none',
            }}
            whileHover={{ scale: !disabled && submissionStatus !== 'submitting' ? 1.03 : 1 }}
            whileTap={{ scale: !disabled && submissionStatus !== 'submitting' ? 0.96 : 1 }}
          >
            {/* Animated background gradient */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-[#0066FF]/0 via-[#00d4ff]/30 to-[#0066FF]/0"
              animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
              style={{ backgroundSize: '200% 100%' }}
            />

            {/* Glow on hover */}
            <motion.div
              className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              style={{
                boxShadow: 'inset 0 0 25px rgba(0, 102, 255, 0.3)',
              }}
            />

            <span className="relative z-10">
              {submissionStatus === 'submitting' ? (
                <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
                  ⟳
                </motion.span>
              ) : (
                '▶ ОТПРАВИТЬ'
              )}
            </span>
          </motion.button>

          {/* Feedback icon */}
          <AnimatePresence mode="wait">
            {submissionStatus === 'correct' && (
              <motion.div
                key="correct"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="w-12 h-12 flex items-center justify-center rounded border-2 border-[#00ff88] bg-[#00ff88]/10"
              >
                <svg className="w-6 h-6 text-[#00ff88]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </motion.div>
            )}

            {submissionStatus === 'incorrect' && (
              <motion.div
                key="incorrect"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0 }}
                transition={{ type: 'spring' }}
                className="w-12 h-12 flex items-center justify-center rounded border-2 border-[#ff3b30] bg-[#ff3b30]/10"
              >
                <svg className="w-6 h-6 text-[#ff3b30]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </motion.div>
  );
}
