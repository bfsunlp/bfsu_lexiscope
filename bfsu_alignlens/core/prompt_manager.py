from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Dict

from .utils import resource_path

_PROMPT_CACHE: Dict[str, str] | None = None


def _parse_prompt_md(text: str) -> Dict[str, str]:
    """Parse root Prompt.md sections headed as `## PROMPT_NAME`."""
    prompts: Dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith('## '):
            if current:
                prompts[current] = '\n'.join(buf).strip()
            current = line[3:].strip()
            buf = []
        elif current:
            buf.append(line)
    if current:
        prompts[current] = '\n'.join(buf).strip()
    return prompts


def load_prompts(force: bool = False) -> Dict[str, str]:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None and not force:
        return _PROMPT_CACHE
    path = resource_path('Prompt.md')
    if path.exists():
        try:
            _PROMPT_CACHE = _parse_prompt_md(path.read_text(encoding='utf-8'))
            return _PROMPT_CACHE
        except Exception:
            pass
    _PROMPT_CACHE = {}
    return _PROMPT_CACHE


def get_prompt(name: str, default: str = '') -> str:
    return load_prompts().get(name, default).strip()


def render_prompt(name: str, default: str = '', **kwargs) -> str:
    text = get_prompt(name, default)
    try:
        return Template(text).safe_substitute(**{k: str(v) for k, v in kwargs.items()}).strip()
    except Exception:
        return text.strip()
