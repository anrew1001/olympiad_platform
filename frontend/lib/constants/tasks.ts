/**
 * Константы для тактической системы миссий
 */

// Переводы предметов (Mission Departments)
export const SUBJECT_LABELS: Record<string, string> = {
  informatics: "ИНФОРМАТИКА",
  mathematics: "МАТЕМАТИКА",
  math: "МАТЕМАТИКА",
  physics: "ФИЗИКА",
};

// Переводы тем (Mission Categories)
export const TOPIC_LABELS: Record<string, string> = {
  algorithms: "АЛГОРИТМЫ",
  data_structures: "СТРУКТУРЫ ДАННЫХ",
  graphs: "ГРАФЫ",
  strings: "СТРОКИ",
  dp: "ДИН. ПРОГРАММИРОВАНИЕ",
  geometry: "ГЕОМЕТРИЯ",
  algebra: "АЛГЕБРА",
  combinatorics: "КОМБИНАТОРИКА",
  number_theory: "ТЕОРИЯ ЧИСЕЛ",
  stereometry: "СТЕРЕОМЕТРИЯ",
  kinematics: "КИНЕМАТИКА",
  dynamics: "ДИНАМИКА",
  conservation: "ЗАКОНЫ СОХРАНЕНИЯ",
  electrostatics: "ЭЛЕКТРОСТАТИКА",
  thermodynamics: "ТЕРМОДИНАМИКА",
};

// Difficulty Levels (Difficulty Colors)
export const DIFFICULTY_COLORS = {
  1: {
    bg: "bg-green-500/5",
    text: "text-green-400",
    border: "border-green-500/30",
    glow: "shadow-green-500/20",
    label: "НОВИЧОК",
    code: "◇",
    hex: "#22c55e",
  },
  2: {
    bg: "bg-cyan-500/5",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
    glow: "shadow-cyan-500/20",
    label: "УЧЕНИК",
    code: "◆",
    hex: "#06b6d4",
  },
  3: {
    bg: "bg-yellow-500/5",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    glow: "shadow-yellow-500/20",
    label: "МАСТЕР",
    code: "★",
    hex: "#eab308",
  },
  4: {
    bg: "bg-orange-500/5",
    text: "text-orange-400",
    border: "border-orange-500/30",
    glow: "shadow-orange-500/20",
    label: "ПРОФИ",
    code: "✦",
    hex: "#f97316",
  },
  5: {
    bg: "bg-red-500/5",
    text: "text-red-400",
    border: "border-red-500/30",
    glow: "shadow-red-500/20",
    label: "ЛЕГЕНДА",
    code: "✧",
    hex: "#ef4444",
  },
} as const;

// Опции фильтров (Filter Parameters)
export const SUBJECT_OPTIONS = [
  { value: "", label: "ВСЕ ПРЕДМЕТЫ" },
  { value: "informatics", label: "ИНФОРМАТИКА" },
  { value: "mathematics", label: "МАТЕМАТИКА" },
  { value: "physics", label: "ФИЗИКА" },
];

export const DIFFICULTY_OPTIONS = [
  { value: "", label: "ВСЕ УРОВНИ СЛОЖНОСТИ" },
  { value: "1", label: "◇ НОВИЧОК" },
  { value: "2", label: "◆ УЧЕНИК" },
  { value: "3", label: "★ МАСТЕР" },
  { value: "4", label: "✦ ПРОФИ" },
  { value: "5", label: "✧ ЛЕГЕНДА" },
];

// Helper функции для PvP компонентов
export function getDifficultyColor(difficulty: number): string {
  return DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS]?.hex || "#666";
}

export function getDifficultyLabel(difficulty: number): string {
  return DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS]?.label || "НЕИЗВЕСТНО";
}
