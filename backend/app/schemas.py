from typing import Any
from pydantic import BaseModel, Field


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
