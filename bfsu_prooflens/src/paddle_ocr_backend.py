# -*- coding: utf-8 -*-
"""PaddleOCR backend with compatibility support for PaddleOCR 2.x and 3.x.

The module imports PaddleOCR lazily so the GUI can start even before heavy OCR
packages are installed.  PaddleOCR 3.x changed both constructor parameters and
inference calls (``predict`` instead of the older ``ocr`` API), so this wrapper
keeps both paths available and parses both result formats.
"""
from __future__ import annotations

import inspect
import os
import time
from pathlib import Path
from typing import Any

from .ocr_backend import OCRBackend, OCRBlock, OCRResult
from .utils import flatten_text, reconstruct_text_from_blocks

LANGUAGE_PRESETS = {
    "zh_en_mixed": {"label": "中文 + English 混排", "paddle_lang": "ch", "languages": ["zh", "en"]},
    "zh": {"label": "中文", "paddle_lang": "ch", "languages": ["zh"]},
    "en": {"label": "English", "paddle_lang": "en", "languages": ["en"]},
    "ja": {"label": "日本語", "paddle_lang": "japan", "languages": ["ja"]},
    "ko": {"label": "한국어", "paddle_lang": "korean", "languages": ["ko"]},
    "fr": {"label": "Français", "paddle_lang": "fr", "languages": ["fr"]},
    "de": {"label": "Deutsch", "paddle_lang": "german", "languages": ["de"]},
    "es": {"label": "Español", "paddle_lang": "es", "languages": ["es"]},
    "ru": {"label": "Русский", "paddle_lang": "ru", "languages": ["ru"]},
    "latin_mixed": {"label": "Latin scripts mixed", "paddle_lang": "latin", "languages": ["en", "fr", "de", "es", "it", "pt"]},
    "multi_mixed": {"label": "多语混排 / Multilingual mixed", "paddle_lang": "ch", "languages": ["zh", "en", "ja", "ko", "fr", "de", "es", "ru"]},
}


def resolve_paddle_lang(options: dict | None) -> str:
    options = options or {}
    preset = options.get("language_preset") or options.get("preset")
    if preset in LANGUAGE_PRESETS:
        return LANGUAGE_PRESETS[preset]["paddle_lang"]
    selected = set(options.get("selected_languages") or [])
    if {"zh", "en"}.intersection(selected) and len(selected) <= 2:
        return "ch"
    if len(selected) > 1:
        # PaddleOCR cannot truly recognize arbitrary language combinations in a
        # single pipeline.  Use the robust mixed Chinese-English default and keep
        # the selected-language metadata for LLM/proofreading prompts and export.
        return options.get("paddle_lang") or "ch"
    return options.get("paddle_lang") or options.get("lang") or "ch"


def _has_var_kw(params: dict[str, Any]) -> bool:
    for p in params.values():
        if getattr(p, "kind", None) == inspect.Parameter.VAR_KEYWORD:
            return True
    return False


def _filtered_kwargs(callable_obj: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Filter kwargs unless the callable accepts **kwargs."""
    try:
        params = inspect.signature(callable_obj).parameters
    except Exception:
        return kwargs
    if _has_var_kw(params):
        # Some PaddleOCR versions expose **kwargs but still reject legacy names
        # internally.  Keep only the names we know are supported by one of the
        # public API generations if they appear in the signature, or return all
        # if the signature has no named parameters beyond **kwargs.
        named = {k for k, p in params.items() if getattr(p, "kind", None) != inspect.Parameter.VAR_KEYWORD}
        if not named:
            return kwargs
        return {k: v for k, v in kwargs.items() if k in named or k in {"lang", "engine", "device"}}
    return {k: v for k, v in kwargs.items() if k in params}


def _to_plain_data(obj: Any) -> Any:
    """Convert PaddleOCR result objects into dictionaries/lists where possible."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_plain_data(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain_data(x) for x in obj]
    # PaddleOCR 3.x result objects usually expose .res and sometimes .json.
    for attr in ("res", "json"):
        try:
            value = getattr(obj, attr)
            if callable(value):
                value = value()
            if value is not None:
                return _to_plain_data(value)
        except Exception:
            pass
    try:
        return _to_plain_data(vars(obj))
    except Exception:
        return obj


def _box_to_poly(box: Any) -> Any:
    """Convert [x1,y1,x2,y2] boxes into four-point polygons."""
    try:
        if isinstance(box, (list, tuple)) and len(box) == 4 and all(not isinstance(x, (list, tuple)) for x in box):
            x1, y1, x2, y2 = [float(x) for x in box]
            return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    except Exception:
        pass
    try:
        # numpy arrays land here without importing numpy.
        as_list = box.tolist()  # type: ignore[attr-defined]
        return _box_to_poly(as_list)
    except Exception:
        return box


def _configure_paddle_runtime(options: dict[str, Any]) -> None:
    """Set conservative Paddle runtime flags before engine creation.

    Some Windows CPU installations of PaddleOCR 3.x / PaddlePaddle 3.x fail in
    oneDNN/PIR conversion with errors such as
    ConvertPirAttribute2RuntimeAttribute not support pir::ArrayAttribute.  For
    OCR GUI use, stability is more important than maximum CPU kernel speed, so
    the defaults disable oneDNN/MKLDNN and the newer PIR path unless the user
    opts out in Settings.
    """
    source = str(options.get("paddle_model_source", "bos") or "bos").strip()
    if source and source.lower() != "auto":
        os.environ["PADDLE_PDX_MODEL_SOURCE"] = source.upper()
    if bool(options.get("paddle_disable_model_source_check", True)):
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    if bool(options.get("paddle_disable_onednn", True)):
        os.environ["FLAGS_use_mkldnn"] = "0"
        os.environ["FLAGS_use_onednn"] = "0"
        os.environ.setdefault("DNNL_VERBOSE", "0")
    if bool(options.get("paddle_disable_pir", True)):
        os.environ["FLAGS_enable_pir_api"] = "0"


def _is_paddle_runtime_compat_error(exc: Exception) -> bool:
    text = str(exc).lower()
    needles = [
        "convertpirattribute2runtimeattribute",
        "onednn_instruction",
        "pir::arrayattribute",
        "oneDNN".lower(),
        "mkldnn",
        "pir",
    ]
    return any(x in text for x in needles)


class PaddleOCRBackend(OCRBackend):
    name = "paddleocr"

    def __init__(self, options: dict | None = None) -> None:
        self.options = options or {}
        self._ocr = None
        self._api_mode = "unknown"

    def _init_engine(self) -> None:
        if self._ocr is not None:
            return

        # Configure Paddle/PaddleX before importing or constructing PaddleOCR.
        _configure_paddle_runtime(self.options)

        try:
            import paddleocr as paddleocr_pkg  # type: ignore
            from paddleocr import PaddleOCR  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "未安装 PaddleOCR 或 PaddlePaddle。请先运行：\n"
                "python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/\n"
                "python -m pip install \"paddleocr[all]\""
            ) from exc

        lang = resolve_paddle_lang(self.options)
        use_angle = bool(self.options.get("use_angle_cls", True))
        use_gpu = bool(self.options.get("use_gpu", False))
        download_enabled = bool(self.options.get("download_enabled", True))
        version = getattr(paddleocr_pkg, "__version__", "unknown")

        # PaddleOCR 3.x public examples use these parameters and predict().
        kwargs_v3: dict[str, Any] = {
            "lang": lang,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": use_angle,
            "engine": "paddle",
            "device": "gpu:0" if use_gpu else "cpu",
            "enable_mkldnn": not bool(self.options.get("paddle_disable_onednn", True)),
            "cpu_threads": int(self.options.get("paddle_cpu_threads", 4) or 4),
        }
        # PaddleOCR 2.x public examples use these parameters and ocr().
        kwargs_v2: dict[str, Any] = {
            "lang": lang,
            "use_angle_cls": use_angle,
            "use_gpu": use_gpu,
            "show_log": False,
            "enable_mkldnn": not bool(self.options.get("paddle_disable_onednn", True)),
            "cpu_threads": int(self.options.get("paddle_cpu_threads", 4) or 4),
        }
        for candidate in ("download_enable", "download_enabled"):
            kwargs_v3[candidate] = download_enabled
            kwargs_v2[candidate] = download_enabled

        for key in ["det_model_dir", "rec_model_dir", "cls_model_dir"]:
            value = self.options.get(key)
            if value:
                p = Path(value)
                if p.exists():
                    kwargs_v2[key] = str(p)
                    # PaddleOCR 3.x model directory names differ; only pass old
                    # names if the installed class explicitly accepts them.
                    kwargs_v3[key] = str(p)

        errors: list[str] = []
        # Try 3.x-style initialization first.  If this is an older 2.x install,
        # unsupported parameters are filtered out and the old path will still work.
        for label, kwargs in (("3.x", kwargs_v3), ("2.x", kwargs_v2)):
            try:
                filtered = _filtered_kwargs(PaddleOCR, kwargs)
                self._ocr = PaddleOCR(**filtered)
                self._api_mode = label
                return
            except Exception as exc:
                errors.append(f"{label}: {exc}")
                self._ocr = None

        detail = " | ".join(errors)
        hosting_hint = ""
        if "No available model hosting platforms detected" in detail or "model hosting" in detail:
            hosting_hint = (
                "\n\nHint: PaddleOCR could not reach or select a model hosting platform. "
                "In Settings > OCR, try setting Paddle model source to 'bos' or 'modelscope', "
                "enable 'Disable Paddle model source check', or pre-download the models and use manual mode."
            )
        if not download_enabled:
            raise RuntimeError(
                "PaddleOCR initialization failed. Automatic model download is disabled. "
                "Please enable model download in Settings or specify existing local model folders. "
                f"PaddleOCR version: {version}. Details: " + detail + hosting_hint
            )
        raise RuntimeError(f"PaddleOCR initialization failed. PaddleOCR version: {version}. Details: " + detail + hosting_hint)

    @staticmethod
    def _parse_v2_result(raw: Any) -> list[OCRBlock]:
        blocks: list[OCRBlock] = []
        if not raw:
            return blocks
        candidates = raw[0] if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], list) else raw
        for i, item in enumerate(candidates or [], start=1):
            try:
                bbox = item[0]
                rec = item[1]
                text = str(rec[0])
                conf = float(rec[1]) if len(rec) > 1 else 0.0
                blocks.append(OCRBlock(text=text, confidence=conf, bbox=bbox, reading_order=i))
            except Exception:
                continue
        return PaddleOCRBackend._sort_blocks(blocks)

    @staticmethod
    def _parse_v3_result(raw: Any) -> list[OCRBlock]:
        blocks: list[OCRBlock] = []
        data = _to_plain_data(raw)
        items = data if isinstance(data, list) else [data]
        for result_item in items:
            if not isinstance(result_item, dict):
                continue
            res = result_item.get("res") if isinstance(result_item.get("res"), dict) else result_item
            # In PP-Structure output, OCR can be nested inside overall_ocr_res.
            if isinstance(res.get("overall_ocr_res"), dict):
                res = res.get("overall_ocr_res") or res
            texts = res.get("rec_texts") or res.get("texts") or []
            scores = res.get("rec_scores") or res.get("scores") or []
            polys = res.get("rec_polys") or res.get("dt_polys") or res.get("polys") or []
            boxes = res.get("rec_boxes") or res.get("boxes") or []
            try:
                texts = texts.tolist()  # type: ignore[attr-defined]
            except Exception:
                pass
            try:
                scores = scores.tolist()  # type: ignore[attr-defined]
            except Exception:
                pass
            try:
                polys = polys.tolist()  # type: ignore[attr-defined]
            except Exception:
                pass
            try:
                boxes = boxes.tolist()  # type: ignore[attr-defined]
            except Exception:
                pass
            for i, text in enumerate(texts, start=1):
                conf = 0.0
                try:
                    conf = float(scores[i - 1]) if scores is not None and len(scores) >= i else 0.0
                except Exception:
                    pass
                bbox = None
                try:
                    if polys is not None and len(polys) >= i:
                        bbox = polys[i - 1]
                    elif boxes is not None and len(boxes) >= i:
                        bbox = _box_to_poly(boxes[i - 1])
                except Exception:
                    bbox = None
                blocks.append(OCRBlock(text=str(text), confidence=conf, bbox=bbox, reading_order=len(blocks) + 1))
        return PaddleOCRBackend._sort_blocks(blocks)

    @staticmethod
    def _sort_blocks(blocks: list[OCRBlock]) -> list[OCRBlock]:
        def sort_key(block: OCRBlock) -> tuple[float, float, int]:
            if block.bbox:
                try:
                    ys = [float(p[1]) for p in block.bbox if len(p) >= 2]
                    xs = [float(p[0]) for p in block.bbox if len(p) >= 2]
                    return (min(ys or [0.0]), min(xs or [0.0]), block.reading_order)
                except Exception:
                    pass
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
        lang = resolve_paddle_lang(merged)
        start = time.perf_counter()
        def _run_once() -> list[OCRBlock]:
            if hasattr(self._ocr, "predict"):
                raw_local = self._ocr.predict(image_path)  # type: ignore[union-attr]
                return self._parse_v3_result(raw_local)
            try:
                raw_local = self._ocr.ocr(image_path, cls=bool(merged.get("use_angle_cls", True)))  # type: ignore[union-attr]
            except TypeError:
                raw_local = self._ocr.ocr(image_path)  # type: ignore[union-attr]
            return self._parse_v2_result(raw_local)

        try:
            blocks = _run_once()
        except Exception as exc:
            if _is_paddle_runtime_compat_error(exc) and not bool(merged.get("_paddle_runtime_retry", False)):
                # Recreate the engine once with the conservative runtime flags.
                merged["paddle_disable_onednn"] = True
                merged["paddle_disable_pir"] = True
                merged["_paddle_runtime_retry"] = True
                self.options = merged
                self._ocr = None
                _configure_paddle_runtime(merged)
                try:
                    self._init_engine()
                    blocks = _run_once()
                except Exception as retry_exc:
                    raise RuntimeError(
                        "PaddleOCR 识别失败：Paddle/PaddleOCR CPU runtime compatibility error. "
                        "The app has disabled oneDNN/MKLDNN and PIR and retried, but the installed "
                        "Paddle runtime still failed. You can use Fast OCR (EasyOCR), enable automatic "
                        "fallback to EasyOCR, or reinstall a compatible CPU PaddlePaddle/PaddleOCR build. "
                        f"Original error: {exc}; Retry error: {retry_exc}"
                    ) from retry_exc
            else:
                raise RuntimeError(f"PaddleOCR 识别失败：{exc}") from exc
        elapsed = time.perf_counter() - start
        text_layout = str(merged.get("text_layout", "paragraph") or "paragraph")
        text = reconstruct_text_from_blocks(blocks, mode=text_layout)
        return OCRResult(text=text, blocks=blocks, engine=self.name, language=lang, elapsed_seconds=elapsed, raw=None)
