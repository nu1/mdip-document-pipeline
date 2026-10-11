import logging
from threading import Lock
from .docx_extraction import extract_docx
from .pdf_extraction import extract_pdf
from .models import NormalizedDocument, build_chunks
from .ocr import OcrProvider
from .storage import DocumentRepository, FileStore

logger = logging.getLogger(__name__)

DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PDF_MIME = 'application/pdf'


class Pipeline:
    def __init__(self, repository: DocumentRepository, files: FileStore, ocr: OcrProvider | None = None):
        self.repository = repository
        self.files = files
        self.ocr = ocr
        self.lock = Lock()

    def process(self, document_id: str) -> None:
        # One extraction at a time locally, with queued records visible while waiting.
        with self.lock:
            record = self.repository.get(document_id)
            if not record:
                return
            result = NormalizedDocument(document_id=document_id, filename=record['filename'], content_type=record['content_type'])
            def progress(**changes):
                self.repository.update(document_id, **changes)
            try:
                progress(status='processing', processing_stage='extracting')
                content = self.files.read(record['storage_uri'])
                if record['content_type'] == PDF_MIME:
                    extract_pdf(content, result, self.ocr, progress)
                elif record['content_type'] in (DOCX_MIME, 'docx'):
                    extract_docx(content, result)
                else:
                    raise ValueError(f"Unsupported content type: {record['content_type']}")
                progress(processing_stage='normalising', extracted_data=result.model_dump(exclude_none=True))
                self.repository.replace_chunks(document_id, build_chunks(result))
                progress(status='completed_with_warnings' if result.warnings else 'completed', processing_stage='done')
            except Exception:
                logger.exception('Document processing failed: %s', document_id)
                progress(status='failed', processing_stage='failed',
                         extracted_data=result.model_dump(exclude_none=True),
                         error_message='Extraction failed. Partial results, if any, are retained. Check the local server log.')
