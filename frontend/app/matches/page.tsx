/**
 * /matches
 * Полная страница истории PvP матчей с фильтрами и пагинацией
 */

export default function MatchesPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            История матчей
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Все ваши PvP матчи с деталями и результатами
          </p>
        </div>

        {/* История матчей */}
        <div className="space-y-6">
          {/* Компонент будет добавлен в следующей итерации */}
          <p className="text-gray-600 dark:text-gray-400">
            Перейдите на страницу профиля для просмотра истории матчей.
          </p>
        </div>
      </div>
    </div>
  );
}
