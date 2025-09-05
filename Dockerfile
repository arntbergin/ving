# --- Build stage ---
FROM astral/uv:0.7-python3.13-bookworm-slim AS builder

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"

# 1) Kopier låsefiler og installer dependencies
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    uv pip install gunicorn whitenoise

# 2) Kopier kildekode og sanity-check
COPY . .
RUN test -f /app/mysite/mysite/settings.py \
 && test -f /app/mysite/mysite/wsgi.py

# 3) Samle alle statiske filer
RUN python manage.py collectstatic --noinput

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS run

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH=/app

# 1) Kopier alt fra builder: kode, venv og staticfiles
COPY --from=builder /app /app

EXPOSE 8000

# 2) Start Gunicorn i én riktig CMD-instruksjon
CMD ["gunicorn","--chdir","/app/mysite","mysite.wsgi:application","--bind","0.0.0.0:8000","--workers","3"]
