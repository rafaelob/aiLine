# AiLine Frontend -- multi-stage Docker build (Next.js 16)
# Stage 1: install + build via pnpm
# Stage 2: standalone runtime with non-root user

# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
FROM node:24-alpine AS builder

RUN corepack enable

WORKDIR /build

# Copy dependency manifest first (layer caching)
COPY package.json pnpm-lock.yaml* ./

# Install dependencies (frozen lockfile enforced -- fail fast if lockfile is stale)
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY . .
RUN pnpm build

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM node:24-alpine AS runtime

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy standalone build output
COPY --from=builder --chown=appuser:appgroup /build/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /build/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /build/public ./public

# Next.js standalone needs HOSTNAME set to listen on all interfaces
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Switch to non-root user
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:3000 || exit 1

CMD ["node", "server.js"]
