# -*- coding: utf-8 -*-
"""Proofreading suggestion panel."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable

from .i18n import I18N
from .utils import enable_mousewheel


class SuggestionPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, on_accept: Callable[[int], None], on_reject: Callable[[int], None], on_accept_all: Callable[[], None], on_clear: Callable[[], None], i18n: I18N | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n or I18N("en")
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.on_accept_all = on_accept_all
        self.on_clear = on_clear
        self.suggestions: list[dict[str, Any]] = []
        self._build()

    def _build(self) -> None:
        t = self.i18n.t
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(header, text=t("revision_suggestions_title"), font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text=t("accept"), command=self._accept_selected).pack(side=tk.RIGHT, padx=2)
        ttk.Button(header, text=t("reject"), command=self._reject_selected).pack(side=tk.RIGHT, padx=2)
        ttk.Button(header, text=t("accept_all"), command=self._accept_all).pack(side=tk.RIGHT, padx=2)
        ttk.Button(header, text=t("clear_suggestions"), command=self.on_clear).pack(side=tk.RIGHT, padx=2)

        cols = ("line", "original", "suggested", "category", "confidence", "status", "reason")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=7)
        headings = {
            "line": t("line_no"), "original": t("original_text"), "suggested": t("suggested_text"),
            "category": t("category"), "confidence": t("confidence"), "status": t("status"), "reason": t("reason")
        }
        widths = {"line": 60, "original": 180, "suggested": 180, "category": 100, "confidence": 80, "status": 80, "reason": 300}
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor=tk.W)
        y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._show_detail)
        enable_mousewheel(self.tree)

    def set_suggestions(self, suggestions: list[dict[str, Any]] | None) -> None:
        self.suggestions = suggestions or []
        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.suggestions):
            self.tree.insert("", tk.END, iid=str(i), values=(
                s.get("line_no", ""), s.get("original", ""), s.get("suggested", ""), s.get("category", ""),
                s.get("confidence", ""), s.get("status", "pending"), s.get("reason", "")
            ))

    def _selected_index(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def _accept_selected(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.on_accept(idx)

    def _reject_selected(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.on_reject(idx)

    def _accept_all(self) -> None:
        if not self.suggestions:
            return
        if messagebox.askyesno(self.i18n.t("confirm"), self.i18n.t("accept_all_confirm"), parent=self):
            self.on_accept_all()

    def _show_detail(self, event=None) -> None:
        idx = self._selected_index()
        if idx is None or idx >= len(self.suggestions):
            return
        s = self.suggestions[idx]
        detail = self.i18n.t(
            "suggestion_detail",
            line=s.get("line_no", ""),
            original=s.get("original", ""),
            suggested=s.get("suggested", ""),
            category=s.get("category", ""),
            confidence=s.get("confidence", ""),
            status=s.get("status", "pending"),
            reason=s.get("reason", ""),
        )
        # A scrollable detail window is more useful than messagebox for LLM
        # feedback, because raw/plain-text model responses can be long.
        top = tk.Toplevel(self)
        top.title(self.i18n.t("suggestion_detail_title"))
        top.transient(self.winfo_toplevel())
        top.geometry("760x460")
        top.minsize(520, 320)
        frame = ttk.Frame(top, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        text = tk.Text(frame, wrap=tk.WORD, height=18)
        y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=y.set)
        text.insert("1.0", detail)
        text.configure(state=tk.DISABLED)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y.pack(side=tk.RIGHT, fill=tk.Y)
        enable_mousewheel(text)
        btns = ttk.Frame(top, padding=(10, 0, 10, 10))
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="OK", command=top.destroy).pack(side=tk.RIGHT)
        top.grab_set()
        top.focus_set()
