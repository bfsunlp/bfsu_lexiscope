from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


APP_NAME = "BFSU ClearLens"
APP_NAME_ZH = "BFSU 文本整理器"
APP_VERSION = "1.5.11"
SOURCE_ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
INTERNAL_ROOT = Path(getattr(sys, "_MEIPASS", EXECUTABLE_ROOT))


def resource_path(relative: str) -> Path:
    external = EXECUTABLE_ROOT / relative
    if external.exists():
        return external
    return INTERNAL_ROOT / relative


PACKAGE_ROOT = EXECUTABLE_ROOT
CONFIG_DIR = resource_path("config")
DEFAULT_SETTINGS_PATH = CONFIG_DIR / "default_settings.json"
REGEX_RULES_PATH = CONFIG_DIR / "regex_rules.json"
USER_CONFIG_DIR = Path(os.getenv("APPDATA") or Path.home()) / "BFSU_ClearLens"
USER_SETTINGS_PATH = USER_CONFIG_DIR / "settings.json"
USER_RULES_PATH = USER_CONFIG_DIR / "regex_rules.json"
USER_LLM_RULES_PATH = USER_CONFIG_DIR / "llm_rules.json"


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def load_settings() -> dict[str, Any]:
    default_settings = load_default_settings()
    user_settings = load_json(USER_SETTINGS_PATH, {})
    user_ai = user_settings.get("ai", {}) if isinstance(user_settings, dict) else {}
    if isinstance(user_ai, dict):
        if user_ai.get("model") and not user_ai.get("openai_model"):
            user_ai["openai_model"] = user_ai["model"]
        if user_ai.get("api_key") and not user_ai.get("openai_api_key"):
            user_ai["openai_api_key"] = user_ai["api_key"]
    return normalize_settings(merge_dicts(default_settings, user_settings))


def load_default_settings() -> dict[str, Any]:
    return normalize_settings(load_json(DEFAULT_SETTINGS_PATH, {}))


def normalize_settings(settings: dict[str, Any]) -> dict[str, Any]:
    processing = settings.setdefault("processing", {})
    if int(processing.get("max_workers", 0) or 0) <= 0:
        processing["max_workers"] = max(1, (os.cpu_count() or 2) // 2)
    settings.setdefault("editor", {}).setdefault("font_size", 11)
    output = settings.setdefault("output", {})
    output.setdefault("encoding", "utf-8")
    if not str(output.get("encoding", "")).strip():
        output["encoding"] = "utf-8"
    settings.pop("display", None)
    ai = settings.setdefault("ai", {})
    ai.setdefault("provider", "openai")
    ai.setdefault("openai_model", str(ai.get("model", "gpt-5.4-mini")))
    ai.setdefault("deepseek_model", "deepseek-v4-flash")
    ai.setdefault("max_chars_per_request", 24000)
    ai.setdefault("max_output_tokens", 16000)
    ai.setdefault("chunk_overlap_lines", 2)
    ai.setdefault("request_timeout_seconds", 180)
    ai.setdefault("retry_attempts", 2)
    ai.setdefault("adaptive_chunking", True)
    if not ai.get("openai_api_key") and ai.get("api_key"):
        ai["openai_api_key"] = ai.get("api_key")
    ai.setdefault("openai_api_key", "")
    ai.setdefault("deepseek_api_key", "")
    ai.pop("api_key", None)
    ai.pop("model", None)
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
