'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { registerUser, APIError } from '@/lib/api';
import type { RegisterRequest } from '@/types/auth';

export default function RegisterPage() {
  const router = useRouter();

  // Form state
  const [formData, setFormData] = useState<RegisterRequest & { confirmPassword: string }>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });

  // UI state
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string>('');

  // Client-side validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.includes('@')) {
      newErrors.email = 'Введите корректный email';
    }

    if (formData.username.length < 3) {
      newErrors.username = 'Минимум 3 символа';
    }

    if (formData.password.length < 6) {
      newErrors.password = 'Минимум 6 символов';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setServerError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await registerUser(registerData);

      // Success - redirect to login
      router.push('/login');
    } catch (error) {
      if (error instanceof APIError) {
        setServerError(error.message);
      } else {
        setServerError('Произошла непредвиденная ошибка');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Input change handler with error clearing
  const handleChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({ ...formData, [field]: e.target.value });
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' });
    }
    // Clear server error
    if (serverError) {
      setServerError('');
    }
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.1,
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3 },
    },
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="w-full max-w-[360px] space-y-6 px-4"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="space-y-2">
          <h1 className="text-5xl font-bold text-white">Олимпиада</h1>
          <p className="text-sm text-gray-500">Регистрация участника</p>
        </motion.div>

        {/* Server Error */}
        {serverError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="rounded-sm border border-[#ff3b30] bg-[#ff3b30]/10 p-3 text-sm text-[#ff3b30]"
          >
            {serverError}
          </motion.div>
        )}

        {/* Form */}
        <motion.form
          onSubmit={handleSubmit}
          className="space-y-6"
          variants={containerVariants}
        >
          {/* Email Field */}
          <motion.div variants={itemVariants} className="space-y-1">
            <input
              type="email"
              value={formData.email}
              onChange={handleChange('email')}
              placeholder="Email"
              disabled={isLoading}
              className="h-12 w-full border-b-2 border-gray-800 bg-transparent px-0 text-white placeholder-gray-600 outline-none transition-all duration-200 focus:border-[#8B5CF6] focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] disabled:opacity-50"
            />
            {errors.email && (
              <p className="text-xs text-[#ff3b30]">{errors.email}</p>
            )}
          </motion.div>

          {/* Username Field */}
          <motion.div variants={itemVariants} className="space-y-1">
            <input
              type="text"
              value={formData.username}
              onChange={handleChange('username')}
              placeholder="Имя пользователя"
              disabled={isLoading}
              className="h-12 w-full border-b-2 border-gray-800 bg-transparent px-0 text-white placeholder-gray-600 outline-none transition-all duration-200 focus:border-[#8B5CF6] focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] disabled:opacity-50"
            />
            {errors.username && (
              <p className="text-xs text-[#ff3b30]">{errors.username}</p>
            )}
          </motion.div>

          {/* Password Field */}
          <motion.div variants={itemVariants} className="space-y-1">
            <input
              type="password"
              value={formData.password}
              onChange={handleChange('password')}
              placeholder="Пароль"
              disabled={isLoading}
              className="h-12 w-full border-b-2 border-gray-800 bg-transparent px-0 text-white placeholder-gray-600 outline-none transition-all duration-200 focus:border-[#8B5CF6] focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] disabled:opacity-50"
            />
            {errors.password && (
              <p className="text-xs text-[#ff3b30]">{errors.password}</p>
            )}
          </motion.div>

          {/* Confirm Password Field */}
          <motion.div variants={itemVariants} className="space-y-1">
            <input
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange('confirmPassword')}
              placeholder="Подтвердите пароль"
              disabled={isLoading}
              className="h-12 w-full border-b-2 border-gray-800 bg-transparent px-0 text-white placeholder-gray-600 outline-none transition-all duration-200 focus:border-[#8B5CF6] focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] disabled:opacity-50"
            />
            {errors.confirmPassword && (
              <p className="text-xs text-[#ff3b30]">{errors.confirmPassword}</p>
            )}
          </motion.div>

          {/* Submit Button */}
          <motion.button
            variants={itemVariants}
            type="submit"
            disabled={isLoading}
            className="h-12 w-full rounded-none border-2 border-white bg-transparent text-white transition-all duration-200 hover:bg-white hover:text-black disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-white"
          >
            {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
          </motion.button>
        </motion.form>

        {/* Login Link */}
        <motion.div variants={itemVariants} className="text-center">
          <p className="text-sm text-gray-500">
            Уже есть аккаунт?{' '}
            <a
              href="/login"
              className="text-white underline transition-colors hover:text-[#8B5CF6]"
            >
              Войти
            </a>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
