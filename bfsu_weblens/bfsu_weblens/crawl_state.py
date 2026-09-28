# -*- coding: utf-8 -*-
"""Serializable collection-state helpers for BFSU WebLens.

The result file itself carries a compact JSON checkpoint so an interrupted
Google/Baidu collection can be imported later and resumed safely.  Formats
that support hidden metadata (XLSX/DOCX) keep the checkpoint out of the normal
result table; plain-text formats use an explicit marker that importers ignore
as result data.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any

CRAWL_STATE_VERSION = 1
CRAWL_STATE_MARKER = "__WEBLENS_CRAWL_STATE_V1__"
CRAWL_STATE_SHEET = "_WebLens_Crawl_State"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def normalize_crawl_state(value: Any) -> dict[str, Any] | None:
    """Return a defensive, JSON-safe crawl-state mapping or ``None``."""
    if not isinstance(value, dict):
        return None
    try:
        # Round-trip through JSON to strip accidental Qt/date/object instances.
        cleaned = json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return None
    if not isinstance(cleaned, dict):
        return None
    version = cleaned.get("state_version")
    try:
        version = int(version)
    except Exception:
        version = 0
    if version != CRAWL_STATE_VERSION:
        return None
    engine = str(cleaned.get("engine") or "").strip().lower()
    if engine not in {"google", "baidu"}:
        return None
    cleaned["engine"] = engine
    cleaned["state_version"] = CRAWL_STATE_VERSION
    return cleaned


def state_to_json(state: dict[str, Any] | None) -> str:
    normalized = normalize_crawl_state(state)
    if not normalized:
        return ""
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def state_from_json(text: str | bytes | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        raw = json.loads(str(text).strip())
    except Exception:
        return None
    return normalize_crawl_state(raw)


def copy_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    normalized = normalize_crawl_state(state)
    return deepcopy(normalized) if normalized else None
