from __future__ import annotations

import copy
import difflib
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    BaseWindow = TkinterDnD.Tk
except Exception:
    DND_FILES = None
    BaseWindow = tk.Tk

from .ai_client import AIClient, AISettings
from .cleaner import clean_text
from .config import load_settings, save_settings
from .document_ops import merge_texts
from .fileio import (
    OUTPUT_ENCODINGS,
    TEXT_EXTENSIONS,
    apply_newline_style,
    discover_text_files,
    export_log_csv,
    export_log_json,
    read_text_file,
    write_output_file,
    write_text_path,
)
from .i18n import I18n
from .history import FileEditState, OperationHistory, file_identity
from .llm_rule_library import load_llm_rules, save_llm_rules
from .models import AIResult, AISuggestion, CleanOptions, LLMRule, RegexRule, TextFile
from .profile import load_profile, save_profile
from .rule_library import load_regex_rules, save_custom_regex_rules
from .statistics import calculate_statistics
from .ui_about import AboutDialog
from .ui_ai_review import AIReviewDialog
from .ui_common import apply_window_icon
from .ui_dialogs import FindReplaceDialog, RegexLibraryDialog
from .ui_llm_rules import LLMRuleLibraryDialog
from .ui_settings import SettingsDialog
from .ui_statistics import StatisticsDialog
from .workers import clean_text_job


class ClearLensApp(BaseWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.i18n = I18n(str(self.settings.get("language", "zh_sim")))
        self.files: list[TextFile] = []
        self.regex_rules: list[RegexRule] = load_regex_rules()
        self.llm_rules: list[LLMRule] = load_llm_rules()
        enabled_rule_keys = self.settings.get("regex_enabled_keys")
        if isinstance(enabled_rule_keys, list):
            enabled = {str(key) for key in enabled_rule_keys}
            for rule in self.regex_rules:
                rule.enabled = rule.key in enabled
        enabled_llm_rule_keys = self.settings.get("llm_rule_enabled_keys")
        if isinstance(enabled_llm_rule_keys, list):
            enabled_llm = {str(key) for key in enabled_llm_rule_keys}
            for rule in self.llm_rules:
                rule.enabled = rule.key in enabled_llm

        ai_data = self.settings.setdefault("ai", {})
        self.session_api_keys = {
            "openai": str(ai_data.get("openai_api_key", ai_data.get("api_key", ""))),
            "deepseek": str(ai_data.get("deepseek_api_key", "")),
        }
        self.output_dir = tk.StringVar(value=str(self.settings.setdefault("output", {}).get("directory", "clearlens_output")))
        self.output_encoding = tk.StringVar(value=str(self.settings.setdefault("output", {}).get("encoding", "utf-8")))
        self.editor_font_size = tk.IntVar(value=int(self.settings.setdefault("editor", {}).get("font_size", 11)))
        self.stats_summary = tk.StringVar(value="")
        self.status = tk.StringVar(value=self.i18n.t("ready"))
        self.progress_value = tk.DoubleVar(value=0)
        self.worker_queue: queue.Queue[tuple[int, str, Any]] = queue.Queue()
        self.log_rows: list[dict[str, object]] = []
        self.busy = False
        self._task_counter = 0
        self._active_task_id: int | None = None
        self._cancel_event: threading.Event | None = None
        self._active_executor: ThreadPoolExecutor | ProcessPoolExecutor | None = None
        self._output_lock = threading.Lock()
        self._preview_truncated = False
        self.option_vars: dict[str, tk.BooleanVar] = {}
        self.rule_vars: dict[str, tk.BooleanVar] = {}
        self.llm_rule_vars: dict[str, tk.BooleanVar] = {}
        self.choice_vars: dict[str, tk.Variable] = {}
        self.editor_widgets: list[tk.Text] = []
        self._setting_preview = False
        self.history = OperationHistory(limit=50)
        self._pending_history: dict[int, tuple[str, dict[str, FileEditState]]] = {}
        self._manual_history_before: dict[str, FileEditState] | None = None
        self._manual_history_path: str | None = None
        self._manual_history_after_id: str | None = None

        self.title(self.i18n.t("app_title"))
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self._set_icon()
        self._setup_style()
        self._build_ui()
        self._bind_shortcuts()
        self.after(100, self._poll_worker_queue)

    def _set_icon(self) -> None:
        apply_window_icon(self, default=True)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.option_add("*Font", ("Microsoft YaHei UI", 9))
        style.configure("TButton", padding=(7, 4))
        style.configure("Tool.TButton", padding=(6, 3))
        style.configure("Accent.TButton", background="#0b6f75", foreground="#ffffff", padding=(8, 5))
        style.map("Accent.TButton", background=[("active", "#095b60"), ("disabled", "#9aa7a8")])
        style.configure("LLM.TButton", background="#155a8a", foreground="#ffffff", padding=(8, 5))
        style.map("LLM.TButton", background=[("active", "#10486e"), ("disabled", "#9aa7a8")])
        style.configure("Treeview", rowheight=24)
        style.configure("Status.TLabel", anchor=tk.W)
        style.configure("Sidebar.TFrame", background="#eef5f7")

    def _build_ui(self) -> None:
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()

    def _build_menu(self) -> None:
        t = self.i18n.t
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label=t("import_files"), accelerator="Ctrl+O", command=self.open_files)
        file_menu.add_command(label=t("import_folder"), accelerator="Ctrl+Shift+O", command=self.open_folder)
        file_menu.add_command(label=t("choose_output"), command=self.choose_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label=t("save_current"), accelerator="Ctrl+S", command=self.save_current_result)
        file_menu.add_command(label=t("save_as"), accelerator="Ctrl+Shift+S", command=self.save_current_as)
        file_menu.add_command(label=t("save_all"), accelerator="Ctrl+Alt+S", command=self.save_all_results)
        file_menu.add_command(label=t("export_log"), command=self.export_log)
        file_menu.add_separator()
        file_menu.add_command(label=t("exit"), command=self.on_exit)
        menubar.add_cascade(label=t("file"), menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label=t("undo"), accelerator="Ctrl+Z", command=self.undo_operation)
        edit_menu.add_command(label=t("redo"), accelerator="Ctrl+Y", command=self.redo_operation)
        edit_menu.add_separator()
        edit_menu.add_command(label=t("find_replace"), accelerator="Ctrl+F", command=self.open_find_replace)
        edit_menu.add_separator()
        edit_menu.add_command(label=t("reset_current"), command=self.reset_current_file)
        edit_menu.add_command(label=t("reset_selected"), command=self.reset_selected_files)
        edit_menu.add_command(label=t("reset_all"), command=self.reset_all_files)
        menubar.add_cascade(label=t("edit"), menu=edit_menu)

        document_menu = tk.Menu(menubar, tearoff=False)
        document_menu.add_command(label=t("merge_selected"), command=self.merge_selected_files)
        document_menu.add_command(label=t("merge_all"), command=self.merge_all_files)
        menubar.add_cascade(label=t("document"), menu=document_menu)

        clean_menu = tk.Menu(menubar, tearoff=False)
        clean_menu.add_command(label=t("preview"), accelerator="Ctrl+P", command=self.preview_rules)
        clean_menu.add_separator()
        clean_menu.add_command(label=t("rule_current"), accelerator="F5", command=self.run_rule_current)
        clean_menu.add_command(label=t("rule_all"), accelerator="Ctrl+F5", command=self.run_rule_all)
        clean_menu.add_separator()
        clean_menu.add_command(label=t("transcode_current"), command=self.transcode_current)
        clean_menu.add_command(label=t("transcode_selected"), command=self.transcode_selected)
        clean_menu.add_command(label=t("transcode_all"), command=self.transcode_all)
        menubar.add_cascade(label=t("cleaning"), menu=clean_menu)

        ai_menu = tk.Menu(menubar, tearoff=False)
        ai_menu.add_command(label=t("ai_direct_current"), accelerator="F6", command=self.run_ai_current)
        ai_menu.add_command(label=t("ai_direct_all"), accelerator="Ctrl+F6", command=self.run_ai_all)
        ai_menu.add_separator()
        ai_menu.add_command(label=t("ai_review_current"), accelerator="F7", command=self.run_ai_review_current)
        ai_menu.add_separator()
        ai_menu.add_command(label=t("llm_rule_safe_current"), command=self.run_llm_rules_current)
        ai_menu.add_command(label=t("llm_rule_safe_selected"), command=self.run_llm_rules_selected)
        ai_menu.add_command(label=t("llm_rule_review_current"), command=self.run_llm_rules_review_current)
        ai_menu.add_command(label=t("llm_rule_library"), command=self.open_llm_rule_library)
        ai_menu.add_separator()
        ai_menu.add_command(label=t("ai_settings"), command=lambda: self.open_settings("ai"))
        menubar.add_cascade(label=t("ai"), menu=ai_menu)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label=t("character_statistics"), command=self.show_statistics)
        tools_menu.add_separator()
        tools_menu.add_command(label=t("regex_library"), command=self.open_regex_library)
        tools_menu.add_command(label=t("reopen_encoding"), command=self.reopen_with_encoding)
        tools_menu.add_command(label=t("open_output"), command=self.open_output_folder)
        tools_menu.add_command(label=t("clear_log"), command=self.clear_log)
        menubar.add_cascade(label=t("tools"), menu=tools_menu)

        settings_menu = tk.Menu(menubar, tearoff=False)
        language_menu = tk.Menu(settings_menu, tearoff=False)
        language_menu.add_command(label="English", command=lambda: self.set_language("en"))
        language_menu.add_command(label="简体中文", command=lambda: self.set_language("zh_sim"))
        language_menu.add_command(label="繁體中文", command=lambda: self.set_language("zh_tra"))
        settings_menu.add_cascade(label=t("language"), menu=language_menu)
        settings_menu.add_separator()
        settings_menu.add_command(label=t("save_profile"), command=self.export_profile)
        settings_menu.add_command(label=t("load_profile"), command=self.import_profile)
        settings_menu.add_separator()
        settings_menu.add_command(label=t("preferences"), command=self.open_settings)
        menubar.add_cascade(label=t("settings"), menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label=t("shortcuts"), command=self.show_shortcuts)
        help_menu.add_command(label=t("about"), command=self.show_about)
        menubar.add_cascade(label=t("help"), menu=help_menu)
        self.configure(menu=menubar)

    def _build_toolbar(self) -> None:
        t = self.i18n.t
        toolbar = ttk.Frame(self, padding=(6, 5))
        toolbar.pack(fill=tk.X)
        for label, command in (
            (t("import_files"), self.open_files),
            (t("import_folder"), self.open_folder),
            (t("remove"), self.remove_selected_files),
        ):
            ttk.Button(toolbar, text=label, style="Tool.TButton", command=command).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(toolbar, text=t("preview"), style="Tool.TButton", command=self.preview_rules).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=t("rule_current"), style="Accent.TButton", command=self.run_rule_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=t("rule_all"), style="Accent.TButton", command=self.run_rule_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(toolbar, text=t("ai_direct_current"), style="LLM.TButton", command=self.run_ai_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=t("ai_review_current"), style="LLM.TButton", command=self.run_ai_review_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=t("save_all"), style="Tool.TButton", command=self.save_all_results).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text=t("save_current"), style="Tool.TButton", command=self.save_current_result).pack(side=tk.RIGHT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="A+", width=3, style="Tool.TButton", command=lambda: self.change_editor_font_size(1)).pack(side=tk.RIGHT, padx=1)
        ttk.Button(toolbar, text="A-", width=3, style="Tool.TButton", command=lambda: self.change_editor_font_size(-1)).pack(side=tk.RIGHT, padx=1)
        ttk.Label(toolbar, textvariable=self.stats_summary).pack(side=tk.RIGHT, padx=6)
        ttk.Button(toolbar, text=t("character_statistics"), style="Tool.TButton", command=self.show_statistics).pack(side=tk.RIGHT, padx=2)

    def _build_workspace(self) -> None:
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, sashrelief=tk.RAISED, bd=0)
        pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))
        left = ttk.Frame(pane, style="Sidebar.TFrame", width=330)
        right = ttk.Frame(pane)
        pane.add(left, minsize=265, width=330)
        pane.add(right, minsize=620)
        self.main_pane = pane
        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        canvas = tk.Canvas(parent, background="#eef5f7", highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        body = ttk.Frame(canvas, style="Sidebar.TFrame", padding=(7, 6))
        window_id = canvas.create_window((0, 0), window=body, anchor=tk.NW)
        body.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=max(180, event.width)))
        self._init_option_vars()
        self._build_action_group(body)
        self._build_option_group(body, "basic_group", (
            "normalize_newlines", "strip_bom", "fix_mojibake", "remove_control_chars",
            "remove_zero_width_chars", "decode_html_entities", "remove_web_code_blocks",
            "strip_leading_whitespace", "trim_lines", "normalize_spaces",
            "tabs_to_spaces", "fix_cjk_spacing",
        ))
        self._build_option_group(body, "line_group", (
            "remove_empty_lines", "collapse_blank_lines", "ensure_final_newline",
        ))
        self._build_option_group(body, "noise_group", (
            "dedupe_adjacent_lines", "dedupe_all_lines", "dedupe_paragraphs",
            "remove_abnormal_symbol_lines", "remove_repeated_short_lines", "remove_private_use_chars",
            "remove_ocr_placeholders", "remove_emoji", "normalize_repeated_punctuation",
        ))
        self._build_paragraph_group(body)
        self._build_regex_group(body)
        self._build_llm_rule_group(body)
        self._build_output_group(body)
        self._bind_mousewheel(canvas, body)

    def _init_option_vars(self) -> None:
        options = CleanOptions.from_dict(self.settings.get("local_cleaning", {}))
        self.option_vars = {}
        for key, value in options.to_dict().items():
            if isinstance(value, bool):
                self.option_vars[key] = tk.BooleanVar(value=value)
        self.choice_vars = {
            "unicode_normalization": tk.StringVar(value=options.unicode_normalization),
            "width_conversion": tk.StringVar(value=options.width_conversion),
            "chinese_conversion": tk.StringVar(value=options.chinese_conversion),
            "punctuation_mode": tk.StringVar(value=options.punctuation_mode),
            "paragraph_indent_mode": tk.StringVar(value=options.paragraph_indent_mode),
            "tab_size": tk.IntVar(value=options.tab_size),
        }

    def _build_action_group(self, parent: ttk.Frame) -> None:
        t = self.i18n.t
        box = ttk.LabelFrame(parent, text=t("action_group"), padding=5)
        box.pack(fill=tk.X, pady=(0, 5))
        for label, command, style in (
            (t("preview"), self.preview_rules, "TButton"),
            (t("rule_current"), self.run_rule_current, "Accent.TButton"),
            (t("rule_all"), self.run_rule_all, "Accent.TButton"),
            (t("ai_direct_current"), self.run_ai_current, "LLM.TButton"),
            (t("ai_direct_all"), self.run_ai_all, "LLM.TButton"),
            (t("ai_review_current"), self.run_ai_review_current, "LLM.TButton"),
        ):
            ttk.Button(box, text=label, command=command, style=style).pack(fill=tk.X, pady=2)

    def _build_option_group(self, parent: ttk.Frame, title_key: str, keys: tuple[str, ...]) -> None:
        box = ttk.LabelFrame(parent, text=self.i18n.t(title_key), padding=4)
        box.pack(fill=tk.X, pady=5)
        for key in keys:
            ttk.Checkbutton(
                box,
                text=self.i18n.t(f"option_{key}"),
                variable=self.option_vars[key],
                command=self.preview_rules,
            ).pack(anchor=tk.W, fill=tk.X, pady=1)
        self._build_selection_buttons(box, [self.option_vars[key] for key in keys])

    def _build_selection_buttons(self, parent: ttk.Frame, variables: list[tk.BooleanVar]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(
            row,
            text=self.i18n.t("select_all"),
            command=lambda: self._set_boolean_variables(variables, True),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(
            row,
            text=self.i18n.t("deselect_all"),
            command=lambda: self._set_boolean_variables(variables, False),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def _set_boolean_variables(self, variables: list[tk.BooleanVar], value: bool) -> None:
        for variable in variables:
            variable.set(value)
        self.preview_rules()

    def _combo_row(self, parent: ttk.Frame, label: str, variable: tk.Variable, values: tuple[str, ...], labels: tuple[str, ...]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label).pack(anchor=tk.W)
        combo = ttk.Combobox(row, state="readonly", values=labels)
        mapping = dict(zip(values, labels))
        reverse = dict(zip(labels, values))
        combo.set(mapping.get(str(variable.get()), labels[0]))
        combo.pack(fill=tk.X, pady=(1, 0))

        def update(_event=None) -> None:
            variable.set(reverse.get(combo.get(), values[0]))
            self.preview_rules()

        combo.bind("<<ComboboxSelected>>", update)

    def _build_paragraph_group(self, parent: ttk.Frame) -> None:
        t = self.i18n.t
        box = ttk.LabelFrame(parent, text=t("paragraph_group"), padding=4)
        box.pack(fill=tk.X, pady=5)
        boolean_keys = ("repair_hyphenated_linebreaks", "paragraph_reflow")
        for key in boolean_keys:
            ttk.Checkbutton(box, text=t(f"option_{key}"), variable=self.option_vars[key], command=self.preview_rules).pack(anchor=tk.W, fill=tk.X, pady=1)
        self._combo_row(box, t("unicode_normalization"), self.choice_vars["unicode_normalization"], ("none", "NFC", "NFKC", "NFD", "NFKD"), (t("unicode_none"), "NFC", "NFKC", "NFD", "NFKD"))
        self._combo_row(box, t("width_conversion"), self.choice_vars["width_conversion"], ("none", "full_to_half", "half_to_full"), (t("width_none"), t("full_to_half"), t("half_to_full")))
        self._combo_row(box, t("chinese_conversion"), self.choice_vars["chinese_conversion"], ("none", "t2s", "s2t"), (t("chinese_none"), t("t2s"), t("s2t")))
        self._combo_row(box, t("punctuation_mode"), self.choice_vars["punctuation_mode"], ("none", "cjk", "ascii"), (t("punctuation_none"), t("punctuation_cjk"), t("punctuation_ascii")))
        self._combo_row(box, t("indent_mode"), self.choice_vars["paragraph_indent_mode"], ("keep", "strip", "cjk_2"), (t("indent_keep"), t("indent_strip"), t("indent_cjk_2")))
        tab_row = ttk.Frame(box)
        tab_row.pack(fill=tk.X, pady=2)
        ttk.Label(tab_row, text=t("tab_size")).pack(side=tk.LEFT)
        ttk.Spinbox(tab_row, from_=1, to=16, width=5, textvariable=self.choice_vars["tab_size"], command=self.preview_rules).pack(side=tk.RIGHT)
        self._build_selection_buttons(box, [self.option_vars[key] for key in boolean_keys])

    def _build_regex_group(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text=self.i18n.t("regex_group"), padding=4)
        box.pack(fill=tk.X, pady=5)
        self.rule_vars = {}
        for rule in self.regex_rules:
            variable = tk.BooleanVar(value=rule.enabled)
            self.rule_vars[rule.key] = variable
            ttk.Checkbutton(
                box,
                text=rule.display_name(self.i18n.language),
                variable=variable,
                command=self.preview_rules,
            ).pack(anchor=tk.W, fill=tk.X, pady=1)
        self._build_selection_buttons(box, list(self.rule_vars.values()))
        ttk.Button(box, text=self.i18n.t("regex_library"), command=self.open_regex_library).pack(fill=tk.X, pady=(5, 1))

    def _build_llm_rule_group(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text=self.i18n.t("llm_rule_group"), padding=4)
        box.pack(fill=tk.X, pady=5)
        self.llm_rule_vars = {}
        if not self.llm_rules:
            ttk.Label(box, text=self.i18n.t("llm_rule_empty"), foreground="#4b6972", wraplength=280).pack(fill=tk.X, pady=3)
        for rule in self.llm_rules:
            variable = tk.BooleanVar(value=rule.enabled)
            self.llm_rule_vars[rule.key] = variable
            ttk.Checkbutton(box, text=rule.name, variable=variable).pack(anchor=tk.W, fill=tk.X, pady=1)
        row = ttk.Frame(box)
        row.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(row, text=self.i18n.t("select_all"), command=lambda: self._set_llm_rule_variables(True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(row, text=self.i18n.t("deselect_all"), command=lambda: self._set_llm_rule_variables(False)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        ttk.Button(box, text=self.i18n.t("llm_rule_library"), command=self.open_llm_rule_library).pack(fill=tk.X, pady=(5, 1))
        ttk.Button(box, text=self.i18n.t("llm_rule_safe_current"), style="LLM.TButton", command=self.run_llm_rules_current).pack(fill=tk.X, pady=1)
        ttk.Button(box, text=self.i18n.t("llm_rule_safe_selected"), style="LLM.TButton", command=self.run_llm_rules_selected).pack(fill=tk.X, pady=1)
        ttk.Button(box, text=self.i18n.t("llm_rule_review_current"), style="LLM.TButton", command=self.run_llm_rules_review_current).pack(fill=tk.X, pady=1)

    def _set_llm_rule_variables(self, value: bool) -> None:
        for variable in self.llm_rule_vars.values():
            variable.set(value)

    def _build_output_group(self, parent: ttk.Frame) -> None:
        t = self.i18n.t
        box = ttk.LabelFrame(parent, text=t("output_group"), padding=5)
        box.pack(fill=tk.X, pady=5)
        ttk.Label(box, text=t("output_folder")).pack(anchor=tk.W)
        row = ttk.Frame(box)
        row.pack(fill=tk.X, pady=2)
        ttk.Entry(row, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text=t("browse"), command=self.choose_output_dir).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Label(box, text=t("output_encoding")).pack(anchor=tk.W, pady=(4, 0))
        encoding_combo = ttk.Combobox(box, textvariable=self.output_encoding, values=OUTPUT_ENCODINGS, state="readonly")
        encoding_combo.pack(fill=tk.X, pady=(2, 0))
        encoding_combo.bind("<<ComboboxSelected>>", lambda _event: self._capture_output_encoding())
        ttk.Button(box, text=t("transcode_current"), command=self.transcode_current).pack(fill=tk.X, pady=(5, 1))

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        t = self.i18n.t
        queue_frame = ttk.LabelFrame(parent, text=t("file_queue"), padding=4)
        queue_frame.pack(fill=tk.X)
        columns = ("name", "encoding", "confidence", "characters", "status")
        self.file_tree = ttk.Treeview(queue_frame, columns=columns, show="headings", height=8, selectmode="extended")
        for column, label, width in (
            ("name", t("file_name"), 400), ("encoding", t("encoding"), 105),
            ("confidence", t("confidence"), 80), ("characters", t("characters"), 90),
            ("status", t("status"), 120),
        ):
            self.file_tree.heading(column, text=label)
            self.file_tree.column(column, width=width, minwidth=60, anchor=tk.W)
        ybar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=ybar.set)
        self.file_tree.grid(row=0, column=0, sticky=tk.EW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        queue_frame.columnconfigure(0, weight=1)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.file_tree.bind("<Double-1>", lambda _event: self.preview_rules())
        self.file_tree.bind("<Button-3>", self._show_file_context_menu)
        self._enable_drop(self.file_tree)

        drop_text = t("drop_hint") if DND_FILES is not None else t("drop_unavailable")
        drop_label = ttk.Label(parent, text=drop_text, anchor=tk.CENTER, foreground="#4b6972")
        drop_label.pack(fill=tk.X, pady=(3, 0))
        self._enable_drop(drop_label)

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        preview_tab = ttk.Frame(self.notebook)
        self.notebook.add(preview_tab, text=t("comparison"))
        preview_pane = ttk.PanedWindow(preview_tab, orient=tk.HORIZONTAL)
        preview_pane.pack(fill=tk.BOTH, expand=True)
        before_frame = ttk.LabelFrame(preview_pane, text=t("before"), padding=3)
        after_frame = ttk.LabelFrame(preview_pane, text=t("after"), padding=3)
        preview_pane.add(before_frame, weight=1)
        preview_pane.add(after_frame, weight=1)
        self.before_text = self._text_with_scrollbars(before_frame, editable=False)
        self.after_text = self._text_with_scrollbars(after_frame, editable=True)
        self.after_text.bind("<<Modified>>", self._on_after_modified)
        self.after_text.bind("<Control-z>", lambda _event: self._history_shortcut(self.undo_operation))
        self.after_text.bind("<Control-Z>", lambda _event: self._history_shortcut(self.undo_operation))
        self.after_text.bind("<Control-y>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Y>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Shift-z>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Shift-Z>", lambda _event: self._history_shortcut(self.redo_operation))

        diff_tab = ttk.Frame(self.notebook)
        self.notebook.add(diff_tab, text=t("diff"))
        self.diff_text = self._text_with_scrollbars(diff_tab, editable=False, wrap=tk.NONE)
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text=t("logs"))
        self.log_text = self._text_with_scrollbars(log_tab, editable=False)
        self._refresh_file_list()

    def _text_with_scrollbars(self, parent: ttk.Frame, editable: bool, wrap: str = tk.WORD) -> tk.Text:
        text = tk.Text(
            parent,
            wrap=wrap,
            undo=editable,
            padx=7,
            pady=7,
            font=("Microsoft YaHei UI", self.editor_font_size.get()),
        )
        self.editor_widgets.append(text)
        ybar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text.yview)
        xbar = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        text.grid(row=0, column=0, sticky=tk.NSEW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        xbar.grid(row=1, column=0, sticky=tk.EW)
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        if not editable:
            text.configure(state=tk.DISABLED)
        return text

    def change_editor_font_size(self, delta: int) -> None:
        size = min(32, max(8, self.editor_font_size.get() + delta))
        if size == self.editor_font_size.get():
            return
        self.editor_font_size.set(size)
        self.settings.setdefault("editor", {})["font_size"] = size
        for widget in list(self.editor_widgets):
            try:
                widget.configure(font=("Microsoft YaHei UI", size))
            except tk.TclError:
                self.editor_widgets.remove(widget)

    def _displayed_current_text(self) -> str:
        index = self._selected_index(show_message=False) if hasattr(self, "file_tree") else None
        if index is None:
            return ""
        if hasattr(self, "after_text") and not self._preview_truncated:
            return self.after_text.get("1.0", "end-1c")
        return self.files[index].active_text

    def _update_stats_summary(self, current_text: str | None = None) -> None:
        if not hasattr(self, "stats_summary"):
            return
        current = self._displayed_current_text() if current_text is None else current_text
        total = sum(len(item.active_text) for item in self.files)
        index = self._selected_index(show_message=False) if hasattr(self, "file_tree") else None
        if index is not None:
            total += len(current) - len(self.files[index].active_text)
        self.stats_summary.set(self.i18n.t("statistics_summary", current=len(current), total=max(0, total)))

    def show_statistics(self) -> None:
        current_index = self._selected_index(show_message=False)
        current_text = self._displayed_current_text()
        selected_indices = self._selected_indices() if hasattr(self, "file_tree") else []

        def texts_for(indices: list[int]) -> list[str]:
            values: list[str] = []
            for index in indices:
                values.append(current_text if index == current_index else self.files[index].active_text)
            return values

        current = calculate_statistics([current_text] if current_index is not None else [])
        selected = calculate_statistics(texts_for(selected_indices))
        all_files = calculate_statistics(texts_for(list(range(len(self.files)))))
        StatisticsDialog(self, self.i18n, current, selected, all_files)

    def _build_statusbar(self) -> None:
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)
        bar = ttk.Frame(self, padding=(7, 3))
        bar.pack(fill=tk.X)
        ttk.Label(bar, textvariable=self.status, style="Status.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress = ttk.Progressbar(bar, variable=self.progress_value, maximum=1, length=220, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=8)
        self.cancel_button = ttk.Button(bar, text=self.i18n.t("cancel_task"), command=self.cancel_current_task, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT)

    @staticmethod
    def _history_shortcut(command: Callable[[], None]) -> str:
        command()
        return "break"

    def _bind_mousewheel(self, canvas: tk.Canvas, child: tk.Widget) -> None:
        def wheel(event) -> None:
            delta = -1 if event.delta > 0 else 1
            canvas.yview_scroll(delta * 3, "units")

        widgets = [canvas, child]
        pending = list(child.winfo_children())
        while pending:
            widget = pending.pop()
            widgets.append(widget)
            pending.extend(widget.winfo_children())
        for widget in widgets:
            widget.bind("<MouseWheel>", wheel, add="+")
            widget.bind("<Button-4>", lambda _event: canvas.yview_scroll(-3, "units"), add="+")
            widget.bind("<Button-5>", lambda _event: canvas.yview_scroll(3, "units"), add="+")

    def _bind_shortcuts(self) -> None:
        bindings = {
            "<Control-o>": self.open_files, "<Control-O>": self.open_files,
            "<Control-Shift-o>": self.open_folder, "<Control-Shift-O>": self.open_folder,
            "<Delete>": self.remove_selected_files, "<Control-p>": self.preview_rules,
            "<F5>": self.run_rule_current, "<Control-F5>": self.run_rule_all,
            "<F6>": self.run_ai_current, "<Control-F6>": self.run_ai_all,
            "<F7>": self.run_ai_review_current, "<Control-s>": self.save_current_result,
            "<Control-Shift-s>": self.save_current_as, "<Control-Shift-S>": self.save_current_as,
            "<Control-Alt-s>": self.save_all_results, "<Control-Alt-S>": self.save_all_results,
            "<Escape>": self.cancel_current_task,
            "<Control-f>": self.open_find_replace,
            "<Control-z>": self.undo_operation, "<Control-Z>": self.undo_operation,
            "<Control-y>": self.redo_operation, "<Control-Y>": self.redo_operation,
            "<Control-Shift-z>": self.redo_operation, "<Control-Shift-Z>": self.redo_operation,
            "<Control-minus>": lambda: self.change_editor_font_size(-1),
            "<Control-equal>": lambda: self.change_editor_font_size(1),
            "<Control-plus>": lambda: self.change_editor_font_size(1),
        }
        for sequence, callback in bindings.items():
            self.bind_all(sequence, lambda _event, command=callback: command())

    def _enable_drop(self, widget: tk.Widget) -> None:
        if DND_FILES is None or not hasattr(widget, "drop_target_register"):
            return
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._handle_drop)
        except Exception:
            pass

    def _handle_drop(self, event) -> None:
        if not self._ensure_idle():
            return
        try:
            paths = [Path(value) for value in self.tk.splitlist(event.data)]
        except Exception:
            return
        self._load_paths(paths)

    def open_files(self) -> None:
        if not self._ensure_idle():
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(TEXT_EXTENSIONS))
        paths = filedialog.askopenfilenames(
            parent=self,
            title=self.i18n.t("import_files"),
            filetypes=[(self.i18n.t("file_queue"), patterns), (self.i18n.t("all_files"), "*.*")],
        )
        if paths:
            self._load_paths([Path(path) for path in paths])

    def open_folder(self) -> None:
        if not self._ensure_idle():
            return
        path = filedialog.askdirectory(parent=self, title=self.i18n.t("import_folder"))
        if path:
            self._load_paths([Path(path)])

    def _load_paths(self, paths: list[Path]) -> None:
        recursive = bool(self.settings.get("import", {}).get("recursive", True))
        existing = {str(item.path.resolve()).lower() for item in self.files}

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            candidates: list[tuple[Path, Path | None]] = []
            skipped = 0
            for path in paths:
                if cancel.is_set():
                    return {"kind": "import", "loaded": 0, "skipped": skipped, "cancelled": True}
                if path.is_dir():
                    discovered = discover_text_files([path], recursive=recursive)
                    candidates.extend((item, path) for item in discovered)
                    if not discovered:
                        skipped += 1
                elif path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
                    candidates.append((path, None))
                else:
                    skipped += 1

            unique: list[tuple[Path, Path | None]] = []
            seen = set(existing)
            for path, source_root in candidates:
                resolved = str(path.resolve()).lower()
                if resolved in seen:
                    skipped += 1
                    continue
                seen.add(resolved)
                unique.append((path, source_root))
            self._post(task_id, "maximum", max(1, len(unique)))
            if not unique:
                return {"kind": "import", "loaded": 0, "skipped": skipped}

            workers = min(self._max_workers(), len(unique))
            executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="clearlens-import")
            self._active_executor = executor
            futures = {
                executor.submit(read_text_file, path, source_root): path
                for path, source_root in unique
            }
            loaded = 0
            try:
                for position, future in enumerate(as_completed(futures), 1):
                    if cancel.is_set():
                        break
                    path = futures[future]
                    self._post(task_id, "status", self.i18n.t("importing", current=position, total=len(unique), name=path.name))
                    try:
                        item = future.result()
                    except Exception as exc:
                        skipped += 1
                        self._post(task_id, "log", self.i18n.t("failed", name=path.name, error=exc))
                    else:
                        loaded += 1
                        self._post(task_id, "import_item", item)
                    self._post(task_id, "progress", position)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                if self._active_executor is executor:
                    self._active_executor = None
            return {"kind": "import", "loaded": loaded, "skipped": skipped, "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=1)

    def _status_label(self, status: str, dirty: bool = False) -> str:
        rendered = self.i18n.t(status) if status in {
            "pending", "previewed", "rule_cleaned", "ai_cleaned", "ai_reviewed", "manual", "transcoded", "failed_status"
        } else status
        return self.i18n.t("unsaved_changes", status=rendered) if dirty else rendered

    def _refresh_file_list(self) -> None:
        if not hasattr(self, "file_tree"):
            return
        selected_paths = {
            str(self.files[int(iid)].path) for iid in self.file_tree.selection() if iid.isdigit() and int(iid) < len(self.files)
        }
        self.file_tree.delete(*self.file_tree.get_children())
        for index, item in enumerate(self.files):
            self.file_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(item.relative_path, item.encoding, f"{item.confidence:.0%}", len(item.active_text), self._status_label(item.status, item.dirty)),
            )
        for index, item in enumerate(self.files):
            if str(item.path) in selected_paths:
                self.file_tree.selection_add(str(index))
        self._update_stats_summary()

    def _selected_indices(self) -> list[int]:
        return sorted(int(iid) for iid in self.file_tree.selection() if iid.isdigit() and int(iid) < len(self.files))

    def _selected_index(self, show_message: bool = True) -> int | None:
        selected = self._selected_indices()
        if selected:
            focus = self.file_tree.focus()
            if focus.isdigit() and int(focus) in selected:
                return int(focus)
            return selected[0]
        if show_message:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
        return None

    def _on_tree_select(self, _event=None) -> None:
        index = self._selected_index(show_message=False)
        if index is not None:
            selected_identity = file_identity(self.files[index].path)
            if self._manual_history_path and self._manual_history_path != selected_identity:
                self._commit_manual_history()
            self.preview_selected()

    def remove_selected_files(self) -> None:
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        indices = self._selected_indices()
        if not indices:
            return
        for index in reversed(indices):
            del self.files[index]
        self.history.clear()
        self._refresh_file_list()
        self._clear_preview()
        self.status.set(self.i18n.t("removed_files", count=len(indices)))

    def clear_files(self) -> None:
        if not self._ensure_idle():
            return
        if self.files and not messagebox.askyesno(self.i18n.t("app_title"), self.i18n.t("clear_files_confirm"), parent=self):
            return
        self._commit_manual_history()
        self.files.clear()
        self.history.clear()
        self._refresh_file_list()
        self._clear_preview()

    def _show_file_context_menu(self, event) -> None:
        iid = self.file_tree.identify_row(event.y)
        if iid and iid not in self.file_tree.selection():
            self.file_tree.selection_set(iid)
            self.file_tree.focus(iid)
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label=self.i18n.t("import_files"), command=self.open_files)
        menu.add_command(label=self.i18n.t("import_folder"), command=self.open_folder)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("remove"), command=self.remove_selected_files)
        menu.add_command(label=self.i18n.t("clear"), command=self.clear_files)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("rule_current"), command=self.run_rule_current)
        menu.add_command(label=self.i18n.t("ai_direct_current"), command=self.run_ai_current)
        menu.add_command(label=self.i18n.t("reopen_encoding"), command=self.reopen_with_encoding)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("save_current"), command=self.save_current_result)
        menu.add_command(label=self.i18n.t("save_as"), command=self.save_current_as)
        menu.add_command(label=self.i18n.t("transcode_selected"), command=self.transcode_selected)
        menu.add_command(label=self.i18n.t("merge_selected"), command=self.merge_selected_files)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("reset_selected"), command=self.reset_selected_files)
        menu.tk_popup(event.x_root, event.y_root)

    def _current_options(self) -> CleanOptions:
        data: dict[str, Any] = {key: variable.get() for key, variable in self.option_vars.items()}
        data.update({key: variable.get() for key, variable in self.choice_vars.items()})
        return CleanOptions.from_dict(data)

    def _current_rules(self) -> list[RegexRule]:
        rules = copy.deepcopy(self.regex_rules)
        for rule in rules:
            variable = self.rule_vars.get(rule.key)
            if variable is not None:
                rule.enabled = bool(variable.get())
        return rules

    def _current_llm_rules(self) -> list[LLMRule]:
        rules = copy.deepcopy(self.llm_rules)
        for rule in rules:
            variable = self.llm_rule_vars.get(rule.key)
            if variable is not None:
                rule.enabled = bool(variable.get())
        return [rule for rule in rules if rule.enabled]

    def _thresholds(self) -> tuple[float, int]:
        values = self.settings.get("thresholds", {})
        return float(values.get("abnormal_symbol_ratio", 0.65)), int(values.get("min_line_length_for_symbol_check", 8))

    def preview_rules(self) -> None:
        self.preview_selected(apply_rules=True)

    def preview_selected(self, apply_rules: bool = False) -> None:
        index = self._selected_index(show_message=False)
        if index is None or not hasattr(self, "after_text"):
            return
        item = self.files[index]
        limit = max(10000, int(self.settings.get("processing", {}).get("preview_max_chars", 200000)))
        if apply_rules:
            source = item.active_text
            before = source[:limit]
            truncated = len(source) > limit
            ratio, minimum = self._thresholds()
            rendered, _result = clean_text(before, self._current_options(), self._current_rules(), ratio, minimum)
            if item.status == "pending":
                item.status = "previewed"
        else:
            before = item.original_text[:limit]
            rendered = item.active_text[:limit]
            truncated = len(item.original_text) > limit or len(item.active_text) > limit
        if truncated:
            marker = "\n\n[" + self.i18n.t("preview_truncated", limit=limit) + "]\n"
            before += marker
            rendered += marker
        self._set_preview(before, rendered, truncated=truncated)
        self._update_stats_summary(rendered)
        if self.file_tree.exists(str(index)):
            self.file_tree.set(str(index), "status", self._status_label(item.status, item.dirty))

    def _set_preview(self, before: str, after: str, truncated: bool = False) -> None:
        self._setting_preview = True
        self._preview_truncated = truncated
        self._set_text_widget(self.before_text, before, readonly=True)
        self.after_text.configure(state=tk.NORMAL)
        self.after_text.delete("1.0", tk.END)
        self.after_text.insert("1.0", after)
        self.after_text.edit_modified(False)
        if truncated:
            self.after_text.configure(state=tk.DISABLED)
        diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile=self.i18n.t("before"), tofile=self.i18n.t("after"), lineterm=""))
        self._set_text_widget(self.diff_text, diff, readonly=True)
        self._setting_preview = False
        self._update_stats_summary()

    @staticmethod
    def _set_text_widget(widget: tk.Text, value: str, readonly: bool) -> None:
        if readonly:
            widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        if readonly:
            widget.configure(state=tk.DISABLED)

    def _clear_preview(self) -> None:
        if not hasattr(self, "before_text"):
            return
        self._setting_preview = True
        self._preview_truncated = False
        self._set_text_widget(self.before_text, "", readonly=True)
        self.after_text.configure(state=tk.NORMAL)
        self.after_text.delete("1.0", tk.END)
        self.after_text.edit_modified(False)
        self._set_text_widget(self.diff_text, "", readonly=True)
        self._setting_preview = False
        self._update_stats_summary("")

    def _on_after_modified(self, _event=None) -> None:
        if self._setting_preview or not self.after_text.edit_modified():
            return
        index = self._selected_index(show_message=False)
        if index is not None:
            item = self.files[index]
            identity = file_identity(item.path)
            if self._manual_history_path != identity:
                self._commit_manual_history()
                self._manual_history_path = identity
                self._manual_history_before = OperationHistory.capture(self.files, [index])
            item.set_working_text(self.after_text.get("1.0", "end-1c"), "manual")
            if self._manual_history_after_id is not None:
                try:
                    self.after_cancel(self._manual_history_after_id)
                except tk.TclError:
                    pass
            self._manual_history_after_id = self.after(700, self._commit_manual_history)
            self._refresh_file_list()
            self._update_stats_summary(item.cleaned_text)
        self.after_text.edit_modified(False)

    def _commit_manual_history(self) -> None:
        if self._manual_history_after_id is not None:
            try:
                self.after_cancel(self._manual_history_after_id)
            except tk.TclError:
                pass
        before = self._manual_history_before
        identity = self._manual_history_path
        self._manual_history_after_id = None
        self._manual_history_before = None
        self._manual_history_path = None
        if before is None or identity is None:
            return
        indices = [index for index, item in enumerate(self.files) if file_identity(item.path) == identity]
        if not indices:
            return
        after = OperationHistory.capture(self.files, indices)
        self.history.record(self.i18n.t("history_manual_edit"), before, after)

    def _apply_history_states(self, states: dict[str, FileEditState]) -> int:
        restored = 0
        for item in self.files:
            state = states.get(file_identity(item.path))
            if state is None:
                continue
            state.restore(item)
            restored += 1
        if restored:
            self._refresh_file_list()
            self.preview_selected()
        return restored

    def undo_operation(self) -> None:
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        result = self.history.undo()
        if result is None:
            self.status.set(self.i18n.t("history_nothing_to_undo"))
            return
        entry, states = result
        restored = self._apply_history_states(states)
        self.status.set(self.i18n.t("history_undone", label=entry.label, count=restored))

    def redo_operation(self) -> None:
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        result = self.history.redo()
        if result is None:
            self.status.set(self.i18n.t("history_nothing_to_redo"))
            return
        entry, states = result
        restored = self._apply_history_states(states)
        self.status.set(self.i18n.t("history_redone", label=entry.label, count=restored))

    def reset_current_file(self) -> None:
        index = self._selected_index()
        if index is not None:
            self._reset_indices([index], self.i18n.t("reset_current"))

    def reset_selected_files(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        self._reset_indices(indices, self.i18n.t("reset_selected"))

    def reset_all_files(self) -> None:
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._reset_indices(list(range(len(self.files))), self.i18n.t("reset_all"))

    def _reset_indices(self, indices: list[int], label: str) -> None:
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        before = OperationHistory.capture(self.files, indices)
        for index in indices:
            self.files[index].reset_working_state(dirty=True)
        after = OperationHistory.capture(self.files, indices)
        self.history.record(label, before, after)
        self._refresh_file_list()
        self.preview_selected()
        self.status.set(self.i18n.t("reset_done", count=len(indices)))

    def _output_config(self) -> dict[str, Any]:
        output = dict(self.settings.get("output", {}))
        output["directory"] = self.output_dir.get() or "clearlens_output"
        output["encoding"] = self.output_encoding.get() or "utf-8"
        return output

    def _capture_output_encoding(self) -> None:
        self.settings.setdefault("output", {})["encoding"] = self.output_encoding.get() or "utf-8"

    def _max_workers(self) -> int:
        processing = self.settings.get("processing", {})
        if not bool(processing.get("parallel_enabled", True)):
            return 1
        return max(1, int(processing.get("max_workers", max(1, (os.cpu_count() or 2) // 2))))

    def _validate_output_dir(self, path: Path | None = None, show_message: bool = True) -> bool:
        target = (path or Path(self.output_dir.get() or "clearlens_output")).resolve()
        source_dirs = {item.path.parent.resolve() for item in self.files}
        source_dirs.update(item.source_root.resolve() for item in self.files if item.source_root)
        valid = target not in source_dirs
        if not valid and show_message:
            messagebox.showwarning(self.i18n.t("app_title"), self.i18n.t("output_matches_source"), parent=self)
        return valid

    @staticmethod
    def _save_item_path_with_config(item: TextFile, text: str, output: dict[str, Any]) -> Path:
        suffix_key = item.output_suffix_key
        return write_output_file(
            text,
            item,
            Path(str(output["directory"])),
            encoding=str(item.target_encoding or output.get("encoding", "utf-8")),
            newline_style=str(output.get("newline", "lf")),
            suffix=str(output.get(suffix_key, "_cleaned" if suffix_key == "clean_suffix" else "_converted")),
            preserve_folders=bool(output.get("preserve_folders", True)),
            overwrite=bool(output.get("overwrite_existing", False)),
        )

    def _save_item_threadsafe(self, item: TextFile, text: str, output: dict[str, Any]) -> Path:
        with self._output_lock:
            return self._save_item_path_with_config(item, text, output)

    def run_rule_current(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is not None:
            self._run_rule_indices([index])

    def run_rule_all(self) -> None:
        if not self._ensure_idle():
            return
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._run_rule_indices(list(range(len(self.files))))

    def _run_rule_indices(self, indices: list[int]) -> None:
        options, rules = self._current_options(), self._current_rules()
        ratio, minimum = self._thresholds()
        jobs = [(index, self.files[index].active_text) for index in indices]
        source_lengths = {index: len(text) for index, text in jobs}

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            max_workers = min(self._max_workers(), len(jobs))
            use_processes = bool(self.settings.get("processing", {}).get("use_multiprocessing", True)) and max_workers > 1
            executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
            executor = executor_class(max_workers=max_workers)
            self._active_executor = executor
            futures = {
                executor.submit(clean_text_job, index, text, options, rules, ratio, minimum): index
                for index, text in jobs
            }
            completed = 0
            processed = 0
            try:
                for future in as_completed(futures):
                    if cancel.is_set():
                        break
                    index = futures[future]
                    item = self.files[index]
                    completed += 1
                    self._post(task_id, "status", self.i18n.t("processing", current=completed, total=len(jobs), name=item.name))
                    try:
                        _index, cleaned, result = future.result()
                        if cancel.is_set():
                            break
                    except Exception as exc:
                        self._post(task_id, "file_failed", (index, exc))
                    else:
                        processed += 1
                        self._post(task_id, "rule_result", (index, cleaned, result.changes, result.warnings, source_lengths[index]))
                    self._post(task_id, "progress", completed)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                if self._active_executor is executor:
                    self._active_executor = None
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=len(jobs),
            history_label=self.i18n.t("operation_rule"),
            history_indices=indices,
        )

    def _ai_settings(self) -> AISettings:
        ai = self.settings.get("ai", {})
        provider = str(ai.get("provider", "openai")).lower()
        model_key = "deepseek_model" if provider == "deepseek" else "openai_model"
        return AISettings(
            enabled=bool(ai.get("enabled", False)),
            provider=provider,
            model=str(ai.get(model_key, "deepseek-v4-flash" if provider == "deepseek" else "gpt-5.4-mini")),
            api_key=self.session_api_keys.get(provider, ""),
            reasoning_effort=str(ai.get("reasoning_effort", "low")),
            max_chars_per_request=int(ai.get("max_chars_per_request", 30000)),
            max_output_tokens=int(ai.get("max_output_tokens", 8000)),
            confirm_before_send=bool(ai.get("confirm_before_send", True)),
            remember_api_key=bool(ai.get("remember_api_key", False)),
        )

    def _confirm_ai(self, count: int) -> bool:
        settings = self._ai_settings()
        if not settings.enabled or not settings.resolved_api_key():
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("ai_disabled_message"), parent=self)
            return False
        if not settings.confirm_before_send:
            return True
        key = "ai_batch_confirm" if count > 1 else "ai_send_confirm"
        provider = "DeepSeek" if settings.provider == "deepseek" else "OpenAI"
        return messagebox.askyesno(self.i18n.t("app_title"), self.i18n.t(key, count=count, provider=provider), parent=self)

    def run_ai_current(self) -> None:
        index = self._selected_index()
        if index is not None:
            self._run_ai_indices([index])

    def run_ai_all(self) -> None:
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._run_ai_indices(list(range(len(self.files))))

    def _run_ai_indices(self, indices: list[int]) -> None:
        if not self._ensure_idle():
            return
        if not self._confirm_ai(len(indices)):
            return
        settings = self._ai_settings()
        jobs = [(index, self.files[index].active_text) for index in indices]

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            client = AIClient(settings)
            processed = 0
            for position, (index, source_text) in enumerate(jobs, 1):
                if cancel.is_set():
                    break
                item = self.files[index]
                self._post(task_id, "status", self.i18n.t("processing", current=position, total=len(indices), name=item.name))
                try:
                    result = client.direct_clean(source_text)
                    if cancel.is_set():
                        break
                    if not result.completed:
                        self._post(task_id, "file_failed", (index, "; ".join(result.warnings)))
                        continue
                    processed += 1
                    changes = [f"ai_safe_edits:{len(result.applied)}", f"ai_rejected_edits:{len(result.rejected)}"]
                    self._post(task_id, "ai_result", (index, result.text, changes, result.warnings, len(source_text)))
                    self._post(task_id, "log", self.i18n.t("ai_guard_summary", total=len(result.suggestions), applied=len(result.applied), rejected=len(result.rejected)))
                except Exception as exc:
                    self._post(task_id, "file_failed", (index, exc))
                finally:
                    self._post(task_id, "progress", position)
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=len(indices),
            history_label=self.i18n.t("operation_ai_direct"),
            history_indices=indices,
        )

    def run_llm_rules_current(self) -> None:
        index = self._selected_index()
        if index is not None:
            self._run_llm_rule_indices([index])

    def run_llm_rules_selected(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        self._run_llm_rule_indices(indices)

    def _run_llm_rule_indices(self, indices: list[int]) -> None:
        if not self._ensure_idle():
            return
        rules = self._current_llm_rules()
        if not rules:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("llm_rule_none_selected"), parent=self)
            return
        if not self._confirm_ai(len(indices)):
            return
        settings = self._ai_settings()
        instructions = [rule.instruction for rule in rules]
        jobs = [(index, self.files[index].active_text) for index in indices]

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            client = AIClient(settings)
            processed = 0
            for position, (index, source_text) in enumerate(jobs, 1):
                if cancel.is_set():
                    break
                item = self.files[index]
                self._post(task_id, "status", self.i18n.t("processing", current=position, total=len(indices), name=item.name))
                try:
                    result = client.clean_with_rules(source_text, instructions)
                    if cancel.is_set():
                        break
                    if not result.completed:
                        self._post(task_id, "file_failed", (index, "; ".join(result.warnings)))
                        continue
                    processed += 1
                    changes = [
                        f"llm_rules:{len(rules)}",
                        f"ai_safe_edits:{len(result.applied)}",
                        f"ai_rejected_edits:{len(result.rejected)}",
                    ]
                    self._post(task_id, "llm_rule_result", (index, result.text, changes, result.warnings, len(source_text)))
                    self._post(task_id, "log", self.i18n.t("ai_guard_summary", total=len(result.suggestions), applied=len(result.applied), rejected=len(result.rejected)))
                except Exception as exc:
                    self._post(task_id, "file_failed", (index, exc))
                finally:
                    self._post(task_id, "progress", position)
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=len(indices),
            history_label=self.i18n.t("operation_llm_rule"),
            history_indices=indices,
        )

    def run_llm_rules_review_current(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        rules = self._current_llm_rules()
        if index is None:
            return
        if not rules:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("llm_rule_none_selected"), parent=self)
            return
        if not self._confirm_ai(1):
            return
        item = self.files[index]
        settings = self._ai_settings()
        source = item.active_text
        instructions = [rule.instruction for rule in rules]

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            suggestions, warnings = AIClient(settings).review_with_rules(source, instructions)
            if not cancel.is_set():
                self._post(
                    task_id,
                    "review_ready",
                    (index, source, suggestions, warnings, self.i18n.t("operation_llm_rule_review")),
                )
                self._post(task_id, "progress", 1)
            return {"kind": "review", "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=1)

    def run_ai_review_current(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is None or not self._confirm_ai(1):
            return
        item = self.files[index]
        settings = self._ai_settings()
        source_text = item.active_text

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            if cancel.is_set():
                return {"kind": "review", "cancelled": True}
            client = AIClient(settings)
            suggestions, warnings = client.review(source_text)
            if not cancel.is_set():
                self._post(
                    task_id,
                    "review_ready",
                    (index, source_text, suggestions, warnings, self.i18n.t("operation_ai_review")),
                )
                self._post(task_id, "progress", 1)
            return {"kind": "review", "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=1)

    def _open_review_dialog(self, payload: tuple[int, str, list[AISuggestion], list[str], str]) -> None:
        index, source, suggestions, warnings, history_label = payload
        for warning in warnings:
            self._append_log(warning)
        if not suggestions:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("ai_review_no_changes"), parent=self)
            return
        if index >= len(self.files):
            return

        def update(text: str) -> None:
            item = self.files[index]
            before = OperationHistory.capture(self.files, [index])
            item.set_working_text(text, "ai_reviewed")
            after = OperationHistory.capture(self.files, [index])
            self.history.record(history_label, before, after)
            self._refresh_file_list()
            self.preview_selected()

        def finish(text: str, applied_count: int) -> None:
            if not applied_count:
                return
            item = self.files[index]
            self._record_processing(
                "ai_review",
                item,
                len(source),
                [f"human_applied_ai_suggestions:{applied_count}"],
                [],
            )
            self.status.set(self.i18n.t("processing_complete_unsaved", count=1))

        AIReviewDialog(self, self.i18n, source, suggestions, update, finish)

    def transcode_current(self) -> None:
        index = self._selected_index()
        if index is not None:
            self._transcode_indices([index])

    def transcode_selected(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        self._transcode_indices(indices)

    def transcode_all(self) -> None:
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._transcode_indices(list(range(len(self.files))))

    def _transcode_indices(self, indices: list[int]) -> None:
        if not self._ensure_idle():
            return
        output = self._output_config()
        encoding = str(output.get("encoding", "utf-8"))
        newline_style = str(output.get("newline", "lf"))
        jobs = [(index, self.files[index].active_text) for index in indices]

        def validate(text: str) -> str:
            apply_newline_style(text, newline_style).encode(encoding, errors="strict")
            return text

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            executor = ThreadPoolExecutor(max_workers=min(self._max_workers(), len(indices)), thread_name_prefix="clearlens-transcode")
            self._active_executor = executor
            futures = {
                executor.submit(validate, text): (index, text)
                for index, text in jobs
            }
            processed = 0
            try:
                for position, future in enumerate(as_completed(futures), 1):
                    if cancel.is_set():
                        break
                    index, source_text = futures[future]
                    item = self.files[index]
                    self._post(task_id, "status", self.i18n.t("processing", current=position, total=len(indices), name=item.name))
                    try:
                        prepared_text = future.result()
                    except Exception as exc:
                        self._post(task_id, "file_failed", (index, exc))
                    else:
                        processed += 1
                        self._post(task_id, "transcode_result", (index, prepared_text, encoding, len(source_text)))
                    self._post(task_id, "progress", position)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                if self._active_executor is executor:
                    self._active_executor = None
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=len(indices),
            history_label=self.i18n.t("operation_transcode"),
            history_indices=indices,
        )

    def save_current_result(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is None:
            return
        self._commit_manual_history()
        self._capture_editor_for_save(index)
        self._save_indices([index])

    def _capture_editor_for_save(self, index: int) -> str:
        item = self.files[index]
        if self._preview_truncated:
            return item.active_text
        text = self.after_text.get("1.0", "end-1c")
        if text != item.active_text:
            before = OperationHistory.capture(self.files, [index])
            item.set_working_text(text, "manual")
            after = OperationHistory.capture(self.files, [index])
            self.history.record(self.i18n.t("history_manual_edit"), before, after)
            self._refresh_file_list()
        return text

    def save_current_as(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is None:
            return
        item = self.files[index]
        self._commit_manual_history()
        text = self._capture_editor_for_save(index)
        output_dir = Path(self.output_dir.get() or "clearlens_output")
        suffix = str(self.settings.get("output", {}).get(item.output_suffix_key, "_cleaned"))
        target_name = item.path.stem + suffix + item.path.suffix
        path = filedialog.asksaveasfilename(
            parent=self,
            title=self.i18n.t("save_as"),
            initialdir=str(output_dir),
            initialfile=target_name,
            defaultextension=item.path.suffix or ".txt",
        )
        if not path:
            return
        target = Path(path)
        protected = [entry.path for entry in self.files]
        output = self._output_config()

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            if not cancel.is_set():
                result = write_text_path(
                    text,
                    target,
                    str(item.target_encoding or output.get("encoding", "utf-8")),
                    str(output.get("newline", "lf")),
                    protected,
                )
                self._post(task_id, "save_as_result", (index, result, text))
                self._post(task_id, "progress", 1)
            return {"kind": "save_as", "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=1)

    def save_all_results(self) -> None:
        if not self._ensure_idle():
            return
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._commit_manual_history()
        self._save_indices(list(range(len(self.files))))

    def _save_indices(self, indices: list[int]) -> None:
        if not self._validate_output_dir():
            return
        output = self._output_config()

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            executor = ThreadPoolExecutor(max_workers=min(self._max_workers(), len(indices)), thread_name_prefix="clearlens-save")
            self._active_executor = executor
            futures = {
                executor.submit(self._save_item_threadsafe, self.files[index], self.files[index].active_text, output): index
                for index in indices
            }
            saved = 0
            try:
                for position, future in enumerate(as_completed(futures), 1):
                    if cancel.is_set():
                        break
                    index = futures[future]
                    item = self.files[index]
                    self._post(task_id, "status", self.i18n.t("processing", current=position, total=len(indices), name=item.name))
                    try:
                        target = future.result()
                    except Exception as exc:
                        self._post(task_id, "file_failed", (index, exc))
                    else:
                        saved += 1
                        self._post(task_id, "save_result", (index, target))
                    self._post(task_id, "progress", position)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                if self._active_executor is executor:
                    self._active_executor = None
            return {"kind": "save", "saved": saved, "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=len(indices))

    def merge_selected_files(self) -> None:
        indices = self._selected_indices()
        if len(indices) < 2:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("merge_requires_two"), parent=self)
            return
        self._merge_indices(indices)

    def merge_all_files(self) -> None:
        if len(self.files) < 2:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("merge_requires_two"), parent=self)
            return
        self._merge_indices(list(range(len(self.files))))

    def _merge_indices(self, indices: list[int]) -> None:
        if not self._ensure_idle() or not self._validate_output_dir():
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title=self.i18n.t("merge_all"),
            initialdir=self.output_dir.get() or None,
            initialfile="merged.txt",
            defaultextension=".txt",
            filetypes=[(self.i18n.t("file_queue"), "*.txt"), (self.i18n.t("all_files"), "*.*")],
        )
        if not path:
            return
        texts = [self.files[index].active_text for index in indices]
        self._write_document(merge_texts(texts), Path(path), "merge")

    def _write_document(self, text: str, target: Path, kind: str) -> None:
        output = self._output_config()
        protected = [item.path for item in self.files]

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            if not cancel.is_set():
                written = write_text_path(text, target, str(output.get("encoding", "utf-8")), str(output.get("newline", "lf")), protected)
                self._post(task_id, "document_saved", written)
                self._post(task_id, "progress", 1)
            return {"kind": kind, "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=1)

    def _start_worker(
        self,
        worker: Callable[[int, threading.Event], dict[str, Any]],
        maximum: int = 1,
        history_label: str | None = None,
        history_indices: list[int] | None = None,
    ) -> None:
        if self.busy:
            return
        self._task_counter += 1
        task_id = self._task_counter
        cancel = threading.Event()
        self._active_task_id = task_id
        self._cancel_event = cancel
        self._active_executor = None
        self.busy = True
        if history_label and history_indices:
            self._commit_manual_history()
            self._pending_history[task_id] = (
                history_label,
                OperationHistory.capture(self.files, history_indices),
            )
        self.progress.configure(maximum=max(1, maximum))
        self.progress_value.set(0)
        self.cancel_button.configure(state=tk.NORMAL)

        def runner() -> None:
            summary: dict[str, Any]
            try:
                summary = worker(task_id, cancel)
            except Exception as exc:
                summary = {"kind": "error", "error": str(exc), "cancelled": cancel.is_set()}
                self._post(task_id, "log", str(exc))
            self._post(task_id, "done", summary)

        threading.Thread(target=runner, daemon=True, name=f"clearlens-task-{task_id}").start()

    def _commit_pending_history(self, task_id: int) -> None:
        pending = self._pending_history.pop(task_id, None)
        if pending is None:
            return
        label, before = pending
        identities = set(before)
        indices = [index for index, item in enumerate(self.files) if file_identity(item.path) in identities]
        after = OperationHistory.capture(self.files, indices)
        self.history.record(label, before, after)

    def _post(self, task_id: int, kind: str, payload: Any) -> None:
        self.worker_queue.put((task_id, kind, payload))

    def cancel_current_task(self) -> None:
        if not self.busy or self._active_task_id is None:
            return
        task_id = self._active_task_id
        if self._cancel_event is not None:
            self._cancel_event.set()
        executor = self._active_executor
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)
        self._commit_pending_history(task_id)
        self._active_task_id = None
        self._cancel_event = None
        self._active_executor = None
        self.busy = False
        self.progress_value.set(0)
        self.cancel_button.configure(state=tk.DISABLED)
        self.status.set(self.i18n.t("task_cancelled"))

    def _ensure_idle(self) -> bool:
        if not self.busy:
            return True
        messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("busy_message"), parent=self)
        return False

    def _poll_worker_queue(self) -> None:
        try:
            while True:
                task_id, kind, payload = self.worker_queue.get_nowait()
                if task_id != self._active_task_id:
                    continue
                if kind == "status":
                    self.status.set(str(payload))
                elif kind == "maximum":
                    self.progress.configure(maximum=max(1, int(payload)))
                elif kind == "progress":
                    self.progress_value.set(float(payload))
                elif kind == "log":
                    self._append_log(str(payload))
                elif kind == "import_item":
                    self.files.append(payload)
                elif kind == "rule_result":
                    index, cleaned, changes, warnings, input_chars = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.set_working_text(cleaned, "rule_cleaned")
                        self._record_processing("rule", item, input_chars, changes, warnings)
                elif kind == "ai_result":
                    index, cleaned, changes, warnings, input_chars = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.set_working_text(cleaned, "ai_cleaned")
                        self._record_processing("ai_direct", item, input_chars, changes, warnings)
                elif kind == "llm_rule_result":
                    index, cleaned, changes, warnings, input_chars = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.set_working_text(cleaned, "ai_cleaned")
                        self._record_processing("llm_rule", item, input_chars, changes, warnings)
                elif kind == "transcode_result":
                    index, _prepared_text, encoding, input_chars = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.prepare_transcode(encoding)
                        self._record_processing("transcode", item, input_chars, [f"target_encoding:{encoding}"], item.warnings)
                elif kind == "save_result":
                    index, target = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.mark_saved(target)
                        self._record_result("manual_save", item, target, [], [])
                elif kind == "save_as_result":
                    index, target, text = payload
                    if index < len(self.files):
                        item = self.files[index]
                        if text != item.active_text:
                            item.set_working_text(text, "manual")
                        item.mark_saved(target)
                        self._record_result("manual_save", item, target, [], [])
                        self.status.set(self.i18n.t("saved_to", path=target))
                        messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("saved_to", path=target), parent=self)
                elif kind == "document_saved":
                    self.status.set(self.i18n.t("saved_to", path=payload))
                    messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("saved_to", path=payload), parent=self)
                elif kind == "file_failed":
                    index, error = payload
                    if index < len(self.files):
                        item = self.files[index]
                        item.status = "failed_status"
                        self._append_log(self.i18n.t("failed", name=item.name, error=error))
                elif kind == "review_ready":
                    self._open_review_dialog(payload)
                elif kind == "done":
                    self._commit_pending_history(task_id)
                    self.busy = False
                    self._active_task_id = None
                    self._cancel_event = None
                    self._active_executor = None
                    self.cancel_button.configure(state=tk.DISABLED)
                    self._refresh_file_list()
                    kind_name = str(payload.get("kind", "batch")) if isinstance(payload, dict) else "batch"
                    if kind_name == "import":
                        loaded = int(payload.get("loaded", 0))
                        skipped = int(payload.get("skipped", 0))
                        if loaded:
                            first = max(0, len(self.files) - loaded)
                            self.file_tree.selection_set(str(first))
                            self.file_tree.focus(str(first))
                            self.file_tree.see(str(first))
                        self.status.set(self.i18n.t("files_loaded", count=loaded, skipped=skipped))
                    elif kind_name == "save":
                        message = self.i18n.t("saved_count", count=int(payload.get("saved", 0)), path=self.output_dir.get())
                        self.status.set(message)
                        if not bool(payload.get("cancelled", False)):
                            messagebox.showinfo(self.i18n.t("app_title"), message, parent=self)
                    elif kind_name == "processing":
                        message = self.i18n.t("processing_complete_unsaved", count=int(payload.get("processed", 0)))
                        self.status.set(message)
                    elif kind_name == "error":
                        error = str(payload.get("error", ""))
                        rendered_error = self.i18n.t("output_matches_source") if "output_path_matches_source" in error else error
                        self.status.set(self.i18n.t("task_failed", error=rendered_error))
                        messagebox.showerror(self.i18n.t("app_title"), rendered_error, parent=self)
                    elif kind_name not in {"merge", "save_as", "review"}:
                        self.status.set(self.i18n.t("finished", path=self.output_dir.get()))
                    self.preview_selected()
        except queue.Empty:
            pass
        self.after(100, self._poll_worker_queue)

    def _record_result(self, operation: str, item: TextFile, target: Path, changes: list[str], warnings: list[str]) -> None:
        row = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "operation": operation,
            "source": str(item.path),
            "output": str(target),
            "input_encoding": item.encoding,
            "output_encoding": item.target_encoding or self.output_encoding.get() or "utf-8",
            "original_chars": len(item.original_text),
            "result_chars": len(item.active_text),
            "changes": "; ".join(changes),
            "warnings": "; ".join(warnings),
        }
        self.log_rows.append(row)
        operation_label = self.i18n.t(f"operation_{operation}")
        self._append_log(f"[{operation_label}] {item.name}: {row['original_chars']} -> {row['result_chars']} | {target}")

    def _record_processing(
        self,
        operation: str,
        item: TextFile,
        input_chars: int,
        changes: list[str],
        warnings: list[str],
    ) -> None:
        row = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "operation": operation,
            "source": str(item.path),
            "output": "",
            "input_encoding": item.encoding,
            "output_encoding": item.target_encoding or self.output_encoding.get() or "utf-8",
            "original_chars": len(item.original_text),
            "input_chars": input_chars,
            "result_chars": len(item.active_text),
            "changes": "; ".join(changes),
            "warnings": "; ".join(warnings),
        }
        self.log_rows.append(row)
        operation_label = self.i18n.t(f"operation_{operation}")
        self._append_log(
            f"[{operation_label}] {item.name}: {input_chars} -> {row['result_chars']} | {self.i18n.t('not_saved_yet')}"
        )

    def _append_log(self, message: str) -> None:
        if not hasattr(self, "log_text"):
            return
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_log(self) -> None:
        self.log_rows.clear()
        if hasattr(self, "log_text"):
            self._set_text_widget(self.log_text, "", readonly=True)

    def export_log(self) -> None:
        if not self.log_rows:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_log"), parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title=self.i18n.t("export_log"),
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json")],
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() == ".json":
            export_log_json(self.log_rows, target)
        else:
            export_log_csv(self.log_rows, target)
        self.status.set(self.i18n.t("log_exported", path=target))

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory(parent=self, initialdir=self.output_dir.get() or None)
        if path and self._validate_output_dir(Path(path)):
            self.output_dir.set(path)
            self.settings.setdefault("output", {})["directory"] = path

    def open_output_folder(self) -> None:
        path = Path(self.output_dir.get())
        path.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror(self.i18n.t("app_title"), self.i18n.t("output_open_failed", error=exc), parent=self)

    def open_regex_library(self) -> None:
        if not self._ensure_idle():
            return
        self._capture_ui_settings()
        index = self._selected_index(show_message=False)
        test_text = self.files[index].active_text if index is not None else ""
        ordered_indices = list(range(len(self.files)))
        if index is not None:
            ordered_indices.remove(index)
            ordered_indices.insert(0, index)
        samples = [
            (f"{sample_index + 1}. {self.files[file_index].relative_path}", self.files[file_index].active_text)
            for sample_index, file_index in enumerate(ordered_indices)
        ]
        dialog = RegexLibraryDialog(
            self,
            self.i18n,
            self.regex_rules,
            test_text,
            ai_settings=self._ai_settings(),
            samples=samples,
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.regex_rules = dialog.result
            save_custom_regex_rules(self.regex_rules)
            self.settings["regex_enabled_keys"] = [rule.key for rule in self.regex_rules if rule.enabled]
            self._rebuild_ui()

    def open_llm_rule_library(self) -> None:
        if not self._ensure_idle():
            return
        self._capture_ui_settings()
        dialog = LLMRuleLibraryDialog(self, self.i18n, self.llm_rules)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.llm_rules = dialog.result
            save_llm_rules(self.llm_rules)
            self.settings["llm_rule_enabled_keys"] = [rule.key for rule in self.llm_rules if rule.enabled]
            self._rebuild_ui()

    def reopen_with_encoding(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is None:
            return
        item = self.files[index]
        encoding = simpledialog.askstring(
            self.i18n.t("reopen_encoding"),
            self.i18n.t("source_encoding_prompt"),
            initialvalue=item.encoding,
            parent=self,
        )
        if not encoding:
            return
        try:
            item.original_text = item.path.read_bytes().decode(encoding.strip(), errors="strict")
        except (LookupError, UnicodeDecodeError, OSError) as exc:
            messagebox.showerror(self.i18n.t("app_title"), str(exc), parent=self)
            return
        item.encoding = encoding.strip().lower()
        item.confidence = 1.0
        item.reset_working_state(dirty=False)
        item.warnings.clear()
        self.history.clear()
        self._refresh_file_list()
        self.preview_selected()

    def open_find_replace(self) -> None:
        if not self._ensure_idle():
            return
        if self._selected_index() is None:
            return
        if self._preview_truncated:
            messagebox.showwarning(self.i18n.t("app_title"), self.i18n.t("preview_edit_unavailable"), parent=self)
            return

        def get_text() -> str:
            return self.after_text.get("1.0", "end-1c")

        def set_text(value: str) -> None:
            self.after_text.delete("1.0", tk.END)
            self.after_text.insert("1.0", value)
            self.after_text.edit_modified(True)
            self._on_after_modified()

        FindReplaceDialog(self, self.i18n, get_text, set_text)

    def export_profile(self) -> None:
        if not self._ensure_idle():
            return
        self._capture_ui_settings()
        path = filedialog.asksaveasfilename(
            parent=self,
            title=self.i18n.t("save_profile"),
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="clearlens_profile.json",
        )
        if not path:
            return
        try:
            save_profile(Path(path), self.settings, self.regex_rules, self.llm_rules)
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror(self.i18n.t("app_title"), self.i18n.t("profile_failed", error=exc), parent=self)
            return
        self.status.set(self.i18n.t("profile_saved", path=path))

    def import_profile(self) -> None:
        if not self._ensure_idle():
            return
        path = filedialog.askopenfilename(
            parent=self,
            title=self.i18n.t("load_profile"),
            filetypes=[("JSON", "*.json"), (self.i18n.t("all_files"), "*.*")],
        )
        if not path:
            return
        try:
            imported, custom_rules, imported_llm_rules = load_profile(Path(path))
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror(self.i18n.t("app_title"), self.i18n.t("profile_failed", error=exc), parent=self)
            return

        imported_ai = imported.setdefault("ai", {})
        imported_ai["openai_api_key"] = self.session_api_keys["openai"]
        imported_ai["deepseek_api_key"] = self.session_api_keys["deepseek"]
        built_in_rules = [rule for rule in load_regex_rules() if not rule.custom]
        seen_rule_keys = {rule.key for rule in built_in_rules}
        unique_custom_rules: list[RegexRule] = []
        for rule in custom_rules:
            if rule.key in seen_rule_keys:
                continue
            seen_rule_keys.add(rule.key)
            unique_custom_rules.append(rule)
        self.regex_rules = built_in_rules + unique_custom_rules
        imported_enabled = imported.get("regex_enabled_keys")
        if isinstance(imported_enabled, list):
            enabled_keys = {str(key) for key in imported_enabled}
            for rule in self.regex_rules:
                rule.enabled = rule.key in enabled_keys
        save_custom_regex_rules(self.regex_rules)
        self.llm_rules = imported_llm_rules
        imported_llm_enabled = imported.get("llm_rule_enabled_keys")
        if isinstance(imported_llm_enabled, list):
            enabled_llm_keys = {str(key) for key in imported_llm_enabled}
            for rule in self.llm_rules:
                rule.enabled = rule.key in enabled_llm_keys
        save_llm_rules(self.llm_rules)
        self.settings = imported
        self.output_dir.set(str(imported.get("output", {}).get("directory", "clearlens_output")))
        self.output_encoding.set(str(imported.get("output", {}).get("encoding", "utf-8")))
        self.editor_font_size.set(int(imported.get("editor", {}).get("font_size", 11)))
        self.i18n.set_language(str(imported.get("language", "zh_sim")))
        self._save_settings()
        self._rebuild_ui()
        self.status.set(self.i18n.t("profile_loaded", path=path))

    def open_settings(self, _tab: str | None = None) -> None:
        if self.busy:
            return
        self._capture_ui_settings()
        dialog_settings = copy.deepcopy(self.settings)
        dialog_ai = dialog_settings.setdefault("ai", {})
        dialog_ai["openai_api_key"] = self.session_api_keys["openai"]
        dialog_ai["deepseek_api_key"] = self.session_api_keys["deepseek"]
        dialog = SettingsDialog(self, dialog_settings, self.i18n, initial_tab=_tab)
        self.wait_window(dialog)
        if dialog.result is not None:
            new_output_dir = Path(str(dialog.result.get("output", {}).get("directory", "clearlens_output")))
            if not self._validate_output_dir(new_output_dir):
                return
            self.settings = dialog.result
            ai = self.settings.setdefault("ai", {})
            self.session_api_keys["openai"] = str(ai.get("openai_api_key", ""))
            self.session_api_keys["deepseek"] = str(ai.get("deepseek_api_key", ""))
            self.output_dir.set(str(self.settings.get("output", {}).get("directory", "clearlens_output")))
            self.output_encoding.set(str(self.settings.get("output", {}).get("encoding", "utf-8")))
            self.editor_font_size.set(int(self.settings.get("editor", {}).get("font_size", 11)))
            self.i18n.set_language(str(self.settings.get("language", "zh_sim")))
            self._save_settings()
            self._rebuild_ui()
            self.status.set(self.i18n.t("settings_saved"))

    def _capture_ui_settings(self) -> None:
        if self.option_vars:
            self.settings["local_cleaning"] = self._current_options().to_dict()
        self.settings.setdefault("output", {})["directory"] = self.output_dir.get()
        self.settings.setdefault("output", {})["encoding"] = self.output_encoding.get() or "utf-8"
        self.settings.setdefault("editor", {})["font_size"] = self.editor_font_size.get()
        if self.rule_vars:
            for rule in self.regex_rules:
                if rule.key in self.rule_vars:
                    rule.enabled = bool(self.rule_vars[rule.key].get())
            self.settings["regex_enabled_keys"] = [rule.key for rule in self.regex_rules if rule.enabled]
        if self.llm_rule_vars:
            for rule in self.llm_rules:
                if rule.key in self.llm_rule_vars:
                    rule.enabled = bool(self.llm_rule_vars[rule.key].get())
            self.settings["llm_rule_enabled_keys"] = [rule.key for rule in self.llm_rules if rule.enabled]
            save_llm_rules(self.llm_rules)

    def _save_settings(self) -> None:
        persisted = copy.deepcopy(self.settings)
        ai = persisted.setdefault("ai", {})
        if bool(ai.get("remember_api_key", False)):
            ai["openai_api_key"] = self.session_api_keys["openai"]
            ai["deepseek_api_key"] = self.session_api_keys["deepseek"]
        else:
            ai["openai_api_key"] = ""
            ai["deepseek_api_key"] = ""
        ai.pop("api_key", None)
        ai.pop("model", None)
        save_settings(persisted)

    def _rebuild_ui(self) -> None:
        selected_path = None
        index = self._selected_index(show_message=False) if hasattr(self, "file_tree") else None
        if index is not None:
            selected_path = self.files[index].path
        for child in self.winfo_children():
            child.destroy()
        self.editor_widgets = []
        self.configure(menu="")
        self.title(self.i18n.t("app_title"))
        self._build_ui()
        self._bind_shortcuts()
        if selected_path is not None:
            for new_index, item in enumerate(self.files):
                if item.path == selected_path:
                    self.file_tree.selection_set(str(new_index))
                    self.file_tree.focus(str(new_index))
                    break
        self.preview_selected()

    def set_language(self, language: str) -> None:
        self._capture_ui_settings()
        self.settings["language"] = language
        self.i18n.set_language(language)
        self._save_settings()
        self._rebuild_ui()

    def show_shortcuts(self) -> None:
        messagebox.showinfo(self.i18n.t("shortcuts"), self.i18n.t("shortcuts_text"), parent=self)

    def show_about(self) -> None:
        AboutDialog(self, self.i18n)

    def on_exit(self) -> None:
        if self.busy and not messagebox.askyesno(self.i18n.t("app_title"), self.i18n.t("busy_exit_confirm"), parent=self):
            return
        if self.busy:
            self.cancel_current_task()
        self._commit_manual_history()
        self._capture_ui_settings()
        self._save_settings()
        self.destroy()


def main() -> None:
    app = ClearLensApp()
    app.mainloop()
