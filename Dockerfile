# Python slim, Poetry, зависимости без root, healthcheck, non-root user.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl для HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry: ставим зависимости без виртуального окружения в образе
RUN pip install --upgrade pip && pip install poetry==1.8.0

# Сначала только зависимости — чтобы кэш слоя работал при изменении кода
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --no-dev

# Код приложения
COPY . .

# Запуск не от root
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Оркестратор проверяет /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Без --reload в проде
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
