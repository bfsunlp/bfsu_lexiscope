from __future__ import annotations

import copy
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import APP_VERSION, load_default_settings, merge_dicts, normalize_settings
from .models import LLMRule, RegexRule


PROFILE_FORMAT = "bfsu-clearlens-profile"
PROFILE_VERSION = 2
SECRET_KEYS = {"api_key", "openai_api_key", "deepseek_api_key", "api_keys"}


def sanitized_settings(settings: dict[str, Any]) -> dict[str, Any]:
    cleaned = copy.deepcopy(settings)

    def strip_secrets(value: Any) -> None:
        if isinstance(value, dict):
            for key in list(value):
                if key.lower() in SECRET_KEYS or key.lower().endswith("_api_key"):
                    value.pop(key, None)
                else:
                    strip_secrets(value[key])
        elif isinstance(value, list):
            for item in value:
                strip_secrets(item)

    strip_secrets(cleaned)
    return cleaned


def save_profile(
    path: Path,
    settings: dict[str, Any],
    rules: list[RegexRule],
    llm_rules: list[LLMRule] | None = None,
) -> None:
    custom_rules = [asdict(rule) for rule in rules if rule.custom]
    payload = {
        "format": PROFILE_FORMAT,
        "profile_version": PROFILE_VERSION,
        "application_version": APP_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "settings": sanitized_settings(settings),
        "custom_regex_rules": custom_rules,
        "llm_rules": [asdict(rule) for rule in (llm_rules or [])],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profile(path: Path) -> tuple[dict[str, Any], list[RegexRule], list[LLMRule]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("format") != PROFILE_FORMAT:
        raise ValueError("invalid_profile_format")
    imported = payload.get("settings")
    if not isinstance(imported, dict):
        raise ValueError("invalid_profile_settings")
    settings = normalize_settings(merge_dicts(load_default_settings(), sanitized_settings(imported)))
    rules: list[RegexRule] = []
    for raw in payload.get("custom_regex_rules", []):
        if not isinstance(raw, dict) or not raw.get("pattern"):
            continue
        allowed = {name: raw[name] for name in RegexRule.__annotations__ if name in raw}
        allowed["custom"] = True
        rules.append(RegexRule(**allowed))
    llm_rules: list[LLMRule] = []
    seen_llm_keys: set[str] = set()
    for raw in payload.get("llm_rules", []):
        if not isinstance(raw, dict):
            continue
        key = str(raw.get("key", "")).strip()
        name = str(raw.get("name", "")).strip()
        instruction = str(raw.get("instruction", "")).strip()
        if not key or not name or not instruction or key in seen_llm_keys:
            continue
        seen_llm_keys.add(key)
        llm_rules.append(LLMRule(key=key, name=name, instruction=instruction, enabled=bool(raw.get("enabled", True))))
    return settings, rules, llm_rules
