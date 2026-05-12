from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DB_PATH, SAMPLE_VIDEO_PATH, UPLOAD_DIR, ensure_data_dirs
from app.persistence.database import Database
from app.routes import health, model, qa, videos
from app.services.molmo_engine import MolmoVideoEngine, VideoAnalyzer
from app.services.video_metadata import VideoMetadataError, extract_video_metadata


def create_app(
    *,
    analyzer: Optional[VideoAnalyzer] = None,
    db_path: Optional[Path] = None,
    upload_dir: Optional[Path] = None,
    sample_video_path: Optional[Path] = None,
) -> FastAPI:
    ensure_data_dirs()
    app = FastAPI(title="Molmo2 Video QA Demo", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.upload_dir = Path(upload_dir or UPLOAD_DIR).resolve()
    app.state.upload_dir.mkdir(parents=True, exist_ok=True)
    app.state.db = Database(Path(db_path or DB_PATH).resolve())
    app.state.analyzer = analyzer or MolmoVideoEngine()
    app.state.inference_lock = asyncio.Lock()
    app.state.sample_video_path = Path(sample_video_path or SAMPLE_VIDEO_PATH).resolve()

    app.include_router(health.router, prefix="/api")
    app.include_router(model.router, prefix="/api")
    app.include_router(videos.router, prefix="/api")
    app.include_router(qa.router, prefix="/api")

    register_sample_video(app)
    return app


def register_sample_video(app: FastAPI) -> None:
    sample_path: Path = app.state.sample_video_path
    if not sample_path.exists():
        return
    try:
        metadata = extract_video_metadata(sample_path)
    except VideoMetadataError:
        return

    app.state.db.upsert_video(
        video_id="sample-test1",
        filename=sample_path.name,
        storage_path=sample_path,
        source="sample",
        duration_sec=metadata.duration_sec,
        width=metadata.width,
        height=metadata.height,
        size_bytes=sample_path.stat().st_size,
        mime_type="video/mp4",
    )


app = create_app()

