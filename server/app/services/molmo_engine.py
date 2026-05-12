from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Protocol

from app.config import MODEL_ID
from app.schemas import ModelStatus, VideoAnswer


class VideoAnalyzer(Protocol):
    def status(self) -> ModelStatus:
        ...

    def answer_video(
        self,
        *,
        video_path: Path,
        question: str,
        max_fps: float,
        max_new_tokens: int,
    ) -> VideoAnswer:
        ...


class MolmoVideoEngine:
    """Lazy Transformers runtime for native Molmo2 video QA."""

    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.processor = None
        self.model = None
        self.device: Optional[str] = None
        self.dtype: Optional[str] = None
        self.loading = False
        self.last_error: Optional[str] = None

    def status(self) -> ModelStatus:
        return ModelStatus(
            model_id=self.model_id,
            loaded=self.model is not None and self.processor is not None,
            loading=self.loading,
            device=self.device,
            dtype=self.dtype,
            last_error=self.last_error,
            cold_start_required=self.model is None or self.processor is None,
        )

    def _load(self) -> None:
        if self.model is not None and self.processor is not None:
            return

        self.loading = True
        self.last_error = None
        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor

            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                trust_remote_code=True,
                dtype="auto",
                device_map="auto",
            )
            self.device = self._detect_device()
            self.dtype = str(getattr(self.model, "dtype", "auto"))
        except Exception as exc:  # pragma: no cover - depends on local/GPU runtime.
            self.last_error = str(exc)
            raise
        finally:
            self.loading = False

    def _detect_device(self) -> Optional[str]:
        if self.model is None:
            return None
        device = getattr(self.model, "device", None)
        if device is not None:
            return str(device)
        try:
            return str(next(self.model.parameters()).device)
        except Exception:
            return None

    def answer_video(
        self,
        *,
        video_path: Path,
        question: str,
        max_fps: float,
        max_new_tokens: int,
    ) -> VideoAnswer:
        started = time.perf_counter()
        self._load()

        import torch

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "video", "video": str(video_path), "max_fps": max_fps},
                ],
            }
        ]

        inputs = self._prepare_inputs(messages)
        model_device = self._model_device()
        inputs = {
            key: value.to(model_device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)

        prompt_len = inputs["input_ids"].size(1)
        generated_tokens = generated_ids[0, prompt_len:]
        answer = self.processor.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        return VideoAnswer(
            answer=answer,
            model_id=self.model_id,
            latency_ms=latency_ms,
            device=self.device,
            dtype=self.dtype,
        )

    def _prepare_inputs(self, messages: list[dict]):
        try:
            from molmo_utils import process_vision_info

            _, videos, video_kwargs = process_vision_info(messages)
            videos, video_metadatas = zip(*videos)
            text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            return self.processor(
                videos=list(videos),
                video_metadata=list(video_metadatas),
                text=text,
                padding=True,
                return_tensors="pt",
                **video_kwargs,
            )
        except Exception:
            return self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            )

    def _model_device(self):
        if self.model is None:
            return "cpu"
        try:
            return next(self.model.parameters()).device
        except Exception:
            return getattr(self.model, "device", "cpu")

