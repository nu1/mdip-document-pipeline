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

### Optional Docker backend

Requires Docker with Compose. Instead of starting the native backend, run from the repository root:

```sh
docker compose up --build
```

In another terminal, run the frontend locally:

```sh
cd frontend
npm ci
npm run dev
```

The image includes Python 3.12 and real Tesseract with English language data; neither needs to be installed on the host. The backend listens at `http://127.0.0.1:8000`, using the existing frontend proxy. SQLite results (`documents.db`) and original uploads (`originals/`) persist under `/data` in the Compose-managed `backend-data` named volume.

From the repository root, `docker compose down` stops and removes the service while retaining the volume. Explicitly removing it with `docker compose down --volumes` deletes its stored documents and results. The native uv workflow above remains available. Containerisation does not make background tasks durable: interrupted jobs are still marked failed on restart and must be uploaded again.

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

