from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import ModelStatus

router = APIRouter()


@router.get("/model/status", response_model=ModelStatus)
def model_status(request: Request) -> ModelStatus:
    return request.app.state.analyzer.status()

