'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import { loginUser } from '@/lib/api/auth';
import { APIError } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import type { LoginRequest } from '@/types/auth';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();

  // Form state
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const showRegisteredMessage = searchParams.get('registered') === 'true';

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace('/');
    }
  }, [isAuthenticated, authLoading, router]);

  // Form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const { access_token } = await loginUser(formData);
      await login(access_token);

      setShowSuccess(true);
      setTimeout(() => {
        router.push('/');
      }, 1200);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('Произошла непредвиденная ошибка');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Input change handler
  const handleChange = (field: keyof LoginRequest) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({ ...formData, [field]: e.target.value });
    if (error) setError('');
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.15,
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 12 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
    },
  };

  const successVariants = {
    hidden: { scale: 0.85, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        duration: 0.5,
        ease: [0.34, 1.56, 0.64, 1],
      },
    },
  };

  // Loading state during auth check
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
          className="h-10 w-10 rounded-full border-2 border-[#0066FF] border-t-transparent"
        />
      </div>
    );
  }

  // Success overlay with "match won" animation
  if (showSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a] relative overflow-hidden">
        {/* Radial pulse background */}
        <motion.div
          initial={{ scale: 0, opacity: 0.8 }}
          animate={{ scale: 3, opacity: 0 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <div className="h-96 w-96 rounded-full bg-[#0066FF] blur-3xl" />
        </motion.div>

        <motion.div
          variants={successVariants}
          initial="hidden"
          animate="visible"
          className="text-center z-10 relative"
        >
          {/* Checkmark with charge-up effect */}
          <motion.div
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
            className="mx-auto mb-6 relative"
          >
            <svg width="80" height="80" viewBox="0 0 80 80" className="mx-auto">
              <motion.circle
                cx="40"
                cy="40"
                r="35"
                stroke="#0066FF"
                strokeWidth="3"
                fill="none"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
              />
              <motion.path
                d="M 25 40 L 35 50 L 55 30"
                stroke="#00ff88"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.4, delay: 0.3 }}
              />
            </svg>
            {/* Electric glow */}
            <motion.div
              animate={{
                boxShadow: [
                  '0 0 20px rgba(0, 102, 255, 0.4)',
                  '0 0 40px rgba(0, 102, 255, 0.8)',
                  '0 0 20px rgba(0, 102, 255, 0.4)',
                ],
              }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 rounded-full pointer-events-none"
            />
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-2xl font-bold text-[#00ff88] font-mono tracking-wide"
          >
            ВХОД ВЫПОЛНЕН
          </motion.p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a] relative overflow-hidden px-4">
      {/* Animated grid background */}
      <div className="absolute inset-0 opacity-[0.03]">
        <motion.div
          animate={{
            backgroundPosition: ['0% 0%', '100% 100%'],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'linear',
          }}
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(90deg, #0066FF 1px, transparent 1px),
              linear-gradient(0deg, #0066FF 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      {/* Scan line effect */}
      <motion.div
        animate={{
          y: ['0%', '100%'],
          opacity: [0, 0.15, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'linear',
        }}
        className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#0066FF] to-transparent"
        style={{
          boxShadow: '0 0 20px rgba(0, 102, 255, 0.8)',
        }}
      />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="w-full max-w-[420px] relative z-10"
      >
        {/* Logo with targeting reticle */}
        <motion.div variants={itemVariants} className="mb-10 relative">
          <div className="relative inline-block">
            <h1 className="text-6xl font-bold text-white font-mono tracking-tighter">
              OLYMPEIT
            </h1>
            {/* Corner brackets (targeting reticle) */}
            <div className="absolute -inset-3 pointer-events-none">
              {/* Top-left */}
              <motion.div
                animate={{
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute top-0 left-0 w-4 h-4 border-l-2 border-t-2 border-[#0066FF]"
              />
              {/* Top-right */}
              <motion.div
                animate={{
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                className="absolute top-0 right-0 w-4 h-4 border-r-2 border-t-2 border-[#0066FF]"
              />
              {/* Bottom-left */}
              <motion.div
                animate={{
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                className="absolute bottom-0 left-0 w-4 h-4 border-l-2 border-b-2 border-[#0066FF]"
              />
              {/* Bottom-right */}
              <motion.div
                animate={{
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{ duration: 2, repeat: Infinity, delay: 1.5 }}
                className="absolute bottom-0 right-0 w-4 h-4 border-r-2 border-b-2 border-[#0066FF]"
              />
            </div>
          </div>
          <p className="text-sm text-[#666] mt-2 tracking-[0.2em] font-mono uppercase">
            Соревновательная арена
          </p>
        </motion.div>

        {/* Registration Success Message */}
        <AnimatePresence>
          {showRegisteredMessage && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginBottom: 0 }}
              animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="relative border border-[#00ff88] bg-[#00ff88]/5 p-4">
                <div className="absolute top-0 left-0 w-1 h-full bg-[#00ff88]" />
                <p className="text-sm text-[#00ff88] font-mono pl-3">
                  ✓ Регистрация успешна! Войдите в систему
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginBottom: 0 }}
              animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="relative border border-[#ff3b30] bg-[#ff3b30]/5 p-4">
                <div className="absolute top-0 left-0 w-1 h-full bg-[#ff3b30]" />
                <p className="text-sm text-[#ff3b30] font-mono pl-3">
                  ✗ {error}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Form */}
        <motion.form
          onSubmit={handleSubmit}
          className="space-y-8"
          variants={containerVariants}
        >
          {/* Email Field */}
          <motion.div variants={itemVariants} className="relative group">
            <label className="block text-xs text-[#666] mb-2 font-mono tracking-wider uppercase">
              Email
            </label>
            <div className="relative">
              <input
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                placeholder="player@olympeit.com"
                disabled={isLoading}
                required
                className="h-14 w-full bg-transparent border-2 border-[#1a1a1a] px-4 text-white placeholder-[#444] font-mono text-sm outline-none transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  borderColor: focusedField === 'email' ? '#0066FF' : '#1a1a1a',
                  boxShadow: focusedField === 'email'
                    ? '0 0 30px rgba(0, 102, 255, 0.3), inset 0 0 20px rgba(0, 102, 255, 0.05)'
                    : 'none',
                }}
              />
              {/* Charging indicator */}
              <AnimatePresence>
                {focusedField === 'email' && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    exit={{ scaleX: 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#0066FF] via-[#00d4ff] to-[#0066FF] origin-left"
                  />
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Password Field */}
          <motion.div variants={itemVariants} className="relative group">
            <label className="block text-xs text-[#666] mb-2 font-mono tracking-wider uppercase">
              Пароль
            </label>
            <div className="relative">
              <input
                type="password"
                value={formData.password}
                onChange={handleChange('password')}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                placeholder="••••••••"
                disabled={isLoading}
                required
                className="h-14 w-full bg-transparent border-2 border-[#1a1a1a] px-4 text-white placeholder-[#444] font-mono text-sm outline-none transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  borderColor: focusedField === 'password' ? '#0066FF' : '#1a1a1a',
                  boxShadow: focusedField === 'password'
                    ? '0 0 30px rgba(0, 102, 255, 0.3), inset 0 0 20px rgba(0, 102, 255, 0.05)'
                    : 'none',
                }}
              />
              {/* Charging indicator */}
              <AnimatePresence>
                {focusedField === 'password' && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    exit={{ scaleX: 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#0066FF] via-[#00d4ff] to-[#0066FF] origin-left"
                  />
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Submit Button */}
          <motion.button
            variants={itemVariants}
            type="submit"
            disabled={isLoading}
            whileHover={{ scale: isLoading ? 1 : 1.02 }}
            whileTap={{ scale: isLoading ? 1 : 0.98 }}
            className="group relative h-14 w-full border-2 border-[#0066FF] bg-[#0066FF]/10 text-white font-mono text-sm tracking-wider uppercase overflow-hidden disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-300"
          >
            {/* Hover glow effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-[#0066FF] via-[#00d4ff] to-[#0066FF] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              animate={{
                backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'linear',
              }}
              style={{
                backgroundSize: '200% 100%',
              }}
            />

            <span className="relative z-10 flex items-center justify-center gap-2">
              {isLoading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="h-4 w-4 rounded-full border-2 border-white border-t-transparent"
                  />
                  Подключение...
                </>
              ) : (
                <>
                  <span className="inline-block w-2 h-2 bg-[#0066FF] group-hover:bg-white transition-colors duration-300" />
                  Войти в систему
                </>
              )}
            </span>
          </motion.button>
        </motion.form>

        {/* Register Link */}
        <motion.div variants={itemVariants} className="mt-8 text-center">
          <p className="text-sm text-[#666] font-mono">
            Нет аккаунта?{' '}
            <a
              href="/register"
              className="text-[#0066FF] hover:text-[#00d4ff] underline transition-colors duration-200"
            >
              Зарегистрироваться
            </a>
          </p>
        </motion.div>

        {/* Version indicator */}
        <motion.div
          variants={itemVariants}
          className="mt-12 text-center text-xs text-[#333] font-mono"
        >
          v1.0.0-alpha
        </motion.div>
      </motion.div>
    </div>
  );
}
