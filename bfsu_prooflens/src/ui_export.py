# -*- coding: utf-8 -*-
"""Export settings dialog."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Any

from .i18n import I18N


FORMATS = ["TXT", "DOCX", "XLSX", "JSON", "XML", "Markdown"]
SCOPES = [("export_scope_current_page", "current_page"), ("export_scope_current_file", "current_file"), ("export_scope_project", "project")]


class ExportDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, default_dir: str = "output", current_file_stem: str = "prooflens_export", i18n: I18N | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n or I18N("en")
        t = self.i18n.t
        self.title(t("export_settings_title"))
        self.geometry("660x500")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result: dict[str, Any] | None = None
        self.scope_var = tk.StringVar(value="project")
        self.format_var = tk.StringVar(value="Markdown")
        self.default_dir = str(default_dir)
        self.current_file_stem = current_file_stem
        self.path_var = tk.StringVar(value=str(Path(default_dir) / f"{current_file_stem}.md"))
        self.include_ocr = tk.BooleanVar(value=True)
        self.include_corrected = tk.BooleanVar(value=True)
        self.include_final = tk.BooleanVar(value=True)
        self.include_suggestions = tk.BooleanVar(value=True)
        self.include_blocks = tk.BooleanVar(value=True)
        self.final_only = tk.BooleanVar(value=False)
        self.split_by_source_file = tk.BooleanVar(value=False)
        self.open_folder = tk.BooleanVar(value=False)
        self._build()
        self.format_var.trace_add("write", lambda *_: self._auto_ext())
        self.split_by_source_file.trace_add("write", lambda *_: self._toggle_split_mode())

    def _scope_labels(self) -> list[str]:
        return [self.i18n.t(key) for key, _ in SCOPES]

    def _scope_value_to_label(self, value: str) -> str:
        for key, val in SCOPES:
            if val == value:
                return self.i18n.t(key)
        return value

    def _scope_label_to_value(self, label: str) -> str:
        for key, val in SCOPES:
            if self.i18n.t(key) == label:
                return val
        return label

    def _build(self) -> None:
        t = self.i18n.t
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=t("export_scope")).grid(row=0, column=0, sticky=tk.W, pady=6)
        self.scope_display_var = tk.StringVar(value=t("export_scope_project"))
        ttk.Combobox(root, textvariable=self.scope_display_var, values=self._scope_labels(), state="readonly").grid(row=0, column=1, sticky=tk.EW, pady=6)
        ttk.Label(root, text=t("export_format")).grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Combobox(root, textvariable=self.format_var, values=FORMATS, state="readonly").grid(row=1, column=1, sticky=tk.EW, pady=6)

        box = ttk.LabelFrame(root, text=t("export_content"))
        box.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)
        ttk.Checkbutton(box, text=t("ocr_original_text"), variable=self.include_ocr).grid(row=0, column=0, sticky=tk.W, padx=8, pady=5)
        ttk.Checkbutton(box, text=t("llm_corrected_text"), variable=self.include_corrected).grid(row=0, column=1, sticky=tk.W, padx=8, pady=5)
        ttk.Checkbutton(box, text=t("final_confirmed_text"), variable=self.include_final).grid(row=1, column=0, sticky=tk.W, padx=8, pady=5)
        ttk.Checkbutton(box, text=t("revision_suggestions"), variable=self.include_suggestions).grid(row=1, column=1, sticky=tk.W, padx=8, pady=5)
        ttk.Checkbutton(box, text=t("ocr_blocks_confidence"), variable=self.include_blocks).grid(row=2, column=0, sticky=tk.W, padx=8, pady=5)
        ttk.Checkbutton(box, text=t("final_text_only"), variable=self.final_only).grid(row=2, column=1, sticky=tk.W, padx=8, pady=5)

        ttk.Label(root, text=t("export_path")).grid(row=3, column=0, sticky=tk.W, pady=6)
        ttk.Entry(root, textvariable=self.path_var).grid(row=3, column=1, sticky=tk.EW, pady=6)
        ttk.Button(root, text=t("choose"), command=self._choose_path).grid(row=3, column=2, padx=6, pady=6)
        ttk.Checkbutton(root, text=t("export_split_by_source_file"), variable=self.split_by_source_file).grid(row=4, column=1, sticky=tk.W, pady=6)
        ttk.Checkbutton(root, text=t("open_folder_after_export"), variable=self.open_folder).grid(row=5, column=1, sticky=tk.W, pady=6)
        root.columnconfigure(1, weight=1)
        btns = ttk.Frame(root)
        btns.grid(row=6, column=0, columnspan=3, sticky=tk.E, pady=18)
        ttk.Button(btns, text=t("export"), command=self._ok).pack(side=tk.RIGHT)
        ttk.Button(btns, text=t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=8)

    def _ext(self) -> str:
        fmt = self.format_var.get().lower()
        return ".md" if fmt == "markdown" else f".{fmt}"

    def _auto_ext(self) -> None:
        if self.split_by_source_file.get():
            return
        p = Path(self.path_var.get())
        ext = self._ext()
        if p.suffix.lower() != ext:
            self.path_var.set(str(p.with_suffix(ext)))

    def _toggle_split_mode(self) -> None:
        p = Path(self.path_var.get().strip() or self.default_dir)
        if self.split_by_source_file.get():
            folder = p.parent if p.suffix else p
            self.path_var.set(str(folder))
        else:
            folder = p if not p.suffix else p.parent
            self.path_var.set(str(folder / f"{self.current_file_stem}{self._ext()}"))

    def _choose_path(self) -> None:
        if self.split_by_source_file.get():
            initial = self.path_var.get().strip() or self.default_dir
            p = filedialog.askdirectory(parent=self, initialdir=initial, title=self.i18n.t("select_export_folder"))
            if p:
                self.path_var.set(p)
            return
        ext = self._ext()
        p = filedialog.asksaveasfilename(parent=self, defaultextension=ext, filetypes=[(self.format_var.get(), f"*{ext}"), (self.i18n.t("all_files"), "*.*")])
        if p:
            self.path_var.set(p)

    def _ok(self) -> None:
        if not self.path_var.get().strip():
            messagebox.showwarning(self.i18n.t("info"), self.i18n.t("select_export_path"), parent=self)
            return
        self.result = {
            "scope": self._scope_label_to_value(self.scope_display_var.get()),
            "format": self.format_var.get(),
            "path": self.path_var.get().strip(),
            "options": {
                "include_ocr_text": self.include_ocr.get(),
                "include_corrected_text": self.include_corrected.get(),
                "include_final_text": self.include_final.get(),
                "include_suggestions": self.include_suggestions.get(),
                "include_ocr_blocks": self.include_blocks.get(),
                "final_text_only": self.final_only.get(),
                "split_by_source_file": self.split_by_source_file.get(),
            },
            "open_folder": self.open_folder.get(),
        }
        self.destroy()
