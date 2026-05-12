from pathlib import Path

from app.persistence.database import Database


def test_database_persists_video_and_qa_run(tmp_path: Path) -> None:
    db = Database(tmp_path / "state.sqlite3")
    video = db.upsert_video(
        video_id="sample-test1",
        filename="test1.mp4",
        storage_path=tmp_path / "test1.mp4",
        source="sample",
        duration_sec=16.42,
        width=1280,
        height=720,
        size_bytes=123,
        mime_type="video/mp4",
    )

    run = db.create_run(
        video_id=video["id"],
        question="what happens?",
        model_id="allenai/Molmo2-8B",
        max_fps=2,
        max_new_tokens=512,
    )
    finished = db.finish_run(run["id"], answer="A bartender is working.", latency_ms=250)

    assert video["id"] == "sample-test1"
    assert finished["status"] == "complete"
    assert finished["answer"] == "A bartender is working."

