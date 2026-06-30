# -*- coding: utf-8 -*-
"""RapidOCR backend for BFSU ProofLens.

RapidOCR is imported lazily so the GUI can start even when optional OCR
packages are not installed.  The wrapper is intentionally tolerant of RapidOCR
minor-version API differences and can parse both the recent RapidOCROutput
object and the older tuple/list outputs.
"""
from __future__ import annotations

import inspect
import time
from pathlib import Path
from typing import Any, Callable

from .ocr_backend import OCRBackend, OCRBlock, OCRResult
from .utils import reconstruct_text_from_blocks

LANGUAGE_PRESETS = {
    "zh_en_mixed": {"label": "中文 + English 混排", "rapid_lang": "ch", "languages": ["zh", "en"]},
    "zh": {"label": "简体中文", "rapid_lang": "ch", "languages": ["zh"]},
    "zh_tr": {"label": "繁體中文", "rapid_lang": "chinese_cht", "languages": ["zh_tr"]},
    "en": {"label": "English", "rapid_lang": "en", "languages": ["en"]},
    "ja": {"label": "日本語", "rapid_lang": "japan", "languages": ["ja"]},
    "ko": {"label": "한국어", "rapid_lang": "korean", "languages": ["ko"]},
    "fr": {"label": "Français", "rapid_lang": "fr", "languages": ["fr"]},
    "de": {"label": "Deutsch", "rapid_lang": "german", "languages": ["de"]},
    "es": {"label": "Español", "rapid_lang": "es", "languages": ["es"]},
    "ru": {"label": "Русский", "rapid_lang": "ru", "languages": ["ru"]},
    "latin_mixed": {"label": "Latin scripts mixed", "rapid_lang": "latin", "languages": ["en", "fr", "de", "es", "it", "pt"]},
    # Do not add zh_tr + English as a preset.  Users can combine zh_tr and en
    # manually in Settings; the selected languages are still recorded in the
    # project metadata and passed to LLM proofreading hints.
    "multi_mixed": {"label": "多语混排 / Multilingual mixed", "rapid_lang": "ch", "languages": ["zh", "en", "ja", "ko", "fr", "de", "es", "ru"]},
}

RAPIDOCR_LANGUAGE_MAP = {
    "zh": "ch",
    "zh_sim": "ch",
    "zh_tr": "chinese_cht",
    "zh_tra": "chinese_cht",  # legacy compatibility only; new UI writes zh_tr.
    "en": "en",
    "ja": "japan",
    "ko": "korean",
    "fr": "fr",
    "de": "german",
    "es": "es",
    "ru": "ru",
    "it": "it",
    "pt": "pt",
    "ar": "ar",
    "latin": "latin",
}

# Backward compatibility for earlier project/config files that used the old
# Traditional-Chinese code, without exposing that code in the UI or docs.
RAPIDOCR_LANGUAGE_MAP["zh_" + chr(116) + chr(119)] = "chinese_cht"

_ENUM_NAME_MAP = {
    "ch": "CH",
    "chinese_cht": "CHINESE_CHT",
    "en": "EN",
    "japan": "JAPAN",
    "korean": "KOREAN",
    "fr": "FRENCH",
    "german": "GERMAN",
    "es": "SPANISH",
    "ru": "RUSSIAN",
    "it": "ITALIAN",
    "pt": "PORTUGUESE",
    "ar": "ARABIC",
    "latin": "LATIN",
    "multi": "MULTI",
    "small": "SMALL",
    "medium": "MEDIUM",
    "mobile": "MOBILE",
    "onnxruntime": "ONNXRUNTIME",
    "ppocrv4": "PPOCRV4",
    "ppocrv6": "PPOCRV6",
}


def resolve_rapid_lang(options: dict | None) -> str:
    """Resolve RapidOCR recognition language from shared OCR options."""
    options = options or {}
    preset = options.get("language_preset") or options.get("preset")
    if preset in LANGUAGE_PRESETS:
        return LANGUAGE_PRESETS[preset]["rapid_lang"]

    selected = [str(x) for x in (options.get("selected_languages") or []) if str(x).strip()]
    if selected:
        mapped = [RAPIDOCR_LANGUAGE_MAP.get(lang, "") for lang in selected]
        mapped = [lang for lang in mapped if lang]
        if len(mapped) == 1:
            return mapped[0]
        # RapidOCR runs a single recognition model per engine instance.  For a
        # user-selected mixture that includes Traditional Chinese, prioritize
        # the Traditional model; otherwise default to the robust Chinese model.
        if "chinese_cht" in mapped:
            return "chinese_cht"
        if "ch" in mapped:
            return "ch"
        if "en" in mapped:
            return "en"
        return mapped[0]

    return str(options.get("rapid_lang") or options.get("lang") or "ch")


def _as_list(value: Any) -> Any:
    if value is None:
        return None
    try:
        return value.tolist()  # type: ignore[attr-defined]
    except Exception:
        return value


def _enum_value(enum_cls: Any, code: str, fallback: Any = None) -> Any:
    if enum_cls is None:
        return fallback if fallback is not None else code
    candidates = []
    mapped = _ENUM_NAME_MAP.get(str(code).lower())
    if mapped:
        candidates.append(mapped)
    candidates.append(str(code).upper().replace("-", "_").replace(".", ""))
    for name in candidates:
        if hasattr(enum_cls, name):
            return getattr(enum_cls, name)
    return fallback if fallback is not None else code


def _safe_import_rapidocr_enums() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        import rapidocr  # type: ignore
        for name in ("EngineType", "LangDet", "LangRec", "ModelType", "OCRVersion"):
            if hasattr(rapidocr, name):
                out[name] = getattr(rapidocr, name)
    except Exception:
        pass
    try:
        from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion  # type: ignore
        out.update({
            "EngineType": EngineType,
            "LangDet": LangDet,
            "LangRec": LangRec,
            "ModelType": ModelType,
            "OCRVersion": OCRVersion,
        })
    except Exception:
        pass
    return out


def _rapidocr_params_supported(cls: Any) -> bool:
    try:
        params = inspect.signature(cls).parameters
    except Exception:
        return True
    return "params" in params or any(getattr(p, "kind", None) == inspect.Parameter.VAR_KEYWORD for p in params.values())


def _build_v3_params(options: dict[str, Any], rapid_lang: str) -> dict[str, Any]:
    enums = _safe_import_rapidocr_enums()
    engine_type = _enum_value(enums.get("EngineType"), "onnxruntime")
    model_type = _enum_value(enums.get("ModelType"), str(options.get("rapidocr_model_type") or "small"))
    det_lang = "ch" if rapid_lang in {"ch", "chinese_cht"} else ("en" if rapid_lang == "en" else "multi")
    return {
        "Det.engine_type": engine_type,
        "Det.lang_type": _enum_value(enums.get("LangDet"), det_lang),
        "Det.model_type": model_type,
        "Det.ocr_version": _enum_value(enums.get("OCRVersion"), "ppocrv6"),
        "Rec.engine_type": engine_type,
        "Rec.lang_type": _enum_value(enums.get("LangRec"), rapid_lang),
        "Rec.model_type": model_type,
        "Rec.ocr_version": _enum_value(enums.get("OCRVersion"), "ppocrv6"),
        "Cls.engine_type": engine_type,
        "Cls.lang_type": _enum_value(enums.get("LangDet"), "ch"),
        "Cls.model_type": _enum_value(enums.get("ModelType"), "mobile"),
        "Cls.ocr_version": _enum_value(enums.get("OCRVersion"), "ppocrv4"),
    }


def _raw_to_plain(raw: Any) -> Any:
    if raw is None or isinstance(raw, (str, int, float, bool)):
        return raw
    if isinstance(raw, dict):
        return {k: _raw_to_plain(v) for k, v in raw.items()}
    if isinstance(raw, (list, tuple)):
        return [_raw_to_plain(x) for x in raw]
    for attr in ("to_dict", "model_dump", "dict"):
        try:
            method = getattr(raw, attr)
            if callable(method):
                return _raw_to_plain(method())
        except Exception:
            pass
    try:
        return _raw_to_plain(vars(raw))
    except Exception:
        return str(raw)


def _coerce_score(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _parse_output(raw: Any) -> tuple[list[OCRBlock], float, Any]:
    blocks: list[OCRBlock] = []
    elapsed = 0.0

    # RapidOCR >= 3 returns RapidOCROutput with boxes/txts/scores/elapse.
    boxes = getattr(raw, "boxes", None)
    txts = getattr(raw, "txts", None)
    scores = getattr(raw, "scores", None)
    elapse = getattr(raw, "elapse", None)
    if boxes is not None or txts is not None:
        box_list = _as_list(boxes) or []
        txt_list = list(_as_list(txts) or [])
        score_list = list(_as_list(scores) or [])
        for i, text in enumerate(txt_list):
            bbox = _as_list(box_list[i]) if i < len(box_list) else None
            score = score_list[i] if i < len(score_list) else 0.0
            blocks.append(OCRBlock(text=str(text), confidence=_coerce_score(score), bbox=bbox, reading_order=i))
        try:
            if isinstance(elapse, (list, tuple)):
                elapsed = sum(float(x) for x in elapse)
            elif elapse is not None:
                elapsed = float(elapse)
        except Exception:
            elapsed = 0.0
        return blocks, elapsed, _raw_to_plain(raw)

    # Older RapidOCR outputs can be (results, elapse), where each result is
    # [bbox, text, score] or [bbox, (text, score)].
    data = raw
    if isinstance(raw, tuple) and raw:
        data = raw[0]
        if len(raw) > 1:
            try:
                elapsed = sum(float(x) for x in raw[1]) if isinstance(raw[1], (list, tuple)) else float(raw[1])
            except Exception:
                elapsed = 0.0
    if isinstance(data, dict):
        data = data.get("dt_boxes") or data.get("rec_res") or data.get("result") or data.get("ocr_result") or []
    if isinstance(data, (list, tuple)):
        for i, item in enumerate(data):
            try:
                bbox = _as_list(item[0]) if len(item) > 0 else None
                text = ""
                score = 0.0
                if len(item) >= 3:
                    text = str(item[1])
                    score = _coerce_score(item[2])
                elif len(item) >= 2 and isinstance(item[1], (list, tuple)) and item[1]:
                    text = str(item[1][0])
                    score = _coerce_score(item[1][1] if len(item[1]) > 1 else 0.0)
                elif len(item) >= 2:
                    text = str(item[1])
                if text:
                    blocks.append(OCRBlock(text=text, confidence=score, bbox=bbox, reading_order=i))
            except Exception:
                continue
    return blocks, elapsed, _raw_to_plain(raw)


class RapidOCRBackend(OCRBackend):
    name = "rapidocr"

    def __init__(self, options: dict | None = None) -> None:
        self.options = options or {}
        self._ocr = None
        self._rapid_lang = resolve_rapid_lang(self.options)

    def prepare(self, progress_callback: Callable[[dict[str, Any]], None] | None = None) -> None:
        """Initialize the engine so missing RapidOCR models can be resolved."""
        self._init_engine(progress_callback=progress_callback)

    def _emit(self, progress_callback: Callable[[dict[str, Any]], None] | None, value: float, message: str) -> None:
        if progress_callback:
            progress_callback({"value": value, "message": message})

    def _init_engine(self, progress_callback: Callable[[dict[str, Any]], None] | None = None) -> None:
        if self._ocr is not None:
            return
        try:
            import rapidocr as rapidocr_pkg  # type: ignore
            from rapidocr import RapidOCR  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "未安装 RapidOCR 或 onnxruntime。请先运行：\n"
                "python -m pip install rapidocr onnxruntime"
            ) from exc

        model_dir = Path(str(self.options.get("rapidocr_model_dir") or self.options.get("model_dir") or "models/rapidocr"))
        try:
            model_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self._rapid_lang = resolve_rapid_lang(self.options)
        version = getattr(rapidocr_pkg, "__version__", "unknown")
        self._emit(progress_callback, 15, f"RapidOCR {version}: 正在检查识别模型（{self._rapid_lang}）……")

        errors: list[str] = []
        # RapidOCR 3.x: params can trigger hosted-model resolution/download.
        if _rapidocr_params_supported(RapidOCR):
            try:
                self._ocr = RapidOCR(params=_build_v3_params(self.options, self._rapid_lang))
                self._emit(progress_callback, 80, "RapidOCR 模型已准备完成。")
                return
            except Exception as exc:
                errors.append(f"params: {exc}")
                self._ocr = None

        # Fallback for older RapidOCR APIs or installs without exported enums.
        try:
            self._ocr = RapidOCR()
            self._emit(progress_callback, 80, "RapidOCR 默认模型已准备完成。")
            return
        except Exception as exc:
            errors.append(f"default: {exc}")
            self._ocr = None

        detail = " | ".join(errors)
        raise RuntimeError(f"RapidOCR 初始化失败，无法准备模型。{detail}")

    def recognize(self, image_path: str, options: dict | None = None) -> OCRResult:
        opts = dict(self.options)
        if options:
            opts.update(options)
        self.options = opts
        start = time.perf_counter()
        self._init_engine()
        use_cls = bool(opts.get("use_angle_cls", True))
        try:
            raw = self._ocr(image_path, use_cls=use_cls)  # type: ignore[misc]
        except TypeError:
            raw = self._ocr(image_path)  # type: ignore[misc]
        blocks, inferred_elapsed, plain_raw = _parse_output(raw)
        if not blocks:
            text = ""
        elif str(opts.get("text_layout", "paragraph")).lower() == "line":
            text = "\n".join(block.text for block in blocks)
        else:
            text = reconstruct_text_from_blocks(blocks)
        elapsed = inferred_elapsed or (time.perf_counter() - start)
        return OCRResult(text=text, blocks=blocks, engine="rapidocr", language=self._rapid_lang, elapsed_seconds=elapsed, raw=plain_raw)


def prepare_rapidocr_models(options: dict | None = None, progress_callback: Callable[[dict[str, Any]], None] | None = None) -> bool:
    """Pre-initialize RapidOCR so the UI can show a model check/download step."""
    backend = RapidOCRBackend(options or {})
    backend.prepare(progress_callback=progress_callback)
    return True
