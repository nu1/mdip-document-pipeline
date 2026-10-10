from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .pipeline import Pipeline
from .routers import documents, health
from .storage import init_storage


def create_app(
    data_dir: Path | None = None,
    ocr=None,
    max_upload_bytes: int | None = None,
    cors_origins: list[str] | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    cfg = settings or get_settings()
    if data_dir is not None:
        cfg = cfg.model_copy(update={"data_dir": data_dir})
    if max_upload_bytes is not None:
        cfg = cfg.model_copy(update={"max_upload_bytes": max_upload_bytes})
    if cors_origins is not None:
        cfg = cfg.model_copy(update={"cors_origins": cors_origins})

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = cfg
        app.state.repository, app.state.files = init_storage(cfg.db_path, cfg.originals_dir)
        app.state.pipeline = Pipeline(app.state.repository, app.state.files, ocr)
        yield

    app = FastAPI(title="Fletchers document workbench", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(documents.router)

    return app


app = create_app()
