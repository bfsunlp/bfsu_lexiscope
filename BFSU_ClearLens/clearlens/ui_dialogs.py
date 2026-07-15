from __future__ import annotations

import copy
import re
import tkinter as tk
import uuid
from tkinter import messagebox, ttk
from typing import Callable

from .ai_client import AISettings
from .cleaner import regex_flags
from .i18n import I18n
from .models import RegexRule
from .ui_common import IconToplevel
from .ui_regex_generator import RegexLLMGeneratorDialog


class RegexLibraryDialog(IconToplevel):
    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        rules: list[RegexRule],
        test_text: str = "",
        ai_settings: AISettings | None = None,
        samples: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.rules = copy.deepcopy(rules)
        self.test_text = test_text
        self.ai_settings = ai_settings
        self.samples = samples or []
        self.result: list[RegexRule] | None = None
        self.title(i18n.t("regex_title"))
        self.geometry("920x560")
        self.minsize(720, 430)
        self.transient(master)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        t = self.i18n.t
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)
        columns = ("enabled", "name", "category", "description")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("enabled", t("regex_enabled"), 70),
            ("name", t("regex_name"), 230),
            ("category", t("regex_category"), 100),
            ("description", t("regex_description"), 430),
        ):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, minwidth=60, anchor=tk.W)
        ybar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        self.tree.bind("<Double-1>", lambda _event: self._toggle())
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        self._refresh()

        buttons = ttk.Frame(root)
        buttons.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        ttk.Button(buttons, text=t("regex_toggle"), command=self._toggle).pack(side=tk.LEFT)
        ttk.Button(buttons, text=t("regex_add_custom"), command=self._add).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=t("regex_edit"), command=self._edit).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=t("regex_delete"), command=self._delete).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=t("regex_test"), command=self._test).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=t("regex_ai_generate"), command=self._generate_with_llm).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text=t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=6)

    def _refresh(self) -> None:
        selection = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for index, rule in enumerate(self.rules):
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    self.i18n.t("yes") if rule.enabled else self.i18n.t("no"),
                    rule.display_name(self.i18n.language),
                    self.i18n.t(f"category_{rule.category}"),
                    rule.display_description(self.i18n.language),
                ),
            )
        if selection and selection[0] in self.tree.get_children():
            self.tree.selection_set(selection[0])

    def _selected_index(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def _toggle(self) -> None:
        index = self._selected_index()
        if index is not None:
            self.rules[index].enabled = not self.rules[index].enabled
            self._refresh()

    def _add(self) -> None:
        dialog = RegexEditDialog(self, self.i18n)
        self.wait_window(dialog)
        if dialog.result:
            self.rules.append(dialog.result)
            self._refresh()

    def _edit(self) -> None:
        index = self._selected_index()
        if index is None or not self.rules[index].custom:
            return
        dialog = RegexEditDialog(self, self.i18n, self.rules[index])
        self.wait_window(dialog)
        if dialog.result:
            self.rules[index] = dialog.result
            self._refresh()

    def _delete(self) -> None:
        index = self._selected_index()
        if index is not None and self.rules[index].custom:
            del self.rules[index]
            self._refresh()

    def _test(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        rule = self.rules[index]
        try:
            count = len(re.findall(rule.pattern, self.test_text, flags=regex_flags(rule.flags)))
        except re.error as exc:
            messagebox.showerror(self.i18n.t("regex_title"), self.i18n.t("regex_invalid", error=exc), parent=self)
            return
        messagebox.showinfo(self.i18n.t("regex_title"), self.i18n.t("regex_test_result", count=count), parent=self)

    def _generate_with_llm(self) -> None:
        if self.ai_settings is None:
            return
        dialog = RegexLLMGeneratorDialog(self, self.i18n, self.ai_settings, self.samples)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        editor = RegexEditDialog(self, self.i18n, dialog.result)
        self.wait_window(editor)
        if editor.result is not None:
            self.rules.append(editor.result)
            self._refresh()

    def _save(self) -> None:
        self.result = self.rules
        self.destroy()


class RegexEditDialog(IconToplevel):
    def __init__(self, master: tk.Misc, i18n: I18n, rule: RegexRule | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.original = copy.deepcopy(rule)
        self.result: RegexRule | None = None
        self.title(i18n.t("regex_add_custom") if rule is None else i18n.t("regex_edit"))
        self.geometry("620x460")
        self.transient(master)
        self.grab_set()
        self.name_var = tk.StringVar(value=rule.name if rule else "")
        self.flags_var = tk.StringVar(value=rule.flags if rule else "m")
        self._build(rule)

    def _build(self, rule: RegexRule | None) -> None:
        t = self.i18n.t
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=t("regex_name")).pack(anchor=tk.W)
        ttk.Entry(root, textvariable=self.name_var).pack(fill=tk.X, pady=(2, 8))
        ttk.Label(root, text=t("regex_pattern")).pack(anchor=tk.W)
        self.pattern = tk.Text(root, height=5, wrap=tk.NONE)
        self.pattern.pack(fill=tk.BOTH, expand=True, pady=(2, 8))
        ttk.Label(root, text=t("regex_replacement")).pack(anchor=tk.W)
        self.replacement = tk.Text(root, height=3, wrap=tk.NONE)
        self.replacement.pack(fill=tk.X, pady=(2, 8))
        ttk.Label(root, text=t("regex_flags")).pack(anchor=tk.W)
        ttk.Entry(root, textvariable=self.flags_var).pack(fill=tk.X, pady=(2, 8))
        ttk.Label(root, text=t("regex_description")).pack(anchor=tk.W)
        self.description = ttk.Entry(root)
        self.description.pack(fill=tk.X, pady=(2, 8))
        if rule:
            self.pattern.insert("1.0", rule.pattern)
            self.replacement.insert("1.0", rule.replacement)
            self.description.insert(0, rule.description)
        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text=t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=6)

    def _save(self) -> None:
        pattern = self.pattern.get("1.0", tk.END).rstrip("\n")
        if not pattern:
            messagebox.showwarning(self.i18n.t("regex_title"), self.i18n.t("regex_pattern_required"), parent=self)
            return
        try:
            re.compile(pattern, regex_flags(self.flags_var.get()))
        except re.error as exc:
            messagebox.showerror(self.i18n.t("regex_title"), self.i18n.t("regex_invalid", error=exc), parent=self)
            return
        self.result = RegexRule(
            key=self.original.key if self.original else f"custom_{uuid.uuid4().hex[:12]}",
            name=self.name_var.get().strip() or self.i18n.t("custom_rule_default"),
            pattern=pattern,
            replacement=self.replacement.get("1.0", tk.END).rstrip("\n"),
            flags=self.flags_var.get().strip(),
            enabled=self.original.enabled if self.original else True,
            description=self.description.get().strip(),
            category="custom",
            custom=True,
        )
        self.destroy()


class FindReplaceDialog(IconToplevel):
    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        get_text: Callable[[], str],
        set_text: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.get_text = get_text
        self.set_text = set_text
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)
        self.case_var = tk.BooleanVar(value=True)
        self.title(i18n.t("find_replace"))
        self.geometry("560x230")
        self.transient(master)
        self._build()

    def _build(self) -> None:
        t = self.i18n.t
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=t("find")).grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        ttk.Entry(root, textvariable=self.find_var).grid(row=0, column=1, sticky=tk.EW, padx=6, pady=6)
        ttk.Label(root, text=t("replace_with")).grid(row=1, column=0, sticky=tk.W, padx=6, pady=6)
        ttk.Entry(root, textvariable=self.replace_var).grid(row=1, column=1, sticky=tk.EW, padx=6, pady=6)
        ttk.Checkbutton(root, text=t("regex_mode"), variable=self.regex_var).grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        ttk.Checkbutton(root, text=t("case_sensitive"), variable=self.case_var).grid(row=2, column=1, sticky=tk.W, padx=6, pady=6)
        buttons = ttk.Frame(root)
        buttons.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=12)
        ttk.Button(buttons, text=t("replace_next"), command=self._replace_next).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text=t("replace_all"), command=self._replace_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text=t("close"), command=self.destroy).pack(side=tk.LEFT, padx=4)
        root.columnconfigure(1, weight=1)

    def _compile(self) -> re.Pattern[str] | None:
        source = self.find_var.get()
        if not source:
            return None
        pattern = source if self.regex_var.get() else re.escape(source)
        flags = 0 if self.case_var.get() else re.IGNORECASE
        try:
            return re.compile(pattern, flags)
        except re.error as exc:
            messagebox.showerror(self.i18n.t("find_replace"), self.i18n.t("regex_invalid", error=exc), parent=self)
            return None

    def _replace_next(self) -> None:
        regex = self._compile()
        if not regex:
            return
        text = self.get_text()
        updated, count = regex.subn(self.replace_var.get(), text, count=1)
        if not count:
            messagebox.showinfo(self.i18n.t("find_replace"), self.i18n.t("find_not_found"), parent=self)
            return
        self.set_text(updated)

    def _replace_all(self) -> None:
        regex = self._compile()
        if not regex:
            return
        updated, count = regex.subn(self.replace_var.get(), self.get_text())
        if not count:
            messagebox.showinfo(self.i18n.t("find_replace"), self.i18n.t("find_not_found"), parent=self)
            return
        self.set_text(updated)
