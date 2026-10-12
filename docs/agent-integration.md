# Agent Integration

External AI agents and host applications interact with extracted documents via REST endpoints. The service provides deterministic, pagination-friendly endpoints designed to be registered directly as LLM tool definitions (functions).

Reference schemas and standard-library Python implementations are available in [`examples/agent_tools.py`](../examples/agent_tools.py).

## Available Tools

| Tool Name | Endpoint | Parameters | Purpose |
|---|---|---|---|
| `list_documents` | `GET /documents` | `limit` (1–100, default: 20)<br>`offset` (default: 0) | Lists uploaded documents with status and metadata. |
| `read_document_chunks` | `GET /documents/{id}/chunks` | `document_id` (required)<br>`limit` (1–20, default: 5)<br>`offset` (default: 0) | Reads ordered document chunks with source provenance. |

## Chunk Schema & Provenance

When an agent calls `read_document_chunks`, it receives structured chunks preserving visual reading order and source location:

```json
{
  "document_id": "example-id",
  "filename": "agreement.docx",
  "status": "completed",
  "processing_stage": "done",
  "warnings": [],
  "chunks": [
    {
      "id": "example-id:0",
      "document_id": "example-id",
      "chunk_index": 0,
      "text": "Supplier agreement",
      "source_location": { "block_index": 0, "paragraph_index": 0 },
      "metadata": {
        "block_order": 0,
        "type": "heading",
        "extraction_method": "native_docx"
      }
    }
  ],
  "next_offset": 5
}
```

### Key Fields for Agents

- **`source_location`**: Exact origin within the document (1-based `page` and bounding boxes for PDFs; 0-based `block_index` for DOCX).
- **`metadata.extraction_method`**: Identifies how the text was extracted (`native_pdf`, `native_docx`, `ocr`, or `mock_ai`).
- **`warnings`**: Quality flags from extraction (e.g., degraded scans or partial image extractions).

## Pagination Pattern

Chunk retrieval uses cursor-based offsets:

1. Start with `offset=0`.
2. Inspect the returned `next_offset`.
3. If `next_offset` is not `null`, pass it as the `offset` in the next call to fetch the next batch.
4. When `next_offset` is `null`, all chunks for the document have been consumed.

## Running the Example Client

A runnable Python script demonstrating tool registration and chunk pagination is provided in `examples/`:

```sh
# List documents and read the first document:
python3 examples/agent_tools.py --limit 2

# Read chunks for a specific document:
python3 examples/agent_tools.py --document-id DOCUMENT_ID --limit 5
```

By default, the script connects to `http://127.0.0.1:8000`. Set `MDIP_API_BASE_URL` to point to an alternate host.

## LLM Host Considerations

- **Context Windows**: Chunks are sequential content blocks, not semantic summaries. Agents should paginate through chunks according to their available context/token budget.
- **Status & Warnings**: Always inspect document `status` and `warnings` before interpreting chunks. Incomplete or failed documents may only return partial content.
