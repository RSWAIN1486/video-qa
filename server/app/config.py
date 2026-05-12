from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("VIDEO_QA_DATA_DIR", ROOT_DIR / "data")).resolve()
UPLOAD_DIR = Path(os.getenv("VIDEO_QA_UPLOAD_DIR", DATA_DIR / "uploads")).resolve()
DB_PATH = Path(os.getenv("VIDEO_QA_DB_PATH", DATA_DIR / "db" / "video_qa.sqlite3")).resolve()
SAMPLE_VIDEO_PATH = Path(os.getenv("VIDEO_QA_SAMPLE_VIDEO", ROOT_DIR / "test1.mp4")).resolve()

MODEL_ID = os.getenv("VIDEO_QA_MODEL_ID", "allenai/Molmo2-8B")
MAX_UPLOAD_BYTES = int(os.getenv("VIDEO_QA_MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))
MAX_VIDEO_SECONDS = float(os.getenv("VIDEO_QA_MAX_VIDEO_SECONDS", "60"))
DEFAULT_MAX_FPS = float(os.getenv("VIDEO_QA_DEFAULT_MAX_FPS", "2"))
DEFAULT_MAX_NEW_TOKENS = int(os.getenv("VIDEO_QA_DEFAULT_MAX_NEW_TOKENS", "512"))

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}
ALLOWED_MIME_PREFIXES = ("video/", "application/octet-stream")


def ensure_data_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
