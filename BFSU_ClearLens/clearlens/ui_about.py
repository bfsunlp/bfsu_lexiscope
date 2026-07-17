from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .config import APP_NAME, APP_VERSION, resource_path
from .i18n import I18n
from .ui_common import COLOR_ACCENT, COLOR_MUTED, FONT_FAMILY, IconToplevel, button_colors


class AboutDialog(IconToplevel):
    def __init__(self, master: tk.Misc, i18n: I18n) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.title(i18n.t("about_title"))
        self.geometry("780x720")
        self.minsize(620, 540)
        self.transient(master)
        self.grab_set()
        self._photo: ctk.CTkImage | None = None

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        top = ctk.CTkFrame(root, fg_color="transparent")
        top.pack(fill=tk.X)
        logo_path = Path(resource_path("assets/logo.png"))
        if logo_path.exists():
            try:
                from PIL import Image

                image = Image.open(logo_path)
                self._photo = ctk.CTkImage(light_image=image, dark_image=image, size=(80, 80))
                ctk.CTkLabel(top, image=self._photo, text="").pack(side=tk.LEFT, padx=(0, 14))
            except (OSError, ValueError):
                pass
        heading = ctk.CTkFrame(top, fg_color="transparent")
        heading.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.W)
        ctk.CTkLabel(
            heading,
            text=i18n.t("app_title"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=COLOR_ACCENT,
        ).pack(anchor=tk.W)
        if i18n.t("app_title") != APP_NAME:
            ctk.CTkLabel(heading, text=APP_NAME, text_color=COLOR_MUTED).pack(anchor=tk.W, pady=(2, 0))

        text = ctk.CTkTextbox(
            root,
            wrap=tk.WORD,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            border_width=1,
        )
        text.insert("1.0", i18n.t("about_text", version=APP_VERSION))
        text.configure(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, pady=12)
        ctk.CTkButton(root, text=i18n.t("about_close"), command=self.destroy, width=96, **button_colors()).pack(anchor=tk.E)
