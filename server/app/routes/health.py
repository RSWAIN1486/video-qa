from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import HealthResponse
from app.services.video_metadata import ffprobe_available

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(
        ok=True,
        ffmpeg_available=ffprobe_available(),
        storage_path=str(request.app.state.upload_dir),
        database_path=str(request.app.state.db.path),
    )

