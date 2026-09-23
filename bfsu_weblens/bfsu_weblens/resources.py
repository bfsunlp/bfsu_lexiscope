# -*- coding: utf-8 -*-
"""Qt resource helpers for BFSU WebLens."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

from .platform_paths import resource_roots


def resource_path(relative: str) -> Path:
    rel = Path(relative)
    roots = resource_roots()
    for base in roots:
        candidate = base / rel
        if candidate.exists():
            return candidate
    return (roots[0] if roots else Path.cwd()) / rel


def application_icon() -> QIcon:
    names = ("assets/app.ico", "assets/app_256.png", "assets/app.png") if sys.platform.startswith("win") else (
        "assets/app_256.png", "assets/app.png", "assets/app.ico"
    )
    for name in names:
        path = resource_path(name)
        if path.exists():
            return QIcon(str(path))
    return QIcon()


def apply_window_icon(widget) -> None:
    widget.setWindowIcon(application_icon())
