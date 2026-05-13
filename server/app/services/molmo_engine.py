from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Optional, Protocol

from app.config import MODEL_ID
from app.schemas import ModelStatus, VideoAnswer, VideoPoint
from app.services.video_metadata import extract_video_metadata

logger = logging.getLogger("uvicorn.error")
COORD_REGEX = re.compile(r"<(?:points|tracks).*? coords=\"([0-9\t:;, .]+)\"/?>")
POINTING_TAG_REGEX = re.compile(r"\s*</?(?:points|tracks)(?:\s+[^>]*)?>\s*")
FRAME_REGEX = re.compile(r"(?:^|\t|:|,|;)([0-9.]+) ([0-9. ]+)")
POINTS_REGEX = re.compile(r"([0-9]+) ([0-9]{3,4}) ([0-9]{3,4})")


class VideoAnalyzer(Protocol):
    def status(self) -> ModelStatus:
        ...

    def load(self) -> ModelStatus:
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

    def load(self) -> ModelStatus:
        self._load()
        return self.status()

    def _load(self) -> None:
        if self.model is not None and self.processor is not None:
            return

        self.loading = True
        self.last_error = None
        started = time.perf_counter()
        logger.info("molmo.load.start model_id=%s", self.model_id)
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
            logger.info(
                "molmo.load.complete model_id=%s device=%s dtype=%s elapsed_ms=%s",
                self.model_id,
                self.device,
                self.dtype,
                int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:  # pragma: no cover - depends on local/GPU runtime.
            self.last_error = str(exc)
            logger.exception("molmo.load.error model_id=%s message=%s", self.model_id, exc)
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
        logger.info(
            "molmo.answer.start video=%s max_fps=%s max_new_tokens=%s question=%r",
            video_path,
            max_fps,
            max_new_tokens,
            question,
        )
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
        logger.info("molmo.answer.inputs_ready video=%s", video_path)
        model_device = self._model_device()
        inputs = {
            key: value.to(model_device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }

        logger.info("molmo.answer.generate_start device=%s", model_device)
        with torch.inference_mode():
            generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        logger.info("molmo.answer.generate_complete")

        prompt_len = inputs["input_ids"].size(1)
        generated_tokens = generated_ids[0, prompt_len:]
        generated_text = self.processor.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        metadata = extract_video_metadata(video_path)
        points = extract_video_points(generated_text, metadata.width, metadata.height)
        answer = clean_pointing_markup(generated_text)
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "molmo.answer.complete latency_ms=%s points=%s answer=%r",
            latency_ms,
            len(points),
            answer[:1000],
        )
        return VideoAnswer(
            answer=answer,
            model_id=self.model_id,
            latency_ms=latency_ms,
            points=points,
            device=self.device,
            dtype=self.dtype,
        )

    def _prepare_inputs(self, messages: list[dict]):
        try:
            from molmo_utils import process_vision_info

            logger.info("molmo.inputs.prepare_with_molmo_utils")
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
        except Exception as exc:
            logger.warning("molmo.inputs.molmo_utils_failed fallback=apply_chat_template message=%s", exc)
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


def _points_from_num_str(text: str, image_w: int, image_h: int):
    for points in POINTS_REGEX.finditer(text):
        label_id, x_text, y_text = points.group(1), points.group(2), points.group(3)
        x = float(x_text) / 1000 * image_w
        y = float(y_text) / 1000 * image_h
        if 0 <= x <= image_w and 0 <= y <= image_h:
            yield label_id, x, y


def extract_video_points(text: str, image_w: int, image_h: int) -> list[VideoPoint]:
    parsed: list[VideoPoint] = []
    for coord in COORD_REGEX.finditer(text):
        for point_group in FRAME_REGEX.finditer(coord.group(1)):
            time_sec = float(point_group.group(1))
            for label_id, x, y in _points_from_num_str(point_group.group(2), image_w, image_h):
                parsed.append(VideoPoint(time_sec=time_sec, x=x, y=y, label_id=label_id))
    return parsed


def clean_pointing_markup(text: str) -> str:
    cleaned = POINTING_TAG_REGEX.sub(" ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()
