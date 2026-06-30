# -*- coding: utf-8 -*-
"""About dialog."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from .i18n import I18N
from .utils import enable_mousewheel, resource_path


class AboutDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n or I18N("en")
        t = self.i18n.t
        self.title(t("about_title"))
        self.geometry("650x620")
        self.minsize(560, 500)
        self.transient(master)
        self.grab_set()
        self._photo = None
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        top = ttk.Frame(root)
        top.pack(fill=tk.X)
        logo_path = Path(resource_path("assets/logo.png"))
        if not logo_path.exists():
            logo_path = Path(resource_path("assets/app.png"))
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk  # type: ignore
                img = Image.open(logo_path)
                img.thumbnail((80, 80))
                self._photo = ImageTk.PhotoImage(img)
                ttk.Label(top, image=self._photo).pack(side=tk.LEFT, padx=(0, 12))
            except Exception:
                pass
        ttk.Label(top, text="BFSU ProofLens", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT, anchor=tk.W)
        text_frame = ttk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        text = tk.Text(text_frame, wrap=tk.WORD, height=24)
        ybar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=ybar.set)
        text.insert("1.0", t("about_text"))
        text.config(state=tk.DISABLED)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        enable_mousewheel(text)
        ttk.Button(root, text=t("about_close"), command=self.destroy).pack(anchor=tk.E)
