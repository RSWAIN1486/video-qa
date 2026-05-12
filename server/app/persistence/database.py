from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    storage_path TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL CHECK (source IN ('sample', 'upload')),
                    duration_sec REAL NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    mime_type TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS qa_runs (
                    id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT,
                    status TEXT NOT NULL,
                    latency_ms INTEGER,
                    model_id TEXT,
                    max_fps REAL,
                    max_new_tokens INTEGER,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_qa_runs_created_at ON qa_runs(created_at DESC);
                """
            )

    def upsert_video(
        self,
        *,
        video_id: Optional[str],
        filename: str,
        storage_path: Path,
        source: str,
        duration_sec: float,
        width: int,
        height: int,
        size_bytes: int,
        mime_type: Optional[str] = None,
    ) -> dict[str, Any]:
        created_at = utc_now()
        row_id = video_id or str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO videos (
                    id, filename, storage_path, source, duration_sec, width, height,
                    size_bytes, mime_type, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(storage_path) DO UPDATE SET
                    filename = excluded.filename,
                    source = excluded.source,
                    duration_sec = excluded.duration_sec,
                    width = excluded.width,
                    height = excluded.height,
                    size_bytes = excluded.size_bytes,
                    mime_type = excluded.mime_type
                """,
                (
                    row_id,
                    filename,
                    str(Path(storage_path).resolve()),
                    source,
                    duration_sec,
                    width,
                    height,
                    size_bytes,
                    mime_type,
                    created_at,
                ),
            )
            row = conn.execute(
                "SELECT * FROM videos WHERE storage_path = ?",
                (str(Path(storage_path).resolve()),),
            ).fetchone()
        return dict(row)

    def list_videos(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY source = 'sample' DESC, created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_video(self, video_id: str) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        return dict(row) if row else None

    def create_run(
        self,
        *,
        video_id: str,
        question: str,
        model_id: str,
        max_fps: float,
        max_new_tokens: int,
    ) -> dict[str, Any]:
        run_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO qa_runs (
                    id, video_id, question, status, model_id, max_fps,
                    max_new_tokens, created_at
                )
                VALUES (?, ?, ?, 'queued', ?, ?, ?, ?)
                """,
                (run_id, video_id, question, model_id, max_fps, max_new_tokens, utc_now()),
            )
            row = conn.execute("SELECT * FROM qa_runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row)

    def update_run_status(self, run_id: str, status: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE qa_runs SET status = ? WHERE id = ?", (status, run_id))

    def finish_run(self, run_id: str, *, answer: str, latency_ms: int) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE qa_runs
                SET status = 'complete', answer = ?, latency_ms = ?, completed_at = ?
                WHERE id = ?
                """,
                (answer, latency_ms, utc_now(), run_id),
            )
            row = conn.execute("SELECT * FROM qa_runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row)

    def fail_run(self, run_id: str, *, error_message: str) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE qa_runs
                SET status = 'error', error_message = ?, completed_at = ?
                WHERE id = ?
                """,
                (error_message, utc_now(), run_id),
            )
            row = conn.execute("SELECT * FROM qa_runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row)

    def list_runs(self, limit: int = 25) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM qa_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

