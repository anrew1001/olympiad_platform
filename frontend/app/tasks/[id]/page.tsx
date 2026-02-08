/**
 * Mission Detail Page (Placeholder)
 * Детальная страница миссии - будет реализована в следующей задаче
 */

"use client";

import { useParams, useRouter } from "next/navigation";
import { motion } from "motion/react";

export default function MissionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = params.id;

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl w-full"
      >
        {/* Tactical container */}
        <div
          className="relative p-12 border border-[#0066FF]/30 bg-black/60 backdrop-blur-md"
          style={{
            clipPath: "polygon(0 0, calc(100% - 24px) 0, 100% 24px, 100% 100%, 24px 100%, 0 calc(100% - 24px))",
            boxShadow: "0 0 30px rgba(0,102,255,0.2), inset 0 0 40px rgba(0,102,255,0.05)",
          }}
        >
          {/* Corner notches */}
          <div className="absolute inset-0 pointer-events-none">
            <div
              className="absolute top-0 left-0 w-6 h-6"
              style={{
                borderTop: "3px solid #0066FF",
                borderLeft: "3px solid #0066FF",
                boxShadow: "0 0 10px #0066FF",
              }}
            />
            <div
              className="absolute top-0 right-0 w-6 h-6"
              style={{
                borderTop: "3px solid #0066FF",
                borderRight: "3px solid #0066FF",
                boxShadow: "0 0 10px #0066FF",
              }}
            />
            <div
              className="absolute bottom-0 left-0 w-6 h-6"
              style={{
                borderBottom: "3px solid #0066FF",
                borderLeft: "3px solid #0066FF",
                boxShadow: "0 0 10px #0066FF",
              }}
            />
            <div
              className="absolute bottom-0 right-0 w-6 h-6"
              style={{
                borderBottom: "3px solid #0066FF",
                borderRight: "3px solid #0066FF",
                boxShadow: "0 0 10px #0066FF",
              }}
            />
          </div>

          {/* Content */}
          <div className="relative z-10 text-center space-y-6">
            {/* Mission ID */}
            <div className="flex items-center justify-center gap-3 mb-8">
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-3 h-3 bg-yellow-400"
                style={{ boxShadow: "0 0 10px #facc15" }}
              />
              <span className="font-mono text-sm text-yellow-400 tracking-[0.3em]">
                MISSION #{missionId}
              </span>
            </div>

            {/* Icon */}
            <motion.div
              animate={{
                rotateY: [0, 360],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "linear",
              }}
              className="text-6xl mb-6"
            >
              🚧
            </motion.div>

            {/* Message */}
            <h1
              className="text-3xl font-bold text-white mb-4"
              style={{
                fontFamily: "Sora, sans-serif",
                textShadow: "0 0 20px rgba(0,102,255,0.3)",
              }}
            >
              В РАЗРАБОТКЕ
            </h1>
            <p className="text-sm font-mono text-gray-400 tracking-wide max-w-md mx-auto">
              Детальная страница миссии будет реализована в следующей задаче разработки
            </p>

            {/* Back button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => router.push("/tasks")}
              className="mt-8 group relative h-12 px-8 border-2 border-[#0066FF] bg-[#0066FF]/10 text-white font-mono text-sm tracking-wider uppercase transition-all duration-300 hover:bg-[#0066FF]/20"
              style={{
                clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)",
              }}
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M8 2L4 6L8 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
                ВЕРНУТЬСЯ К МИССИЯМ
              </span>
              <motion.div
                whileHover={{ opacity: 0.1 }}
                className="absolute inset-0 bg-[#0066FF]"
              />
            </motion.button>
          </div>

          {/* Scanning line */}
          <motion.div
            animate={{
              x: ["-100%", "200%"],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "linear",
            }}
            className="absolute top-0 left-0 w-1/3 h-full opacity-5"
            style={{
              background: "linear-gradient(90deg, transparent, #0066FF, transparent)",
            }}
          />
        </div>

        {/* System info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 text-center text-xs font-mono text-gray-700 tracking-wider"
        >
          TACTICAL MISSION SYSTEM v2.0.0
        </motion.div>
      </motion.div>

      {/* Background grid */}
      <div className="fixed inset-0 opacity-[0.01] pointer-events-none -z-10">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #0066FF 1px, transparent 1px),
              linear-gradient(0deg, #0066FF 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />
      </div>
    </div>
  );
}
