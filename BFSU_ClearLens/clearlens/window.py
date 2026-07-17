from __future__ import annotations

from typing import Any

import customtkinter as ctk

from .config import resource_path


ctk.set_appearance_mode("light")
try:
    ctk.set_default_color_theme(str(resource_path("assets/clearlens_theme.json")))
except (OSError, ValueError):
    ctk.set_default_color_theme("blue")

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    ApplicationWindow = ctk.CTk
else:
    class ApplicationWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        """CustomTkinter root and tkinterdnd2 on one Tcl interpreter."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)


__all__ = ["ApplicationWindow", "DND_FILES"]
