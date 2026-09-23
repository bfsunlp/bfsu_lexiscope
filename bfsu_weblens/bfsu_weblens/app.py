# -*- coding: utf-8 -*-
"""PySide6 bootstrap for BFSU WebLens."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _configure_frozen_qt_plugins() -> None:
    """Fallback Qt platform-plugin discovery for frozen Windows/macOS builds."""
    if not getattr(sys, "frozen", False):
        return
    exe_dir = Path(sys.executable).resolve().parent
    meipass = Path(getattr(sys, "_MEIPASS", exe_dir / "_internal"))
    if os.name == "nt":
        platform_file, platform_name = "qwindows.dll", "windows"
    elif sys.platform == "darwin":
        platform_file, platform_name = "libqcocoa.dylib", "cocoa"
    else:
        platform_file, platform_name = "libqxcb.so", "xcb"
    candidates = [
        meipass / "qt_plugins",
        meipass / "PySide6" / "Qt" / "plugins",
        meipass / "PySide6" / "plugins",
        exe_dir / "_internal" / "qt_plugins",
        exe_dir / "_internal" / "PySide6" / "Qt" / "plugins",
        exe_dir / "qt_plugins",
    ]
    for root in candidates:
        if (root / "platforms" / platform_file).exists():
            os.environ.setdefault("QT_PLUGIN_PATH", str(root))
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(root / "platforms"))
            os.environ.setdefault("QT_QPA_PLATFORM", platform_name)
            break


_configure_frozen_qt_plugins()

from PySide6.QtCore import QCoreApplication, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from . import __version__  # noqa: E402
from .resources import application_icon  # noqa: E402
from .ui.main_window import BFSUWebLensWindow  # noqa: E402
from .ui.theme import apply_global_theme  # noqa: E402

APP_NAME = "BFSU WebLens"
APP_VERSION = __version__


def main() -> None:
    # Qt 6 is high-DPI aware by default. PassThrough keeps the actual logical
    # scale factor (for example 125%, 150% or 175%) instead of rounding it to a
    # coarser step before widget layouts are calculated.
    if QApplication.instance() is None:
        try:
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass
    app = QApplication.instance() or QApplication(sys.argv)
    QCoreApplication.setOrganizationName("BFSU")
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(application_icon())
    apply_global_theme(app)
    if "--qt-smoke-test" in sys.argv:
        # Frozen-release smoke test: validate Qt startup, bundled resources and
        # the lazily imported modules used by export/content workflows.
        import importlib
        from .resources import resource_path
        for module_name in (
            "bs4", "charset_normalizer", "lxml_html_clean", "newspaper",
            "openpyxl", "docx", "requests", "selenium",
        ):
            importlib.import_module(module_name)
        for relative in ("assets/app_256.png", "config/default_settings.json"):
            if not resource_path(relative).exists():
                raise RuntimeError(f"Bundled resource is missing: {relative}")
        app.processEvents()
        return
    window = BFSUWebLensWindow()
    window.show()
    raise SystemExit(app.exec())
