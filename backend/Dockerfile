FROM python:3.12.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    DATA_DIR=/data

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app \
    && install -d -o app -g app /data

WORKDIR /app

# Keep dependency installation cached when only application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-cache

COPY app/ ./app/

USER app
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
