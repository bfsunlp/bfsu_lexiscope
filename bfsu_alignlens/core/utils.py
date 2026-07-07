from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def app_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_path(*parts: str) -> Path:
    """Return a project resource path in source and PyInstaller builds.

    In source mode and in the preferred one-dir package, resources live beside
    the program.  Some PyInstaller configurations place --add-data files under
    sys._MEIPASS / _internal; this fallback keeps the app usable in both layouts.
    Writable folders such as config, log and models should still be copied or
    created beside the executable for normal user operation.
    """
    candidate = app_root().joinpath(*parts)
    if candidate.exists():
        return candidate
    bundle_root = getattr(sys, '_MEIPASS', None)
    if bundle_root:
        bundled = Path(bundle_root).joinpath(*parts)
        if bundled.exists():
            return bundled
    return candidate


def ensure_dirs() -> None:
    for name in ["log", "models", "config", "assets", "locales"]:
        resource_path(name).mkdir(parents=True, exist_ok=True)


def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def safe_json_load(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default
    return default


def safe_json_dump(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def conv(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, Path):
            return str(o)
        return str(o)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=conv), encoding='utf-8')


def open_path(path: str) -> None:
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception as exc:
        raise RuntimeError(f"Cannot open path: {path}\n{exc}") from exc



def normalized_file_key(path: str) -> str:
    """Return a stable, case-insensitive key for duplicate file detection."""
    try:
        return str(Path(path).expanduser().resolve()).casefold()
    except Exception:
        return os.path.abspath(os.path.expanduser(str(path))).casefold()


def file_already_imported(path: str, records: List[Any]) -> bool:
    """True when a path is already present in the imported FileRecord list."""
    key = normalized_file_key(path)
    for rec in records:
        try:
            if normalized_file_key(getattr(rec, 'path', '')) == key:
                return True
        except Exception:
            continue
    return False


def format_bytes(n: int) -> str:
    n = int(n or 0)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == 'B' else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def now_str() -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S')


class UndoRedoStack:
    def __init__(self, max_steps: int = 50):
        self.max_steps = max_steps
        self.undo_stack: List[Any] = []
        self.redo_stack: List[Any] = []

    def push(self, state: Any):
        self.undo_stack.append(deepcopy(state))
        if len(self.undo_stack) > self.max_steps:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_state: Any) -> Optional[Any]:
        if not self.undo_stack:
            return None
        self.redo_stack.append(deepcopy(current_state))
        return self.undo_stack.pop()

    def redo(self, current_state: Any) -> Optional[Any]:
        if not self.redo_stack:
            return None
        self.undo_stack.append(deepcopy(current_state))
        return self.redo_stack.pop()


def strip_markdown(text: str) -> str:
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.S)
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'^[#>*\-+\s]+', '', text, flags=re.M)
    return text
