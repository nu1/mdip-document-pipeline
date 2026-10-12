# Specialist extraction fallback (mocked)

Pages that meet the fallback criteria are passed to an optional specialist extraction provider. Production implementations could use a managed document-analysis service or a self-hosted OCR/layout model. This assessment uses a mock provider to demonstrate the integration; the provider interface does not require an LLM or a third-party cloud service. Its bundled implementation makes **no network or model calls** and responds to every eligible page: a clearly labelled fixture table for the exact bytes of [ai-fallback.pdf](../demo/ai-fallback.pdf), page 2, and a generic mock acknowledgement for all other inputs. It demonstrates orchestration and response mapping; extraction accuracy has not been evaluated against an external provider.

## Mock output and provenance

The canned response is defined in [`backend/app/fixtures/ai_fallback.json`](../backend/app/fixtures/ai_fallback.json), inside its `response` object. The same file's `default_response` defines the generic acknowledgement. Both are loaded by `MockAiExtractor` in [`backend/app/fallback.py`](../backend/app/fallback.py). It contains a table with `TOTAL | 125`. The structured view and readable text explicitly say: **“This is a mock response for demonstration; no external service was called.”** This notice is derived from mock provenance when displaying content; it is kept separate from the table values and stored chunk text. Chunk responses identify the mock through extraction-method and provider metadata, with document warnings alongside them.

For any other eligible page, the mock returns `blocks: []` with a note that explicitly says it is a mock response, identifies the page and trigger, and explains that no document content was extracted. This is shown in page decisions, warnings and readable text, and persists with the fallback attempt. The outcome is `no_content`, rather than claiming recovery. No placeholder notice is added to canonical content blocks or document chunks. For example, `demo/scan.pdf` triggers this generic response when local OCR is unavailable; successful local OCR bypasses the fallback.

## Run the demo

Enable the demo, then upload `demo/ai-fallback.pdf`:

```sh
# Docker, from the repository root:
AI_FALLBACK=mock docker compose up --build

# Or native, from backend/:
AI_FALLBACK=mock uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Page 1 extracts locally. Page 2 spells `TOTAL 125` using vector strokes, so native text/image routing reports `EMPTY_OR_UNKNOWN`; the fallback returns a mock table. Page 3 is blank and skips the fallback. Page decisions show the original route, escalation reason, provider/version and outcome. Blocks, readable text and retrieved chunks identify mocked content. The final status remains `completed_with_warnings`. Set `AI_FALLBACK=disabled` (the default) to disable it; re-upload to process with changed settings.

## Escalation policy

Fallback policy is explicit and page-local: OCR unavailable, OCR failure, OCR returning no text, native extraction returning no blocks, or an unknown page with content marks. Marks and images are only evidence of possible content; they do not prove readable text. Warning counts, HYBRID limitations and searchable-scan warnings alone do not trigger it. Existing content and original routing evidence are retained. Each eligible page gets at most one attempt; no retry loop is added. An empty response, timeout, invalid response or service error remains visible and processing continues to later pages.

## Provider contract

`FallbackProvider` in `backend/app/fallback.py` accepts a single-page PDF, its original page number, a reason, a document hash and a 30-second timeout budget. A production adapter must enforce that budget in its client or model execution, identify its provider/version with `mocked=False`, and return the documented paragraph/table response schema. The current mock returns immediately. Responses are validated atomically before canonical blocks are appended; original page references are assigned by the application. The fixture is selected by document hash and page, never by filename. Other uploads receive the generic acknowledgement and cannot receive this demo's table values. Native routing never calls the fallback service or renders pixels.

The fixture depends on the exact PDF bytes. If the demo PDF changes, update `document_sha256` in the fixture JSON alongside it and rerun the fallback tests.

## Possible production replacements

The provider boundary could be implemented using a managed service or a self-hosted model, depending on the document types and deployment requirements:

- **[Google Cloud Document AI](https://docs.cloud.google.com/document-ai/docs/overview):** Enterprise Document OCR for text recognition, Layout Parser for text/tables/lists, or Form Parser for tables and key-value pairs.
- **[Azure AI Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0):** the `prebuilt-layout` model combines OCR with extraction of text, tables, selection marks and document structure.
- **[Amazon Textract](https://docs.aws.amazon.com/textract/latest/dg/how-it-works-analyzing.html):** document analysis extracts text, tables and forms; an adapter could map its text and table blocks into this application's response schema.
- **Self-hosted OCR/layout model:** run a suitable model within the application or behind an internal service, and map its recognised text and layout into ordered paragraph/table blocks. An internal service is external to the application process without being a third-party provider.

These are candidate implementations, not currently connected integrations. Each needs an adapter to translate its native response into validated paragraph/table blocks; none is a drop-in replacement for the fixture JSON. Keep the original page mapping and provider/version provenance, enforce client timeouts and bounded retries, and configure any service credentials outside the repository. For self-hosted models, also manage model versions, runtime dependencies and compute limits. Add support for asynchronous completion if the selected API requires it. Choose a provider by measuring recovery accuracy on representative difficult pages, alongside latency, cost and data handling requirements; the mock does not establish those results.
