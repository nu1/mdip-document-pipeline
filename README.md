Local DOCX upload, ordered extraction, persisted processing status and results.

## Run

### 1. Backend

From the `backend` directory (managed with [uv](https://docs.astral.sh/uv/)):

```sh
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend

In a second terminal:

```sh
cd frontend
npm install # or npm ci
npm run dev
```

Open http://127.0.0.1:5173. Use one backend process. Original uploads and SQLite results live under `data/`.

## Verify

```sh
# Backend tests
cd backend
uv run pytest tests -q

# Frontend build check
cd ../frontend
npm run build
```

DOCX extraction preserves headings, paragraphs and table cells in body order. Background tasks are local and not durable; interrupted jobs are marked failed on restart.

