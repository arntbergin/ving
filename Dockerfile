# --- Build stage ---
FROM astral/uv:0.7-python3.13-bookworm-slim AS builder

WORKDIR /app

# Kopier kun låsefilene først for cache
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Kopier resten av prosjektet
COPY . .

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS run

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

# Start Gunicorn med Django WSGI-app
CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
