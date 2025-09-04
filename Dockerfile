# --- Build stage ---
FROM astral/uv:0.7-python3.13-bookworm-slim AS builder
WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    uv pip install gunicorn

RUN gunicorn --version  # fungerer nå
# Kopier resten av prosjektet
COPY . .

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS run

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"

COPY --from=builder /app /app

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]