'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/lib/hooks/useAuth';
import { useMatchWebSocket } from '@/lib/hooks/useMatchWebSocket';
import { getMatch, type MatchDetailResponse } from '@/lib/api/pvp';
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
  const { user, isAuthenticated } = useAuth();
  const matchId = parseInt(params.id as string);

  // === Local State ===

  const [matchData, setMatchData] = useState<MatchDetailResponse | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [submissionStatus, setSubmissionStatus] = useState<'submitting' | 'correct' | 'incorrect'>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const {
    connectionState,
    matchState,
    opponentStatus,
    submitAnswer,
    canSubmit,
    isReady,
  } = useMatchWebSocket({
    matchId,
    // Передаём пустую строку пока matchData не загружен → WebSocket не подключается
    token: matchData ? (typeof window !== 'undefined' ? localStorage.getItem('access_token') || '' : '') : '',
    yourPlayerId: user?.id || 0,
    opponent: matchData?.player2 || null,
    initialTasks: matchData?.match_tasks || [],
    onMatchEnd: (result) => {
      console.log('[Match] Ended:', result);
      // Results overlay will show automatically via matchState.isFinished
    },
  });

  // === Handle Answer Submission ===

  const handleSubmitAnswer = (answer: string) => {
    if (!selectedTaskId || !canSubmit) return;

    setSubmissionStatus('submitting');

    const success = submitAnswer(selectedTaskId, answer);
    if (!success) {
      setSubmissionStatus(undefined);
      return;
    }

    // Simulate submission (real response comes via WebSocket)
    setTimeout(() => {
      // Will be updated by WebSocket answer_result event
      setSubmissionStatus(undefined);
      // Auto-select next unsolved task (optional)
      const nextUnsolved = matchData?.match_tasks.find(
        (t) => !matchState.yourSolvedTasks.has(t.task_id)
      );
      if (nextUnsolved) {
        setSelectedTaskId(nextUnsolved.task_id);
      }
    }, 500);
  };

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

  const isYouPlayer1 = matchData.player1.id === user?.id;
  const player1 = { ...matchData.player1, isYou: isYouPlayer1 };
  const player2 = matchData.player2 ? { ...matchData.player2, isYou: !isYouPlayer1 } : null;

  const yourScore = isYouPlayer1 ? matchData.player1_score : matchData.player2_score;
  const opponentScore = isYouPlayer1 ? matchData.player2_score : matchData.player1_score;

  const selectedTask = matchData.match_tasks.find((t) => t.task_id === selectedTaskId);

  // === Render ===

  return (
    <div className="min-h-screen bg-[#121212] relative">
      {/* Статичный grid background (без анимации для читабельности) */}
      <div
        className="fixed inset-0 opacity-[0.02] z-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(90deg, #0066FF 1px, transparent 1px),
            linear-gradient(0deg, #0066FF 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
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
              opponentSolvedCount={matchState.opponentSolvedTasks.size}
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
