from __future__ import annotations

import difflib
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .ai_client import AIClient
from .i18n import I18n
from .models import AISuggestion
from .ui_common import IconToplevel


class SuggestionReviewSession:
    def __init__(self, source_text: str, suggestions: list[AISuggestion]) -> None:
        self.text = source_text
        self.suggestions = suggestions
        self.applied_count = 0

    def accept(self, index: int) -> bool:
        item = self.suggestions[index]
        if item.status in {"applied", "stale"}:
            return False
        updated, applied = AIClient.apply_suggestion(self.text, item)
        if not applied and self.text.count(item.original_fragment) == 1:
            item.occurrence = 1
            updated, applied = AIClient.apply_suggestion(self.text, item)
        if not applied:
            item.status = "stale"
            return False
        item.status = "applied"
        self.text = updated
        self.applied_count += 1
        return True

    def reject(self, index: int) -> bool:
        item = self.suggestions[index]
        if item.status in {"applied", "stale", "rejected"}:
            return False
        item.status = "rejected"
        return True

    def accept_all(self) -> int:
        accepted = 0
        for index, item in enumerate(self.suggestions):
            if item.status in {"pending", "rejected"} and self.accept(index):
                accepted += 1
        return accepted

    def reject_all(self) -> int:
        rejected = 0
        for index, item in enumerate(self.suggestions):
            if item.status == "pending" and self.reject(index):
                rejected += 1
        return rejected

    def counts(self) -> dict[str, int]:
        result = {"pending": 0, "applied": 0, "rejected": 0, "stale": 0}
        for item in self.suggestions:
            result[item.status if item.status in result else "pending"] += 1
        return result


class AIReviewDialog(IconToplevel):
    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        source_text: str,
        suggestions: list[AISuggestion],
        on_update: Callable[[str], None],
        on_finish: Callable[[str, int], None],
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.session = SuggestionReviewSession(source_text, suggestions)
        self.suggestions = self.session.suggestions
        self.on_update = on_update
        self.on_finish = on_finish
        self.summary = tk.StringVar()
        self.title(i18n.t("ai_review_title"))
        self.geometry("980x650")
        self.minsize(760, 480)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()

    def _build(self) -> None:
        t = self.i18n.t
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=t("select_suggestion")).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(root, textvariable=self.summary, foreground="#4b6972").pack(anchor=tk.W, pady=(0, 8))

        columns = ("operation", "original", "replacement", "reason", "status")
        tree_frame = ttk.Frame(root)
        tree_frame.pack(fill=tk.X)
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=11, selectmode="browse")
        headings = (t("operation"), t("original_fragment"), t("replacement_fragment"), t("reason"), t("suggestion_status"))
        widths = (100, 220, 220, 280, 90)
        for column, heading, width in zip(columns, headings, widths):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, minwidth=70, anchor=tk.W)
        ybar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._show_selected)
        self.tree.bind("<Double-1>", lambda _event: self._accept_selected())
        self.tree.bind("<Return>", lambda _event: self._accept_selected())
        self.tree.bind("<Delete>", lambda _event: self._reject_selected())
        self._refresh_tree()

        buttons = ttk.Frame(root)
        buttons.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ttk.Button(buttons, text=t("close"), command=self._close).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=t("review_accept"), command=self._accept_selected).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(buttons, text=t("review_reject"), command=self._reject_selected).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(buttons, text=t("review_accept_all"), command=self._accept_all).pack(side=tk.LEFT)
        ttk.Button(buttons, text=t("review_reject_all"), command=self._reject_all).pack(side=tk.LEFT, padx=(6, 0))

        preview = ttk.LabelFrame(root, text=t("diff"))
        preview.pack(fill=tk.BOTH, expand=True, pady=10)
        self.diff_text = tk.Text(preview, wrap=tk.NONE, padx=8, pady=8)
        preview_y = ttk.Scrollbar(preview, orient=tk.VERTICAL, command=self.diff_text.yview)
        preview_x = ttk.Scrollbar(preview, orient=tk.HORIZONTAL, command=self.diff_text.xview)
        self.diff_text.configure(yscrollcommand=preview_y.set, xscrollcommand=preview_x.set, state=tk.DISABLED)
        self.diff_text.grid(row=0, column=0, sticky=tk.NSEW)
        preview_y.grid(row=0, column=1, sticky=tk.NS)
        preview_x.grid(row=1, column=0, sticky=tk.EW)
        preview.rowconfigure(0, weight=1)
        preview.columnconfigure(0, weight=1)
        if self.tree.get_children():
            self.tree.selection_set("0")
            self.tree.focus("0")
            self._show_selected()

    def _refresh_tree(self) -> None:
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for index, item in enumerate(self.suggestions):
            state_key = {
                "applied": "suggestion_applied",
                "rejected": "suggestion_rejected",
                "stale": "suggestion_stale",
            }.get(item.status, "suggestion_pending")
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    self.i18n.t(f"op_{item.operation}"),
                    item.original_fragment.replace("\n", "↵"),
                    item.replacement_fragment.replace("\n", "↵"),
                    item.reason,
                    self.i18n.t(state_key),
                ),
            )
        if selected and selected[0] in self.tree.get_children():
            self.tree.selection_set(selected[0])
        counts = self.session.counts()
        self.summary.set(self.i18n.t("review_decision_summary", **counts))

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _show_selected(self, _event=None) -> None:
        index = self._selected_index()
        if index is None:
            return
        item = self.suggestions[index]
        diff = difflib.unified_diff(
            item.original_fragment.splitlines(),
            item.replacement_fragment.splitlines(),
            fromfile=self.i18n.t("before"),
            tofile=self.i18n.t("after"),
            lineterm="",
        )
        rendered = "\n".join(diff) or f"- {item.original_fragment}\n+ {item.replacement_fragment}"
        self.diff_text.configure(state=tk.NORMAL)
        self.diff_text.delete("1.0", tk.END)
        self.diff_text.insert("1.0", rendered)
        self.diff_text.configure(state=tk.DISABLED)

    def _accept_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(self.i18n.t("ai_review_title"), self.i18n.t("select_suggestion"), parent=self)
            return
        if self.session.accept(index):
            self.on_update(self.session.text)
        self._refresh_tree()
        self._select_next_pending(index)
        self._show_selected()

    def _reject_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(self.i18n.t("ai_review_title"), self.i18n.t("select_suggestion"), parent=self)
            return
        self.session.reject(index)
        self._refresh_tree()
        self._select_next_pending(index)
        self._show_selected()

    def _select_next_pending(self, current: int) -> None:
        indices = list(range(current + 1, len(self.suggestions))) + list(range(0, current))
        for index in indices:
            if self.suggestions[index].status == "pending":
                iid = str(index)
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.tree.see(iid)
                return

    def _accept_all(self) -> None:
        if self.session.accept_all():
            self.on_update(self.session.text)
        self._refresh_tree()
        self._show_selected()

    def _reject_all(self) -> None:
        self.session.reject_all()
        self._refresh_tree()
        self._show_selected()

    def _close(self) -> None:
        self.on_finish(self.session.text, self.session.applied_count)
        self.destroy()
