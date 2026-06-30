# -*- coding: utf-8 -*-
"""Application launcher."""
from __future__ import annotations

from tkinter import messagebox

from .logger import logger
from .ui_main import MainWindow
from .utils import ensure_runtime_dirs


def main() -> None:
    ensure_runtime_dirs()
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as exc:
        logger.exception("Fatal application error")
        try:
            messagebox.showerror("BFSU ProofLens", f"Application startup failed：{exc}")
        except Exception:
            raise
