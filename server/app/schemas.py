from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool
    ffmpeg_available: bool
    storage_path: str
    database_path: str


class ModelStatus(BaseModel):
    model_id: str
    loaded: bool
    loading: bool
    device: Optional[str] = None
    dtype: Optional[str] = None
    last_error: Optional[str] = None
    cold_start_required: bool


class VideoRecord(BaseModel):
    id: str
    filename: str
    duration_sec: float
    width: int
    height: int
    size_bytes: int
    created_at: str
    source: Literal["sample", "upload"]
    content_url: str


class QaRequest(BaseModel):
    video_id: str
    question: str = Field(min_length=1, max_length=2000)
    max_fps: Optional[float] = Field(default=None, gt=0, le=12)
    max_new_tokens: Optional[int] = Field(default=None, ge=32, le=2048)


class QaRunRecord(BaseModel):
    id: str
    video_id: str
    question: str
    answer: Optional[str] = None
    status: str
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str


class VideoAnswer(BaseModel):
    answer: str
    model_id: str
    latency_ms: int
    device: Optional[str] = None
    dtype: Optional[str] = None

