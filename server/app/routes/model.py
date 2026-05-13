from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request

from app.schemas import ModelStatus

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@router.get("/model/status", response_model=ModelStatus)
def model_status(request: Request) -> ModelStatus:
    return request.app.state.analyzer.status()


@router.post("/model/load", response_model=ModelStatus)
async def load_model(request: Request) -> ModelStatus:
    logger.info("model.load.request")
    async with request.app.state.inference_lock:
        status = await asyncio.to_thread(request.app.state.analyzer.load)
    logger.info(
        "model.load.response loaded=%s loading=%s device=%s dtype=%s",
        status.loaded,
        status.loading,
        status.device,
        status.dtype,
    )
    return status
