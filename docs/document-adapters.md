# Document Adapters

The extraction pipeline uses an adapter pattern to decouple format-specific parsing from shared pipeline concerns (file validation, SQLite persistence, chunk generation, and REST APIs).

## The Adapter Protocol

Every supported format implements the `DocumentAdapter` protocol defined in [`backend/app/extraction.py`](../backend/app/extraction.py):

```python
class DocumentAdapter(Protocol):
    @property
    def extensions(self) -> tuple[str, ...]: ...
    @property
    def content_type(self) -> str: ...

    def validate(self, content: bytes) -> None:
        """Validate file headers and check expansion limits before processing."""
        ...

    def extract(self, content: bytes, result: NormalizedDocument, progress: ProgressCallback) -> None:
        """Extract content into normalized blocks (paragraphs, tables, headings)."""
        ...
```

The application registers adapters at startup in an `AdapterRegistry`. Incoming uploads are validated against actual file bytes (magic numbers) rather than trusting client-supplied MIME types.

## Current Adapters

- **`PdfAdapter`** ([`backend/app/adapters.py`](../backend/app/adapters.py)): Manages PDF parsing with page-level routing (native text, OCR, or hybrid) and passes unextractable pages to the optional specialist fallback.
- **`DocxAdapter`** ([`backend/app/adapters.py`](../backend/app/adapters.py)): Extracts DOCX body elements (headings, paragraphs, tables) in visual document order.

## Adding a New Format (e.g. `.txt` or `.html`)

To add support for a new document format:

1. **Implement `DocumentAdapter`**: Create an adapter class defining `extensions`, `content_type`, byte validation, and block extraction.
2. **Register the adapter**: Add the instance to `default_registry()` in `backend/app/adapters.py`.
3. **Frontend updates**: Add the extension to accepted file types in `frontend/src/components/library/UploadZone.tsx`.
4. **Tests**: Add unit tests verifying byte validation, extraction output, and error handling.

Shared capabilities—such as progress tracking, SQLite persistence, and agent chunk retrieval (`/api/documents/{id}/chunks`)—work automatically without modification.
