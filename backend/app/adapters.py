"""PDF and DOCX adapters translate parser behaviour into the common contract."""
from io import BytesIO
from zipfile import ZipFile

import pymupdf
from docx import Document

from .docx_extraction import extract_docx
from .extraction import AdapterRegistry, DocumentTooLarge, ProgressCallback
from .models import NormalizedDocument
from .fallback import FallbackProvider
from .ocr import OcrProvider
from .pdf_extraction import PDF_LOCK, extract_pdf

MAX_UNPACKED_DOCX = 40 * 1024 * 1024


class PdfAdapter:
    extensions = ('.pdf',)
    content_type = 'application/pdf'

    def __init__(self, ocr: OcrProvider | None = None, fallback: FallbackProvider | None = None):
        self.ocr = ocr
        self.fallback = fallback

    def validate(self, content: bytes) -> None:
        if not content.startswith(b'%PDF-'):
            raise ValueError('Missing PDF header')
        with PDF_LOCK, pymupdf.open(stream=content, filetype='pdf') as document:
            if document.needs_pass or document.page_count == 0:
                raise ValueError('Encrypted or empty PDF')

    def extract(self, content: bytes, result: NormalizedDocument, progress: ProgressCallback) -> None:
        extract_pdf(content, result, self.ocr, progress, self.fallback)


class DocxAdapter:
    extensions = ('.docx',)
    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    def validate(self, content: bytes) -> None:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(e.file_size for e in entries) > MAX_UNPACKED_DOCX:
                raise DocumentTooLarge('DOCX expands beyond the supported archive limits.')
            if 'word/document.xml' not in archive.namelist() or '[Content_Types].xml' not in archive.namelist():
                raise ValueError('Missing OOXML document')
            if any(e.flag_bits & 1 for e in entries):
                raise ValueError('Encrypted archive')
        Document(BytesIO(content))

    def extract(self, content: bytes, result: NormalizedDocument, progress: ProgressCallback) -> None:
        extract_docx(content, result)


def default_registry(ocr: OcrProvider | None = None, fallback: FallbackProvider | None = None) -> AdapterRegistry:
    return AdapterRegistry(
        (PdfAdapter(ocr, fallback), DocxAdapter()),
        aliases={'docx': DocxAdapter.content_type},  # Preserve legacy stored type support.
    )
