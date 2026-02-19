# AiLine Frontend -- multi-stage Docker build (Next.js 16)
# Stage 1: install deps via pnpm (shared by build + test)
# Stage 2: build production bundle
# Stage 3: test runner (devDependencies available)
# Stage 4: standalone runtime with non-root user

# ---------------------------------------------------------------------------
# Deps (shared layer: all dependencies installed)
# ---------------------------------------------------------------------------
FROM node:24-alpine AS deps

RUN corepack enable

WORKDIR /build

# Copy dependency manifest first (layer caching)
COPY package.json pnpm-lock.yaml* ./

# Install all dependencies including devDependencies
RUN pnpm install --frozen-lockfile

# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
FROM deps AS builder

# Copy source and build
COPY . .
RUN pnpm build

# ---------------------------------------------------------------------------
# Test (devDependencies available for pnpm test / typecheck / lint)
# ---------------------------------------------------------------------------
FROM deps AS test

COPY . .

CMD ["pnpm", "test"]

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
    CMD wget -q --spider http://127.0.0.1:3000 || exit 1

CMD ["node", "server.js"]
