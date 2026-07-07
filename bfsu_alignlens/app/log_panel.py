from __future__ import annotations

import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from core.utils import resource_path, ensure_dirs, now_str


def setup_logging():
    ensure_dirs()
    log_path = resource_path('log', 'alignlens.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()],
    )
    return logging.getLogger('bfsu_alignlens')


class LogPanel(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.text = ScrolledText(self, height=7, wrap='word')
        self.text.pack(fill='both', expand=True)
        self.text.configure(state='disabled')

    def log(self, message: str, level: str = 'INFO'):
        line = f'{now_str()} [{level}] {message}\n'
        self.text.configure(state='normal')
        self.text.insert('end', line)
        self.text.see('end')
        self.text.configure(state='disabled')
        logging.getLogger('bfsu_alignlens').info(message)
