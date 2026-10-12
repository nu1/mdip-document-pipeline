# Specialist Extraction Fallback

When a PDF page cannot be extracted locally—such as scanned pages when local OCR is unavailable, or complex pages with vector-rendered text and unparsed tables—the pipeline can escalate that individual page to a specialist fallback provider.

## How It Works

Fallback is evaluated **page-by-page** during PDF extraction:

1. **Escalation trigger**: If native inspection or OCR yields no usable text (e.g., page route is `EMPTY_OR_UNKNOWN` despite visual content), the page is marked for fallback.
2. **Provider execution**: The single-page PDF is passed to an implementation of `FallbackProvider` ([`backend/app/fallback.py`](../backend/app/fallback.py)).
3. **Validation & Isolation**: Fallback responses are validated against strict Pydantic schemas before blocks are merged into the document. Failures or timeouts on one page never fail the entire document.
4. **Provenance**: Extracted fallback blocks and chunks retain clear provider metadata (`extraction_method: "mock_ai"`, `mocked: true`), ensuring downstream consumers and agents know how the content was produced.

## Trying the Demo (Mock Provider)

To demonstrate fallback orchestration without requiring external cloud accounts or paid API keys, a local mock provider is included:

```sh
# Run with mock fallback enabled (Docker):
AI_FALLBACK=mock docker compose up --build

# Or run natively:
AI_FALLBACK=mock uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Upload `demo/ai-fallback.pdf`:
- **Page 1**: Extracts locally using native PDF parsing.
- **Page 2**: Contains text rendered as vector strokes (which normal font extractors miss). The fallback recovers a demonstration table (`TOTAL | 125`), clearly labelled with a mock notice.
- **Page 3**: Blank page; skips fallback.

To disable fallback, set `AI_FALLBACK=disabled` (the default).

## Production Replacements

In production, the `FallbackProvider` interface can be backed by a managed service or dedicated layout model:

- **Cloud APIs**: AWS Textract (Layout/Tables), Google Cloud Document AI, or Azure AI Document Intelligence.
- **Self-hosted models**: Open-source vision-language models or layout parsers (e.g., Surya, Nougat, or Docling) running behind an internal service.

Because fallback is encapsulated behind the `FallbackProvider` protocol, integrating a real service only requires translating the provider's API output into normalized `FallbackBlock` models and enforcing a client timeout.
