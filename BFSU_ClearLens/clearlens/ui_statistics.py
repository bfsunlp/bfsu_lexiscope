from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from .i18n import I18n
from .statistics import TextStatistics
from .ui_common import COLOR_MUTED, DpiAwareTreeview, IconToplevel, button_colors


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
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        columns = ("metric", "current", "selected", "all")
        tree = DpiAwareTreeview(outer, columns=columns, show="headings")
        tree.heading("metric", text=self.i18n.t("statistics_metric"))
        tree.heading("current", text=self.i18n.t("statistics_current"))
        tree.heading("selected", text=self.i18n.t("statistics_selected"))
        tree.heading("all", text=self.i18n.t("statistics_all"))
        tree.logical_column("metric", width=220, minwidth=100, anchor=tk.W)
        for column in columns[1:]:
            tree.logical_column(column, width=130, minwidth=80, anchor=tk.E)

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
        ctk.CTkLabel(
            outer,
            text=self.i18n.t("statistics_note"),
            text_color=COLOR_MUTED,
            wraplength=650,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(8, 0))
        ctk.CTkButton(outer, text=self.i18n.t("close"), command=self.destroy, width=90, **button_colors()).pack(side=tk.RIGHT, pady=(10, 0))
