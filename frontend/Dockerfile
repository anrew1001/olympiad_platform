# Multi-stage build для Next.js оптимизации

# Stage 1: Builder
FROM node:20-alpine as builder

WORKDIR /app

# Копируем dependency files
COPY package*.json ./
COPY tsconfig.json ./
COPY next.config.ts ./
COPY postcss.config.mjs ./
COPY eslint.config.mjs ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходный код
COPY app ./app/
COPY components ./components/
COPY context ./context/
COPY hooks ./hooks/
COPY lib ./lib/
COPY types ./types/
COPY assets ./assets/
COPY public ./public/

# Строим приложение
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine

WORKDIR /app

# Копируем только необходимые файлы из builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules/
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.ts ./

# Создаём non-root пользователя для безопасности
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app
USER nextjs

# Environment переменные
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (res) => {if (res.statusCode !== 200) throw new Error(res.statusCode)})"

# Expose порт
EXPOSE 3000

# Start production server
CMD ["npm", "start"]
