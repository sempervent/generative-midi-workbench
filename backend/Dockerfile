# Multi-stage Dockerfile for MIDINecromancer backend
# Targets: dev (development with hot reload) and prod (production)

# Base stage: Install uv
FROM python:3.12-slim as base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dev target: Development with hot reload
FROM base as dev

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files (including README.md which is referenced in pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Copy source code structure (needed for uv sync to build editable package)
COPY src/ ./src/

# Install dependencies (including dev)
RUN uv sync --frozen

# Copy rest of files (will be bind-mounted in compose, but needed for initial build)
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Default command (overridden in compose)
CMD ["uv", "run", "uvicorn", "midinecromancer.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Prod target: Production build
FROM base as prod

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files (including README.md which is referenced in pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Copy source code structure (needed for uv sync to build package)
COPY src/ ./src/

# Install production dependencies only (no dev deps)
RUN uv sync --frozen --no-dev

# Copy rest of files
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck (python is available in PATH via uv environment)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Default command
CMD ["gunicorn", "midinecromancer.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

