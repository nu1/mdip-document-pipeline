import logging
from threading import Lock
from .docx_extraction import extract_docx
from .models import NormalizedDocument, build_chunks
from .storage import DocumentRepository, FileStore

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, repository: DocumentRepository, files: FileStore, ocr=None):
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
                extract_docx(content, result)
                progress(processing_stage='normalising', extracted_data=result.model_dump(exclude_none=True))
                self.repository.replace_chunks(document_id, build_chunks(result))
                progress(status='completed_with_warnings' if result.warnings else 'completed', processing_stage='done')
            except Exception:
                logger.exception('Document processing failed: %s', document_id)
                progress(status='failed', processing_stage='failed',
                         extracted_data=result.model_dump(exclude_none=True),
                         error_message='Extraction failed. Partial results, if any, are retained. Check the local server log.')
