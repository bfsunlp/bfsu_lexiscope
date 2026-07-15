from __future__ import annotations

import json
from dataclasses import asdict

from .config import USER_CONFIG_DIR, USER_LLM_RULES_PATH, load_json
from .models import LLMRule


def load_llm_rules() -> list[LLMRule]:
    payload = load_json(USER_LLM_RULES_PATH, [])
    if not isinstance(payload, list):
        return []
    rules: list[LLMRule] = []
    seen: set[str] = set()
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        key = str(raw.get("key", "")).strip()
        name = str(raw.get("name", "")).strip()
        instruction = str(raw.get("instruction", "")).strip()
        if not key or not name or not instruction or key in seen:
            continue
        seen.add(key)
        rules.append(LLMRule(key=key, name=name, instruction=instruction, enabled=bool(raw.get("enabled", True))))
    return rules


def save_llm_rules(rules: list[LLMRule]) -> None:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_LLM_RULES_PATH.write_text(
        json.dumps([asdict(rule) for rule in rules], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
