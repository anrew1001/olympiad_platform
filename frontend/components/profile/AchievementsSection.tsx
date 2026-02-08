/**
 * AchievementsSection.tsx
 * Компонент для отображения достижений в гибридном формате (grid + timeline)
 * Grid сверху для обзора, timeline снизу для хронологии разблокировок
 */

"use client";

import { motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";
import type { AchievementItem } from "@/lib/types/stats";

interface AchievementsSectionProps {
  achievements: AchievementItem[];
  loading?: boolean;
}

/**
 * Achievement icon based on type
 */
function getAchievementIcon(type: string): string {
  const iconMap: Record<string, string> = {
    first_solve: "🎯",
    solved_5: "🚀",
    solved_10: "⭐",
    solved_25: "👑",
    solved_50: "🔥",
    accuracy_80: "🎖️",
    accuracy_90: "💎",
    streak_3: "⚡",
    streak_7: "🌟",
    streak_15: "🏆",
    // Default for unknown types
  };
  return iconMap[type] || "🏅";
}

/**
 * Achievement card for grid display
 */
function AchievementCard({
  achievement,
  isUnlocked,
  index,
}: {
  achievement: AchievementItem;
  isUnlocked: boolean;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className={`relative p-4 border-2 rounded-lg transition-all ${
        isUnlocked
          ? "bg-gradient-to-br from-amber-500/10 to-yellow-600/10 border-yellow-500/60"
          : "bg-gray-800/20 border-gray-700/40 opacity-50"
      }`}
      style={{
        clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
      }}
    >
      {/* Unlock animation glow */}
      {isUnlocked && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.2, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "radial-gradient(circle, #FFD700 0%, transparent 70%)",
            clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
          }}
        />
      )}

      {/* Content */}
      <div className="relative z-10 text-center">
        {/* Icon */}
        <div className="text-4xl mb-2">{getAchievementIcon(achievement.type)}</div>

        {/* Title */}
        <h4 className="text-xs font-bold font-mono tracking-wider uppercase mb-1 text-white">
          {achievement.title}
        </h4>

        {/* Description */}
        <p className="text-xs text-gray-400 line-clamp-2 mb-2">
          {achievement.description}
        </p>

        {/* Unlock date (if unlocked) */}
        {isUnlocked && (
          <p className="text-[10px] font-mono text-yellow-600/70">
            {new Date(achievement.unlocked_at).toLocaleDateString("ru-RU", {
              month: "short",
              day: "numeric",
            })}
          </p>
        )}
      </div>
    </motion.div>
  );
}

/**
 * Timeline item for recent achievements
 */
function TimelineItem({
  achievement,
  isFirst,
  index,
}: {
  achievement: AchievementItem;
  isFirst: boolean;
  index: number;
}) {
  const unlockDate = new Date(achievement.unlocked_at);
  const timeAgo = formatDistanceToNow(unlockDate, { addSuffix: true, locale: ru });

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className="flex gap-4"
    >
      {/* Timeline dot */}
      <div className="relative flex flex-col items-center">
        <motion.div
          animate={{
            scale: isFirst ? [1, 1.3, 1] : 1,
            opacity: isFirst ? [1, 0.6, 1] : 0.5,
          }}
          transition={{
            duration: 2,
            repeat: isFirst ? Infinity : 0,
          }}
          className="w-3 h-3 rounded-full bg-yellow-500"
          style={{
            boxShadow: `0 0 12px #FFD700, inset 0 0 6px #FFA500`,
          }}
        />
        {!isFirst && (
          <div className="w-[2px] h-12 bg-gradient-to-b from-yellow-500/50 to-transparent mt-1" />
        )}
      </div>

      {/* Timeline content */}
      <div className="pb-4 flex-1">
        <p className="font-mono text-sm font-bold text-white mb-1">
          {achievement.title}
        </p>
        <p className="text-xs text-gray-400 mb-1">
          {achievement.description}
        </p>
        <p className="text-xs font-mono text-yellow-600/60">
          {timeAgo}
        </p>
      </div>
    </motion.div>
  );
}

export function AchievementsSection({ achievements, loading }: AchievementsSectionProps) {
  if (loading) {
    return (
      <div className="space-y-8">
        {/* Grid skeleton */}
        <div>
          <p className="text-xs font-mono tracking-widest text-gray-500 mb-4">СЕТКА</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-800/30 animate-pulse rounded-lg border border-gray-700/30" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (achievements.length === 0) {
    return (
      <div className="rounded-lg border border-gray-700/50 bg-gray-800/20 p-8 text-center">
        <p className="text-gray-400 font-mono text-sm">
          ДОСТИЖЕНИЯ БУДУТ РАЗБЛОКИРОВАНЫ
        </p>
        <p className="text-gray-500 font-mono text-xs mt-2">
          Продолжайте решать задачи для получения новых достижений
        </p>
      </div>
    );
  }

  // Sort achievements: unlocked first (by unlock date desc), then locked
  const unlockedAchievements = achievements.filter((a) => a.unlocked_at);
  const lockedAchievements = achievements.filter((a) => !a.unlocked_at);
  const sortedAchievements = [
    ...unlockedAchievements.sort((a, b) =>
      new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime()
    ),
    ...lockedAchievements,
  ];

  // Timeline shows only unlocked achievements (max 5 most recent)
  const timelineAchievements = unlockedAchievements
    .sort((a, b) => new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime())
    .slice(0, 5);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-10"
    >
      {/* Grid Section */}
      <div>
        <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-4">
          Все достижения ({unlockedAchievements.length} разблокировано)
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {sortedAchievements.map((achievement, idx) => (
            <AchievementCard
              key={achievement.type}
              achievement={achievement}
              isUnlocked={!!achievement.unlocked_at}
              index={idx}
            />
          ))}
        </div>
      </div>

      {/* Timeline Section (only if there are unlocked achievements) */}
      {timelineAchievements.length > 0 && (
        <div className="border-t border-gray-700/30 pt-8">
          <h3 className="text-xs font-mono tracking-widest uppercase text-gray-400 mb-6">
            Недавние разблокировки
          </h3>
          <div className="space-y-2">
            {timelineAchievements.map((achievement, idx) => (
              <TimelineItem
                key={achievement.type}
                achievement={achievement}
                isFirst={idx === 0}
                index={idx}
              />
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
