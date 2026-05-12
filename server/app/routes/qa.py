from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import DEFAULT_MAX_FPS, DEFAULT_MAX_NEW_TOKENS
from app.schemas import QaRequest

router = APIRouter()


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/qa/stream")
async def stream_qa(request: Request, payload: QaRequest) -> StreamingResponse:
    video = request.app.state.db.get_video(payload.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    video_path = Path(video["storage_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file is missing from local storage.")

    max_fps = payload.max_fps or DEFAULT_MAX_FPS
    max_new_tokens = payload.max_new_tokens or DEFAULT_MAX_NEW_TOKENS
    run = request.app.state.db.create_run(
        video_id=payload.video_id,
        question=payload.question.strip(),
        model_id=request.app.state.analyzer.status().model_id,
        max_fps=max_fps,
        max_new_tokens=max_new_tokens,
    )

    async def events() -> AsyncIterator[str]:
        yield _sse("status", {"run_id": run["id"], "status": "queued"})
        try:
            async with request.app.state.inference_lock:
                if request.app.state.analyzer.status().cold_start_required:
                    request.app.state.db.update_run_status(run["id"], "loading_model")
                    yield _sse("status", {"run_id": run["id"], "status": "loading_model"})

                request.app.state.db.update_run_status(run["id"], "preprocessing_video")
                yield _sse("status", {"run_id": run["id"], "status": "preprocessing_video"})
                request.app.state.db.update_run_status(run["id"], "generating")
                yield _sse("status", {"run_id": run["id"], "status": "generating"})

                result = await asyncio.to_thread(
                    request.app.state.analyzer.answer_video,
                    video_path=video_path,
                    question=payload.question.strip(),
                    max_fps=max_fps,
                    max_new_tokens=max_new_tokens,
                )

                if result.answer:
                    yield _sse("token", {"run_id": run["id"], "text": result.answer})
                finished = request.app.state.db.finish_run(
                    run["id"],
                    answer=result.answer,
                    latency_ms=result.latency_ms,
                )
                yield _sse(
                    "final",
                    {
                        "run_id": run["id"],
                        "answer": finished["answer"],
                        "latency_ms": finished["latency_ms"],
                        "model_id": result.model_id,
                        "device": result.device,
                        "dtype": result.dtype,
                    },
                )
                yield _sse("status", {"run_id": run["id"], "status": "complete"})
        except Exception as exc:
            message = str(exc) or "Video QA failed."
            request.app.state.db.fail_run(run["id"], error_message=message)
            yield _sse(
                "error",
                {
                    "run_id": run["id"],
                    "code": "VIDEO_QA_FAILED",
                    "message": message,
                },
            )

    return StreamingResponse(events(), media_type="text/event-stream")

