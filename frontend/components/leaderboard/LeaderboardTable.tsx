"use client";

import { LeaderboardEntry } from "@/lib/types/leaderboard";

interface Props {
  /** Записи таблицы лидеров */
  entries: LeaderboardEntry[];
  /** Запись текущего пользователя (если не в топе) */
  currentUserEntry?: LeaderboardEntry | null;
}

/**
 * Компонент таблицы лидеров
 *
 * Отображает:
 * - Позицию с медалями для топ-3 (🥇🥈🥉)
 * - Имя игрока, рейтинг, матчи, процент побед
 * - Текущего пользователя выделенным (фиолетовый цвет)
 * - Если текущий пользователь не в топе, показывает его позицию внизу
 */
export default function LeaderboardTable({
  entries,
  currentUserEntry,
}: Props) {
  const getMedalEmoji = (position: number): string => {
    switch (position) {
      case 1:
        return "🥇";
      case 2:
        return "🥈";
      case 3:
        return "🥉";
      default:
        return "";
    }
  };

  return (
    <div className="w-full bg-black rounded-lg overflow-hidden border border-gray-800">
      {/* Заголовок таблицы */}
      <div className="grid grid-cols-12 gap-4 bg-gray-900 p-4 border-b border-gray-800 font-semibold text-sm text-gray-300">
        <div className="col-span-1 text-center">#</div>
        <div className="col-span-4">Игрок</div>
        <div className="col-span-2 text-right">Рейтинг</div>
        <div className="col-span-2 text-right">Матчи</div>
        <div className="col-span-3 text-right">Win %</div>
      </div>

      {/* Строки таблицы */}
      <div className="divide-y divide-gray-800">
        {entries.map((entry) => (
          <div
            key={entry.user_id}
            className={`
              grid grid-cols-12 gap-4 p-4 transition-colors
              ${
                entry.is_current_user
                  ? "bg-purple-900/20 border-l-4 border-purple-500"
                  : "hover:bg-gray-900"
              }
            `}
          >
            {/* Позиция с медалью */}
            <div className="col-span-1 text-center font-bold">
              {getMedalEmoji(entry.position) || entry.position}
            </div>

            {/* Имя пользователя */}
            <div
              className={`col-span-4 ${
                entry.is_current_user ? "text-purple-400 font-semibold" : ""
              }`}
            >
              {entry.username}
              {entry.is_current_user && " (Вы)"}
            </div>

            {/* Рейтинг */}
            <div className="col-span-2 text-right text-yellow-400 font-semibold">
              {entry.rating}
            </div>

            {/* Количество матчей */}
            <div className="col-span-2 text-right text-gray-400">
              {entry.matches_played}
            </div>

            {/* Win rate */}
            <div className="col-span-3 text-right">
              <span
                className={`
                  font-semibold
                  ${
                    entry.win_rate >= 70
                      ? "text-green-400"
                      : entry.win_rate >= 50
                        ? "text-blue-400"
                        : "text-red-400"
                  }
                `}
              >
                {entry.win_rate.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Текущий пользователь, если не в топе */}
      {currentUserEntry && !entries.some((e) => e.user_id === currentUserEntry.user_id) && (
        <>
          <div className="px-4 py-2 bg-gray-900 text-center text-gray-500 text-xs">
            Ваша позиция
          </div>
          <div
            className={`
              grid grid-cols-12 gap-4 p-4 bg-purple-900/20 border-l-4 border-purple-500
            `}
          >
            <div className="col-span-1 text-center font-bold text-purple-400">
              {currentUserEntry.position}
            </div>
            <div className="col-span-4 text-purple-400 font-semibold">
              {currentUserEntry.username} (Вы)
            </div>
            <div className="col-span-2 text-right text-yellow-400 font-semibold">
              {currentUserEntry.rating}
            </div>
            <div className="col-span-2 text-right text-gray-400">
              {currentUserEntry.matches_played}
            </div>
            <div className="col-span-3 text-right">
              <span className="font-semibold text-blue-400">
                {currentUserEntry.win_rate.toFixed(1)}%
              </span>
            </div>
          </div>
        </>
      )}

      {/* Пустое состояние */}
      {entries.length === 0 && !currentUserEntry && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">Будьте первым в рейтинге!</p>
          <p className="text-sm mt-2">Сыграйте свой первый матч</p>
        </div>
      )}

      {/* Если текущий пользователь с 0 матчами */}
      {entries.length > 0 && !currentUserEntry && (
        <div className="px-4 py-3 bg-gray-900 border-t border-gray-800 text-center text-gray-400 text-sm">
          Сыграйте первый матч, чтобы попасть в рейтинг
        </div>
      )}
    </div>
  );
}
