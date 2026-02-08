/**
 * Task Detail Page - Neon Academy ⚡
 * Страница детализации задачи с интерактивной формой проверки ответа
 * Электрическая энергия знаний - яркая, высоковольтная, charged
 */

"use client";

import { useState, useEffect, FormEvent, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { use } from "react";
import { fetchTaskDetail, checkAnswer } from "@/lib/api/tasks";
import { useAuth } from "@/hooks/useAuth";
import type { TaskDetail, TaskCheckResponse } from "@/lib/types/task";
import { DifficultyBadge } from "@/components/tasks/DifficultyBadge";
import { TopicBadge } from "@/components/tasks/TopicBadge";
import { SUBJECT_LABELS } from "@/lib/constants/tasks";

export default function TaskDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { id: idParam } = use(params);

  // Parse и validate task ID
  const taskId = parseInt(idParam as string, 10);
  if (isNaN(taskId)) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
        <div className="text-center space-y-6">
          <h1 className="text-4xl font-bold text-[#ff0080]">⚠️ INVALID ID</h1>
          <p className="text-gray-400">Неверный ID задания</p>
          <button
            onClick={() => router.push("/tasks")}
            className="px-6 py-3 border-2 border-[#00d4ff] text-[#00d4ff] hover:bg-[#00d4ff]/10 transition"
          >
            Вернуться к каталогу
          </button>
        </div>
      </div>
    );
  }

  // Task data state
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Hints state (progressive disclosure)
  const [shownHintsCount, setShownHintsCount] = useState(0);

  // Answer form state
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [checkResult, setCheckResult] = useState<TaskCheckResponse | null>(
    null
  );

  const inputRef = useRef<HTMLInputElement>(null);

  // Load task on mount
  useEffect(() => {
    let cancelled = false;

    const loadTask = async () => {
      try {
        setLoading(true);
        setError(null);
        const taskData = await fetchTaskDetail(taskId);
        if (!cancelled) {
          setTask(taskData);
        }
      } catch (err) {
        if (!cancelled) {
          const errorMessage =
            err instanceof Error ? err.message : "Ошибка загрузки задания";
          setError(errorMessage);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadTask();

    return () => {
      cancelled = true;
    };
  }, [taskId]);

  // Handle answer submit
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!task || !answer.trim() || submitting) return;

    setSubmitting(true);
    try {
      const result = await checkAnswer(task.id, answer);
      setCheckResult(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Ошибка проверки ответа";
      setCheckResult({
        is_correct: false,
        message: errorMessage,
        correct_answer: null,
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Handle retry
  const handleRetry = () => {
    setAnswer("");
    setCheckResult(null);
    inputRef.current?.focus();
  };

  // Show next hint
  const showNextHint = () => {
    if (task && shownHintsCount < task.hints.length) {
      setShownHintsCount((prev) => prev + 1);
    }
  };

  // === RENDER STATES ===

  if (loading) {
    return <TaskDetailSkeleton />;
  }

  if (error) {
    return <TaskNotFoundState error={error} router={router} />;
  }

  if (!task) {
    return null;
  }

  // === MAIN RENDER ===
  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Electrical field background */}
      <ElectricalFieldBackground />

      {/* Grid background */}
      <div className="fixed inset-0 opacity-[0.01] pointer-events-none -z-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #00d4ff 1px, transparent 1px),
              linear-gradient(0deg, #00d4ff 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Back button */}
        <motion.button
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          whileHover={{ x: -5 }}
          onClick={() => router.push("/tasks")}
          className="flex items-center gap-2 text-[#0096c7] hover:text-[#d4a000] transition mb-8"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M10 2L4 8L10 14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="font-mono text-sm tracking-wider">
            ВЕРНУТЬСЯ К КАТАЛОГУ
          </span>
        </motion.button>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-8">
          {/* Left column: Task content (60%) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-7 space-y-8"
          >
            {/* Task Header */}
            <TaskHeader task={task} />

            {/* Task Text */}
            <TaskText task={task} />

            {/* Hints Section */}
            {task.hints && task.hints.length > 0 && (
              <HintsSection
                hints={task.hints}
                shownCount={shownHintsCount}
                onShowNext={showNextHint}
              />
            )}
          </motion.div>

          {/* Right column: Answer form (40%) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-5 lg:sticky lg:top-8 h-fit"
          >
            <AnswerForm
              isAuthenticated={isAuthenticated}
              authLoading={authLoading}
              answer={answer}
              setAnswer={setAnswer}
              submitting={submitting}
              checkResult={checkResult}
              onSubmit={handleSubmit}
              onRetry={handleRetry}
              inputRef={inputRef}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

// === SUB-COMPONENTS ===

function ElectricalFieldBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none -z-10">
      {/* Subtle glow animation */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{
            opacity: [0, 0.015, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 6 + i * 1.5,
            repeat: Infinity,
            delay: i * 2,
            ease: "easeInOut",
          }}
          className="absolute"
          style={{
            width: "250px",
            height: "250px",
            left: `${15 + i * 35}%`,
            top: `${5 + i * 25}%`,
            background: `radial-gradient(circle, rgba(0, 150, 199, 0.15) 0%, transparent 70%)`,
            filter: "blur(50px)",
          }}
        />
      ))}
    </div>
  );
}

interface TaskHeaderProps {
  task: TaskDetail;
}

function TaskHeader({ task }: TaskHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="space-y-4"
    >
      {/* Subject label */}
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 bg-[#0096c7]" style={{ boxShadow: "0 0 4px #0096c7" }} />
        <span className="font-mono text-xs tracking-widest text-[#0096c7]">
          {SUBJECT_LABELS[task.subject] || task.subject.toUpperCase()}
        </span>
      </div>

      {/* Task ID - subtle glow */}
      <motion.h1
        animate={{
          textShadow: [
            "0 0 8px rgba(0, 150, 199, 0.6), 0 0 15px rgba(0, 150, 199, 0.3)",
            "0 0 4px rgba(0, 150, 199, 0.4)",
            "0 0 8px rgba(0, 150, 199, 0.6), 0 0 15px rgba(0, 150, 199, 0.3)",
          ],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatType: "reverse",
        }}
        className="text-4xl font-black tracking-widest"
        style={{
          fontFamily: '"Orbitron", "Space Mono", monospace',
          color: "#e0e000",
        }}
      >
        ЗАДАНИЕ #{String(task.id).padStart(4, "0")}
      </motion.h1>

      {/* Badges */}
      <div className="flex flex-wrap gap-3 pt-2">
        <DifficultyBadge difficulty={task.difficulty} />
        <TopicBadge topic={task.topic} />
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-xs text-gray-500 font-mono self-center"
        >
          {new Date(task.created_at).toLocaleDateString("ru-RU")}
        </motion.span>
      </div>
    </motion.div>
  );
}

interface TaskTextProps {
  task: TaskDetail;
}

function TaskText({ task }: TaskTextProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="space-y-4 p-6"
      style={{
        border: "2px solid #0096c7",
        background: "linear-gradient(135deg, #0a0a0a 0%, rgba(0, 150, 199, 0.02) 50%, rgba(100, 50, 150, 0.01) 100%)",
        clipPath:
          "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
        boxShadow: "0 0 20px rgba(0, 150, 199, 0.15), inset 0 0 20px rgba(0, 150, 199, 0.03)",
      }}
    >
      {/* Title */}
      <h2 className="text-2xl font-bold text-white leading-tight">
        {task.title}
      </h2>

      {/* Task text (code formatting) */}
      <div
        className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap font-mono"
        style={{ color: "#e0e0e0" }}
      >
        {task.text}
      </div>
    </motion.div>
  );
}

interface HintsSectionProps {
  hints: string[];
  shownCount: number;
  onShowNext: () => void;
}

function HintsSection({ hints, shownCount, onShowNext }: HintsSectionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="space-y-4"
    >
      <h3
        className="text-sm font-mono tracking-widest"
        style={{ color: "#b8860b" }}
      >
        ПОДСКАЗКИ
      </h3>

      {/* Shown hints */}
      <AnimatePresence mode="popLayout">
        {hints.slice(0, shownCount).map((hint, index) => (
          <motion.div
            key={`hint-${index}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{
              duration: 0.4,
              ease: "easeOut",
            }}
            className="p-4 border-l-4"
            style={{
              borderLeft: "4px solid #eab308",
              background: "rgba(234, 179, 8, 0.08)",
              borderTop: "1px solid rgba(234, 179, 8, 0.3)",
              borderRight: "1px solid rgba(234, 179, 8, 0.3)",
              borderBottom: "1px solid rgba(234, 179, 8, 0.3)",
            }}
          >
            <p
              className="text-sm leading-relaxed"
              style={{ color: "#fef3c7" }}
            >
              {hint}
            </p>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Show next hint button */}
      {shownCount < hints.length && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onShowNext}
          className="w-full py-3 border-2 border-[#eab308] text-[#eab308] hover:bg-[#eab308]/10 transition font-mono text-sm tracking-wider"
          style={{
            clipPath:
              "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
          }}
        >
          ПОКАЗАТЬ ПОДСКАЗКУ ({shownCount + 1}/{hints.length})
        </motion.button>
      )}
    </motion.div>
  );
}

interface AnswerFormProps {
  isAuthenticated: boolean;
  authLoading: boolean;
  answer: string;
  setAnswer: (value: string) => void;
  submitting: boolean;
  checkResult: TaskCheckResponse | null;
  onSubmit: (e: FormEvent) => void;
  onRetry: () => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

function AnswerForm({
  isAuthenticated,
  authLoading,
  answer,
  setAnswer,
  submitting,
  checkResult,
  onSubmit,
  onRetry,
  inputRef,
}: AnswerFormProps) {
  // Show skeleton while auth is loading
  if (authLoading) {
    return (
      <div
        className="p-6 space-y-4"
        style={{
          border: "2px solid rgba(0, 212, 255, 0.3)",
          background: "rgba(10, 10, 10, 0.8)",
          clipPath:
            "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
        }}
      >
        <div className="h-8 bg-gray-700 animate-pulse" />
        <div className="h-12 bg-gray-700 animate-pulse" />
        <div className="h-10 bg-gray-700 animate-pulse" />
      </div>
    );
  }

  // Unauthenticated state
  if (!isAuthenticated) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="p-8 text-center space-y-6"
        style={{
          border: "2px solid #ff0080",
          background: "rgba(255, 0, 128, 0.05)",
          clipPath:
            "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
          boxShadow: "0 0 30px rgba(255, 0, 128, 0.2)",
        }}
      >
        <div className="text-4xl">🔒</div>
        <h3
          className="text-lg font-bold tracking-widest"
          style={{ color: "#ff0080" }}
        >
          ДОСТУП ОГРАНИЧЕН
        </h3>
        <p className="text-sm text-gray-400">
          Войдите в систему чтобы проверить ответ
        </p>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => (window.location.href = "/login")}
          className="w-full py-3 border-2 border-[#ff0080] text-[#ff0080] hover:bg-[#ff0080]/20 transition font-mono text-sm tracking-wider"
          style={{
            clipPath:
              "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
          }}
        >
          ВОЙТИ
        </motion.button>
      </motion.div>
    );
  }

  // Authenticated form
  return (
    <motion.form
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      onSubmit={onSubmit}
      className="space-y-4 p-6"
      style={{
        border: "2px solid #0096c7",
        background: "linear-gradient(135deg, #0a0a0a 0%, rgba(0, 150, 199, 0.02) 100%)",
        clipPath:
          "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
        boxShadow: "0 0 20px rgba(0, 150, 199, 0.15), inset 0 0 20px rgba(0, 150, 199, 0.03)",
      }}
    >
      <h3
        className="text-sm font-mono tracking-widest mb-4"
        style={{ color: "#0096c7" }}
      >
        ПРОВЕРКА ОТВЕТА
      </h3>

      {/* Input field with electric styling */}
      <motion.input
        ref={inputRef}
        type="text"
        placeholder="Введите ответ..."
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        disabled={submitting}
        className="w-full h-12 px-4 bg-[#0a0a0a] text-white placeholder-gray-600 font-mono text-sm outline-none disabled:opacity-50 disabled:cursor-not-allowed transition"
        style={{
          border: "2px solid #0096c7",
          boxShadow: "0 0 15px rgba(0, 150, 199, 0.3), inset 0 0 15px rgba(0, 150, 199, 0.08)",
        }}
        whileFocus={{
          boxShadow:
            "0 0 20px rgba(0, 150, 199, 0.6), inset 0 0 20px rgba(0, 150, 199, 0.15), 0 0 30px rgba(100, 50, 150, 0.2)",
        }}
        onFocus={(e) => {
          e.target.style.borderColor = "#7b4397";
        }}
        onBlur={(e) => {
          e.target.style.borderColor = "#0096c7";
        }}
      />

      {/* Submit button */}
      <motion.button
        type="submit"
        disabled={submitting || !answer.trim()}
        whileHover={submitting || !answer.trim() ? {} : { scale: 1.02 }}
        whileTap={submitting || !answer.trim() ? {} : { scale: 0.98 }}
        className="w-full h-12 border-2 border-[#00d4ff] text-white font-mono text-sm tracking-wider uppercase font-bold disabled:opacity-50 disabled:cursor-not-allowed transition overflow-hidden relative"
        style={{
          clipPath:
            "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
          background: submitting
            ? "linear-gradient(90deg, #00d4ff 0%, #ff00ff 50%, #ffff00 100%)"
            : "rgba(0, 212, 255, 0.1)",
        }}
      >
        <motion.div
          animate={{
            x: submitting ? ["0%", "100%"] : 0,
            opacity: submitting ? 1 : 0,
          }}
          transition={{ duration: 0.8, repeat: Infinity }}
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20"
        />
        <span className="relative z-10">
          {submitting ? "⚡ ПРОВЕРКА..." : "ПРОВЕРИТЬ ОТВЕТ"}
        </span>
      </motion.button>

      {/* Result display */}
      <AnimatePresence mode="wait">
        {checkResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="p-4 space-y-3"
            style={{
              border: `2px solid ${
                checkResult.is_correct ? "#00ff88" : "#ff0080"
              }`,
              background: checkResult.is_correct
                ? "rgba(0, 255, 136, 0.05)"
                : "rgba(255, 0, 128, 0.05)",
              clipPath:
                "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
              boxShadow: `0 0 20px ${
                checkResult.is_correct
                  ? "rgba(0, 255, 136, 0.3)"
                  : "rgba(255, 0, 128, 0.3)"
              }`,
            }}
          >
            {/* Result message */}
            <div
              className="text-sm font-mono"
              style={{
                color: checkResult.is_correct ? "#00ff88" : "#ff9ec4",
              }}
            >
              <span className="font-bold">
                {checkResult.is_correct ? "✓ ВЕРНО!" : "✗ НЕВЕРНО"}
              </span>
              {!checkResult.is_correct && checkResult.correct_answer && (
                <div className="mt-2 text-xs text-[#ffff00]">
                  Правильный ответ:
                  <div className="mt-1 font-bold">{checkResult.correct_answer}</div>
                </div>
              )}
            </div>

            {/* Action button */}
            {checkResult.is_correct ? (
              <motion.button
                type="button"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => (window.location.href = "/tasks")}
                className="w-full h-10 border-2 border-[#00ff88] text-[#00ff88] hover:bg-[#00ff88]/10 font-mono text-xs tracking-wider uppercase transition"
                style={{
                  clipPath:
                    "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)",
                }}
              >
                РЕШИТЬ ЕЩЕ
              </motion.button>
            ) : (
              <motion.button
                type="button"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onRetry}
                className="w-full h-10 border-2 border-[#ff0080] text-[#ff0080] hover:bg-[#ff0080]/10 font-mono text-xs tracking-wider uppercase transition"
                style={{
                  clipPath:
                    "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)",
                }}
              >
                ПОПРОБОВАТЬ ЕЩЕ
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.form>
  );
}

// === SKELETON & ERROR STATES ===

function TaskDetailSkeleton() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      <div className="fixed inset-0 opacity-[0.01] pointer-events-none -z-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #00d4ff 1px, transparent 1px),
              linear-gradient(0deg, #00d4ff 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      <div className="relative z-10 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-6">
            {[1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="h-32 bg-gray-800/30 border border-gray-700 animate-pulse"
                style={{
                  clipPath:
                    "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
                }}
              >
                <motion.div
                  animate={{ y: ["-100%", "200%"], opacity: [0, 0.3, 0] }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear",
                    delay: i * 0.2,
                  }}
                  className="w-full h-8 bg-gradient-to-r from-transparent via-[#0066FF] to-transparent"
                />
              </motion.div>
            ))}
          </div>

          <div className="lg:col-span-5">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="h-64 bg-gray-800/30 border border-gray-700 animate-pulse"
              style={{
                clipPath:
                  "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
              }}
            >
              <motion.div
                animate={{ y: ["-100%", "200%"], opacity: [0, 0.3, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-full h-8 bg-gradient-to-r from-transparent via-[#0066FF] to-transparent"
              />
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface TaskNotFoundStateProps {
  error: string;
  router: ReturnType<typeof useRouter>;
}

function TaskNotFoundState({ error, router }: TaskNotFoundStateProps) {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4 relative overflow-hidden">
      <div className="fixed inset-0 opacity-[0.01] pointer-events-none -z-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #00d4ff 1px, transparent 1px),
              linear-gradient(0deg, #00d4ff 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
        className="text-center space-y-8 max-w-sm"
        style={{
          border: "2px solid #ff0080",
          background: "linear-gradient(135deg, rgba(255, 0, 128, 0.05) 0%, rgba(255, 0, 128, 0.02) 100%)",
          padding: "48px 32px",
          clipPath:
            "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
          boxShadow: "0 0 40px rgba(255, 0, 128, 0.3)",
        }}
      >
        <motion.div
          animate={{ rotateY: [0, 360] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
          className="text-6xl"
        >
          🔍
        </motion.div>

        <h1
          className="text-3xl font-black tracking-widest"
          style={{
            fontFamily: '"Orbitron", "Space Mono", monospace',
            color: "#ff0080",
          }}
        >
          ЗАДАНИЕ НЕ НАЙДЕНО
        </h1>

        <p className="text-gray-400 font-mono text-sm">{error}</p>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => router.push("/tasks")}
          className="w-full py-4 border-2 border-[#ff0080] text-[#ff0080] hover:bg-[#ff0080]/10 font-mono text-sm tracking-wider uppercase font-bold transition"
          style={{
            clipPath:
              "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
          }}
        >
          ВЕРНУТЬСЯ К КАТАЛОГУ
        </motion.button>
      </motion.div>
    </div>
  );
}
