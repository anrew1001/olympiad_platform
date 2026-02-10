/**
 * MatchCard.tsx
 * Карточка одного матча с основной информацией
 * Cyberpunk стиль с неоновыми акцентами
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

  // Цвета в зависимости от результата
  const resultColor = isWon ? "#00ff88" : isDraw ? "#999" : "#ff3b30";
  const borderColor = isWon ? "#00ff8840" : isDraw ? "#99999940" : "#ff3b3040";
  const bgColor = isWon ? "#001a0f" : isDraw ? "#1a1a1a" : "#1a0a0a";

  // Форматировать дату
  const finishedDate = match.finished_at
    ? format(new Date(match.finished_at), "dd MMM yyyy, HH:mm", { locale: ru })
    : format(new Date(match.created_at), "dd MMM yyyy, HH:mm", { locale: ru });

  // Результат в виде строки
  const resultLabel = isWon ? "ПОБЕДА" : isDraw ? "НИЧЬЯ" : "ПОРАЖЕНИЕ";

  return (
    <button
      onClick={onClick}
      className="w-full text-left relative border transition-all hover:brightness-110"
      style={{
        backgroundColor: bgColor,
        borderColor: borderColor,
        clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))',
      }}
    >
      {/* Corner bracket */}
      <div
        className="absolute top-0 right-0 w-2 h-2"
        style={{
          backgroundColor: resultColor,
          boxShadow: `0 0 8px ${resultColor}`,
        }}
      />

      <div className="p-4 flex items-center justify-between gap-4">
        {/* Левая часть: результат + дата */}
        <div className="flex flex-col gap-2">
          <span
            className="inline-block w-fit px-3 py-1 text-[10px] font-mono font-bold tracking-wider"
            style={{
              color: resultColor,
              backgroundColor: bgColor,
              border: `1px solid ${resultColor}`,
              clipPath: 'polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))',
            }}
          >
            {resultLabel}
          </span>
          <span className="text-[10px] font-mono text-gray-600">{finishedDate}</span>
        </div>

        {/* Центр: информация о сопернике и счёте */}
        <div className="flex-1 flex items-center justify-between gap-6">
          <div>
            <p className="font-mono text-sm font-bold text-white">{match.opponent.username}</p>
            <p className="text-[10px] font-mono text-gray-600">Рейтинг: {match.opponent.rating}</p>
          </div>

          <div className="text-center">
            <p className="text-2xl font-bold font-mono text-white">
              {match.my_score} : {match.opponent_score}
            </p>
            <p className="text-[9px] font-mono text-gray-600 uppercase tracking-wider">счёт</p>
          </div>
        </div>

        {/* Правая часть: изменение рейтинга */}
        {match.my_rating_change !== null && (
          <div className="flex flex-col items-end gap-1">
            <p
              className="text-xl font-bold font-mono"
              style={{
                color: match.my_rating_change > 0 ? "#00ff88" : match.my_rating_change < 0 ? "#ff3b30" : "#999",
              }}
            >
              {match.my_rating_change > 0 ? "+" : ""}
              {match.my_rating_change}
            </p>
            <p className="text-[9px] font-mono text-gray-600 uppercase tracking-wider">рейтинг</p>
          </div>
        )}
      </div>
    </button>
  );
}
