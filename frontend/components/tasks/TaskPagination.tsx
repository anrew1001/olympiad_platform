/**
 * Tactical Grid Coordinate Navigation (Pagination)
 * Тактическая навигация по координатам сетки
 */

"use client";

import { motion } from "motion/react";
import { useRouter, useSearchParams } from "next/navigation";

interface TaskPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

export function TaskPagination({
  currentPage,
  totalPages,
  totalItems,
}: TaskPaginationProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const goToPage = (page: number) => {
    if (page < 1 || page > totalPages) return;

    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(page));
    router.push(`/tasks?${params.toString()}`);
  };

  /**
   * Генерация видимых номеров страниц с ellipsis
   */
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);

      if (currentPage > 3) {
        pages.push("...");
      }

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push("...");
      }

      pages.push(totalPages);
    }

    return pages;
  };

  if (totalPages <= 1) return null;

  const itemsStart = (currentPage - 1) * 20 + 1;
  const itemsEnd = Math.min(currentPage * 20, totalItems);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="relative"
    >
      {/* Container with tactical borders */}
      <div
        className="relative p-6 border border-gray-800 bg-black/40 backdrop-blur-sm"
        style={{
          clipPath: "polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)",
        }}
      >
        {/* Corner notches */}
        <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-cyan-500" style={{ boxShadow: "0 0 6px #06b6d4" }} />
        <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-cyan-500" style={{ boxShadow: "0 0 6px #06b6d4" }} />

        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          {/* Grid coordinates info */}
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="flex gap-1"
            >
              <div className="w-1.5 h-1.5 bg-[#00ff88]" style={{ boxShadow: "0 0 4px #00ff88" }} />
              <div className="w-1.5 h-1.5 bg-[#00ff88]/60" />
              <div className="w-1.5 h-1.5 bg-[#00ff88]/30" />
            </motion.div>
            <div className="font-mono text-sm">
              <span className="text-gray-500">КООРДИНАТЫ:</span>{" "}
              <span className="text-white font-semibold">{itemsStart}–{itemsEnd}</span>
              <span className="text-gray-600"> / </span>
              <span className="text-gray-400">{totalItems}</span>
            </div>
          </div>

          {/* Navigation controls */}
          <div className="flex items-center gap-2">
            {/* Previous */}
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className={`
                group relative h-10 px-4
                border font-mono text-xs tracking-wider
                transition-all duration-200
                ${
                  currentPage === 1
                    ? "border-gray-800 text-gray-700 cursor-not-allowed"
                    : "border-gray-700 text-gray-300 hover:border-[#0066FF] hover:text-[#0066FF]"
                }
              `}
              style={{
                clipPath: "polygon(6px 0, 100% 0, 100% 100%, 0 100%, 0 6px)",
              }}
              aria-label="Предыдущая страница"
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg width="8" height="12" viewBox="0 0 8 12" fill="none">
                  <path d="M6 2L2 6L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
                НАЗАД
              </span>
              {currentPage !== 1 && (
                <motion.div
                  whileHover={{ opacity: 0.1 }}
                  className="absolute inset-0 bg-[#0066FF]"
                />
              )}
            </button>

            {/* Page numbers */}
            <div className="flex gap-1">
              {getPageNumbers().map((page, i) =>
                typeof page === "number" ? (
                  <motion.button
                    key={i}
                    onClick={() => goToPage(page)}
                    whileHover={{ scale: page !== currentPage ? 1.05 : 1 }}
                    whileTap={{ scale: 0.95 }}
                    className={`
                      relative w-10 h-10
                      border font-mono text-sm
                      transition-all duration-200
                      ${
                        page === currentPage
                          ? "border-[#0066FF] bg-[#0066FF]/20 text-[#0066FF] font-bold"
                          : "border-gray-700 text-gray-400 hover:border-cyan-500 hover:text-cyan-400"
                      }
                    `}
                    style={{
                      clipPath: "polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)",
                      boxShadow: page === currentPage ? "0 0 15px rgba(0,102,255,0.3)" : "none",
                    }}
                    aria-label={`Страница ${page}`}
                    aria-current={page === currentPage ? "page" : undefined}
                  >
                    <span className="relative z-10">{page}</span>
                    {page === currentPage && (
                      <motion.div
                        animate={{
                          opacity: [0.2, 0.4, 0.2],
                        }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="absolute inset-0 bg-[#0066FF]"
                      />
                    )}
                  </motion.button>
                ) : (
                  <div
                    key={i}
                    className="w-10 h-10 flex items-center justify-center text-gray-700 font-mono"
                  >
                    {page}
                  </div>
                )
              )}
            </div>

            {/* Next */}
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={`
                group relative h-10 px-4
                border font-mono text-xs tracking-wider
                transition-all duration-200
                ${
                  currentPage === totalPages
                    ? "border-gray-800 text-gray-700 cursor-not-allowed"
                    : "border-gray-700 text-gray-300 hover:border-[#0066FF] hover:text-[#0066FF]"
                }
              `}
              style={{
                clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)",
              }}
              aria-label="Следующая страница"
            >
              <span className="relative z-10 flex items-center gap-2">
                ВПЕРЕД
                <svg width="8" height="12" viewBox="0 0 8 12" fill="none">
                  <path d="M2 2L6 6L2 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
              </span>
              {currentPage !== totalPages && (
                <motion.div
                  whileHover={{ opacity: 0.1 }}
                  className="absolute inset-0 bg-[#0066FF]"
                />
              )}
            </button>
          </div>
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
    </motion.div>
  );
}
