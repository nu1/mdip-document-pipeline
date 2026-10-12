# Agent integration

The UI and Python tools retrieve already-extracted content through REST. They do not reprocess documents or access SQLite directly. No model or agent SDK is required; a host application can register the functions and their JSON argument schemas from [examples/agent_tools.py](../examples/agent_tools.py).

## Callable tools

| Function | REST request | Arguments |
|---|---|---|
| `list_documents` | `GET /documents` | `limit=20` (1–100), `offset=0` (non-negative). |
| `read_document_chunks` | `GET /documents/{document_id}/chunks` | Required `document_id`, `limit=5` (1–20), `offset=0` (non-negative). |

Document listing returns a newest-first array of summaries, including IDs, filenames and processing states. Chunk retrieval returns:

```json
{
  "document_id": "example-id",
  "filename": "agreement.docx",
  "status": "completed",
  "processing_stage": "done",
  "warnings": [],
  "error_message": null,
  "chunks": [
    {
      "id": "example-id:0",
      "document_id": "example-id",
      "chunk_index": 0,
      "text": "Supplier agreement",
      "source_location": {"block_index": 0, "paragraph_index": 0},
      "metadata": {
        "block_order": 0,
        "type": "heading",
        "extraction_method": "native_docx"
      }
    }
  ],
  "next_offset": null
}
```

Chunks retain their original order and source locations. PDF pages are 1-based; DOCX body indexes are 0-based, with no invented page numbers. Extraction methods distinguish native PDF, native DOCX and OCR; `mock_ocr` is reserved for labelled test fixtures. Optional specialist output uses `mock_ai` for the bundled mock or `ai_extractor` for a real provider. Provider metadata is retained in `metadata.provider`; `mocked: true` and document warnings identify demonstration output. Generic mock acknowledgements create no content chunks. See the [specialist fallback guide](specialist-fallback.md).

Pass `next_offset` into the next call until it is `null`. This means no further persisted chunks, not that extraction succeeded. Queued, processing and failed documents report their actual state and any available partial content. Check status, warnings and errors before using the text. Invalid pagination returns HTTP 422; missing documents return 404. Interactive response schemas are available at `/docs` on the backend.

## Run the example

With the backend running, from the repository root:

```sh
python3 examples/agent_tools.py --limit 2
python3 examples/agent_tools.py --document-id DOCUMENT_ID --limit 2
```

The first command lists documents and reads the first one; the second selects an explicit ID. The example follows continuation for a second batch when present. It calls tools in a fixed sequence rather than demonstrating autonomous model selection.

The API defaults to `http://127.0.0.1:8000`; set `MDIP_API_BASE_URL` to override it. The example uses Python's standard library. Imported HTTP failures retain their status and response body; connection failures propagate to the host.

This interface supports sequential reading, not relevance-ranked retrieval. Individual chunks can be long, so the host must enforce its own token/context budget. Extraction warnings remain relevant to any generated answer.
