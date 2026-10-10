import logging
from uuid import uuid4
from fastapi import BackgroundTasks, HTTPException, UploadFile
from .models import NormalizedDocument, render_for_agent
from .pipeline import Pipeline
from .schemas import DocumentDetailResponse, DocumentListItem, UploadResponse
from .storage import DocumentRepository, FileStore
from .validation import validate_upload

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        files: FileStore,
        pipeline: Pipeline,
        max_upload_bytes: int,
    ):
        self.repository = repository
        self.files = files
        self.pipeline = pipeline
        self.max_upload_bytes = max_upload_bytes

    def upload_document(
        self, file: UploadFile, background_tasks: BackgroundTasks
    ) -> UploadResponse:
        try:
            content = file.file.read(self.max_upload_bytes + 1)
        finally:
            file.file.close()

        if len(content) > self.max_upload_bytes:
            raise HTTPException(
                413,
                f"File exceeds the {self.max_upload_bytes // (1024 * 1024)} MiB upload limit.",
            )

        name, content_type = validate_upload(file.filename or "", content)
        document_id = str(uuid4())

        try:
            uri = self.files.save(document_id, content)
            self.repository.create({
                "id": document_id,
                "filename": name,
                "content_type": content_type,
                "storage_uri": uri,
            })
        except Exception as error:
            logger.exception("Upload persistence failed for %s", document_id)
            raise HTTPException(
                503, "Local storage is unavailable. Check disk space and permissions."
            ) from error

        background_tasks.add_task(self.pipeline.process, document_id)
        return UploadResponse(id=document_id, status="queued")

    def list_documents(self, limit: int = 20, offset: int = 0) -> list[DocumentListItem]:
        records = self.repository.list_documents(limit, offset)
        return [DocumentListItem.model_validate(r) for r in records]

    def get_document(self, document_id: str) -> DocumentDetailResponse:
        record = self.repository.get(document_id)
        if not record:
            raise HTTPException(404, "Document not found.")

        rendered_text = ""
        if record.get("extracted_data"):
            rendered_text = render_for_agent(
                NormalizedDocument.model_validate(record["extracted_data"])
            )

        return DocumentDetailResponse(
            **record,
            rendered_text=rendered_text,
        )
