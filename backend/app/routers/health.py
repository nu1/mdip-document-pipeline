from fastapi import APIRouter, Depends
from ..config import Settings
from ..dependencies import get_settings
from ..schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)):
    return HealthResponse(status="ok", max_upload_bytes=settings.max_upload_bytes)
