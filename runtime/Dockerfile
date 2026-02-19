# AiLine Runtime API -- multi-stage Docker build
# Build context: repo root (docker-compose.yml sets context: .)
# Stage 1: install deps via uv into system Python
# Stage 2: slim runtime with non-root user

# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy agents package first (runtime depends on it)
COPY agents/pyproject.toml agents/uv.lock agents/
COPY agents/ailine_agents/ agents/ailine_agents/

# Build agents wheel and install it with all LLM provider extras.
# Export lock-pinned versions as constraints (filter out the local package itself).
RUN cd agents \
    && uv export --frozen --no-hashes --no-dev -o /tmp/raw-constraints.txt \
    && grep -v '^file://' /tmp/raw-constraints.txt | grep -v '^\-e ' | grep '==' > /tmp/agent-constraints.txt || true \
    && uv build --wheel --out-dir /tmp/wheels \
    && AGENTS_WHL=$(ls /tmp/wheels/ailine_agents-*.whl) \
    && if [ -s /tmp/agent-constraints.txt ]; then \
         uv pip install --system --constraint /tmp/agent-constraints.txt "${AGENTS_WHL}[all]"; \
       else \
         uv pip install --system "${AGENTS_WHL}[all]"; \
       fi

# Copy runtime dependency manifest AND source (hatchling needs package dir)
COPY runtime/pyproject.toml runtime/uv.lock* runtime/
COPY runtime/ailine_runtime/ runtime/ailine_runtime/

# Build arg: set INSTALL_DEV=true to include test/dev dependencies
ARG INSTALL_DEV=false

# Build runtime wheel and install it with all extras
RUN cd runtime && uv build --wheel --out-dir /tmp/wheels \
    && RUNTIME_WHL=$(ls /tmp/wheels/ailine_runtime-*.whl) \
    && uv pip install --system "${RUNTIME_WHL}[all]" \
    && uv pip install --system aiosqlite \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         uv pip install --system pytest pytest-asyncio pytest-cov httpx ruff mypy python-dotenv; \
       fi

# Copy remaining runtime files (tests, alembic, etc.)
COPY runtime/ runtime/

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY --from=builder /build/runtime /app

# Create local store directory owned by appuser
RUN mkdir -p /app/.local_store && chown -R appuser:appgroup /app/.local_store

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "ailine_runtime.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
