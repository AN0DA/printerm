FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
COPY printerm ./printerm

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
--mount=type=bind,source=README.md,target=README.md \
uv sync --locked --no-dev



EXPOSE 5555
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "printerm", "web"]
