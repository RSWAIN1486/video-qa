from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import ModelStatus, VideoAnswer


class MockAnalyzer:
    def status(self) -> ModelStatus:
        return ModelStatus(
            model_id="mock-molmo",
            loaded=True,
            loading=False,
            device="cpu",
            dtype="mock",
            cold_start_required=False,
        )

    def answer_video(
        self,
        *,
        video_path: Path,
        question: str,
        max_fps: float,
        max_new_tokens: int,
    ) -> VideoAnswer:
        return VideoAnswer(
            answer=f"Mock answer for: {question}",
            model_id="mock-molmo",
            latency_ms=12,
            device="cpu",
            dtype="mock",
        )


def test_health_and_model_status(tmp_path: Path) -> None:
    sample = tmp_path / "sample.mp4"
    sample.write_bytes(b"not-a-real-video")
    app = create_app(
        analyzer=MockAnalyzer(),
        db_path=tmp_path / "state.sqlite3",
        upload_dir=tmp_path / "uploads",
        sample_video_path=sample,
    )
    client = TestClient(app)

    health = client.get("/api/health")
    status = client.get("/api/model/status")

    assert health.status_code == 200
    assert status.status_code == 200
    assert status.json()["model_id"] == "mock-molmo"


def test_qa_stream_contract(tmp_path: Path) -> None:
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"fake")
    app = create_app(
        analyzer=MockAnalyzer(),
        db_path=tmp_path / "state.sqlite3",
        upload_dir=tmp_path / "uploads",
        sample_video_path=tmp_path / "missing.mp4",
    )
    row = app.state.db.upsert_video(
        video_id="vid-1",
        filename="sample.mp4",
        storage_path=video,
        source="sample",
        duration_sec=1,
        width=1280,
        height=720,
        size_bytes=4,
        mime_type="video/mp4",
    )
    client = TestClient(app)

    response = client.post(
        "/api/qa/stream",
        json={"video_id": row["id"], "question": "what do you see?"},
    )

    assert response.status_code == 200
    body = response.text
    assert "event: status" in body
    assert "event: token" in body
    assert "event: final" in body
    assert "Mock answer for: what do you see?" in body

