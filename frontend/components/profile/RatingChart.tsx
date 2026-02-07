/**
 * RatingChart.tsx
 * Интерактивный график изменения рейтинга с использованием recharts
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
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6">
        <p className="text-center text-gray-600 dark:text-gray-400">
          Недостаточно данных для отображения графика
        </p>
      </div>
    );
  }

  const minRating = Math.min(...data.map((d) => d.rating)) - 10;
  const maxRating = Math.max(...data.map((d) => d.rating)) + 10;

  return (
    <div className="rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        История рейтинга
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
          <XAxis
            dataKey="created_at"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getDate()}.${d.getMonth() + 1}`;
            }}
            stroke="#9ca3af"
          />
          <YAxis
            domain={[minRating, maxRating]}
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            label={{ value: "Рейтинг", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #e5e7eb",
              borderRadius: "0.5rem",
            }}
            labelFormatter={(date: any) => {
              const d = new Date(date);
              return d.toLocaleDateString("ru-RU", {
                year: "numeric",
                month: "long",
                day: "numeric",
              });
            }}
            formatter={(value: any) => [value, "Рейтинг"]}
            cursor={{ stroke: "#3b82f6", strokeWidth: 2 }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12 }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="rating"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: "#3b82f6", r: 4 }}
            activeDot={{ r: 6 }}
            isAnimationActive={true}
            name="Рейтинг"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Статистика под графиком */}
      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-gray-200 dark:border-gray-700 pt-6">
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Минимальный</p>
          <p className="text-2xl font-bold text-red-600">
            {Math.min(...data.map((d) => d.rating))}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Текущий</p>
          <p className="text-2xl font-bold text-blue-600">
            {data[data.length - 1]?.rating || 0}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">Максимальный</p>
          <p className="text-2xl font-bold text-green-600">
            {Math.max(...data.map((d) => d.rating))}
          </p>
        </div>
      </div>
    </div>
  );
}
