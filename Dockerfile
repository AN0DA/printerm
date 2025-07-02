# Build stage
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies to a virtual environment
ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
RUN uv sync --locked --no-dev

# Runtime stage
FROM python:3.13-slim AS runtime

# Copy uv from the builder stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY printerm ./printerm

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

EXPOSE 5555

CMD ["printerm", "web", "--port", "5555", "--host", "0.0.0.0"]
