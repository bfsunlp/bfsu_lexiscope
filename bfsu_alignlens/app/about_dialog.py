from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from core.utils import resource_path
from app.theme import PROOFLENS_COLORS
from app.i18n import I18N


class AboutDialog(tk.Toplevel):
    def __init__(self, master, i18n: I18N | None = None):
        super().__init__(master)
        self.i18n = i18n or I18N(getattr(master, 'state_data', None).settings.get('gui_language', 'zh_sim') if hasattr(getattr(master, 'state_data', None), 'settings') else 'zh_sim')
        t = self.i18n.t
        self.title(t('about_title'))
        self.geometry('650x620')
        self.minsize(560, 500)
        self.configure(bg=PROOFLENS_COLORS['bg'])
        self.transient(master)
        self.grab_set()
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        top = ttk.Frame(root)
        top.pack(fill=tk.X)
        self._photo = None
        logo_path = Path(resource_path('assets', 'logo.png'))
        if not logo_path.exists():
            logo_path = Path(resource_path('assets', 'app.png'))
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk  # type: ignore
                img = Image.open(logo_path)
                img.thumbnail((80, 80))
                self._photo = ImageTk.PhotoImage(img)
                ttk.Label(top, image=self._photo).pack(side=tk.LEFT, padx=(0, 12))
            except Exception:
                pass
        title_box = ttk.Frame(top)
        title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_box, text='BFSU AlignLens', font=('Segoe UI', 18, 'bold'), foreground=PROOFLENS_COLORS['deep']).pack(anchor=tk.W)
        ttk.Label(title_box, text=t('about_subtitle'), font=('Segoe UI', 10, 'italic'), foreground=PROOFLENS_COLORS['muted']).pack(anchor=tk.W)
        text_frame = ttk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        text = tk.Text(text_frame, wrap=tk.WORD, height=22, bg=PROOFLENS_COLORS['panel'], fg=PROOFLENS_COLORS['text'], relief='solid', bd=1)
        ybar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=ybar.set)
        about_text = t('about_full')
        if about_text == 'about_full':
            about_text = (
                f"{t('about_line1')}\n\n"
                f"{t('about_line2')}\n\n"
                f"{t('author')}\n"
                f"{t('bfsu')}\n"
                f"{t('version')}"
            )
        text.insert('1.0', about_text)
        text.config(state=tk.DISABLED)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(root, text=t('close'), command=self.destroy).pack(anchor=tk.E)
