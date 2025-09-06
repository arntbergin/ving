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

# Installer systempakker som Playwright trenger
RUN apt-get update && apt-get install -y \
    curl gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxrandr2 libxss1 libasound2 libxdamage1 libxext6 libxfixes3 libx11-xcb1 \
    libxcb1 libx11-6 libxrender1 libdbus-glib-1-2 libgtk-3-0 libdrm2 libgbm1 \
    libxshmfence1

# Installer Playwright og last ned browser-binaries
RUN /app/.venv/bin/pip install playwright && playwright install --with-deps

# Kopier både kode og venv eksplisitt
COPY --from=builder /app /app
COPY --from=builder /app/.venv /app/.venv

EXPOSE 8000

# Start Gunicorn med riktig WSGI-app
CMD ["gunicorn", "--chdir", "/app/mysite", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
