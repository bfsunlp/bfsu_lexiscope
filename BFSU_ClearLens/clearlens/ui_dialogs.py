from __future__ import annotations

import copy
import re
import tkinter as tk
import uuid
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Sequence

from .ai_client import AISettings
from .cleaner import regex_flags
from .i18n import I18n
from .models import RegexRule
from .ui_common import DpiAwareTreeview, FONT_FAMILY, IconToplevel, button_colors
from .ui_regex_generator import RegexLLMGeneratorDialog


class EncodingSelectDialog(IconToplevel):
    """Scaled CTk encoding chooser used instead of the fixed-size Tk prompt."""

    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        encodings: Sequence[str],
        current: str = "utf-8",
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        normalized = current.strip().lower() or "utf-8"
        self.values = list(dict.fromkeys((normalized, *encodings)))
        self.encoding_var = tk.StringVar(value=normalized)
        self.result: str | None = None
        self.title(i18n.t("reopen_encoding"))
        self.geometry("560x220")
        self.minsize(500, 210)
        self.transient(master)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        ctk.CTkLabel(
            root,
            text=self.i18n.t("source_encoding_prompt"),
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=510,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        ).pack(fill=tk.X, pady=(0, 10))
        combo = ctk.CTkComboBox(
            root,
            variable=self.encoding_var,
            values=self.values,
            state="readonly",
            height=34,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        combo.pack(fill=tk.X)
        combo.set(self.encoding_var.get())
        buttons = ctk.CTkFrame(root, fg_color="transparent")
        buttons.pack(side=tk.BOTTOM, fill=tk.X, pady=(16, 0))
        ctk.CTkButton(buttons, text=self.i18n.t("cancel"), command=self.destroy, width=96, **button_colors()).pack(side=tk.RIGHT)
        ctk.CTkButton(buttons, text=self.i18n.t("reopen"), command=self._accept, width=96, **button_colors("accent")).pack(side=tk.RIGHT, padx=(0, 8))
        self.bind("<Return>", lambda _event: self._accept())
        self.bind("<Escape>", lambda _event: self.destroy())
        combo.focus_set()

    def _accept(self) -> None:
        value = self.encoding_var.get().strip().lower()
        if value:
            self.result = value
            self.destroy()


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
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        columns = ("enabled", "name", "category", "description")
        self.tree = DpiAwareTreeview(root, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("enabled", t("regex_enabled"), 70),
            ("name", t("regex_name"), 230),
            ("category", t("regex_category"), 100),
            ("description", t("regex_description"), 430),
        ):
            self.tree.heading(column, text=label)
            self.tree.logical_column(column, width=width, minwidth=60, anchor=tk.W)
        ybar = ctk.CTkScrollbar(root, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        self.tree.bind("<Double-1>", lambda _event: self._toggle())
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        self._refresh()

        buttons = ctk.CTkFrame(root, fg_color="transparent")
        buttons.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        actions = ctk.CTkFrame(buttons, fg_color="transparent")
        actions.pack(fill=tk.X)
        ctk.CTkButton(actions, text=t("regex_toggle"), command=self._toggle, width=86, **button_colors()).pack(side=tk.LEFT)
        ctk.CTkButton(actions, text=t("regex_add_custom"), command=self._add, width=100, **button_colors()).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(actions, text=t("regex_edit"), command=self._edit, width=86, **button_colors()).pack(side=tk.LEFT)
        ctk.CTkButton(actions, text=t("regex_delete"), command=self._delete, width=86, **button_colors()).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(actions, text=t("regex_test"), command=self._test, width=86, **button_colors()).pack(side=tk.LEFT)
        ctk.CTkButton(actions, text=t("regex_ai_generate"), command=self._generate_with_llm, width=120, **button_colors("llm")).pack(side=tk.LEFT, padx=5)
        decisions = ctk.CTkFrame(buttons, fg_color="transparent")
        decisions.pack(fill=tk.X, pady=(6, 0))
        ctk.CTkButton(decisions, text=t("save"), command=self._save, width=86, **button_colors("accent")).pack(side=tk.RIGHT)
        ctk.CTkButton(decisions, text=t("cancel"), command=self.destroy, width=86, **button_colors()).pack(side=tk.RIGHT, padx=6)

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
        self.geometry("700x600")
        self.minsize(560, 430)
        self.transient(master)
        self.grab_set()
        self.name_var = tk.StringVar(value=rule.name if rule else "")
        self.flags_var = tk.StringVar(value=rule.flags if rule else "m")
        self._build(rule)

    def _build(self, rule: RegexRule | None) -> None:
        t = self.i18n.t
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        # Reserve the decision row before the scrollable form. At high Windows
        # scale factors the old expanding pattern editor could consume all
        # available height and push Save/Cancel outside the visible window.
        buttons = ctk.CTkFrame(root, fg_color="transparent")
        buttons.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        ctk.CTkButton(buttons, text=t("save"), command=self._save, width=100, **button_colors("accent")).pack(side=tk.RIGHT)
        ctk.CTkButton(buttons, text=t("cancel"), command=self.destroy, width=100, **button_colors()).pack(side=tk.RIGHT, padx=8)

        form = ctk.CTkScrollableFrame(root, fg_color="transparent")
        form.pack(fill=tk.BOTH, expand=True)
        ctk.CTkLabel(form, text=t("regex_name")).pack(anchor=tk.W)
        ctk.CTkEntry(form, textvariable=self.name_var).pack(fill=tk.X, pady=(2, 8))
        ctk.CTkLabel(form, text=t("regex_pattern")).pack(anchor=tk.W)
        self.pattern = ctk.CTkTextbox(form, height=125, wrap=tk.NONE, font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.pattern.pack(fill=tk.X, pady=(2, 8))
        ctk.CTkLabel(form, text=t("regex_replacement")).pack(anchor=tk.W)
        self.replacement = ctk.CTkTextbox(form, height=90, wrap=tk.NONE, font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.replacement.pack(fill=tk.X, pady=(2, 8))
        ctk.CTkLabel(form, text=t("regex_flags")).pack(anchor=tk.W)
        ctk.CTkEntry(form, textvariable=self.flags_var).pack(fill=tk.X, pady=(2, 8))
        ctk.CTkLabel(form, text=t("regex_description")).pack(anchor=tk.W)
        self.description = ctk.CTkEntry(form)
        self.description.pack(fill=tk.X, pady=(2, 8))
        if rule:
            self.pattern.insert("1.0", rule.pattern)
            self.replacement.insert("1.0", rule.replacement)
            self.description.insert(0, rule.description)

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
        highlight_matches: Callable[[list[tuple[int, int]]], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.get_text = get_text
        self.set_text = set_text
        self.highlight_matches = highlight_matches
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)
        self.case_var = tk.BooleanVar(value=True)
        self.result_var = tk.StringVar(value="")
        self.search_position = 0
        self.title(i18n.t("find_replace"))
        self.geometry("650x275")
        self.minsize(600, 260)
        self.transient(master)
        self._build()

    def _build(self) -> None:
        t = self.i18n.t
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        ctk.CTkLabel(root, text=t("find")).grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        ctk.CTkEntry(root, textvariable=self.find_var).grid(row=0, column=1, sticky=tk.EW, padx=6, pady=6)
        ctk.CTkLabel(root, text=t("replace_with")).grid(row=1, column=0, sticky=tk.W, padx=6, pady=6)
        ctk.CTkEntry(root, textvariable=self.replace_var).grid(row=1, column=1, sticky=tk.EW, padx=6, pady=6)
        ctk.CTkCheckBox(root, text=t("regex_mode"), variable=self.regex_var).grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        ctk.CTkCheckBox(root, text=t("case_sensitive"), variable=self.case_var).grid(row=2, column=1, sticky=tk.W, padx=6, pady=6)
        ctk.CTkLabel(root, textvariable=self.result_var, anchor=tk.W, text_color="#587076").grid(
            row=3, column=0, columnspan=2, sticky=tk.EW, padx=6, pady=(4, 0)
        )
        buttons = ctk.CTkFrame(root, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=12)
        ctk.CTkButton(buttons, text=t("find_next"), command=self._find_next, width=90, **button_colors()).pack(side=tk.LEFT, padx=3)
        ctk.CTkButton(buttons, text=t("find_all"), command=self._find_all, width=90, **button_colors()).pack(side=tk.LEFT, padx=3)
        ctk.CTkButton(buttons, text=t("replace_next"), command=self._replace_next, width=100, **button_colors()).pack(side=tk.LEFT, padx=3)
        ctk.CTkButton(buttons, text=t("replace_all"), command=self._replace_all, width=100, **button_colors("accent")).pack(side=tk.LEFT, padx=3)
        ctk.CTkButton(buttons, text=t("close"), command=self.destroy, width=80, **button_colors()).pack(side=tk.LEFT, padx=3)
        root.columnconfigure(1, weight=1)
        for variable in (self.find_var, self.regex_var, self.case_var):
            variable.trace_add("write", self._reset_search)
        self.bind("<Return>", lambda _event: self._find_next())
        self.bind("<F3>", lambda _event: self._find_next())

    def _reset_search(self, *_args: object) -> None:
        self.search_position = 0
        self.result_var.set("")

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
        match = regex.search(text, self.search_position) or (regex.search(text, 0, self.search_position) if self.search_position else None)
        if match is None:
            messagebox.showinfo(self.i18n.t("find_replace"), self.i18n.t("find_not_found"), parent=self)
            return
        try:
            replacement = match.expand(self.replace_var.get()) if self.regex_var.get() else self.replace_var.get()
        except re.error as exc:
            messagebox.showerror(self.i18n.t("find_replace"), self.i18n.t("regex_invalid", error=exc), parent=self)
            return
        updated = text[:match.start()] + replacement + text[match.end():]
        self.set_text(updated)
        self.search_position = match.start() + max(1, len(replacement))
        spans = [(match.start(), match.start() + len(replacement))] if replacement else []
        if self.highlight_matches is not None:
            self.highlight_matches(spans)
        self.result_var.set(self.i18n.t("replace_count_inline", count=1))

    def _replace_all(self) -> None:
        regex = self._compile()
        if not regex:
            return
        try:
            replacement: str | Callable[[re.Match[str]], str]
            replacement = self.replace_var.get() if self.regex_var.get() else (lambda _match: self.replace_var.get())
            updated, count = regex.subn(replacement, self.get_text())
        except re.error as exc:
            messagebox.showerror(self.i18n.t("find_replace"), self.i18n.t("regex_invalid", error=exc), parent=self)
            return
        if not count:
            messagebox.showinfo(self.i18n.t("find_replace"), self.i18n.t("find_not_found"), parent=self)
            return
        self.set_text(updated)
        self.search_position = 0
        self.result_var.set(self.i18n.t("replace_count_inline", count=count))
        messagebox.showinfo(
            self.i18n.t("find_replace"), self.i18n.t("replace_count_message", count=count), parent=self
        )

    def _find_next(self) -> None:
        regex = self._compile()
        if not regex:
            return
        text = self.get_text()
        match = regex.search(text, self.search_position)
        wrapped = False
        if match is None and self.search_position:
            match = regex.search(text, 0, self.search_position)
            wrapped = match is not None
        if match is None:
            self.result_var.set(self.i18n.t("find_count_inline", count=0))
            messagebox.showinfo(self.i18n.t("find_replace"), self.i18n.t("find_not_found"), parent=self)
            return
        self.search_position = max(match.end(), match.start() + 1)
        if self.highlight_matches is not None:
            self.highlight_matches([(match.start(), match.end())])
        self.result_var.set(self.i18n.t("find_next_result", start=match.start() + 1, wrapped=self.i18n.t("search_wrapped") if wrapped else ""))

    def _find_all(self) -> None:
        regex = self._compile()
        if not regex:
            return
        count = 0
        spans: list[tuple[int, int]] = []
        for match in regex.finditer(self.get_text()):
            count += 1
            if len(spans) < 2000:
                spans.append((match.start(), match.end()))
        if self.highlight_matches is not None:
            self.highlight_matches(spans)
        self.result_var.set(self.i18n.t("find_count_inline", count=count))
        messagebox.showinfo(
            self.i18n.t("find_replace"),
            self.i18n.t("find_count_message", count=count, highlighted=len(spans)),
            parent=self,
        )
