from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .config import APP_NAME, APP_VERSION, resource_path
from .i18n import I18n
from .ui_common import IconToplevel


class AboutDialog(IconToplevel):
    def __init__(self, master: tk.Misc, i18n: I18n) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.title(i18n.t("about_title"))
        self.geometry("780x720")
        self.minsize(620, 540)
        self.transient(master)
        self.grab_set()
        self._photo = None

        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        top = ttk.Frame(root)
        top.pack(fill=tk.X)
        logo_path = Path(resource_path("assets/logo.png"))
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk

                image = Image.open(logo_path)
                image.thumbnail((80, 80))
                self._photo = ImageTk.PhotoImage(image)
                ttk.Label(top, image=self._photo).pack(side=tk.LEFT, padx=(0, 12))
            except Exception:
                pass
        heading = ttk.Frame(top)
        heading.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.W)
        ttk.Label(heading, text=i18n.t("app_title"), font=("Microsoft YaHei UI", 18, "bold")).pack(anchor=tk.W)
        if i18n.t("app_title") != APP_NAME:
            ttk.Label(heading, text=APP_NAME, foreground="#4b6972").pack(anchor=tk.W, pady=(2, 0))

        text_frame = ttk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        text = tk.Text(text_frame, wrap=tk.WORD, height=22, padx=8, pady=8)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.insert("1.0", i18n.t("about_text", version=APP_VERSION))
        text.configure(state=tk.DISABLED)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(root, text=i18n.t("about_close"), command=self.destroy).pack(anchor=tk.E)
