# Supporting more document formats

Each format implements the `DocumentAdapter` protocol in [extraction.py](../backend/app/extraction.py): supported extensions, a canonical MIME type, content validation, and extraction into `NormalizedDocument`. `PdfAdapter` and `DocxAdapter` in [adapters.py](../backend/app/adapters.py) wrap the existing parsers. The PDF adapter receives its OCR provider and keeps page-level native/OCR/hybrid routing inside the PDF implementation.

The app creates one explicit adapter registry and shares it between upload validation and the pipeline. Uploads select an adapter by extension and validate the actual bytes; client MIME types are not trusted. Processing selects the adapter by the recorded MIME type. Unknown formats are rejected, and duplicate registrations fail at startup. Filename sanitisation, upload limits and HTTP errors remain in the upload layer; status updates, partial-output retention, persistence and derived chunks remain in the common pipeline. Adapters append blocks incrementally so an extraction failure can preserve available results.

## Adding a format

To add a format such as `.txt`:

1. Implement an adapter with an explicit decoding policy, content checks and ordered canonical blocks; register it alongside PDF and DOCX in `default_registry()`.
2. Add its extraction-method value to the model's explicit allowed values. Extend source locations if needed, such as line/character offsets for text or sheet/cell positions for spreadsheets, and update their display formatting.
3. Update the frontend's accepted formats and upload copy, then add format-specific fixtures and tests. The pipeline, persistence and chunk-generation code can be reused for formats that map to the existing block types.

The registry is deliberately explicit and local; there is no dynamic plugin loading. [Adapter tests](../backend/tests/test_adapters.py) register a third, test-only format and verifies validation, extraction, warnings, persistence, readable text and chunk retrieval through the existing API. It also checks partial results after adapter failure. Only PDF and DOCX are enabled in the application by default.
