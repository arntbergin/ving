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

# Kopier over både prosjekt og venv
COPY --from=builder /app /app

# Bruk virtuell miljø binærmappe
ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000
CMD ["python", "mysite/manage.py", "runserver", "0.0.0.0:8000"]
