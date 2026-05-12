from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class VideoMetadataError(RuntimeError):
    pass


@dataclass(frozen=True)
class VideoMetadata:
    duration_sec: float
    width: int
    height: int


def ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def extract_video_metadata(path: Path) -> VideoMetadata:
    if not ffprobe_available():
        raise VideoMetadataError("ffprobe is required. Install ffmpeg before using video uploads.")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "ffprobe could not inspect the video."
        raise VideoMetadataError(message) from exc

    payload = json.loads(completed.stdout)
    video_stream = next(
        (stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        raise VideoMetadataError("The uploaded file does not contain a video stream.")

    duration_text = (
        video_stream.get("duration")
        or payload.get("format", {}).get("duration")
        or "0"
    )
    try:
        duration = float(duration_text)
    except (TypeError, ValueError) as exc:
        raise VideoMetadataError("Could not determine video duration.") from exc

    return VideoMetadata(
        duration_sec=duration,
        width=int(video_stream.get("width") or 0),
        height=int(video_stream.get("height") or 0),
    )

