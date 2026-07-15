from __future__ import annotations

import json
from pathlib import Path

from .config import REGEX_RULES_PATH, USER_RULES_PATH
from .models import RegexRule


def _rule_from_dict(item: dict[str, object], custom: bool = False) -> RegexRule | None:
    pattern = str(item.get("pattern", ""))
    if not pattern:
        return None
    raw_name = item.get("name", "Unnamed rule")
    names = dict(raw_name) if isinstance(raw_name, dict) else {}
    name = str(names.get("en") or raw_name)
    raw_description = item.get("description", "")
    descriptions = dict(raw_description) if isinstance(raw_description, dict) else {}
    description = str(descriptions.get("en") or raw_description)
    return RegexRule(
        key=str(item.get("key") or name.lower().replace(" ", "_")),
        name=name,
        pattern=pattern,
        replacement=str(item.get("replacement", "")),
        flags=str(item.get("flags", "")),
        enabled=bool(item.get("enabled", False)),
        description=description,
        category=str(item.get("category", "general")),
        names={str(key): str(value) for key, value in names.items()},
        descriptions={str(key): str(value) for key, value in descriptions.items()},
        custom=custom,
    )


def _load_path(path: Path, custom: bool = False) -> list[RegexRule]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rules: list[RegexRule] = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, dict):
            rule = _rule_from_dict(item, custom=custom)
            if rule:
                rules.append(rule)
    return rules


def load_regex_rules(path: Path = REGEX_RULES_PATH) -> list[RegexRule]:
    builtins = _load_path(path)
    custom_rules = _load_path(USER_RULES_PATH, custom=True)
    known = {rule.key for rule in builtins}
    builtins.extend(rule for rule in custom_rules if rule.key not in known)
    return builtins


def save_custom_regex_rules(rules: list[RegexRule]) -> None:
    USER_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "key": rule.key,
            "name": rule.name,
            "description": rule.description,
            "pattern": rule.pattern,
            "replacement": rule.replacement,
            "flags": rule.flags,
            "enabled": rule.enabled,
            "category": rule.category,
        }
        for rule in rules
        if rule.custom
    ]
    USER_RULES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
