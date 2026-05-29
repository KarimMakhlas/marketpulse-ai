# MarketPulse AI — API image.
# Single-stage build using uv for fast, reproducible dependency installs.
FROM python:3.12-slim

# uv: copied from the official distroless image (pinned tag for reproducibility).
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (cached layer) using only the lock + manifest.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the application source and migrations, then install the project itself.
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    API_HOST=0.0.0.0 \
    API_PORT=8000

EXPOSE 8000

# Apply migrations (no-op if already at head), then serve the API.
CMD ["sh", "-c", "alembic upgrade head && python -m marketpulse.api"]
