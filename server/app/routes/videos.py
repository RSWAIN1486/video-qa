from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, MAX_VIDEO_SECONDS
from app.schemas import VideoRecord
from app.services.video_metadata import VideoMetadataError, extract_video_metadata

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


def _record_to_schema(row: dict) -> VideoRecord:
    return VideoRecord(
        id=row["id"],
        filename=row["filename"],
        duration_sec=row["duration_sec"],
        width=row["width"],
        height=row["height"],
        size_bytes=row["size_bytes"],
        created_at=row["created_at"],
        source=row["source"],
        content_url=f"/api/videos/{row['id']}/content",
    )


def _safe_filename(filename: str) -> str:
    base = Path(filename or "video.mp4").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return cleaned or "video.mp4"


@router.get("/videos", response_model=list[VideoRecord])
def list_videos(request: Request) -> list[VideoRecord]:
    rows = request.app.state.db.list_videos()
    logger.info("video.list count=%s", len(rows))
    return [_record_to_schema(row) for row in rows]


@router.post("/videos", response_model=VideoRecord)
async def upload_video(request: Request, file: UploadFile = File(...)) -> VideoRecord:
    filename = _safe_filename(file.filename or "video.mp4")
    extension = Path(filename).suffix.lower()
    logger.info("video.upload.start filename=%s content_type=%s", filename, file.content_type)
    if extension not in ALLOWED_EXTENSIONS:
        logger.warning("video.upload.reject filename=%s reason=unsupported_extension", filename)
        raise HTTPException(status_code=400, detail="Upload an MP4, MOV, or WebM video.")

    upload_dir: Path = request.app.state.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid.uuid4().hex}{extension}"

    size = 0
    with stored_path.open("wb") as handle:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                stored_path.unlink(missing_ok=True)
                logger.warning("video.upload.reject filename=%s reason=too_large size=%s", filename, size)
                raise HTTPException(status_code=413, detail="Video is larger than the 200 MB demo limit.")
            handle.write(chunk)

    try:
        metadata = extract_video_metadata(stored_path)
    except VideoMetadataError as exc:
        stored_path.unlink(missing_ok=True)
        logger.exception("video.upload.metadata_error filename=%s message=%s", filename, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if metadata.duration_sec > MAX_VIDEO_SECONDS:
        stored_path.unlink(missing_ok=True)
        logger.warning(
            "video.upload.reject filename=%s reason=too_long duration=%.2f",
            filename,
            metadata.duration_sec,
        )
        raise HTTPException(
            status_code=400,
            detail="V1 is tuned for short videos up to 60 seconds. Long-video chunking is planned next.",
        )

    row = request.app.state.db.upsert_video(
        video_id=None,
        filename=filename,
        storage_path=stored_path,
        source="upload",
        duration_sec=metadata.duration_sec,
        width=metadata.width,
        height=metadata.height,
        size_bytes=size,
        mime_type=file.content_type,
    )
    logger.info(
        "video.upload.complete id=%s filename=%s size=%s duration=%.2f resolution=%sx%s path=%s",
        row["id"],
        filename,
        size,
        metadata.duration_sec,
        metadata.width,
        metadata.height,
        stored_path,
    )
    return _record_to_schema(row)


@router.get("/videos/{video_id}/content")
def video_content(request: Request, video_id: str) -> FileResponse:
    row = request.app.state.db.get_video(video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Video not found.")
    path = Path(row["storage_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file is missing from local storage.")
    media_type = row.get("mime_type") or "video/mp4"
    return FileResponse(path, media_type=media_type, filename=row["filename"])
