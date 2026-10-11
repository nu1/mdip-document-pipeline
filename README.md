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

## Supporting more document formats

Each format implements the `DocumentAdapter` protocol in `backend/app/extraction.py`: supported extensions, a canonical MIME type, content validation, and extraction into `NormalizedDocument`. `PdfAdapter` and `DocxAdapter` in `backend/app/adapters.py` wrap the existing parsers. The PDF adapter receives its OCR provider and keeps page-level native/OCR/hybrid routing inside the PDF implementation.

The app creates one explicit adapter registry and shares it between upload validation and the pipeline. Uploads select an adapter by extension and validate the actual bytes; client MIME types are not trusted. Processing selects the adapter by the recorded MIME type. Unknown formats are rejected, and duplicate registrations fail at startup. Filename sanitisation, upload limits and HTTP errors remain in the upload layer; status updates, partial-output retention, persistence and derived chunks remain in the common pipeline. Adapters append blocks incrementally so an extraction failure can preserve available results.

To add a format such as `.txt`:

1. Implement an adapter with an explicit decoding policy, content checks and ordered canonical blocks; register it alongside PDF and DOCX in `default_registry()`.
2. Add its extraction-method value to the model's explicit allowed values. Extend source locations if needed, such as line/character offsets for text or sheet/cell positions for spreadsheets, and update their display formatting.
3. Update the frontend's accepted formats and upload copy, then add format-specific fixtures and tests. The pipeline, persistence and chunk-generation code can be reused for formats that map to the existing block types.

The registry is deliberately explicit and local; there is no dynamic plugin loading. `backend/tests/test_adapters.py` registers a third, test-only format and verifies validation, extraction, warnings, persistence, readable text and chunk retrieval through the existing API. It also checks partial results after adapter failure. Only PDF and DOCX are enabled in the application by default.
