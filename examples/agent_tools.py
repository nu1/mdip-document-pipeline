"""REST integration building blocks; no model, SDK, or direct database access."""

import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import urlopen


LIST_DOCUMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
        "offset": {"type": "integer", "minimum": 0, "default": 0},
    },
    "additionalProperties": False,
}

READ_DOCUMENT_CHUNKS_SCHEMA = {
    "type": "object",
    "properties": {
        "document_id": {"type": "string", "minLength": 1},
        "offset": {"type": "integer", "minimum": 0, "default": 0},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
    },
    "required": ["document_id"],
    "additionalProperties": False,
}


def _get(path: str, *, limit: int, offset: int):
    base_url = os.environ.get("MDIP_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    url = f"{base_url}{path}?{urlencode({'limit': limit, 'offset': offset})}"
    # HTTPError retains the API status and response body for the calling host.
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def list_documents(limit: int = 20, offset: int = 0) -> list[dict]:
    """List document summaries and actual processing states via GET /documents."""
    return _get("/documents", limit=limit, offset=offset)


def read_document_chunks(document_id: str, offset: int = 0, limit: int = 5) -> dict:
    """Read persisted chunks in source order, with warnings and next_offset."""
    return _get(f"/documents/{quote(document_id, safe='')}/chunks", limit=limit, offset=offset)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic REST tool example; no model is connected.")
    parser.add_argument("--document-id", help="Document to read; defaults to the first document listed.")
    parser.add_argument("--limit", type=int, choices=range(1, 21), default=2, help="Chunks per batch (default: 2).")
    args = parser.parse_args()
    try:
        documents = list_documents()
        print("list_documents:")
        print(json.dumps(documents, indent=2, ensure_ascii=False))
        document_id = args.document_id or (documents[0]['id'] if documents else None)
        if document_id is None:
            print("No documents yet. Upload a PDF or DOCX in the frontend first.")
            return
        batch = read_document_chunks(document_id, limit=args.limit)
        print("read_document_chunks:")
        print(json.dumps(batch, indent=2, ensure_ascii=False))
        if batch['next_offset'] is not None:
            print(f"Continuation at offset {batch['next_offset']}:")
            next_batch = read_document_chunks(document_id, offset=batch['next_offset'], limit=args.limit)
            print(json.dumps(next_batch, indent=2, ensure_ascii=False))
            if next_batch['next_offset'] is not None:
                print(f"More chunks remain at offset {next_batch['next_offset']}.")
        else:
            print(f"No further persisted chunks in this batch. Document status: {batch['status']}.")
    except HTTPError as error:
        parser.exit(1, f"API error {error.code}: {error.read().decode('utf-8', errors='replace')}\n")
    except (URLError, TimeoutError) as error:
        parser.exit(1, f"Cannot reach the API: {error}\n")


if __name__ == "__main__":
    main()
