from __future__ import annotations

import copy
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from .i18n import I18n
from .models import LLMRule
from .ui_common import IconToplevel


class LLMRuleLibraryDialog(IconToplevel):
    def __init__(self, master: tk.Misc, i18n: I18n, rules: list[LLMRule]) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.rules = copy.deepcopy(rules)
        self.result: list[LLMRule] | None = None
        self.title(i18n.t("llm_rule_library"))
        self.geometry("820x520")
        self.minsize(680, 420)
        self.transient(master)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)
        columns = ("enabled", "name", "instruction")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("enabled", self.i18n.t("llm_rule_enabled"), 80),
            ("name", self.i18n.t("llm_rule_name"), 210),
            ("instruction", self.i18n.t("llm_rule_instruction"), 500),
        ):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, minwidth=70, anchor=tk.W)
        ybar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        self.tree.bind("<Double-1>", lambda _event: self._edit())
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        buttons = ttk.Frame(root)
        buttons.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        ttk.Button(buttons, text=self.i18n.t("llm_rule_toggle"), command=self._toggle).pack(side=tk.LEFT)
        ttk.Button(buttons, text=self.i18n.t("llm_rule_add"), command=self._add).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=self.i18n.t("llm_rule_edit"), command=self._edit).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=self.i18n.t("llm_rule_delete"), command=self._delete).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=self.i18n.t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=self.i18n.t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=6)
        self._refresh()

    def _refresh(self) -> None:
        selection = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for index, rule in enumerate(self.rules):
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(self.i18n.t("yes") if rule.enabled else self.i18n.t("no"), rule.name, rule.instruction),
            )
        if selection and selection[0] in self.tree.get_children():
            self.tree.selection_set(selection[0])

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _toggle(self) -> None:
        index = self._selected_index()
        if index is not None:
            self.rules[index].enabled = not self.rules[index].enabled
            self._refresh()

    def _add(self) -> None:
        dialog = LLMRuleEditDialog(self, self.i18n)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.rules.append(dialog.result)
            self._refresh()

    def _edit(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        dialog = LLMRuleEditDialog(self, self.i18n, self.rules[index])
        self.wait_window(dialog)
        if dialog.result is not None:
            self.rules[index] = dialog.result
            self._refresh()

    def _delete(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        if messagebox.askyesno(self.i18n.t("llm_rule_library"), self.i18n.t("llm_rule_delete_confirm"), parent=self):
            del self.rules[index]
            self._refresh()

    def _save(self) -> None:
        self.result = self.rules
        self.destroy()


class LLMRuleEditDialog(IconToplevel):
    def __init__(self, master: tk.Misc, i18n: I18n, rule: LLMRule | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.original = copy.deepcopy(rule)
        self.result: LLMRule | None = None
        self.name_var = tk.StringVar(value=rule.name if rule else "")
        self.title(i18n.t("llm_rule_edit") if rule else i18n.t("llm_rule_add"))
        self.geometry("660x420")
        self.minsize(560, 340)
        self.transient(master)
        self.grab_set()
        self._build(rule)

    def _build(self, rule: LLMRule | None) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=self.i18n.t("llm_rule_name")).pack(anchor=tk.W)
        ttk.Entry(root, textvariable=self.name_var).pack(fill=tk.X, pady=(2, 10))
        ttk.Label(root, text=self.i18n.t("llm_rule_instruction")).pack(anchor=tk.W)
        self.instruction = tk.Text(root, height=12, wrap=tk.WORD, padx=6, pady=6)
        self.instruction.pack(fill=tk.BOTH, expand=True, pady=(2, 8))
        if rule:
            self.instruction.insert("1.0", rule.instruction)
        ttk.Label(root, text=self.i18n.t("llm_rule_tip"), foreground="#4b6972", wraplength=620).pack(anchor=tk.W)
        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text=self.i18n.t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=self.i18n.t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=6)

    def _save(self) -> None:
        instruction = self.instruction.get("1.0", "end-1c").strip()
        if not instruction:
            messagebox.showwarning(self.i18n.t("llm_rule_library"), self.i18n.t("llm_rule_required"), parent=self)
            return
        self.result = LLMRule(
            key=self.original.key if self.original else f"llm_{uuid.uuid4().hex[:12]}",
            name=self.name_var.get().strip() or self.i18n.t("llm_rule_default_name"),
            instruction=instruction,
            enabled=self.original.enabled if self.original else True,
        )
        self.destroy()
