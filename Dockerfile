# --- Build stage ---
FROM astral/uv:0.7-python3.13-bookworm-slim AS builder

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"

# Kopier låsefilene først for cache
COPY pyproject.toml uv.lock ./

# Installer dependencies + gunicorn
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    uv pip install gunicorn

# Bekreft at gunicorn finnes
RUN gunicorn --version

# Kopier resten av prosjektet (uten .venv pga .dockerignore)
COPY . .

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS run

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH=/app

# Kopier både kode og venv eksplisitt
COPY --from=builder /app /app
COPY --from=builder /app/.venv /app/.venv

EXPOSE 8000

# Start Gunicorn med riktig WSGI-app
CMD ["gunicorn", "--chdir", "/app/mysite", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
