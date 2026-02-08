/**
 * /admin/tasks
 * Управление задачами - CRUD операции
 * Список всех задач + форма создания/редактирования
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  getAdminTasks,
  createTask,
  updateTask,
  deleteTask,
  type AdminPaginatedTasks,
  type TaskAdmin,
  type TaskCreate,
  type TaskUpdate,
} from "@/lib/api/admin";
import { LoadingScreen } from "@/components/ui/LoadingScreen";

export default function AdminTasksPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [tasks, setTasks] = useState<AdminPaginatedTasks | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Форма
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<TaskAdmin | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  // Пагинация
  const [page, setPage] = useState(1);

  // Редирект если не админ
  useEffect(() => {
    if (!authLoading && (!isAuthenticated || user?.role !== "admin")) {
      router.push("/");
    }
  }, [isAuthenticated, user, authLoading, router]);

  // Загрузить задачи
  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAdminTasks({ page, per_page: 20 });
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user?.role === "admin") {
      loadTasks();
    }
  }, [isAuthenticated, user, page]);

  // Создать задачу
  const handleCreate = async (data: TaskCreate) => {
    setFormLoading(true);
    try {
      await createTask(data);
      setShowForm(false);
      await loadTasks();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка создания");
    } finally {
      setFormLoading(false);
    }
  };

  // Обновить задачу
  const handleUpdate = async (taskId: number, data: TaskUpdate) => {
    setFormLoading(true);
    try {
      await updateTask(taskId, data);
      setEditingTask(null);
      setShowForm(false);
      await loadTasks();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка обновления");
    } finally {
      setFormLoading(false);
    }
  };

  // Удалить задачу
  const handleDelete = async (taskId: number, title: string) => {
    if (!confirm(`Удалить задачу "${title}"?`)) return;

    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка удаления");
    }
  };

  if (authLoading) {
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
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link
              href="/admin"
              className="text-xs font-mono text-[#0066FF] hover:text-[#0080FF] mb-2 inline-block"
            >
              ← НАЗАД В АДМИН ПАНЕЛЬ
            </Link>
            <h1 className="text-5xl font-bold text-white mb-2 font-mono tracking-tight">
              УПРАВЛЕНИЕ ЗАДАЧАМИ
            </h1>
            <p className="text-[#0066FF] font-mono text-sm tracking-wider uppercase">
              Создание, редактирование и удаление
            </p>
          </div>

          <button
            onClick={() => {
              setEditingTask(null);
              setShowForm(true);
            }}
            className="px-6 py-3 bg-[#0066FF] text-white font-mono text-sm font-bold hover:bg-[#0080FF] transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
              boxShadow: '0 0 15px rgba(0, 102, 255, 0.5)',
            }}
          >
            + СОЗДАТЬ ЗАДАЧУ
          </button>
        </div>

        {/* Форма */}
        {showForm && (
          <TaskForm
            task={editingTask}
            onSubmit={editingTask ? (data) => handleUpdate(editingTask.id, data) : handleCreate}
            onCancel={() => {
              setShowForm(false);
              setEditingTask(null);
            }}
            loading={formLoading}
          />
        )}

        {/* Ошибка */}
        {error && (
          <div
            className="relative mb-6 p-4 border border-[#ff3b30] bg-[#1a0a0a]"
            style={{
              clipPath: 'polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)',
            }}
          >
            <p className="text-sm font-mono text-[#ff3b30]">⚠ {error}</p>
          </div>
        )}

        {/* Список задач */}
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="h-32 bg-[#1a1a1a] border border-[#333] animate-pulse"
                style={{
                  clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
                }}
              />
            ))}
          </div>
        ) : !tasks || tasks.items.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 font-mono text-sm">ЗАДАЧИ НЕ НАЙДЕНЫ</p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {tasks.items.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onEdit={() => {
                    setEditingTask(task);
                    setShowForm(true);
                  }}
                  onDelete={() => handleDelete(task.id, task.title)}
                />
              ))}
            </div>

            {/* Пагинация */}
            {tasks.pages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-[#1a1a1a] border border-[#333] text-white font-mono text-xs disabled:opacity-30 hover:border-[#0066FF]"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                  }}
                >
                  ← ПРЕД
                </button>

                <span className="px-4 py-2 text-xs font-mono text-gray-400">
                  {page} / {tasks.pages}
                </span>

                <button
                  onClick={() => setPage((p) => Math.min(tasks.pages, p + 1))}
                  disabled={page === tasks.pages}
                  className="px-4 py-2 bg-[#1a1a1a] border border-[#333] text-white font-mono text-xs disabled:opacity-30 hover:border-[#0066FF]"
                  style={{
                    clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
                  }}
                >
                  СЛЕД →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// TaskCard Component
// ============================================================================

interface TaskCardProps {
  task: TaskAdmin;
  onEdit: () => void;
  onDelete: () => void;
}

function TaskCard({ task, onEdit, onDelete }: TaskCardProps) {
  const difficultyColors = ["#666", "#00ff88", "#ffcc00", "#ff9900", "#ff3b30"];
  const color = difficultyColors[task.difficulty - 1] || "#666";

  return (
    <div
      className="relative p-6 border bg-[#0a0f1a] hover:brightness-110 transition-all"
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

      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-mono text-gray-600">#{task.id}</span>
            <span
              className="text-[10px] font-mono font-bold uppercase px-2 py-1"
              style={{
                color,
                border: `1px solid ${color}`,
                clipPath: 'polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))',
              }}
            >
              {task.subject}
            </span>
            <span className="text-[10px] font-mono text-gray-600 uppercase">{task.topic}</span>
            <span className="text-[10px] font-mono font-bold" style={{ color }}>
              {"⬤".repeat(task.difficulty)}
            </span>
          </div>

          <h3 className="text-lg font-mono font-bold text-white mb-2">{task.title}</h3>
          <p className="text-sm font-mono text-gray-400 line-clamp-2 mb-2">{task.text}</p>
          <p className="text-xs font-mono text-[#00ff88]">
            <span className="text-gray-600">ОТВЕТ:</span> {task.answer}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="px-4 py-2 bg-[#1a1a1a] border border-[#0066FF]/40 text-[#0066FF] font-mono text-xs hover:border-[#0066FF] transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          >
            РЕДАКТ
          </button>
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-[#1a0a0a] border border-[#ff3b30]/40 text-[#ff3b30] font-mono text-xs hover:border-[#ff3b30] transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))',
            }}
          >
            УДАЛИТЬ
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// TaskForm Component
// ============================================================================

interface TaskFormProps {
  task: TaskAdmin | null;
  onSubmit: (data: TaskCreate | TaskUpdate) => void;
  onCancel: () => void;
  loading: boolean;
}

function TaskForm({ task, onSubmit, onCancel, loading }: TaskFormProps) {
  const [formData, setFormData] = useState({
    subject: task?.subject || "",
    topic: task?.topic || "",
    difficulty: task?.difficulty || 1,
    title: task?.title || "",
    text: task?.text || "",
    answer: task?.answer || "",
    hints: task?.hints?.join("\n") || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data: TaskCreate = {
      subject: formData.subject,
      topic: formData.topic,
      difficulty: formData.difficulty,
      title: formData.title,
      text: formData.text,
      answer: formData.answer,
      hints: formData.hints ? formData.hints.split("\n").filter((h) => h.trim()) : null,
    };

    onSubmit(data);
  };

  const inputClass = "w-full bg-[#1a1a1a] border border-[#333] px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-[#0066FF] transition-all";

  return (
    <div
      className="relative mb-8 p-6 border border-[#0066FF]/40 bg-[#0a0f1a]"
      style={{
        clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
      }}
    >
      <div
        className="absolute top-0 right-0 w-3 h-3 bg-[#0066FF]"
        style={{ boxShadow: '0 0 10px #0066FF' }}
      />

      <h2 className="text-xl font-mono font-bold text-white mb-6 uppercase">
        {task ? "РЕДАКТИРОВАТЬ ЗАДАЧУ" : "СОЗДАТЬ ЗАДАЧУ"}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
              Предмет
            </label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              className={inputClass}
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
              Тема
            </label>
            <input
              type="text"
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              className={inputClass}
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
              Сложность (1-5)
            </label>
            <input
              type="number"
              min="1"
              max="5"
              value={formData.difficulty}
              onChange={(e) => setFormData({ ...formData, difficulty: parseInt(e.target.value) })}
              className={inputClass}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
            Название
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className={inputClass}
            required
          />
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
            Условие задачи
          </label>
          <textarea
            value={formData.text}
            onChange={(e) => setFormData({ ...formData, text: e.target.value })}
            className={inputClass}
            rows={6}
            required
          />
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
            Ответ
          </label>
          <input
            type="text"
            value={formData.answer}
            onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
            className={inputClass}
            required
          />
        </div>

        <div>
          <label className="block text-[10px] font-mono text-[#0066FF] uppercase mb-2">
            Подсказки (по одной на строку)
          </label>
          <textarea
            value={formData.hints}
            onChange={(e) => setFormData({ ...formData, hints: e.target.value })}
            className={inputClass}
            rows={3}
            placeholder="Подсказка 1&#10;Подсказка 2&#10;Подсказка 3"
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-[#0066FF] text-white font-mono text-sm font-bold hover:bg-[#0080FF] disabled:opacity-50 transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
            }}
          >
            {loading ? "СОХРАНЕНИЕ..." : task ? "СОХРАНИТЬ" : "СОЗДАТЬ"}
          </button>

          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-3 bg-[#1a1a1a] border border-[#333] text-white font-mono text-sm hover:border-[#0066FF] disabled:opacity-50 transition-all"
            style={{
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
            }}
          >
            ОТМЕНА
          </button>
        </div>
      </form>
    </div>
  );
}
