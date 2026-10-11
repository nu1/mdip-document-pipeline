from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from ..dependencies import get_document_service
from ..schemas import DocumentChunksResponse, DocumentDetailResponse, DocumentListItem, UploadResponse
from ..services import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", status_code=202, response_model=UploadResponse)
def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    service: DocumentService = Depends(get_document_service),
):
    return service.upload_document(file, background_tasks)


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DocumentService = Depends(get_document_service),
):
    return service.list_documents(limit, offset)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    return service.get_document(document_id)


@router.get("/{document_id}/chunks", response_model=DocumentChunksResponse, response_model_exclude_unset=True)
def read_document_chunks(
    document_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=20),
    service: DocumentService = Depends(get_document_service),
):
    return service.read_document_chunks(document_id, offset, limit)
