/**
 * MatchCard.tsx
 * Карточка одного матча с основной информацией
 * - Результат (Победа/Поражение/Ничья)
 * - Данные соперника
 * - Счёт
 * - Изменение рейтинга
 * - Дата матча
 */

"use client";

import { format } from "date-fns";
import { ru } from "date-fns/locale";
import type { MatchHistoryItem } from "@/lib/types/match";

interface MatchCardProps {
  match: MatchHistoryItem;
  onClick: () => void;
}

export function MatchCard({ match, onClick }: MatchCardProps) {
  const isWon = match.result === "won";
  const isDraw = match.result === "draw";
  const isLost = match.result === "lost";

  // Определить цвет результата
  const resultColor = isWon ? "bg-green-50 border-green-200" : isDraw ? "bg-gray-50 border-gray-200" : "bg-red-50 border-red-200";
  const resultTextColor = isWon ? "text-green-700" : isDraw ? "text-gray-700" : "text-red-700";
  const ratingChangeColor = (match.my_rating_change ?? 0) > 0 ? "text-green-600" : (match.my_rating_change ?? 0) < 0 ? "text-red-600" : "text-gray-600";

  // Форматировать дату
  const finishedDate = match.finished_at
    ? format(new Date(match.finished_at), "dd MMM yyyy, HH:mm", { locale: ru })
    : format(new Date(match.created_at), "dd MMM yyyy, HH:mm", { locale: ru });

  // Результат в виде строки
  const resultLabel = isWon ? "Победа" : isDraw ? "Ничья" : "Поражение";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border ${resultColor} p-4 transition-all hover:shadow-md active:shadow-sm`}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Левая часть: результат + дата */}
        <div className="flex flex-col gap-1">
          <span className={`inline-block w-fit rounded px-2 py-1 text-sm font-semibold ${resultTextColor}`}>
            {resultLabel}
          </span>
          <span className="text-xs text-gray-500">{finishedDate}</span>
        </div>

        {/* Центр: информация о сопернике и счёте */}
        <div className="flex-1 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-900">{match.opponent.username}</p>
              <p className="text-xs text-gray-600">Рейтинг: {match.opponent.rating}</p>
            </div>

            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {match.my_score} : {match.opponent_score}
              </p>
              <p className="text-xs text-gray-600">счёт</p>
            </div>
          </div>
        </div>

        {/* Правая часть: изменение рейтинга */}
        {match.my_rating_change !== null && (
          <div className="flex flex-col items-end gap-1">
            <p className={`text-xl font-bold ${ratingChangeColor}`}>
              {match.my_rating_change > 0 ? "+" : ""}
              {match.my_rating_change}
            </p>
            <p className="text-xs text-gray-600">рейтинг</p>
          </div>
        )}
      </div>
    </button>
  );
}
