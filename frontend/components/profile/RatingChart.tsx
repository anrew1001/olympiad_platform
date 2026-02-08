/**
 * RatingChart.tsx
 * Интерактивный график изменения рейтинга с использованием recharts
 * Cyberpunk стиль с неоновыми акцентами
 */

"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { RatingHistoryPoint } from "@/lib/types/match";

interface RatingChartProps {
  data: RatingHistoryPoint[];
}

export function RatingChart({ data }: RatingChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="relative p-8 border border-[#333] bg-[#1a1a1a]"
        style={{
          clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
        }}
      >
        <p className="text-center text-gray-500 font-mono text-sm tracking-wider">
          НЕДОСТАТОЧНО ДАННЫХ ДЛЯ ГРАФИКА
        </p>
      </div>
    );
  }

  const minRating = Math.min(...data.map((d) => d.rating)) - 10;
  const maxRating = Math.max(...data.map((d) => d.rating)) + 10;
  const currentRating = data[data.length - 1]?.rating || 0;
  const initialRating = data[0]?.rating || 0;
  const ratingChange = currentRating - initialRating;

  return (
    <div
      className="relative p-6 border border-[#0066FF]/30 bg-[#0a0f1a]"
      style={{
        clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
      }}
    >
      {/* Corner bracket */}
      <div
        className="absolute top-0 right-0 w-3 h-3 bg-[#0066FF]"
        style={{ boxShadow: '0 0 10px #0066FF' }}
      />

      <h3 className="text-sm font-mono tracking-widest uppercase text-[#0066FF] mb-6">
        ИСТОРИЯ РЕЙТИНГА
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333333" opacity={0.3} />
          <XAxis
            dataKey="created_at"
            tick={{ fontSize: 11, fill: '#666', fontFamily: 'monospace' }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getDate()}.${d.getMonth() + 1}`;
            }}
            stroke="#333"
          />
          <YAxis
            domain={[minRating, maxRating]}
            tick={{ fontSize: 11, fill: '#666', fontFamily: 'monospace' }}
            stroke="#333"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #0066FF',
              borderRadius: 0,
              fontFamily: 'monospace',
              fontSize: 12,
            }}
            labelStyle={{ color: '#0066FF' }}
            itemStyle={{ color: '#00ff88' }}
            labelFormatter={(date: any) => {
              const d = new Date(date);
              return d.toLocaleDateString("ru-RU", {
                year: "numeric",
                month: "long",
                day: "numeric",
              });
            }}
            formatter={(value: any) => [value, "Рейтинг"]}
            cursor={{ stroke: '#0066FF', strokeWidth: 1, strokeDasharray: '3 3' }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, fontFamily: 'monospace', color: '#666' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="rating"
            stroke="#00ff88"
            strokeWidth={2}
            dot={{ fill: '#0066FF', r: 3, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: '#00ff88', stroke: '#00ff88', strokeWidth: 2 }}
            isAnimationActive={true}
            name="Рейтинг"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Статистика под графиком */}
      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-[#333] pt-6">
        {/* Минимальный */}
        <div className="text-center">
          <p className="text-[10px] font-mono tracking-wider uppercase text-[#ff3b30] mb-1">
            МИНИМУМ
          </p>
          <p className="text-2xl font-bold font-mono text-[#ff3b30]">
            {Math.min(...data.map((d) => d.rating))}
          </p>
        </div>

        {/* Текущий */}
        <div className="text-center">
          <p className="text-[10px] font-mono tracking-wider uppercase text-[#0066FF] mb-1">
            ТЕКУЩИЙ
          </p>
          <p className="text-2xl font-bold font-mono text-[#0066FF]">
            {currentRating}
          </p>
          {ratingChange !== 0 && (
            <p className={`text-xs font-mono mt-1 ${ratingChange > 0 ? 'text-[#00ff88]' : 'text-[#ff3b30]'}`}>
              {ratingChange > 0 ? '+' : ''}{ratingChange}
            </p>
          )}
        </div>

        {/* Максимальный */}
        <div className="text-center">
          <p className="text-[10px] font-mono tracking-wider uppercase text-[#00ff88] mb-1">
            МАКСИМУМ
          </p>
          <p className="text-2xl font-bold font-mono text-[#00ff88]">
            {Math.max(...data.map((d) => d.rating))}
          </p>
        </div>
      </div>
    </div>
  );
}
