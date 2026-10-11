from typing import Any
from pydantic import BaseModel, Field
from .models import SourceLocation


class HealthResponse(BaseModel):
    status: str = "ok"
    max_upload_bytes: int


class UploadResponse(BaseModel):
    id: str
    status: str = "queued"


class DocumentListItem(BaseModel):
    id: str
    filename: str
    content_type: str
    status: str
    processing_stage: str
    processed_pages: int | None = None
    total_pages: int | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: str
    processing_stage: str
    processed_pages: int | None = None
    total_pages: int | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str
    extracted_data: dict[str, Any] | None = None
    rendered_text: str = ""


class PersistedChunk(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    text: str
    source_location: SourceLocation
    metadata: dict[str, Any]


class DocumentChunksResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    processing_stage: str
    warnings: list[str]
    error_message: str | None
    chunks: list[PersistedChunk]
    next_offset: int | None
