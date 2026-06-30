# -*- coding: utf-8 -*-
"""Configuration loading and saving."""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

from .utils import read_json, write_json, resource_path, writable_path


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class ConfigManager:
    def __init__(self) -> None:
        self.default_path = Path(resource_path("config/default_config.json"))
        self.user_path = writable_path("config/user_config.json")
        self.config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        default = read_json(self.default_path, default={}) or {}
        user = read_json(self.user_path, default={}) or {}
        merged = _deep_merge(default, user)
        env_key = os.getenv("OPENAI_API_KEY", "")
        if env_key and not merged.get("llm", {}).get("api_key"):
            merged.setdefault("llm", {})["api_key"] = env_key
        self.config = merged
        return self.config

    def save(self, config: dict[str, Any] | None = None) -> None:
        cfg = copy.deepcopy(config or self.config)
        if cfg.get("privacy", {}).get("do_not_save_api_key"):
            cfg.setdefault("llm", {})["api_key"] = ""
        write_json(self.user_path, cfg)
        self.config = cfg

    def get(self) -> dict[str, Any]:
        if not self.config:
            return self.load()
        return self.config
