from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .i18n import I18n
from .statistics import TextStatistics
from .ui_common import IconToplevel


class StatisticsDialog(IconToplevel):
    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        current: TextStatistics,
        selected: TextStatistics,
        all_files: TextStatistics,
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.title(i18n.t("statistics_title"))
        self.geometry("700x500")
        self.minsize(600, 420)
        self.transient(master)
        self.grab_set()
        self._build(current, selected, all_files)

    def _build(
        self,
        current: TextStatistics,
        selected: TextStatistics,
        all_files: TextStatistics,
    ) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        columns = ("metric", "current", "selected", "all")
        tree = ttk.Treeview(outer, columns=columns, show="headings")
        tree.heading("metric", text=self.i18n.t("statistics_metric"))
        tree.heading("current", text=self.i18n.t("statistics_current"))
        tree.heading("selected", text=self.i18n.t("statistics_selected"))
        tree.heading("all", text=self.i18n.t("statistics_all"))
        tree.column("metric", width=220, anchor=tk.W)
        for column in columns[1:]:
            tree.column(column, width=130, anchor=tk.E)

        metrics = (
            ("statistics_files", "files"),
            ("statistics_total_chars", "total_chars"),
            ("statistics_non_whitespace", "non_whitespace_chars"),
            ("statistics_cjk_chars", "cjk_chars"),
            ("statistics_letters", "letters"),
            ("statistics_digits", "digits"),
            ("statistics_whitespace", "whitespace"),
            ("statistics_punctuation", "punctuation"),
            ("statistics_symbols", "symbols"),
            ("statistics_words", "latin_words"),
            ("statistics_lines", "lines"),
            ("statistics_paragraphs", "paragraphs"),
            ("statistics_utf8_bytes", "utf8_bytes"),
        )
        for label_key, field in metrics:
            tree.insert(
                "",
                tk.END,
                values=(
                    self.i18n.t(label_key),
                    f"{getattr(current, field):,}",
                    f"{getattr(selected, field):,}",
                    f"{getattr(all_files, field):,}",
                ),
            )
        tree.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            outer,
            text=self.i18n.t("statistics_note"),
            foreground="#4b6972",
            wraplength=650,
        ).pack(fill=tk.X, pady=(8, 0))
        ttk.Button(outer, text=self.i18n.t("close"), command=self.destroy).pack(side=tk.RIGHT, pady=(10, 0))
