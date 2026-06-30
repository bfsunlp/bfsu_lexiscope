# -*- coding: utf-8 -*-
"""Top-level worker functions for threaded/process batch tasks.

These functions intentionally avoid importing any Tkinter UI modules so that
ProcessPoolExecutor can import them safely on Windows and in PyInstaller builds.
"""
from __future__ import annotations

from typing import Any
import json
import threading

from .llm_backend import LLMBackend
from .rapid_ocr_backend import RapidOCRBackend
from .easy_ocr_backend import EasyOCRBackend


_thread_local = threading.local()


def _options_key(options: dict[str, Any]) -> str:
    try:
        return json.dumps(options, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        return str(sorted((str(k), str(v)) for k, v in options.items()))


def _get_cached_backend(cache_name: str, backend_cls: Any, options: dict[str, Any]) -> Any:
    key = _options_key(options)
    cache = getattr(_thread_local, cache_name, None)
    if not isinstance(cache, dict):
        cache = {}
        setattr(_thread_local, cache_name, cache)
    backend = cache.get(key)
    if backend is None:
        backend = backend_cls(options)
        cache.clear()
        cache[key] = backend
    return backend


def rapidocr_recognize_page(job: dict[str, Any]) -> dict[str, Any]:
    """Recognize one image page with RapidOCR and return a serializable dict.

    If RapidOCR fails with a runtime/model error and automatic fallback is
    enabled, use EasyOCR as a fast safety net.  This keeps demonstrations moving
    on machines where model download or ONNXRuntime initialization fails.
    """
    image_path = str(job.get("image_path") or "")
    options = dict(job.get("options") or {})
    try:
        backend = _get_cached_backend("rapidocr_cache", RapidOCRBackend, options)
        result = backend.recognize(image_path, options)
        return result.to_dict()
    except Exception as rapid_exc:
        if not bool(options.get("auto_fallback_to_easyocr", True)):
            raise
        try:
            fallback_options = dict(options)
            fallback_options["easyocr_light_mode"] = True
            fallback_options["parallel_backend"] = "thread"
            fallback_backend = _get_cached_backend("easyocr_fallback_cache", EasyOCRBackend, fallback_options)
            result = fallback_backend.recognize(image_path, fallback_options)
            data = result.to_dict()
            data["engine"] = "easyocr_fallback"
            data["fallback_reason"] = str(rapid_exc)
            data["warnings"] = ["RapidOCR failed; EasyOCR fallback was used."]
            return data
        except Exception as easy_exc:
            raise RuntimeError(
                "RapidOCR failed and EasyOCR fallback also failed. "
                f"RapidOCR error: {rapid_exc}; EasyOCR fallback error: {easy_exc}"
            ) from easy_exc


def easyocr_recognize_page(job: dict[str, Any]) -> dict[str, Any]:
    """Recognize one image page with EasyOCR and return a serializable dict."""
    image_path = str(job.get("image_path") or "")
    options = dict(job.get("options") or {})
    backend = _get_cached_backend("easyocr_cache", EasyOCRBackend, options)
    result = backend.recognize(image_path, options)
    return result.to_dict()


def llm_ocr_page(job: dict[str, Any]) -> dict[str, Any]:
    """Run LLM OCR for one image page."""
    image_path = str(job.get("image_path") or "")
    language_hint = str(job.get("language_hint") or "")
    llm_cfg = dict(job.get("llm_cfg") or {})
    backend = LLMBackend(llm_cfg)
    return backend.ocr_image(image_path, language_hint=language_hint)


def llm_proofread_page(job: dict[str, Any]) -> dict[str, Any]:
    """Run LLM proofreading for one page."""
    llm_cfg = dict(job.get("llm_cfg") or {})
    backend = LLMBackend(llm_cfg)
    return backend.proofread(
        str(job.get("ocr_text") or ""),
        str(job.get("edited_text") or ""),
        image_path=job.get("image_path"),
        language_hint=str(job.get("language_hint") or ""),
    )
