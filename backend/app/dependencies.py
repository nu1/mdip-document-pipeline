from fastapi import Request
from .config import Settings
from .pipeline import Pipeline
from .services import DocumentService
from .storage import DocumentRepository, FileStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(request: Request) -> DocumentRepository:
    return request.app.state.repository


def get_file_store(request: Request) -> FileStore:
    return request.app.state.files


def get_pipeline(request: Request) -> Pipeline:
    return request.app.state.pipeline


def get_document_service(request: Request) -> DocumentService:
    settings: Settings = request.app.state.settings
    return DocumentService(
        repository=request.app.state.repository,
        files=request.app.state.files,
        pipeline=request.app.state.pipeline,
        max_upload_bytes=settings.max_upload_bytes,
    )
