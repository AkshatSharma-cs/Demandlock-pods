"""Opt-in, CPU-only speech-to-text using faster-whisper."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any


class ASRDisabled(RuntimeError):
    """Raised when speech recognition has not been explicitly enabled."""


class ASRUnavailable(RuntimeError):
    """Raised when faster-whisper or its model cannot be loaded."""


_LANGUAGE_PROMPTS: dict[str, str] = {
    "hi": (
        "मोबाइल स्क्रीन की मरम्मत, सिलाई प्रशिक्षण, सोलर पैनल, "
        "रसोई सहायक, कंप्यूटर ऑपरेटर, हर महीने का वेतन।"
    ),
    "ta": (
        "மொபைல் திரை பழுது பார்க்குதல், தையல் பயிற்சி, சோலார் பேனல், "
        "சமையலறை உதவியாளர், கணினி இயக்குநர், மாத சம்பளம்."
    ),
    "en": (
        "Mobile screen repair, tailoring training, solar panel, kitchen helper, "
        "computer operator, salary per month."
    ),
    "te": (
        "మొబైల్ స్క్రీన్ మరమ్మత్తు, టైలరింగ్ శిక్షణ, సోలార్ ప్యానెల్, "
        "వంటగది సహాయకుడు, కంప్యూటర్ ఆపరేటర్, నెలవారీ జీతం."
    ),
}

_model_lock = threading.Lock()
_cached_model: Any | None = None
_cached_model_size: str | None = None


def _resolve_model_size(model_size: str | None) -> str:
    selected = model_size or os.getenv("WHISPER_MODEL") or "small"
    selected = selected.strip()
    if not selected:
        return "small"
    return selected


def _get_model(model_size: str) -> Any:
    """Load at most one model instance and reuse it across calls."""
    global _cached_model, _cached_model_size

    if _cached_model is not None and _cached_model_size == model_size:
        return _cached_model

    with _model_lock:
        if _cached_model is not None and _cached_model_size == model_size:
            return _cached_model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASRUnavailable(
                "Speech recognition is unavailable because faster-whisper is not installed. "
                "Install it with `python -m pip install faster-whisper`, or use typed input."
            ) from exc

        try:
            loaded_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
            )
        except Exception as exc:
            raise ASRUnavailable(
                f"Could not load the faster-whisper '{model_size}' model. The model may need "
                "to be downloaded or the local cache may be unavailable. Check the model/cache "
                f"and use typed input meanwhile. Details: {exc}"
            ) from exc

        _cached_model = loaded_model
        _cached_model_size = model_size
        return loaded_model


def transcribe_file(
    path: str,
    language: str | None = None,
    model_size: str | None = None,
) -> dict[str, Any]:
    """Transcribe an audio file and return text, language, timings, and model size.

    ASR is opt-in: set ``ENABLE_ASR=true`` before calling this function.
    Model loading is excluded from ``elapsed_s``; the evaluator separately records
    total wall-clock time, including model loading.
    """
    if os.getenv("ENABLE_ASR", "").strip().lower() != "true":
        raise ASRDisabled(
            "Speech recognition is disabled. Set ENABLE_ASR=true to enable it; "
            "typed input remains available."
        )

    audio_path = Path(path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    selected_language = language.strip().lower() if language is not None else None
    if selected_language == "":
        selected_language = None

    if selected_language is not None and selected_language not in _LANGUAGE_PROMPTS:
        supported = ", ".join(sorted(_LANGUAGE_PROMPTS))
        raise ValueError(
            f"Unsupported language '{language}'. Use one of: {supported}."
        )

    selected_model = _resolve_model_size(model_size)
    whisper_model = _get_model(selected_model)

    transcribe_options: dict[str, Any] = {
        "beam_size": 5,
        "vad_filter": True,
    }

    if selected_language is not None:
        transcribe_options["language"] = selected_language
        transcribe_options["initial_prompt"] = _LANGUAGE_PROMPTS[selected_language]

    started = time.perf_counter()

    segments, info = whisper_model.transcribe(
        str(audio_path),
        **transcribe_options,
    )
    text = "".join(segment.text for segment in segments).strip()

    elapsed_s = time.perf_counter() - started

    duration_value = getattr(info, "duration", None)
    try:
        duration_s = (
            float(duration_value)
            if duration_value is not None
            else None
        )
    except (TypeError, ValueError):
        duration_s = None

    detected_language = getattr(info, "language", None) or selected_language

    return {
        "text": text,
        "language": detected_language,
        "duration_s": duration_s,
        "elapsed_s": elapsed_s,
        "model": selected_model,
    }