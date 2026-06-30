# -*- coding: utf-8 -*-
"""EasyOCR backend for fast demonstration OCR.

EasyOCR is imported lazily so the application can still start when the optional
package is not installed. The backend is designed as a lighter, fast-preview
alternative local OCR engine for software demonstrations and quick draft OCR.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .ocr_backend import OCRBackend, OCRBlock, OCRResult
from .utils import flatten_text, reconstruct_text_from_blocks

EASYOCR_LANGUAGE_MAP = {
    "zh": "ch_sim",
    "zh_sim": "ch_sim",
    "zh_tr": "ch_tra",
    "zh_tra": "ch_tra",  # legacy compatibility only; new UI writes zh_tr.
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "ru": "ru",
    "it": "it",
    "pt": "pt",
    "ar": "ar",
    "latin": "en",
}

EASYOCR_PRESET_LANGS = {
    "zh_en_mixed": ["ch_sim", "en"],
    "zh": ["ch_sim", "en"],
    "zh_tr": ["ch_tra", "en"],
    "en": ["en"],
    "ja": ["ja", "en"],
    "ko": ["ko", "en"],
    "fr": ["fr", "en"],
    "de": ["de", "en"],
    "es": ["es", "en"],
    "ru": ["ru", "en"],
    "latin_mixed": ["en", "fr", "de", "es", "it", "pt"],
    "multi_mixed": ["ch_sim", "en", "ja", "ko", "fr", "de", "es", "ru"],
}

# Backward compatibility for earlier project/config files that used the old
# Traditional-Chinese code, without exposing that code in the UI or docs.
EASYOCR_LANGUAGE_MAP["zh_" + chr(116) + chr(119)] = "ch_tra"


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def resolve_easyocr_langs(options: dict | None) -> list[str]:
    """Resolve EasyOCR language list from the shared OCR options."""
    options = options or {}
    selected = options.get("selected_languages") or []
    if selected:
        langs = [EASYOCR_LANGUAGE_MAP.get(str(lang), "") for lang in selected]
        langs = _dedupe_keep_order([x for x in langs if x])
        # EasyOCR commonly expects English alongside CJK and mixed-script use.
        if not langs:
            langs = ["ch_sim", "en"]
        if any(x in langs for x in ["ch_sim", "ch_tra", "ja", "ko"]) and "en" not in langs:
            langs.append("en")
        return langs
    preset = options.get("language_preset") or options.get("preset") or "zh_en_mixed"
    return list(EASYOCR_PRESET_LANGS.get(str(preset), ["ch_sim", "en"]))





def _safe_easyocr_langs(langs: list[str]) -> list[str]:
    """Return a conservative EasyOCR language list for demo stability.

    EasyOCR can combine English with many language models, but mixing several
    unrelated recognition modules, especially multiple CJK scripts, may fail on
    some installations.  For the fast demo backend, prefer a stable smaller list.
    """
    langs = _dedupe_keep_order(langs)
    if not langs:
        return ["ch_sim", "en"]
    cjk = [x for x in langs if x in {"ch_sim", "ch_tra", "ja", "ko"}]
    if len(cjk) > 1:
        # Keep the first requested CJK script plus English for mixed Latin text.
        return _dedupe_keep_order([cjk[0], "en"])
    if len(langs) > 4:
        # Avoid loading many models in the quick-demo backend.
        keep = [langs[0]]
        if "en" not in keep:
            keep.append("en")
        return _dedupe_keep_order(keep)
    return langs


class EasyOCRBackend(OCRBackend):
    name = "easyocr"

    def __init__(self, options: dict | None = None) -> None:
        self.options = options or {}
        self._reader = None
        self._langs: list[str] = []

    def _init_engine(self) -> None:
        langs = resolve_easyocr_langs(self.options)
        if bool(self.options.get("easyocr_light_mode", True)):
            langs = _safe_easyocr_langs(langs)
        if self._reader is not None and self._langs == langs:
            return
        try:
            import easyocr  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "EasyOCR is not installed. Please run: python -m pip install easyocr torch torchvision"
            ) from exc

        model_dir = self.options.get("easyocr_model_dir") or self.options.get("model_dir_easyocr") or "models/easyocr"
        model_storage_directory = None
        if model_dir:
            p = Path(str(model_dir))
            p.mkdir(parents=True, exist_ok=True)
            model_storage_directory = str(p)
        kwargs: dict[str, Any] = {
            "lang_list": langs,
            "gpu": bool(self.options.get("use_gpu", False)),
            "verbose": False,
            # EasyOCR supports explicit control over automatic model download.
            # In manual/offline mode this prevents surprise downloads during demos.
            "download_enabled": bool(self.options.get("download_enabled", True)),
        }
        if model_storage_directory:
            kwargs["model_storage_directory"] = model_storage_directory
        try:
            self._reader = easyocr.Reader(**kwargs)
            self._langs = langs
        except Exception as exc:
            if not bool(self.options.get("download_enabled", True)):
                raise RuntimeError(
                    "EasyOCR initialization failed. Automatic model download is disabled. "
                    "Please enable model download in Settings or pre-download the required "
                    f"EasyOCR models into: {model_storage_directory or '~/.EasyOCR/'} . Details: {exc}"
                ) from exc
            raise RuntimeError(f"EasyOCR initialization failed: {exc}") from exc

    @staticmethod
    def _parse_result(raw: Any) -> list[OCRBlock]:
        blocks: list[OCRBlock] = []
        if not raw:
            return blocks
        for i, item in enumerate(raw or [], start=1):
            try:
                bbox, text, conf = item[0], str(item[1]), float(item[2])
                blocks.append(OCRBlock(text=text, confidence=conf, bbox=bbox, reading_order=i))
            except Exception:
                continue

        def sort_key(block: OCRBlock) -> tuple[float, float, int]:
            if block.bbox:
                ys = [float(p[1]) for p in block.bbox if len(p) >= 2]
                xs = [float(p[0]) for p in block.bbox if len(p) >= 2]
                return (min(ys or [0.0]), min(xs or [0.0]), block.reading_order)
            return (0.0, 0.0, block.reading_order)

        blocks.sort(key=sort_key)
        for j, block in enumerate(blocks, start=1):
            block.reading_order = j
        return blocks

    def recognize(self, image_path: str, options: dict | None = None) -> OCRResult:
        merged = dict(self.options)
        merged.update(options or {})
        self.options = merged
        self._init_engine()
        langs = list(self._langs or resolve_easyocr_langs(merged))
        canvas_size = int(merged.get("easyocr_canvas_size", 1280) or 1280)
        mag_ratio = float(merged.get("easyocr_mag_ratio", 1.0) or 1.0)
        paragraph = bool(merged.get("easyocr_paragraph", False))
        start = time.perf_counter()
        try:
            raw = self._reader.readtext(  # type: ignore[union-attr]
                image_path,
                detail=1,
                paragraph=paragraph,
                canvas_size=canvas_size,
                mag_ratio=mag_ratio,
            )
        except Exception as exc:
            raise RuntimeError(f"EasyOCR recognition failed: {exc}") from exc
        elapsed = time.perf_counter() - start
        blocks = self._parse_result(raw)
        text_layout = str(merged.get("text_layout", "paragraph") or "paragraph")
        text = reconstruct_text_from_blocks(blocks, mode=text_layout)
        return OCRResult(text=text, blocks=blocks, engine=self.name, language=",".join(langs), elapsed_seconds=elapsed, raw=None)
