# -*- coding: utf-8 -*-
"""Cross-platform filesystem locations for BFSU WebLens.

Windows releases remain portable: writable application data lives beside the
executable. A macOS .app bundle is treated as read-only after packaging, so
frozen macOS builds use ``~/Library/Application Support/BFSU WebLens``.
Source checkouts continue to use the project root.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "BFSU WebLens"


def source_root() -> Path:
    return Path(__file__).resolve().parent.parent


def install_root() -> Path:
    """Return the install/application root without assuming it is writable."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        if sys.platform == "darwin":
            for parent in exe.parents:
                if parent.suffix.lower() == ".app":
                    return parent
        return exe.parent
    return source_root()


def user_data_root(create: bool = True) -> Path:
    """Return the writable WebLens data root for the current platform."""
    if not getattr(sys, "frozen", False):
        root = source_root()
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    elif os.name == "nt":
        root = Path(sys.executable).resolve().parent
    else:
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        root = (Path(xdg) if xdg else Path.home() / ".local" / "share") / "BFSU_WebLens"
    if create:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return root


def user_cache_root(create: bool = True) -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches" / APP_DIR_NAME
    elif os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        root = (Path(local) / "BFSU_WebLens" / "cache") if local else (user_data_root() / "cache")
    else:
        xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
        root = (Path(xdg) if xdg else Path.home() / ".cache") / "bfsu_weblens"
    if create:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return root


def resource_roots() -> list[Path]:
    """Return candidate roots that may contain bundled assets/config/tools."""
    roots: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        roots.extend([exe.parent, exe.parent / "_internal"])
        if sys.platform == "darwin":
            app = install_root()
            if app.suffix.lower() == ".app":
                roots.extend([
                    app / "Contents" / "Resources",
                    app / "Contents" / "Frameworks",
                    app / "Contents" / "MacOS" / "_internal",
                ])
    roots.append(source_root())

    out: list[Path] = []
    seen: set[str] = set()
    for raw in roots:
        try:
            path = raw.expanduser().resolve()
        except Exception:
            path = raw.expanduser()
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out
