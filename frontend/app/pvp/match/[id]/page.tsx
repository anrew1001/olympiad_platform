'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/hooks/useAuth';
import { useMatchWebSocket } from '@/lib/hooks/useMatchWebSocket';
import { getMatch, forfeitMatch, type MatchDetailResponse } from '@/lib/api/pvp';
import type { MatchTask, PlayerInfo } from '@/lib/types/websocket';
import { MatchHeader } from '@/components/pvp/MatchHeader';
import { TaskList } from '@/components/pvp/TaskList';
import { TaskViewer } from '@/components/pvp/TaskViewer';
import { MatchResults } from '@/components/pvp/MatchResults';
import { ConnectionStatus } from '@/components/pvp/ConnectionStatus';
import { DisconnectWarning } from '@/components/pvp/DisconnectWarning';
import { LoadingScreen } from '@/components/ui/LoadingScreen';

/**
 * Live PvP Match Page
 * Layout: Header (top) | TaskList (left) + TaskViewer (right)
 * Real-time WebSocket updates via useMatchWebSocket
 */
export default function PvPMatchPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, refreshUser } = useAuth();
  const matchId = parseInt(params.id as string);

  // === Local State ===

  const [matchData, setMatchData] = useState<MatchDetailResponse | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [submissionStatus, setSubmissionStatus] = useState<'submitting' | 'correct' | 'incorrect'>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Timeout ref для автоочистки feedback иконки
  const feedbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // === Auth Check ===

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login?returnUrl=/pvp');
    }
  }, [isAuthenticated, router]);

  // === Load Match Data ===

  useEffect(() => {
    if (!matchId || !isAuthenticated) return;

    const loadMatch = async () => {
      try {
        setLoading(true);
        const data = await getMatch(matchId);
        setMatchData(data);
        // Select first task by default
        if (data.match_tasks.length > 0) {
          setSelectedTaskId(data.match_tasks[0].task_id);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load match';
        if (errorMsg === 'NOT_PARTICIPANT') {
          router.push('/pvp');
        } else if (errorMsg === 'MATCH_NOT_FOUND') {
          setError('Матч не найден');
        } else {
          setError(errorMsg);
        }
      } finally {
        setLoading(false);
      }
    };

    loadMatch();
  }, [matchId, isAuthenticated, router]);

  // === WebSocket Setup ===

  // Определить кто вы - player1 или player2
  const isYouPlayer1 = matchData ? matchData.player1.id === user?.id : false;

  const {
    connectionState,
    matchState,
    opponentStatus,
    submitAnswer,
    canSubmit,
    isReady,
    submittedTasks,
  } = useMatchWebSocket({
    matchId,
    // Передаём пустую строку пока matchData не загружен → WebSocket не подключается
    token: matchData ? (typeof window !== 'undefined' ? localStorage.getItem('access_token') || '' : '') : '',
    yourPlayerId: user?.id || 0,
    opponent: matchData?.player2 || null,
    initialTasks: matchData?.match_tasks || [],
    isYouPlayer1, // передаём чтобы правильно определить rating_change
    onMatchEnd: async (result) => {
      // Обновить рейтинг пользователя в navbar сразу после матча
      try {
        await refreshUser();
      } catch (err) {
        // Failed to refresh user rating
      }
    },
    onAnswerResult: (taskId, isCorrect) => {
      // Обработка feedback от сервера
      // Установить статус correct/incorrect
      setSubmissionStatus(isCorrect ? 'correct' : 'incorrect');

      // Очистить предыдущий таймаут если был
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }

      // Автоочистка feedback через 2.5 секунды
      feedbackTimeoutRef.current = setTimeout(() => {
        setSubmissionStatus(undefined);
      }, 2500);
    },
  });

  // === Handle Answer Submission ===

  const handleSubmitAnswer = (answer: string) => {
    if (!selectedTaskId || !canSubmit) return;

    // Разрешаем повторные попытки - backend блокирует только правильные ответы

    // Очистить предыдущий feedback если был
    if (feedbackTimeoutRef.current) {
      clearTimeout(feedbackTimeoutRef.current);
    }

    setSubmissionStatus('submitting');

    const success = submitAnswer(selectedTaskId, answer);
    if (!success) {
      setSubmissionStatus(undefined);
      return;
    }

    // Теперь НЕ очищаем submissionStatus здесь!
    // Он будет обновлён через onAnswerResult callback когда сервер ответит
  };

  // === Handle Forfeit ===

  const handleForfeit = async () => {
    try {
      await forfeitMatch(matchId);
      // WebSocket отправит match_end event автоматически
      // или можно перезагрузить страницу
      setTimeout(() => {
        router.push('/pvp');
      }, 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка при сдаче');
    }
  };

  // === Cleanup ===

  useEffect(() => {
    return () => {
      // Очистить таймаут feedback при размонтировании
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }
    };
  }, []);

  // === Render Loading ===

  if (!isAuthenticated) {
    return null; // Redirecting in effect
  }

  if (loading) {
    return <LoadingScreen text="ЗАГРУЖАЕМ МАТЧ..." />;
  }

  if (error || !matchData) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <motion.div
          className="text-center space-y-4 max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-lg font-mono text-[#ff3b30]">✗ {error || 'Ошибка загрузки матча'}</p>
          <button
            onClick={() => router.push('/pvp')}
            className="px-6 py-2 text-sm font-mono text-white border border-[#0066FF] hover:bg-[#0066FF]/10 transition-all"
          >
            Вернуться на поиск
          </button>
        </motion.div>
      </div>
    );
  }

  // === Determine Player Order ===

  // isYouPlayer1 уже определён выше для WebSocket hook
  const player1 = { ...matchData.player1, isYou: isYouPlayer1 };
  const player2 = matchData.player2 ? { ...matchData.player2, isYou: !isYouPlayer1 } : null;

  const yourScore = isYouPlayer1 ? matchData.player1_score : matchData.player2_score;
  const opponentScore = isYouPlayer1 ? matchData.player2_score : matchData.player1_score;

  const selectedTask = matchData.match_tasks.find((t) => t.task_id === selectedTaskId);

  // === Render ===

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ backgroundColor: '#121212' }}>
      {/* Electrical field background */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        {/* Subtle glow animation */}
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{
              opacity: [0, 0.012, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 6 + i * 1.5,
              repeat: Infinity,
              delay: i * 2,
              ease: 'easeInOut',
            }}
            className="absolute"
            style={{
              width: '250px',
              height: '250px',
              left: `${15 + i * 35}%`,
              top: `${5 + i * 25}%`,
              background: `radial-gradient(circle, rgba(0, 150, 199, 0.12) 0%, transparent 70%)`,
              filter: 'blur(50px)',
            }}
          />
        ))}
      </div>

      {/* Grid background */}
      <div className="fixed inset-0 opacity-[0.01] pointer-events-none -z-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #00d4ff 1px, transparent 1px),
              linear-gradient(0deg, #00d4ff 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* Scanlines overlay для атмосферы */}
      <div
        className="fixed inset-0 pointer-events-none -z-10 opacity-[0.015]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 212, 255, 0.02) 2px, rgba(0, 212, 255, 0.02) 4px)',
        }}
      />

      {/* Connection status */}
      <ConnectionStatus state={connectionState} />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <MatchHeader
          player1={player1}
          player2={player2 || ({ id: 0, username: 'Ожидание...', rating: 0, isYou: false } as any)}
          score1={isYouPlayer1 ? matchState.yourScore : matchState.opponentScore}
          score2={isYouPlayer1 ? matchState.opponentScore : matchState.yourScore}
          timeElapsed={matchState.timeElapsed}
          opponentDisconnected={opponentStatus.disconnectWarning}
          onForfeit={handleForfeit}
          matchFinished={matchState.isFinished}
        />

        {/* Disconnect Warning */}
        <AnimatePresence>
          {opponentStatus.disconnectWarning && (
            <DisconnectWarning
              secondsRemaining={opponentStatus.disconnectWarning.secondsRemaining}
              opponentName={isYouPlayer1 ? player2?.username || 'Соперник' : player1.username}
            />
          )}
        </AnimatePresence>

        {/* Task area - Asymmetric grid */}
        <motion.div
          className="grid grid-cols-[300px_1fr] gap-6 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {/* Left: Task List */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <TaskList
              tasks={matchData.match_tasks}
              yourSolvedTasks={matchState.yourSolvedTasks}
              opponentSolvedTasks={matchState.opponentSolvedTasks}
              selectedTaskId={selectedTaskId}
              onSelectTask={setSelectedTaskId}
            />
          </motion.div>

          {/* Right: Task Viewer */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
          >
            <TaskViewer
              task={selectedTask || null}
              onSubmit={handleSubmitAnswer}
              submissionStatus={submissionStatus}
              disabled={!isReady || matchState.isFinished}
            />
          </motion.div>
        </motion.div>
      </div>

      {/* Match Results Overlay */}
      <AnimatePresence>
        {matchState.isFinished && matchState.result && (
          <MatchResults
            outcome={matchState.result.outcome}
            finalScores={{
              player1_score: isYouPlayer1 ? matchState.yourScore : matchState.opponentScore,
              player2_score: isYouPlayer1 ? matchState.opponentScore : matchState.yourScore,
            }}
            ratingChange={matchState.result.ratingChange}
            newRating={matchState.result.newRating}
            reason={matchState.result.reason}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
