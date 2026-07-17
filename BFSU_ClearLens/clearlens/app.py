from __future__ import annotations

import copy
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
import customtkinter as ctk
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable

from .ai_client import AIClient, AISettings
from .cleaner import clean_text
from .config import load_settings, save_settings
from .document_ops import merge_texts
from .fileio import (
    OUTPUT_ENCODINGS,
    READ_ENCODINGS,
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
from .history import FileEditState, HistoryEntry, OperationHistory, file_identity
from .llm_rule_library import load_llm_rules, save_llm_rules
from .models import AIResult, AISuggestion, CleanOptions, CleanResult, LLMRule, RegexRule, TextFile
from .profile import load_profile, save_profile
from .rule_library import load_regex_rules, save_custom_regex_rules
from .statistics import calculate_statistics
from .ui_about import AboutDialog
from .ui_ai_review import AIReviewDialog
from .ui_common import (
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_LLM,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_SURFACE,
    COLOR_TEXT,
    CTkSpinbox,
    CTkSplitPane,
    DpiAwareMenu,
    DpiAwareTreeview,
    EditorTextbox,
    FONT_FAMILY,
    VariableProgressBar,
    apply_window_icon,
    button_colors,
    make_section,
)
from .ui_dialogs import EncodingSelectDialog, FindReplaceDialog, RegexLibraryDialog
from .ui_llm_rules import LLMRuleLibraryDialog
from .ui_settings import SettingsDialog
from .ui_statistics import StatisticsDialog
from .ui_text import (
    LineDiffRow,
    TextExcerpt,
    TextLineNumbers,
    build_line_diff_rows,
    excerpt_around_line,
    first_line_difference,
)
from .window import ApplicationWindow, DND_FILES
from .workers import clean_text_job


class ClearLensApp(ApplicationWindow):
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
        configured_encoding = str(self.settings.setdefault("output", {}).get("encoding", "utf-8")).strip() or "utf-8"
        self.output_encoding = tk.StringVar(value=configured_encoding)
        self.editor_font_size = tk.IntVar(value=int(self.settings.setdefault("editor", {}).get("font_size", 11)))
        self.stats_summary = tk.StringVar(value="")
        self.status = tk.StringVar(value=self.i18n.t("ready"))
        self.progress_value = tk.DoubleVar(value=0)
        self.progress_summary = tk.StringVar(value=self.i18n.t("progress_overall", current=0, total=0, percent=0))
        self.preview_notice = tk.StringVar(value="")
        self._progress_maximum = 1
        self.worker_queue: queue.Queue[tuple[int, str, Any]] = queue.Queue()
        self.log_rows: list[dict[str, object]] = []
        self._log_sequence = 0
        self._task_log_ids: dict[int, list[str]] = {}
        self._task_failures: dict[int, list[str]] = {}
        self.busy = False
        self._task_counter = 0
        self._active_task_id: int | None = None
        self._cancel_event: threading.Event | None = None
        self._active_executor: ThreadPoolExecutor | ProcessPoolExecutor | None = None
        self._output_lock = threading.Lock()
        self._preview_truncated = False
        self._preview_token: tuple[object, ...] | None = None
        self._preview_snapshot_identity: str | None = None
        self._preview_snapshot_source: str | None = None
        self._selection_preview_after_id: str | None = None
        self._active_task_started_at: float | None = None
        self._active_task_phase_started_at: float | None = None
        self._active_task_phase: str = ""
        self._active_task_phase_payload: dict[str, object] = {}
        self._active_task_status_base: str = ""
        self._task_watchdog_after_id: str | None = None
        self.option_vars: dict[str, tk.BooleanVar] = {}
        self.rule_vars: dict[str, tk.BooleanVar] = {}
        self.llm_rule_vars: dict[str, tk.BooleanVar] = {}
        self.choice_vars: dict[str, tk.Variable] = {}
        self.choice_widgets: dict[str, ctk.CTkComboBox] = {}
        self.task_action_widgets: list[ctk.CTkBaseClass] = []
        self._task_widget_states: list[tuple[tk.Misc, object]] = []
        self._task_menu_states: list[tuple[tk.Menu, int, str]] = []
        self.editor_widgets: list[EditorTextbox] = []
        self.line_number_gutters: dict[EditorTextbox, TextLineNumbers] = {}
        self._diff_rows: dict[str, LineDiffRow] = {}
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
        self._schedule_task_watchdog()

    def _set_icon(self) -> None:
        apply_window_icon(self, default=True)

    def _setup_style(self) -> None:
        self.configure(fg_color=COLOR_BG)
        self.option_add("*Font", (FONT_FAMILY, 10))
        self.option_add("*Menu.Font", (FONT_FAMILY, 13))

    def _build_ui(self) -> None:
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()

    def _build_menu(self) -> None:
        t = self.i18n.t
        menubar = DpiAwareMenu(self)
        self.menubar = menubar

        file_menu = DpiAwareMenu(menubar, tearoff=False)
        file_menu.add_command(label=t("import_files"), accelerator="Ctrl+O", command=self.open_files)
        file_menu.add_command(label=t("import_folder"), accelerator="Ctrl+Shift+O", command=self.open_folder)
        file_menu.add_command(label=t("clear_all_files"), command=self.clear_all_files)
        file_menu.add_command(label=t("new_session"), command=self.new_session)
        file_menu.add_command(label=t("choose_output"), command=self.choose_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label=t("save_current"), accelerator="Ctrl+S", command=self.save_current_result)
        file_menu.add_command(label=t("save_as"), accelerator="Ctrl+Shift+S", command=self.save_current_as)
        file_menu.add_command(label=t("save_all"), accelerator="Ctrl+Alt+S", command=self.save_all_results)
        file_menu.add_command(label=t("export_log"), command=self.export_log)
        file_menu.add_separator()
        file_menu.add_command(label=t("exit"), command=self.on_exit)
        menubar.add_cascade(label=t("file"), menu=file_menu)

        edit_menu = DpiAwareMenu(menubar, tearoff=False)
        edit_menu.add_command(label=t("undo"), accelerator="Ctrl+Z", command=self.undo_operation)
        edit_menu.add_command(label=t("redo"), accelerator="Ctrl+Y", command=self.redo_operation)
        edit_menu.add_separator()
        edit_menu.add_command(label=t("find_replace"), accelerator="Ctrl+F", command=self.open_find_replace)
        edit_menu.add_separator()
        edit_menu.add_command(label=t("reset_current"), command=self.reset_current_file)
        edit_menu.add_command(label=t("reset_selected"), command=self.reset_selected_files)
        edit_menu.add_command(label=t("reset_all"), command=self.reset_all_files)
        menubar.add_cascade(label=t("edit"), menu=edit_menu)

        document_menu = DpiAwareMenu(menubar, tearoff=False)
        document_menu.add_command(label=t("merge_selected"), command=self.merge_selected_files)
        document_menu.add_command(label=t("merge_all"), command=self.merge_all_files)
        menubar.add_cascade(label=t("document"), menu=document_menu)

        clean_menu = DpiAwareMenu(menubar, tearoff=False)
        clean_menu.add_command(label=t("preview"), accelerator="Ctrl+P", command=self.preview_rules)
        clean_menu.add_separator()
        clean_menu.add_command(label=t("rule_current"), accelerator="F5", command=self.run_rule_current)
        clean_menu.add_command(label=t("rule_selected"), command=self.run_rule_selected)
        clean_menu.add_command(label=t("rule_all"), accelerator="Ctrl+F5", command=self.run_rule_all)
        clean_menu.add_separator()
        clean_menu.add_command(label=t("transcode_current"), command=self.transcode_current)
        clean_menu.add_command(label=t("transcode_selected"), command=self.transcode_selected)
        clean_menu.add_command(label=t("transcode_all"), command=self.transcode_all)
        menubar.add_cascade(label=t("cleaning"), menu=clean_menu)

        ai_menu = DpiAwareMenu(menubar, tearoff=False)
        ai_menu.add_command(label=t("ai_direct_current"), accelerator="F6", command=self.run_ai_current)
        ai_menu.add_command(label=t("ai_direct_selected"), command=self.run_ai_selected)
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

        tools_menu = DpiAwareMenu(menubar, tearoff=False)
        tools_menu.add_command(label=t("character_statistics"), command=self.show_statistics)
        tools_menu.add_separator()
        tools_menu.add_command(label=t("regex_library"), command=self.open_regex_library)
        tools_menu.add_command(label=t("reopen_encoding"), command=self.reopen_with_encoding)
        tools_menu.add_command(label=t("open_output"), command=self.open_output_folder)
        tools_menu.add_command(label=t("clear_log"), command=self.clear_log)
        menubar.add_cascade(label=t("tools"), menu=tools_menu)

        settings_menu = DpiAwareMenu(menubar, tearoff=False)
        language_menu = DpiAwareMenu(settings_menu, tearoff=False)
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

        help_menu = DpiAwareMenu(menubar, tearoff=False)
        help_menu.add_command(label=t("shortcuts"), command=self.show_shortcuts)
        help_menu.add_command(label=t("about"), command=self.show_about)
        menubar.add_cascade(label=t("help"), menu=help_menu)
        self.configure(menu=menubar)

    def _build_toolbar(self) -> None:
        t = self.i18n.t
        toolbar = ctk.CTkFrame(self, fg_color="#dfeaec", corner_radius=0, height=80)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 6))
        toolbar.pack_propagate(False)
        self.task_action_widgets = []

        row_top = ctk.CTkFrame(toolbar, fg_color="transparent", height=38)
        row_bottom = ctk.CTkFrame(toolbar, fg_color="transparent", height=38)
        row_top.pack(fill=tk.X, padx=4, pady=(2, 0))
        row_bottom.pack(fill=tk.X, padx=4, pady=(0, 2))
        row_top.pack_propagate(False)
        row_bottom.pack_propagate(False)

        def tool_button(
            parent: tk.Misc,
            label: str,
            command: Callable[[], None],
            kind: str = "normal",
            width: int | None = None,
            task_action: bool = True,
        ) -> ctk.CTkButton:
            visual_width = width or max(58, min(128, 24 + sum(13 if ord(ch) > 255 else 7 for ch in label)))
            button = ctk.CTkButton(
                parent,
                text=label,
                command=command,
                width=visual_width,
                height=30,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                **button_colors(kind),
            )
            if task_action:
                self.task_action_widgets.append(button)
            return button

        def separator(parent: ctk.CTkFrame, side: str) -> None:
            ctk.CTkFrame(parent, width=1, fg_color="#a9c0c4", corner_radius=0).pack(side=side, fill=tk.Y, padx=6, pady=5)

        for label, command in (
            (t("toolbar_import"), self.open_files),
            (t("toolbar_folder"), self.open_folder),
            (t("toolbar_remove"), self.remove_selected_files),
            (t("toolbar_clear_all"), self.clear_all_files),
        ):
            tool_button(row_top, label, command).pack(side=tk.LEFT, padx=2, pady=4)
        separator(row_top, tk.LEFT)
        tool_button(row_top, t("toolbar_reset_current"), self.reset_current_file).pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_top, t("toolbar_reset_selected"), self.reset_selected_files).pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_top, t("toolbar_reset_all"), self.reset_all_files).pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_top, t("toolbar_save_all"), self.save_all_results).pack(side=tk.RIGHT, padx=2, pady=4)
        tool_button(row_top, t("toolbar_save"), self.save_current_result).pack(side=tk.RIGHT, padx=2, pady=4)
        tool_button(row_top, t("toolbar_open_output"), self.open_output_folder).pack(side=tk.RIGHT, padx=2, pady=4)

        tool_button(row_bottom, t("toolbar_preview"), self.preview_rules).pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_bottom, t("toolbar_rule_current"), self.run_rule_current, "accent").pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_bottom, t("toolbar_rule_selected"), self.run_rule_selected, "accent").pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_bottom, t("toolbar_rule_all"), self.run_rule_all, "accent").pack(side=tk.LEFT, padx=2, pady=4)
        separator(row_bottom, tk.LEFT)
        tool_button(row_bottom, t("toolbar_llm_current"), self.run_ai_current, "danger").pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_bottom, t("toolbar_llm_selected"), self.run_ai_selected, "danger").pack(side=tk.LEFT, padx=2, pady=4)
        tool_button(row_bottom, t("toolbar_llm_review"), self.run_ai_review_current, "llm").pack(side=tk.LEFT, padx=2, pady=4)

        tool_button(row_bottom, "A+", lambda: self.change_editor_font_size(1), width=38, task_action=False).pack(side=tk.RIGHT, padx=1, pady=4)
        tool_button(row_bottom, "A−", lambda: self.change_editor_font_size(-1), width=38, task_action=False).pack(side=tk.RIGHT, padx=1, pady=4)
        ctk.CTkLabel(row_bottom, textvariable=self.stats_summary, text_color=COLOR_MUTED).pack(side=tk.RIGHT, padx=6)
        tool_button(row_bottom, t("character_statistics"), self.show_statistics, task_action=False).pack(side=tk.RIGHT, padx=2, pady=4)

    def _build_workspace(self) -> None:
        pane = CTkSplitPane(
            self,
            orientation="horizontal",
            initial_ratio=0.26,
            min_first=280,
            min_second=620,
            separator_width=8,
            first_color=COLOR_PANEL,
            second_color="transparent",
        )
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))
        left, right = pane.first, pane.second
        self.main_pane = pane
        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ctk.CTkFrame) -> None:
        body = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLOR_PANEL,
            corner_radius=0,
            scrollbar_button_color="#88a7ac",
            scrollbar_button_hover_color="#65878d",
        )
        body.pack(fill=tk.BOTH, expand=True, padx=(4, 2), pady=4)
        self._init_option_vars()
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

    def _init_option_vars(self) -> None:
        options = CleanOptions.from_dict(self.settings.get("local_cleaning", {}))
        self.option_vars = {}
        self.choice_widgets = {}
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

    def _build_option_group(self, parent: ctk.CTkFrame, title_key: str, keys: tuple[str, ...]) -> None:
        box = make_section(parent, self.i18n.t(title_key))
        box.pack(fill=tk.X, padx=5, pady=6)
        for key in keys:
            ctk.CTkCheckBox(
                box,
                text=self.i18n.t(f"option_{key}"),
                variable=self.option_vars[key],
                height=24,
                checkbox_width=19,
                checkbox_height=19,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            ).pack(anchor=tk.W, fill=tk.X, padx=10, pady=2)
        self._build_selection_buttons(box, [self.option_vars[key] for key in keys])

    def _build_selection_buttons(self, parent: ctk.CTkFrame, variables: list[tk.BooleanVar]) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, padx=10, pady=(6, 9))
        ctk.CTkButton(
            row,
            text=self.i18n.t("select_all"),
            command=lambda: self._set_boolean_variables(variables, True),
            height=28,
            **button_colors(),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        ctk.CTkButton(
            row,
            text=self.i18n.t("deselect_all"),
            command=lambda: self._set_boolean_variables(variables, False),
            height=28,
            **button_colors(),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

    def _set_boolean_variables(self, variables: list[tk.BooleanVar], value: bool) -> None:
        for variable in variables:
            variable.set(value)
        self._sync_choice_widget_states()

    def _sync_choice_widget_states(self) -> None:
        enabled_keys = {
            "unicode_normalization": "unicode_normalization_enabled",
            "width_conversion": "width_conversion_enabled",
            "chinese_conversion": "chinese_conversion_enabled",
            "punctuation_mode": "punctuation_mode_enabled",
            "paragraph_indent_mode": "paragraph_indent_enabled",
        }
        for key, enabled_key in enabled_keys.items():
            widget = self.choice_widgets.get(key)
            variable = self.option_vars.get(enabled_key)
            if widget is not None and variable is not None:
                widget.configure(state="readonly" if variable.get() else tk.DISABLED)

    def _combo_row(
        self,
        parent: ctk.CTkFrame,
        key: str,
        label: str,
        variable: tk.Variable,
        enabled_variable: tk.BooleanVar,
        values: tuple[str, ...],
        labels: tuple[str, ...],
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, padx=10, pady=3)
        mapping = dict(zip(values, labels))
        reverse = dict(zip(labels, values))
        def update(selected: str) -> None:
            variable.set(reverse.get(selected, values[0]))

        def toggle() -> None:
            combo.configure(state="readonly" if enabled_variable.get() else tk.DISABLED)

        ctk.CTkCheckBox(
            row,
            text=label,
            variable=enabled_variable,
            command=toggle,
            height=24,
            checkbox_width=19,
            checkbox_height=19,
        ).pack(anchor=tk.W, fill=tk.X)
        combo = ctk.CTkComboBox(
            row,
            state="readonly" if enabled_variable.get() else tk.DISABLED,
            values=list(labels),
            command=update,
            height=30,
        )
        combo.set(mapping.get(str(variable.get()), labels[0]))
        combo.pack(fill=tk.X, pady=(2, 0))
        self.choice_widgets[key] = combo

    def _build_paragraph_group(self, parent: ctk.CTkFrame) -> None:
        t = self.i18n.t
        box = make_section(parent, t("paragraph_group"))
        box.pack(fill=tk.X, padx=5, pady=6)
        boolean_keys = ("repair_hyphenated_linebreaks", "paragraph_reflow")
        for key in boolean_keys:
            ctk.CTkCheckBox(
                box,
                text=t(f"option_{key}"),
                variable=self.option_vars[key],
                height=24,
                checkbox_width=19,
                checkbox_height=19,
            ).pack(anchor=tk.W, fill=tk.X, padx=10, pady=2)
        self._combo_row(box, "unicode_normalization", t("unicode_normalization"), self.choice_vars["unicode_normalization"], self.option_vars["unicode_normalization_enabled"], ("none", "NFC", "NFKC", "NFD", "NFKD"), (t("unicode_none"), "NFC", "NFKC", "NFD", "NFKD"))
        self._combo_row(box, "width_conversion", t("width_conversion"), self.choice_vars["width_conversion"], self.option_vars["width_conversion_enabled"], ("none", "full_to_half", "half_to_full"), (t("width_none"), t("full_to_half"), t("half_to_full")))
        self._combo_row(box, "chinese_conversion", t("chinese_conversion"), self.choice_vars["chinese_conversion"], self.option_vars["chinese_conversion_enabled"], ("none", "t2s", "s2t"), (t("chinese_none"), t("t2s"), t("s2t")))
        self._combo_row(box, "punctuation_mode", t("punctuation_mode"), self.choice_vars["punctuation_mode"], self.option_vars["punctuation_mode_enabled"], ("none", "cjk", "ascii"), (t("punctuation_none"), t("punctuation_cjk"), t("punctuation_ascii")))
        self._combo_row(box, "paragraph_indent_mode", t("indent_mode"), self.choice_vars["paragraph_indent_mode"], self.option_vars["paragraph_indent_enabled"], ("keep", "strip", "cjk_2"), (t("indent_keep"), t("indent_strip"), t("indent_cjk_2")))
        tab_row = ctk.CTkFrame(box, fg_color="transparent")
        tab_row.pack(fill=tk.X, padx=10, pady=4)
        ctk.CTkLabel(tab_row, text=t("tab_size"), text_color=COLOR_MUTED).pack(side=tk.LEFT)
        CTkSpinbox(tab_row, from_=1, to=16, width=92, textvariable=self.choice_vars["tab_size"]).pack(side=tk.RIGHT)
        enabled_keys = (
            "unicode_normalization_enabled", "width_conversion_enabled", "chinese_conversion_enabled",
            "punctuation_mode_enabled", "paragraph_indent_enabled",
        )
        self._build_selection_buttons(box, [self.option_vars[key] for key in (*boolean_keys, *enabled_keys)])

    def _build_regex_group(self, parent: ctk.CTkFrame) -> None:
        box = make_section(parent, self.i18n.t("regex_group"))
        box.pack(fill=tk.X, padx=5, pady=6)
        self.rule_vars = {}
        for rule in self.regex_rules:
            variable = tk.BooleanVar(value=rule.enabled)
            self.rule_vars[rule.key] = variable
            ctk.CTkCheckBox(
                box,
                text=rule.display_name(self.i18n.language),
                variable=variable,
                height=24,
                checkbox_width=19,
                checkbox_height=19,
            ).pack(anchor=tk.W, fill=tk.X, padx=10, pady=2)
        self._build_selection_buttons(box, list(self.rule_vars.values()))
        ctk.CTkButton(box, text=self.i18n.t("regex_library"), command=self.open_regex_library, height=30, **button_colors()).pack(fill=tk.X, padx=10, pady=(0, 9))

    def _build_llm_rule_group(self, parent: ctk.CTkFrame) -> None:
        box = make_section(parent, self.i18n.t("llm_rule_group"))
        box.pack(fill=tk.X, padx=5, pady=6)
        self.llm_rule_vars = {}
        if not self.llm_rules:
            ctk.CTkLabel(box, text=self.i18n.t("llm_rule_empty"), text_color=COLOR_MUTED, wraplength=280, justify=tk.LEFT).pack(fill=tk.X, padx=10, pady=4)
        for rule in self.llm_rules:
            variable = tk.BooleanVar(value=rule.enabled)
            self.llm_rule_vars[rule.key] = variable
            ctk.CTkCheckBox(box, text=rule.name, variable=variable, height=24, checkbox_width=19, checkbox_height=19).pack(anchor=tk.W, fill=tk.X, padx=10, pady=2)
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill=tk.X, padx=10, pady=(6, 3))
        ctk.CTkButton(row, text=self.i18n.t("select_all"), command=lambda: self._set_llm_rule_variables(True), height=28, **button_colors()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        ctk.CTkButton(row, text=self.i18n.t("deselect_all"), command=lambda: self._set_llm_rule_variables(False), height=28, **button_colors()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))
        ctk.CTkButton(box, text=self.i18n.t("llm_rule_library"), command=self.open_llm_rule_library, height=30, **button_colors()).pack(fill=tk.X, padx=10, pady=3)
        ctk.CTkLabel(
            box,
            text=self.i18n.t("llm_auto_warning"),
            text_color=COLOR_DANGER,
            wraplength=280,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=10, pady=(6, 3))
        for label_key, command, kind, pady in (
            ("llm_rule_safe_current", self.run_llm_rules_current, "danger", 2),
            ("llm_rule_safe_selected", self.run_llm_rules_selected, "danger", 2),
            ("llm_rule_review_current", self.run_llm_rules_review_current, "llm", (2, 9)),
        ):
            button = ctk.CTkButton(box, text=self.i18n.t(label_key), command=command, height=32, **button_colors(kind))
            button.pack(fill=tk.X, padx=10, pady=pady)
            self.task_action_widgets.append(button)

    def _set_llm_rule_variables(self, value: bool) -> None:
        for variable in self.llm_rule_vars.values():
            variable.set(value)

    def _build_output_group(self, parent: ctk.CTkFrame) -> None:
        t = self.i18n.t
        box = make_section(parent, t("output_group"))
        box.pack(fill=tk.X, padx=5, pady=6)
        ctk.CTkLabel(box, text=t("output_folder"), text_color=COLOR_MUTED).pack(anchor=tk.W, padx=10)
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill=tk.X, padx=10, pady=3)
        ctk.CTkEntry(row, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ctk.CTkButton(row, text=t("browse"), command=self.choose_output_dir, width=68, height=30, **button_colors()).pack(side=tk.RIGHT, padx=(5, 0))
        ctk.CTkLabel(box, text=t("output_encoding"), text_color=COLOR_MUTED).pack(anchor=tk.W, padx=10, pady=(5, 0))
        encoding_combo = ctk.CTkComboBox(box, variable=self.output_encoding, values=list(OUTPUT_ENCODINGS), state="readonly", command=lambda _value: self._capture_output_encoding())
        encoding_combo.pack(fill=tk.X, padx=10, pady=(3, 0))
        for label_key, command in (
            ("transcode_current", self.transcode_current),
            ("transcode_selected", self.transcode_selected),
            ("transcode_all", self.transcode_all),
        ):
            button = ctk.CTkButton(box, text=t(label_key), command=command, height=30, **button_colors())
            button.pack(fill=tk.X, padx=10, pady=(7 if label_key == "transcode_current" else 2, 2))
            self.task_action_widgets.append(button)
        ctk.CTkFrame(box, fg_color="transparent", height=5).pack()

    def _build_right_panel(self, parent: ctk.CTkFrame) -> None:
        t = self.i18n.t
        vertical = CTkSplitPane(
            parent,
            orientation="vertical",
            initial_ratio=0.36,
            min_first=180,
            min_second=300,
            separator_width=8,
        )
        vertical.pack(fill=tk.BOTH, expand=True, padx=(6, 0))
        queue_container, content_container = vertical.first, vertical.second
        self.vertical_pane = vertical

        queue_section = make_section(queue_container, t("file_queue"))
        queue_section.pack(fill=tk.BOTH, expand=True)
        queue_frame = ctk.CTkFrame(queue_section, fg_color="transparent")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=7, pady=(0, 6))
        columns = ("number", "name", "encoding", "confidence", "characters", "status")
        self.file_tree = DpiAwareTreeview(queue_frame, columns=columns, show="headings", selectmode="extended")
        for column, label, width in (
            ("number", t("sequence_number"), 58), ("name", t("file_name"), 400), ("encoding", t("encoding"), 105),
            ("confidence", t("confidence"), 80), ("characters", t("characters"), 90),
            ("status", t("status"), 120),
        ):
            self.file_tree.heading(column, text=label)
            self.file_tree.logical_column(column, width=width, minwidth=48, anchor=tk.CENTER if column == "number" else tk.W)
        ybar = ctk.CTkScrollbar(queue_frame, orientation="vertical", command=self.file_tree.yview)
        xbar = ctk.CTkScrollbar(queue_frame, orientation="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.file_tree.grid(row=0, column=0, sticky=tk.NSEW)
        ybar.grid(row=0, column=1, sticky=tk.NS)
        xbar.grid(row=1, column=0, sticky=tk.EW)
        queue_frame.rowconfigure(0, weight=1)
        queue_frame.columnconfigure(0, weight=1)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.file_tree.bind("<Double-1>", lambda _event: self.preview_rules())
        self.file_tree.bind("<Button-3>", self._show_file_context_menu)
        self.file_tree.bind("<Delete>", self._delete_selected_from_queue)
        self._enable_drop(self.file_tree)

        drop_text = t("drop_hint") if DND_FILES is not None else t("drop_unavailable")
        drop_label = ctk.CTkLabel(queue_section, text=drop_text, anchor=tk.CENTER, text_color=COLOR_MUTED, height=24)
        drop_label.pack(fill=tk.X, padx=8, pady=(0, 5))
        self._enable_drop(drop_label)

        self.notebook = ctk.CTkTabview(content_container, fg_color="#edf4f5", segmented_button_selected_color=COLOR_ACCENT)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.preview_tab_name = t("comparison")
        self.diff_tab_name = t("diff")
        self.log_tab_name = t("logs")
        preview_tab = self.notebook.add(self.preview_tab_name)
        self.preview_notice_label = ctk.CTkLabel(
            preview_tab,
            textvariable=self.preview_notice,
            anchor=tk.W,
            text_color=COLOR_MUTED,
            height=20,
        )
        preview_pane = CTkSplitPane(preview_tab, orientation="horizontal", initial_ratio=0.50, min_first=260, min_second=260, separator_width=7)
        preview_pane.pack(fill=tk.BOTH, expand=True, padx=1, pady=(0, 2))
        self.preview_pane = preview_pane
        before_frame = make_section(preview_pane.first, t("before"))
        after_frame = make_section(preview_pane.second, t("after"))
        before_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 3))
        after_frame.pack(fill=tk.BOTH, expand=True, padx=(3, 0))
        self.before_text = self._text_with_scrollbars(before_frame, editable=False)
        self.after_text = self._text_with_scrollbars(after_frame, editable=True)
        self.after_text.bind("<<Modified>>", self._on_after_modified, add="+")
        self.after_text.bind("<Control-z>", lambda _event: self._history_shortcut(self.undo_operation))
        self.after_text.bind("<Control-Z>", lambda _event: self._history_shortcut(self.undo_operation))
        self.after_text.bind("<Control-y>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Y>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Shift-z>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Control-Shift-Z>", lambda _event: self._history_shortcut(self.redo_operation))
        self.after_text.bind("<Button-3>", self._show_editor_context_menu)

        diff_tab = self.notebook.add(self.diff_tab_name)
        diff_columns = ("change", "original_line", "current_line", "original_text", "current_text")
        self.diff_tree = DpiAwareTreeview(diff_tab, columns=diff_columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("change", t("diff_change"), 90),
            ("original_line", t("original_line"), 90),
            ("current_line", t("current_line"), 90),
            ("original_text", t("diff_original_text"), 420),
            ("current_text", t("diff_current_text"), 420),
        ):
            self.diff_tree.heading(column, text=label)
            self.diff_tree.logical_column(column, width=width, minwidth=65, anchor=tk.W)
        diff_y = ctk.CTkScrollbar(diff_tab, orientation="vertical", command=self.diff_tree.yview)
        diff_x = ctk.CTkScrollbar(diff_tab, orientation="horizontal", command=self.diff_tree.xview)
        self.diff_tree.configure(yscrollcommand=diff_y.set, xscrollcommand=diff_x.set)
        self.diff_tree.grid(row=0, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        diff_y.grid(row=0, column=1, sticky=tk.NS)
        diff_x.grid(row=1, column=0, sticky=tk.EW, padx=(5, 0))
        diff_tab.rowconfigure(0, weight=1)
        diff_tab.columnconfigure(0, weight=1)
        self.diff_tree.bind("<Double-1>", self._on_diff_double_click)

        log_tab = self.notebook.add(self.log_tab_name)
        log_tools = ctk.CTkFrame(log_tab, fg_color="transparent")
        log_tools.pack(fill=tk.X, padx=5, pady=(5, 3))
        ctk.CTkButton(log_tools, text=t("undo_selected_log"), command=self.undo_selected_log, height=28, **button_colors()).pack(side=tk.LEFT)
        ctk.CTkButton(log_tools, text=t("export_log"), command=self.export_log, height=28, **button_colors()).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(log_tools, text=t("clear_log"), command=self.clear_log, height=28, **button_colors()).pack(side=tk.LEFT)
        log_frame = ctk.CTkFrame(log_tab, fg_color="transparent")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 3))
        log_columns = ("time", "operation", "source", "input_chars", "result_chars", "log_status", "details")
        self.log_tree = DpiAwareTreeview(log_frame, columns=log_columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("time", t("log_time"), 150), ("operation", t("operation"), 150),
            ("source", t("file_name"), 220), ("input_chars", t("log_input_chars"), 90),
            ("result_chars", t("log_result_chars"), 90), ("log_status", t("log_status"), 90),
            ("details", t("log_details"), 420),
        ):
            self.log_tree.heading(column, text=label)
            self.log_tree.logical_column(column, width=width, minwidth=65, anchor=tk.W)
        log_y = ctk.CTkScrollbar(log_frame, orientation="vertical", command=self.log_tree.yview)
        log_x = ctk.CTkScrollbar(log_frame, orientation="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=log_y.set, xscrollcommand=log_x.set)
        self.log_tree.grid(row=0, column=0, sticky=tk.NSEW)
        log_y.grid(row=0, column=1, sticky=tk.NS)
        log_x.grid(row=1, column=0, sticky=tk.EW)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_tree.tag_configure("undone", foreground="#808080", background="#f1f1f1")
        self.log_tree.tag_configure("warning", foreground="#8b1e2d")
        self.log_tree.bind("<Button-3>", self._show_log_context_menu)
        self._refresh_file_list()
        self._refresh_log_tree()
        self.after_idle(self._set_initial_queue_sash)

    def _text_with_scrollbars(self, parent: ctk.CTkFrame, editable: bool, wrap: str = tk.WORD) -> EditorTextbox:
        host = ctk.CTkFrame(parent, fg_color="transparent")
        host.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        text = EditorTextbox(
            host,
            wrap=wrap,
            undo=editable,
            padx=7,
            pady=7,
            font=ctk.CTkFont(family=FONT_FAMILY, size=self.editor_font_size.get()),
            activate_scrollbars=False,
            corner_radius=5,
            border_width=1,
        )
        self.editor_widgets.append(text)
        line_numbers = TextLineNumbers(host, text)
        self.line_number_gutters[text] = line_numbers

        def scroll_text(*args: object) -> None:
            text.yview(*args)
            line_numbers.schedule_redraw()

        ybar = ctk.CTkScrollbar(host, orientation="vertical", command=scroll_text)
        xbar = ctk.CTkScrollbar(host, orientation="horizontal", command=text.xview)
        def yscroll(first: str, last: str) -> None:
            ybar.set(first, last)
            line_numbers.schedule_redraw()

        text.configure(yscrollcommand=yscroll, xscrollcommand=xbar.set)
        line_numbers.grid(row=0, column=0, sticky=tk.NS)
        text.grid(row=0, column=1, sticky=tk.NSEW)
        ybar.grid(row=0, column=2, sticky=tk.NS)
        xbar.grid(row=1, column=1, sticky=tk.EW)
        host.rowconfigure(0, weight=1)
        host.columnconfigure(1, weight=1)
        for sequence in ("<Configure>", "<KeyRelease>", "<ButtonRelease-1>", "<MouseWheel>", "<Button-4>", "<Button-5>"):
            text.bind(sequence, line_numbers.schedule_redraw, add="+")
        if not editable:
            text.configure(state=tk.DISABLED)
        line_numbers.schedule_redraw()
        return text

    def change_editor_font_size(self, delta: int) -> None:
        size = min(32, max(8, self.editor_font_size.get() + delta))
        if size == self.editor_font_size.get():
            return
        self.editor_font_size.set(size)
        self.settings.setdefault("editor", {})["font_size"] = size
        for widget in list(self.editor_widgets):
            try:
                widget.configure(font=ctk.CTkFont(family=FONT_FAMILY, size=size))
                gutter = self.line_number_gutters.get(widget)
                if gutter is not None:
                    gutter.schedule_redraw()
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
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER, corner_radius=0).pack(fill=tk.X)
        bar = ctk.CTkFrame(self, fg_color="#dfeaec", corner_radius=0, height=38)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, textvariable=self.status, anchor=tk.W, text_color=COLOR_TEXT).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        ctk.CTkLabel(bar, textvariable=self.progress_summary, anchor=tk.E, text_color=COLOR_MUTED, width=120).pack(side=tk.LEFT, padx=(5, 0))
        self.progress = VariableProgressBar(bar, variable=self.progress_value, maximum=1, width=220, height=10)
        self.progress.pack(side=tk.LEFT, padx=8)
        self.cancel_button = ctk.CTkButton(
            bar,
            text=self.i18n.t("cancel_task"),
            command=self.cancel_current_task,
            state=tk.DISABLED,
            width=88,
            height=28,
            **button_colors("danger"),
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(4, 10), pady=5)

    @staticmethod
    def _history_shortcut(command: Callable[[], None]) -> str:
        command()
        return "break"

    def _bind_shortcuts(self) -> None:
        bindings = {
            "<Control-o>": self.open_files, "<Control-O>": self.open_files,
            "<Control-Shift-o>": self.open_folder, "<Control-Shift-O>": self.open_folder,
            "<Control-p>": self.preview_rules,
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
            allow_busy = sequence == "<Escape>"
            self.bind_all(sequence, lambda _event, command=callback, allowed=allow_busy: self._run_shortcut(command, allowed))

    def _run_shortcut(self, command: Callable[[], None], allow_busy: bool = False) -> str:
        if self.busy and not allow_busy:
            return "break"
        command()
        return "break"

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
            self._post(task_id, "status", self.i18n.t("scanning_files"))
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

        self._start_worker(worker, maximum=1, task_label=self.i18n.t("import_task"))

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
                values=(index + 1, item.relative_path, item.encoding, f"{item.confidence:.0%}", len(item.active_text), self._status_label(item.status, item.dirty)),
            )
        for index, item in enumerate(self.files):
            if str(item.path) in selected_paths:
                self.file_tree.selection_add(str(index))
        self._update_stats_summary()

    def _refresh_file_row(self, index: int) -> None:
        """Update one queue row without rebuilding the tree or moving the caret."""
        if not hasattr(self, "file_tree") or not 0 <= index < len(self.files):
            return
        iid = str(index)
        if not self.file_tree.exists(iid):
            return
        item = self.files[index]
        values = (
            index + 1,
            item.relative_path,
            item.encoding,
            f"{item.confidence:.0%}",
            len(item.active_text),
            self._status_label(item.status, item.dirty),
        )
        self.file_tree.item(iid, values=values)

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
            item = self.files[index]
            selected_identity = file_identity(item.path)
            if self._manual_history_path and self._manual_history_path != selected_identity:
                self._commit_manual_history()
            # Refreshing the queue after an asynchronous preview can emit a
            # synthetic TreeviewSelect event.  Preserve the explicit preview
            # snapshot for the same unchanged file instead of overwriting it
            # with the current working text a fraction of a second later.
            if self._preview_snapshot_matches(item):
                return
            if self._preview_snapshot_identity is not None:
                self._clear_preview_snapshot()
            self._schedule_selected_preview()

    def _schedule_selected_preview(self, delay_ms: int = 120) -> None:
        self._cancel_scheduled_preview()
        index = self._selected_index(show_message=False)
        scheduled_identity = file_identity(self.files[index].path) if index is not None else None

        def render() -> None:
            self._selection_preview_after_id = None
            current = self._selected_index(show_message=False)
            if current is None:
                return
            item = self.files[current]
            if scheduled_identity is not None and file_identity(item.path) != scheduled_identity:
                return
            if self._preview_snapshot_matches(item):
                return
            self.preview_selected()

        self._selection_preview_after_id = self.after(delay_ms, render)

    def _cancel_scheduled_preview(self) -> None:
        if self._selection_preview_after_id is None:
            return
        try:
            self.after_cancel(self._selection_preview_after_id)
        except tk.TclError:
            pass
        self._selection_preview_after_id = None

    def remove_selected_files(self) -> None:
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        self._cancel_scheduled_preview()
        indices = self._selected_indices()
        if not indices:
            return
        for index in reversed(indices):
            del self.files[index]
        self.history.clear()
        self._refresh_file_list()
        self._clear_preview()
        self.status.set(self.i18n.t("removed_files", count=len(indices)))

    def _delete_selected_from_queue(self, event=None) -> str:
        if self.busy:
            return "break"
        if event is None or event.widget is self.file_tree:
            self.remove_selected_files()
        return "break"

    def clear_all_files(self) -> None:
        self._clear_workspace("clear_all_files_confirm", "clear_all_files_done")

    def new_session(self) -> None:
        self._clear_workspace("new_session_confirm", "new_session_done")

    def _clear_workspace(self, confirm_key: str, done_key: str) -> None:
        if not self._ensure_idle():
            return
        if (self.files or self.log_rows) and not messagebox.askyesno(
            self.i18n.t("app_title"), self.i18n.t(confirm_key), parent=self, icon="warning"
        ):
            return
        self._commit_manual_history()
        self._cancel_scheduled_preview()
        self.files.clear()
        self.history.clear()
        self._pending_history.clear()
        self.log_rows.clear()
        self._log_sequence = 0
        self._task_log_ids.clear()
        self._task_failures.clear()
        self._refresh_file_list()
        self._refresh_log_tree()
        self._clear_preview()
        self._progress_maximum = 1
        self.progress_value.set(0)
        self.progress_summary.set(self.i18n.t("progress_overall", current=0, total=0, percent=0))
        if hasattr(self, "progress"):
            self.progress.configure(maximum=1)
        self.status.set(self.i18n.t(done_key))

    def clear_files(self) -> None:
        """Compatibility alias for queue/context-menu integrations."""
        self.clear_all_files()

    def _show_file_context_menu(self, event) -> None:
        self.file_tree.focus_set()
        iid = self.file_tree.identify_row(event.y)
        if iid and iid not in self.file_tree.selection():
            self.file_tree.selection_set(iid)
            self.file_tree.focus(iid)
        menu = DpiAwareMenu(self, tearoff=False)
        menu.add_command(label=self.i18n.t("import_files"), command=self.open_files)
        menu.add_command(label=self.i18n.t("import_folder"), command=self.open_folder)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("remove"), command=self.remove_selected_files)
        menu.add_command(label=self.i18n.t("clear_all_files"), command=self.clear_all_files)
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
        if not self._ensure_idle():
            return
        self.update_idletasks()
        if hasattr(self, "after_text") and self.after_text.edit_modified():
            self._on_after_modified()
        self._commit_manual_history()
        index = self._selected_index(show_message=False)
        if index is None:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        item = self.files[index]
        source = item.active_text
        limit = self._preview_limit_for_item(item)
        options, rules = self._current_options(), self._current_rules()
        llm_rules = self._current_llm_rules()
        llm_instructions = [rule.instruction for rule in llm_rules]
        ratio, minimum = self._thresholds()
        ai_settings: AISettings | None = None
        llm_chunks = 0
        if llm_instructions:
            if not self._preflight_ai_request([index], custom_rules=llm_instructions):
                return
            if not self._confirm_ai([index], custom_rules=llm_instructions):
                return
            ai_settings = self._ai_settings()
            llm_client = AIClient(ai_settings)
            llm_chunks = sum(
                llm_client.estimate_chunk_count(source, custom_rules=[instruction])
                for instruction in llm_instructions
            )

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            if cancel.is_set():
                return {"kind": "preview", "cancelled": True}
            preview_input, rendered, result = self._compute_local_preview(
                source,
                options,
                rules,
                ratio,
                minimum,
            )
            local_rendered = rendered
            self._post(task_id, "progress", 1)
            enabled_regex_count = sum(1 for rule in rules if rule.enabled and rule.pattern)
            regex_match_count = 0
            for applied in result.applied_regex_rules:
                try:
                    regex_match_count += int(applied.rsplit(":", 1)[1])
                except (IndexError, ValueError):
                    continue
            llm_applied = 0
            llm_rejected = 0
            llm_warnings: list[str] = []
            llm_completed = True
            if llm_instructions and ai_settings is not None and not cancel.is_set():
                client = AIClient(ai_settings)

                def llm_progress(current: int, total: int) -> None:
                    self._post(task_id, "status", self.i18n.t(
                        "previewing_llm_rules",
                        current=current,
                        total=total,
                    ))
                    self._post(task_id, "progress", 1 + current)

                def llm_activity(payload: dict[str, object]) -> None:
                    self._post(task_id, "ai_activity", payload)

                llm_result = client.clean_with_rules(
                    rendered,
                    llm_instructions,
                    llm_progress,
                    cancel,
                    llm_activity,
                )
                llm_completed = llm_result.completed
                llm_applied = len(llm_result.applied)
                llm_rejected = len(llm_result.rejected)
                llm_warnings = llm_result.warnings
                if llm_result.completed:
                    rendered = llm_result.text
                for warning in llm_warnings:
                    self._post(task_id, "log", self._format_ai_warning(warning))

            # The preview baseline must always be the current working text.
            # Using an intermediate locally-cleaned state here hid selected
            # local options whenever any regex rule was also enabled.
            local_changed = local_rendered != source
            difference = first_line_difference(preview_input, rendered)
            if difference is None:
                before_excerpt = self._leading_excerpt(preview_input, limit)
                after_excerpt = self._leading_excerpt(rendered, limit)
            else:
                old_line, new_line, old_column, new_column = difference
                before_excerpt = self._focused_excerpt(preview_input, old_line, old_column, limit)
                after_excerpt = self._focused_excerpt(rendered, new_line, new_column, limit)
            truncated = before_excerpt.truncated or after_excerpt.truncated
            if not cancel.is_set():
                self._post(task_id, "preview_result", {
                    "index": index,
                    "source": source,
                    "before": before_excerpt.text,
                    "after": after_excerpt.text,
                    "before_start_line": before_excerpt.first_line,
                    "after_start_line": after_excerpt.first_line,
                    "truncated": truncated,
                })
            return {
                "kind": "preview",
                "cancelled": cancel.is_set(),
                "changed": rendered != source,
                "visible_change": difference is not None,
                "input_chars": len(source),
                "result_chars": len(rendered),
                "operations": len(result.changes),
                "truncated": truncated,
                "enabled_regex_count": enabled_regex_count,
                "regex_match_count": regex_match_count,
                "local_changed": local_changed,
                "llm_rule_count": len(llm_instructions),
                "llm_applied": llm_applied,
                "llm_rejected": llm_rejected,
                "llm_completed": llm_completed,
                "llm_warnings": llm_warnings,
            }

        self._start_worker(worker, maximum=max(1, 1 + llm_chunks), task_label=self.i18n.t("previewing"))

    @staticmethod
    def _compute_local_preview(
        source: str,
        options: CleanOptions,
        rules: list[RegexRule],
        ratio: float,
        minimum: int,
    ) -> tuple[str, str, CleanResult]:
        rendered, result = clean_text(source, options, rules, ratio, minimum)
        # Never replace the left-side baseline with an intermediate cleaning
        # stage. Users must always compare against the exact working text on
        # which the selected rules will operate.
        return source, rendered, result

    @staticmethod
    def _has_expensive_long_lines(text: str) -> bool:
        sample = text[:100000]
        if not sample:
            return False
        average = len(sample) / max(1, sample.count("\n") + 1)
        longest = max((len(line) for line in sample.splitlines()), default=len(sample))
        return average > 1800 or longest > 6000

    def _preview_limit_for_item(self, item: TextFile) -> int:
        processing = self.settings.get("processing", {})
        configured = max(10000, int(processing.get("preview_max_chars", 200000)))
        compact_limit = max(10000, int(processing.get("compact_markup_preview_chars", 40000)))
        markup = item.path.suffix.lower() in {".html", ".htm", ".xml"}
        expensive = self._has_expensive_long_lines(item.original_text) or self._has_expensive_long_lines(item.active_text)
        if expensive:
            return min(configured, compact_limit, 12000)
        return min(configured, compact_limit) if markup else configured

    @staticmethod
    def _leading_excerpt(text: str, limit: int) -> TextExcerpt:
        return TextExcerpt(text=text[:limit], first_line=1, truncated=len(text) > limit)

    @staticmethod
    def _focused_excerpt(text: str, line: int, column: int, limit: int) -> TextExcerpt:
        if len(text) <= limit:
            return TextExcerpt(text=text, first_line=1, truncated=False)
        return excerpt_around_line(text, line, limit, column, context_lines=10)

    @classmethod
    def _preview_wrap_mode(cls, before: str, after: str) -> str:
        return tk.NONE if cls._has_expensive_long_lines(before) or cls._has_expensive_long_lines(after) else tk.WORD

    def _set_preview_notice(self, message: str) -> None:
        self.preview_notice.set(message)
        label = getattr(self, "preview_notice_label", None)
        if label is None or not label.winfo_exists():
            return
        manager = label.winfo_manager()
        if message:
            if manager != "pack":
                label.pack(before=self.preview_pane, fill=tk.X, padx=5, pady=(1, 0))
        elif manager == "pack":
            label.pack_forget()

    def _clear_preview_snapshot(self) -> None:
        self._preview_snapshot_identity = None
        self._preview_snapshot_source = None

    def _preview_snapshot_matches(self, item: TextFile) -> bool:
        return (
            self._preview_snapshot_identity == file_identity(item.path)
            and self._preview_snapshot_source == item.active_text
        )

    def preview_selected(self, apply_rules: bool = False) -> None:
        index = self._selected_index(show_message=False)
        if index is None or not hasattr(self, "after_text"):
            return
        item = self.files[index]
        if not apply_rules and self._preview_snapshot_matches(item):
            return
        if self._preview_snapshot_identity is not None:
            self._clear_preview_snapshot()
        limit = self._preview_limit_for_item(item)
        if apply_rules:
            source = item.active_text
            ratio, minimum = self._thresholds()
            rendered, _result = clean_text(source, self._current_options(), self._current_rules(), ratio, minimum)
            difference = first_line_difference(source, rendered)
            if difference is None:
                before_excerpt = self._leading_excerpt(source, limit)
                after_excerpt = self._leading_excerpt(rendered, limit)
            else:
                old_line, new_line, old_column, new_column = difference
                before_excerpt = self._focused_excerpt(source, old_line, old_column, limit)
                after_excerpt = self._focused_excerpt(rendered, new_line, new_column, limit)
            if item.status == "pending":
                item.status = "previewed"
        else:
            token = (file_identity(item.path), id(item.original_text), id(item.active_text), limit)
            if token == self._preview_token:
                return
            before_excerpt = self._leading_excerpt(item.original_text, limit)
            after_excerpt = self._leading_excerpt(item.active_text, limit)
        truncated = before_excerpt.truncated or after_excerpt.truncated
        self._set_preview(
            before_excerpt.text,
            after_excerpt.text,
            truncated=truncated,
            before_start_line=before_excerpt.first_line,
            after_start_line=after_excerpt.first_line,
        )
        self._preview_token = None if apply_rules else token
        self._update_stats_summary(item.active_text)
        if self.file_tree.exists(str(index)):
            self.file_tree.set(str(index), "status", self._status_label(item.status, item.dirty))

    def _set_preview(
        self,
        before: str,
        after: str,
        truncated: bool = False,
        before_start_line: int = 1,
        after_start_line: int = 1,
    ) -> None:
        self._setting_preview = True
        self._preview_token = None
        self._preview_truncated = truncated
        self._set_preview_notice(
            self.i18n.t(
                "preview_excerpt_notice",
                before_line=before_start_line,
                after_line=after_start_line,
            )
            if truncated
            else ""
        )
        wrap_mode = self._preview_wrap_mode(before, after)
        self.before_text.set_wrap_mode(wrap_mode)
        self.after_text.set_wrap_mode(wrap_mode)
        self.before_text.set_line_number_start(before_start_line)
        self.after_text.set_line_number_start(after_start_line)
        self._set_text_widget(self.before_text, before, readonly=True)
        self.after_text.configure(state=tk.NORMAL)
        self.after_text.delete("1.0", tk.END)
        self.after_text.insert("1.0", after)
        self.after_text.edit_modified(False)
        self.after_text.reset_undo()
        if truncated or self.busy:
            self.after_text.configure(state=tk.DISABLED)
        self._populate_diff_table(before, after, before_start_line, after_start_line)
        self._setting_preview = False
        for widget in (self.before_text, self.after_text):
            gutter = self.line_number_gutters.get(widget)
            if gutter is not None:
                gutter.schedule_redraw()
        self._update_stats_summary()

    @staticmethod
    def _set_text_widget(widget: EditorTextbox, value: str, readonly: bool) -> None:
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
        self._preview_token = None
        self._clear_preview_snapshot()
        self._preview_truncated = False
        self._set_preview_notice("")
        self._set_text_widget(self.before_text, "", readonly=True)
        self.before_text.set_line_number_start(1)
        self.after_text.configure(state=tk.NORMAL)
        self.after_text.delete("1.0", tk.END)
        self.after_text.edit_modified(False)
        self.after_text.reset_undo()
        self.after_text.set_line_number_start(1)
        if self.busy:
            self.after_text.configure(state=tk.DISABLED)
        if hasattr(self, "diff_tree"):
            self.diff_tree.delete(*self.diff_tree.get_children())
            self._diff_rows.clear()
        self._setting_preview = False
        self._update_stats_summary("")

    def _set_initial_queue_sash(self) -> None:
        if not hasattr(self, "vertical_pane") or not self.vertical_pane.winfo_exists():
            return
        self.vertical_pane.set_ratio(0.36)

    def _populate_diff_table(
        self,
        before: str,
        after: str,
        before_start_line: int = 1,
        after_start_line: int = 1,
    ) -> None:
        if not hasattr(self, "diff_tree"):
            return
        self.diff_tree.delete(*self.diff_tree.get_children())
        self._diff_rows.clear()
        if before == after:
            return
        labels = {
            "replace": self.i18n.t("diff_replace"),
            "delete": self.i18n.t("diff_delete"),
            "insert": self.i18n.t("diff_insert"),
        }
        for index, row in enumerate(build_line_diff_rows(
            before,
            after,
            original_start_line=before_start_line,
            current_start_line=after_start_line,
        )):
            iid = str(index)
            self._diff_rows[iid] = row
            self.diff_tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    labels.get(row.change, row.change),
                    row.original_line or "—",
                    row.current_line or "—",
                    row.original_text,
                    row.current_text,
                ),
            )

    def _on_diff_double_click(self, event) -> str:
        iid = self.diff_tree.identify_row(event.y)
        row = self._diff_rows.get(iid)
        if row is None or row.original_line is None:
            return "break"
        self.diff_tree.selection_set(iid)
        self.notebook.set(self.preview_tab_name)
        self._highlight_text_lines(self.before_text, [row.original_line], "diff_target")
        return "break"

    def _highlight_text_lines(self, widget: EditorTextbox, lines: list[int], tag: str = "navigation_target") -> None:
        if not lines:
            return
        previous_state = str(widget.cget("state"))
        if previous_state == tk.DISABLED:
            widget.configure(state=tk.NORMAL)
        widget.tag_delete(tag)
        widget.tag_configure(tag, background="#ffe49a", foreground="#3b2b00")
        valid = sorted({displayed for line in lines if (displayed := widget.displayed_line_number(int(line))) is not None})
        if not valid:
            if previous_state == tk.DISABLED:
                widget.configure(state=tk.DISABLED)
            return
        for displayed in valid:
            widget.tag_add(tag, f"{displayed}.0", f"{displayed}.end+1c")
        widget.mark_set(tk.INSERT, f"{valid[0]}.0")
        widget.see(f"{valid[0]}.0")
        if previous_state == tk.DISABLED:
            widget.configure(state=tk.DISABLED)
        gutter = self.line_number_gutters.get(widget)
        if gutter is not None:
            gutter.schedule_redraw()

    def _navigate_review_lines(self, lines: list[int]) -> None:
        self.notebook.set(self.preview_tab_name)
        index = self._selected_index(show_message=False)
        if index is not None and lines:
            item = self.files[index]
            limit = self._preview_limit_for_item(item)
            before_excerpt = self._focused_excerpt(item.original_text, max(0, lines[0] - 1), 0, limit)
            after_excerpt = self._focused_excerpt(item.active_text, max(0, lines[0] - 1), 0, limit)
            self._set_preview(
                before_excerpt.text,
                after_excerpt.text,
                truncated=before_excerpt.truncated or after_excerpt.truncated,
                before_start_line=before_excerpt.first_line,
                after_start_line=after_excerpt.first_line,
            )
        self._highlight_text_lines(self.after_text, lines, "review_target")
        self.status.set(self.i18n.t("review_lines_highlighted", lines=", ".join(map(str, lines))))

    def _show_editor_context_menu(self, event) -> str:
        self.after_text.focus_set()
        self.after_text.mark_set(tk.INSERT, f"@{event.x},{event.y}")
        menu = DpiAwareMenu(self, tearoff=False)
        menu.add_command(label=self.i18n.t("cut"), command=lambda: self.after_text.event_generate("<<Cut>>"))
        menu.add_command(label=self.i18n.t("copy"), command=lambda: self.after_text.event_generate("<<Copy>>"))
        menu.add_command(label=self.i18n.t("paste"), command=lambda: self.after_text.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label=self.i18n.t("select_all"), command=lambda: self.after_text.tag_add(tk.SEL, "1.0", "end-1c"))
        menu.add_command(label=self.i18n.t("find_replace"), command=self.open_find_replace)
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _on_after_modified(self, _event=None) -> None:
        if self._setting_preview or not self.after_text.edit_modified():
            return
        index = self._selected_index(show_message=False)
        if index is not None:
            item = self.files[index]
            self._clear_preview_snapshot()
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
            self._refresh_file_row(index)
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
        entry = self.history.record(self.i18n.t("history_manual_edit"), before, after)
        if entry is not None:
            item = self.files[indices[0]]
            state = before.get(identity)
            self._add_log_row({
                "operation": "manual_edit",
                "source": str(item.path),
                "input_chars": len(state.text if state is not None else item.original_text),
                "result_chars": len(item.active_text),
                "changes": self.i18n.t("history_manual_edit"),
                "log_status": "active",
            }, history_entry=entry, undoable=True)

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

    def undo_operation(self, expected_entry_id: int | None = None) -> bool:
        if not self._ensure_idle():
            return False
        self._commit_manual_history()
        latest = self.history.peek_undo()
        if expected_entry_id is not None and (latest is None or latest.entry_id != expected_entry_id):
            return False
        result = self.history.undo()
        if result is None:
            self.status.set(self.i18n.t("history_nothing_to_undo"))
            return False
        entry, states = result
        restored = self._apply_history_states(states)
        self._mark_history_logs(entry.entry_id, "undone")
        self._add_log_row({
            "operation": "history_undo",
            "details": self.i18n.t("history_undone", label=entry.label, count=restored),
            "log_status": "completed",
        })
        self.status.set(self.i18n.t("history_undone", label=entry.label, count=restored))
        return True

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
        self._mark_history_logs(entry.entry_id, "redone")
        self._add_log_row({
            "operation": "history_redo",
            "details": self.i18n.t("history_redone", label=entry.label, count=restored),
            "log_status": "completed",
        })
        self.status.set(self.i18n.t("history_redone", label=entry.label, count=restored))

    def undo_selected_log(self) -> None:
        if not hasattr(self, "log_tree"):
            return
        if not self._ensure_idle():
            return
        self._commit_manual_history()
        selection = self.log_tree.selection()
        if not selection:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("log_select_first"), parent=self)
            return
        log_id = selection[0]
        row = next((item for item in self.log_rows if item.get("_id") == log_id), None)
        if row is None or not bool(row.get("_undoable")) or row.get("log_status") != "active":
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("log_not_undoable"), parent=self)
            return
        try:
            history_id = int(row.get("_history_id", 0))
        except (TypeError, ValueError):
            history_id = 0
        latest = self.history.peek_undo()
        if history_id <= 0 or latest is None or latest.entry_id != history_id:
            messagebox.showwarning(self.i18n.t("app_title"), self.i18n.t("log_undo_not_latest"), parent=self)
            return
        self.undo_operation(expected_entry_id=history_id)

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
        entry = self.history.record(label, before, after)
        if entry is not None:
            for index in indices:
                item = self.files[index]
                state = before.get(file_identity(item.path))
                self._add_log_row({
                    "operation": "reset",
                    "source": str(item.path),
                    "input_chars": len(state.text if state is not None else item.active_text),
                    "result_chars": len(item.active_text),
                    "changes": label,
                    "log_status": "active",
                }, history_entry=entry, undoable=True)
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

    def run_rule_selected(self) -> None:
        if not self._ensure_idle():
            return
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        self._run_rule_indices(indices)

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
            max_chars_per_request=int(ai.get("max_chars_per_request", 24000)),
            max_output_tokens=int(ai.get("max_output_tokens", 16000)),
            chunk_overlap_lines=int(ai.get("chunk_overlap_lines", 2)),
            request_timeout_seconds=int(ai.get("request_timeout_seconds", 180)),
            retry_attempts=int(ai.get("retry_attempts", 2)),
            adaptive_chunking=bool(ai.get("adaptive_chunking", True)),
            confirm_before_send=bool(ai.get("confirm_before_send", True)),
            remember_api_key=bool(ai.get("remember_api_key", False)),
        )

    def _confirm_ai(
        self,
        indices: list[int],
        request_multiplier: int = 1,
        custom_rules: list[str] | None = None,
        review: bool = False,
    ) -> bool:
        settings = self._ai_settings()
        if not settings.enabled or not settings.resolved_api_key():
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("ai_disabled_message"), parent=self)
            return False
        if not settings.confirm_before_send:
            return True
        count = len(indices)
        largest = max((len(self.files[index].active_text) for index in indices), default=0)
        client = AIClient(settings)
        multiplier = max(1, int(request_multiplier))
        if custom_rules:
            chunk_counts = [
                sum(
                    client.estimate_chunk_count(
                        self.files[index].active_text,
                        review=review,
                        custom_rules=[rule],
                    )
                    for rule in custom_rules
                )
                for index in indices
            ]
        else:
            chunk_counts = [
                client.estimate_chunk_count(self.files[index].active_text, review=review) * multiplier
                for index in indices
            ]
        chunks = sum(chunk_counts)
        largest_chunks = max(chunk_counts, default=0)
        key = "ai_batch_confirm" if count > 1 else "ai_send_confirm"
        provider = "DeepSeek" if settings.provider == "deepseek" else "OpenAI"
        return messagebox.askyesno(
            self.i18n.t("app_title"),
            self.i18n.t(
                key,
                count=count,
                provider=provider,
                largest=largest,
                limit=settings.max_chars_per_request,
                chunks=chunks,
                largest_chunks=largest_chunks,
            ),
            parent=self,
        )

    def _ensure_ai_ready(self) -> bool:
        settings = self._ai_settings()
        if settings.enabled and settings.resolved_api_key():
            return True
        messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("ai_disabled_message"), parent=self)
        return False

    def _preflight_ai_request(self, indices: list[int], custom_rules: list[str] | None = None) -> bool:
        if not self._ensure_ai_ready():
            return False
        client = AIClient(self._ai_settings())
        failures: list[str] = []
        task_warnings = AIClient.assess_task(custom_rules)
        failures.extend(self._format_ai_warning(warning) for warning in task_warnings)
        if failures:
            messagebox.showwarning(
                self.i18n.t("ai_preflight_title"),
                self.i18n.t("ai_preflight_failed", details="\n".join(f"• {failure}" for failure in failures)),
                parent=self,
            )
            return False
        for index in indices:
            item = self.files[index]
            warnings = client.preflight(item.active_text)
            failures.extend(f"{item.name}: {self._format_ai_warning(warning)}" for warning in warnings)
        if not failures:
            return True
        visible = failures[:12]
        if len(failures) > len(visible):
            visible.append(self.i18n.t("ai_preflight_more", count=len(failures) - len(visible)))
        messagebox.showwarning(
            self.i18n.t("ai_preflight_title"),
            self.i18n.t("ai_preflight_failed", details="\n".join(f"• {failure}" for failure in visible)),
            parent=self,
        )
        return False

    def _confirm_llm_auto_risk(self, count: int) -> bool:
        return messagebox.askyesno(
            self.i18n.t("llm_auto_warning_title"),
            self.i18n.t("llm_auto_risk_confirm", count=count),
            parent=self,
            icon="warning",
        )

    def _format_ai_warning(self, warning: str) -> str:
        rule_context = ""
        if ":rule=" in warning:
            warning, rule_number = warning.rsplit(":rule=", 1)
            rule_context = self.i18n.t("ai_rule_failure_context", rule=rule_number)
        chunk_context = ""
        base_warning = warning
        if ":chunk=" in warning:
            base_warning, chunk = warning.rsplit(":chunk=", 1)
            chunk_context = self.i18n.t("ai_chunk_failure_context", chunk=chunk)
        if base_warning.startswith("ai_text_too_long:"):
            parts = base_warning.split(":")
            if len(parts) >= 3:
                return self.i18n.t("ai_text_too_long_message", actual=parts[1], limit=parts[2]) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_limit_too_small:"):
            parts = base_warning.split(":")
            return self.i18n.t("ai_chunk_limit_too_small_message", actual=parts[1], minimum=parts[2]) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_edits_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_edits_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_locations_repaired:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_locations_repaired_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_fragments_not_found:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_fragments_not_found_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_fragments_ambiguous:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_fragments_ambiguous_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_overlap_edits_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_overlap_edits_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_chunk_duplicate_edits_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_chunk_duplicate_edits_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_edits_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_edits_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_provider_items_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_provider_items_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_suggestions_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_suggestions_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_rule_scope_rejected:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_rule_scope_rejected_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_adaptive_retry:"):
            parts = base_warning.split(":")
            level = parts[1] if len(parts) > 1 else "1"
            budget = parts[2] if len(parts) > 2 else ""
            return self.i18n.t("ai_adaptive_retry_message", level=level, budget=budget) + chunk_context + rule_context
        if base_warning.startswith("ai_request_timeout:"):
            return self.i18n.t("ai_request_timeout_message", error=base_warning.split(":", 1)[1]) + chunk_context + rule_context
        if base_warning.startswith("ai_request_failed:"):
            return self.i18n.t("ai_request_failed_message", error=base_warning.split(":", 1)[1]) + chunk_context + rule_context
        if base_warning.startswith("ai_response_invalid_json:"):
            return self.i18n.t("ai_response_invalid_message", error=base_warning.split(":", 1)[1]) + chunk_context + rule_context
        if base_warning.startswith("ai_response_no_valid_items:"):
            count = base_warning.rsplit(":", 1)[-1]
            return self.i18n.t("ai_response_no_valid_items_message", count=count) + chunk_context + rule_context
        if base_warning.startswith("ai_task_unsuitable:"):
            reason = base_warning.split(":", 1)[1]
            return self.i18n.t("ai_task_unsuitable_message", reason=self.i18n.t(f"ai_task_reason_{reason}")) + chunk_context + rule_context
        if base_warning == "ai_response_empty_or_refused":
            return self.i18n.t("ai_response_empty_message") + chunk_context + rule_context
        if base_warning == "ai_response_truncated":
            return self.i18n.t("ai_response_truncated_message") + chunk_context + rule_context
        if base_warning == "empty_text":
            return self.i18n.t("ai_empty_text_message") + chunk_context + rule_context
        if base_warning == "api_key_missing":
            return self.i18n.t("ai_disabled_message") + chunk_context + rule_context
        return base_warning + chunk_context + rule_context

    def run_ai_current(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is not None:
            self._run_ai_indices([index])

    def run_ai_selected(self) -> None:
        if not self._ensure_idle():
            return
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_selection"), parent=self)
            return
        self._run_ai_indices(indices)

    def run_ai_all(self) -> None:
        if not self._ensure_idle():
            return
        if not self.files:
            messagebox.showinfo(self.i18n.t("app_title"), self.i18n.t("no_files"), parent=self)
            return
        self._run_ai_indices(list(range(len(self.files))))

    def _run_ai_indices(self, indices: list[int]) -> None:
        if not self._ensure_idle():
            return
        if not self._preflight_ai_request(indices):
            return
        if not self._confirm_llm_auto_risk(len(indices)):
            return
        if not self._confirm_ai(indices):
            return
        settings = self._ai_settings()
        jobs = [(index, self.files[index].active_text) for index in indices]
        total_chunks = sum(AIClient(settings).estimate_chunk_count(text) for _index, text in jobs)

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            client = AIClient(settings)
            processed = 0
            completed_chunks = 0
            for position, (index, source_text) in enumerate(jobs, 1):
                if cancel.is_set():
                    break
                item = self.files[index]
                self._post(task_id, "status", self.i18n.t("ai_processing_single", current=position, total=len(indices), name=item.name))
                file_chunks = client.estimate_chunk_count(source_text)
                try:
                    base = completed_chunks
                    def chunk_progress(current: int, total: int) -> None:
                        self._post(task_id, "status", self.i18n.t(
                            "ai_processing_chunk", file_current=position, file_total=len(indices),
                            name=item.name, chunk_current=current, chunk_total=total,
                        ))
                        self._post(task_id, "progress", base + current)
                    def ai_activity(payload: dict[str, object]) -> None:
                        self._post(task_id, "ai_activity", payload)

                    result = client.direct_clean(source_text, chunk_progress, cancel, ai_activity)
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
                    completed_chunks += file_chunks
                    self._post(task_id, "progress", completed_chunks)
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=max(1, total_chunks),
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
        instructions = [rule.instruction for rule in rules]
        if not self._preflight_ai_request(indices, custom_rules=instructions):
            return
        if not self._confirm_llm_auto_risk(len(indices)):
            return
        if not self._confirm_ai(indices, custom_rules=instructions):
            return
        settings = self._ai_settings()
        jobs = [(index, self.files[index].active_text) for index in indices]
        counter = AIClient(settings)
        total_chunks = sum(
            sum(counter.estimate_chunk_count(text, custom_rules=[instruction]) for instruction in instructions)
            for _index, text in jobs
        )

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            client = AIClient(settings)
            processed = 0
            completed_chunks = 0
            for position, (index, source_text) in enumerate(jobs, 1):
                if cancel.is_set():
                    break
                item = self.files[index]
                self._post(task_id, "status", self.i18n.t("ai_processing_single", current=position, total=len(indices), name=item.name))
                file_chunks = sum(
                    client.estimate_chunk_count(source_text, custom_rules=[instruction])
                    for instruction in instructions
                )
                try:
                    base = completed_chunks
                    def chunk_progress(current: int, total: int) -> None:
                        self._post(task_id, "status", self.i18n.t(
                            "ai_processing_chunk", file_current=position, file_total=len(indices),
                            name=item.name, chunk_current=current, chunk_total=total,
                        ))
                        self._post(task_id, "progress", base + current)
                    def ai_activity(payload: dict[str, object]) -> None:
                        self._post(task_id, "ai_activity", payload)

                    result = client.clean_with_rules(
                        source_text,
                        instructions,
                        chunk_progress,
                        cancel,
                        ai_activity,
                    )
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
                    completed_chunks += file_chunks
                    self._post(task_id, "progress", completed_chunks)
            return {"kind": "processing", "processed": processed, "cancelled": cancel.is_set()}

        self._start_worker(
            worker,
            maximum=max(1, total_chunks),
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
        instructions = [rule.instruction for rule in rules]
        if not self._preflight_ai_request([index], custom_rules=instructions):
            return
        if not self._confirm_ai([index], custom_rules=instructions, review=True):
            return
        item = self.files[index]
        settings = self._ai_settings()
        source = item.active_text
        counter = AIClient(settings)
        total_chunks = sum(
            counter.estimate_chunk_count(source, review=True, custom_rules=[instruction])
            for instruction in instructions
        )

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            client = AIClient(settings)
            def chunk_progress(current: int, total: int) -> None:
                self._post(task_id, "status", self.i18n.t(
                    "ai_processing_chunk", file_current=1, file_total=1, name=item.name,
                    chunk_current=current, chunk_total=total,
                ))
                self._post(task_id, "progress", current)
            def ai_activity(payload: dict[str, object]) -> None:
                self._post(task_id, "ai_activity", payload)

            suggestions, warnings = client.review_with_rules(
                source,
                instructions,
                chunk_progress,
                cancel,
                ai_activity,
            )
            if not cancel.is_set():
                self._post(
                    task_id,
                    "review_ready",
                    (index, source, suggestions, warnings, self.i18n.t("operation_llm_rule_review")),
                )
                self._post(task_id, "progress", total_chunks)
            return {"kind": "review", "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=max(1, total_chunks))

    def run_ai_review_current(self) -> None:
        if not self._ensure_idle():
            return
        index = self._selected_index()
        if index is None:
            return
        if not self._preflight_ai_request([index]):
            return
        if not self._confirm_ai([index], review=True):
            return
        item = self.files[index]
        settings = self._ai_settings()
        source_text = item.active_text
        total_chunks = AIClient(settings).estimate_chunk_count(source_text, review=True)

        def worker(task_id: int, cancel: threading.Event) -> dict[str, Any]:
            if cancel.is_set():
                return {"kind": "review", "cancelled": True}
            client = AIClient(settings)
            def chunk_progress(current: int, total: int) -> None:
                self._post(task_id, "status", self.i18n.t(
                    "ai_processing_chunk", file_current=1, file_total=1, name=item.name,
                    chunk_current=current, chunk_total=total,
                ))
                self._post(task_id, "progress", current)
            def ai_activity(payload: dict[str, object]) -> None:
                self._post(task_id, "ai_activity", payload)

            suggestions, warnings = client.review(
                source_text,
                chunk_progress,
                cancel,
                ai_activity,
            )
            if not cancel.is_set():
                self._post(
                    task_id,
                    "review_ready",
                    (index, source_text, suggestions, warnings, self.i18n.t("operation_ai_review")),
                )
                self._post(task_id, "progress", total_chunks)
            return {"kind": "review", "cancelled": cancel.is_set()}

        self._start_worker(worker, maximum=max(1, total_chunks))

    def _open_review_dialog(self, payload: tuple[int, str, list[AISuggestion], list[str], str]) -> None:
        index, source, suggestions, warnings, history_label = payload
        if index >= len(self.files):
            return
        item = self.files[index]
        if item.active_text != source:
            message = self.i18n.t("ai_review_source_changed")
            self._append_log(message, level="warning")
            messagebox.showwarning(self.i18n.t("app_title"), message, parent=self)
            return
        if self.file_tree.exists(str(index)):
            self.file_tree.selection_set(str(index))
            self.file_tree.focus(str(index))
            self.file_tree.see(str(index))
            self.preview_selected()
        for warning in warnings:
            self._append_log(self._format_ai_warning(warning), level="warning")
        if not suggestions:
            if warnings:
                details = "\n".join(f"• {self._format_ai_warning(warning)}" for warning in warnings)
                messagebox.showwarning(
                    self.i18n.t("app_title"),
                    self.i18n.t("ai_review_unavailable", details=details),
                    parent=self,
                )
            else:
                messagebox.showinfo(
                    self.i18n.t("app_title"),
                    self.i18n.t("ai_review_no_changes_confirmed"),
                    parent=self,
                )
            return
        review_before = OperationHistory.capture(self.files, [index])

        def update(text: str) -> None:
            item = self.files[index]
            item.set_working_text(text, "ai_reviewed")
            self._refresh_file_list()
            self.preview_selected()

        def finish(text: str, applied_count: int) -> None:
            if not applied_count:
                return
            item = self.files[index]
            review_after = OperationHistory.capture(self.files, [index])
            history_entry = self.history.record(history_label, review_before, review_after)
            self._record_processing(
                "ai_review",
                item,
                len(source),
                [f"human_applied_ai_suggestions:{applied_count}"],
                [],
                history_entry=history_entry,
            )
            self.status.set(self.i18n.t("processing_complete_unsaved", count=1))

        AIReviewDialog(self, self.i18n, source, suggestions, update, finish, self._navigate_review_lines)

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
            entry = self.history.record(self.i18n.t("history_manual_edit"), before, after)
            if entry is not None:
                state = before.get(file_identity(item.path))
                self._add_log_row({
                    "operation": "manual_edit",
                    "source": str(item.path),
                    "input_chars": len(state.text if state is not None else item.original_text),
                    "result_chars": len(item.active_text),
                    "changes": self.i18n.t("history_manual_edit"),
                    "log_status": "active",
                }, history_entry=entry, undoable=True)
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
        task_label: str | None = None,
    ) -> bool:
        if self.busy:
            self._ensure_idle()
            return False
        self._commit_manual_history()
        self._task_counter += 1
        task_id = self._task_counter
        cancel = threading.Event()
        self._active_task_id = task_id
        self._task_failures[task_id] = []
        self._cancel_event = cancel
        self._active_executor = None
        self.busy = True
        now = time.monotonic()
        self._active_task_started_at = now
        self._active_task_phase_started_at = now
        self._active_task_phase = "starting"
        self._active_task_phase_payload = {}
        if history_label and history_indices:
            self._pending_history[task_id] = (
                history_label,
                OperationHistory.capture(self.files, history_indices),
            )
        self._set_overall_progress(0, max(1, maximum))
        self.cancel_button.configure(state=tk.NORMAL)
        self._set_task_ui_busy(True)
        self._active_task_status_base = task_label or history_label or self.i18n.t("task_starting")
        self.status.set(self._active_task_status_base)

        def runner() -> None:
            summary: dict[str, Any]
            try:
                summary = worker(task_id, cancel)
            except Exception as exc:
                summary = {"kind": "error", "error": str(exc), "cancelled": cancel.is_set()}
                self._post(task_id, "log", str(exc))
            self._post(task_id, "done", summary)

        threading.Thread(target=runner, daemon=True, name=f"clearlens-task-{task_id}").start()
        return True

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        total = max(0, int(seconds))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"

    def _schedule_task_watchdog(self) -> None:
        if self._task_watchdog_after_id is not None:
            return
        self._task_watchdog_after_id = self.after(1000, self._task_watchdog_tick)

    def _task_watchdog_tick(self) -> None:
        self._task_watchdog_after_id = None
        if self.busy and self._active_task_started_at is not None:
            now = time.monotonic()
            total_elapsed = self._format_elapsed(now - self._active_task_started_at)
            phase_elapsed = self._format_elapsed(now - (self._active_task_phase_started_at or self._active_task_started_at))
            if self._active_task_phase == "waiting_llm":
                payload = self._active_task_phase_payload
                self.status.set(self.i18n.t(
                    "ai_waiting_response",
                    current=int(payload.get("current", 1)),
                    total=int(payload.get("total", 1)),
                    attempt=int(payload.get("attempt", 1)),
                    elapsed=phase_elapsed,
                    timeout=int(payload.get("timeout", 180)),
                    retries=int(payload.get("retries", 0)),
                ))
            elif self._active_task_phase == "adaptive_retry":
                payload = self._active_task_phase_payload
                self.status.set(self.i18n.t(
                    "ai_adaptive_retry_status",
                    level=int(payload.get("level", 1)),
                    budget=int(payload.get("budget", 0)),
                    elapsed=total_elapsed,
                ))
            elif now - self._active_task_started_at >= 15:
                self.status.set(self.i18n.t(
                    "task_still_running",
                    task=self._active_task_status_base or self.i18n.t("task_starting"),
                    elapsed=total_elapsed,
                ))
        self._schedule_task_watchdog()

    def _reset_task_runtime(self) -> None:
        self._active_task_started_at = None
        self._active_task_phase_started_at = None
        self._active_task_phase = ""
        self._active_task_phase_payload = {}
        self._active_task_status_base = ""

    def _set_overall_progress(self, current: float, maximum: int | None = None) -> None:
        if maximum is not None:
            self._progress_maximum = max(1, int(maximum))
            if hasattr(self, "progress"):
                self.progress.configure(maximum=self._progress_maximum)
        bounded = min(float(self._progress_maximum), max(0.0, float(current)))
        self.progress_value.set(bounded)
        total = self._progress_maximum
        percent = int(round((bounded / total) * 100)) if total else 0
        self.progress_summary.set(
            self.i18n.t("progress_overall", current=int(bounded), total=total, percent=percent)
        )

    def _set_task_ui_busy(self, busy: bool) -> None:
        stateful_types = (
            ctk.CTkButton,
            ctk.CTkCheckBox,
            ctk.CTkEntry,
            ctk.CTkComboBox,
            ctk.CTkSegmentedButton,
            EditorTextbox,
            DpiAwareTreeview,
        )
        if busy:
            self._task_widget_states.clear()

            def freeze(widget: tk.Misc) -> None:
                if widget is self.cancel_button:
                    return
                if isinstance(widget, DpiAwareTreeview):
                    try:
                        previous = tuple(widget.state())
                        widget.state(("disabled",))
                        self._task_widget_states.append((widget, previous))
                    except tk.TclError:
                        pass
                elif isinstance(widget, stateful_types):
                    try:
                        previous = str(widget.cget("state"))
                        widget.configure(state=tk.DISABLED)
                        self._task_widget_states.append((widget, previous))
                    except (AttributeError, tk.TclError, ValueError):
                        pass
                for child in widget.winfo_children():
                    freeze(child)

            freeze(self)
            self._task_menu_states.clear()
            if hasattr(self, "menubar"):
                end = self.menubar.index(tk.END)
                for index in range((end if end is not None else -1) + 1):
                    try:
                        previous = str(self.menubar.entrycget(index, "state"))
                        self.menubar.entryconfigure(index, state=tk.DISABLED)
                        self._task_menu_states.append((self.menubar, index, previous))
                    except tk.TclError:
                        continue
            self.cancel_button.configure(state=tk.NORMAL)
            return

        for widget, previous in reversed(self._task_widget_states):
            try:
                if not widget.winfo_exists():
                    continue
                if isinstance(widget, DpiAwareTreeview):
                    widget.state(("!disabled",))
                    if isinstance(previous, tuple) and previous:
                        widget.state(previous)
                else:
                    widget.configure(state=previous)
            except (AttributeError, tk.TclError, ValueError):
                continue
        self._task_widget_states.clear()
        for menu, index, previous in self._task_menu_states:
            try:
                menu.entryconfigure(index, state=previous)
            except tk.TclError:
                pass
        self._task_menu_states.clear()
        if hasattr(self, "after_text") and self.after_text.winfo_exists():
            self.after_text.configure(state=tk.DISABLED if self._preview_truncated else tk.NORMAL)

    def _commit_pending_history(self, task_id: int) -> HistoryEntry | None:
        pending = self._pending_history.pop(task_id, None)
        if pending is None:
            self._task_log_ids.pop(task_id, None)
            return None
        label, before = pending
        identities = set(before)
        indices = [index for index, item in enumerate(self.files) if file_identity(item.path) in identities]
        after = OperationHistory.capture(self.files, indices)
        entry = self.history.record(label, before, after)
        self._attach_task_logs(task_id, entry)
        return entry

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
        self._task_failures.pop(task_id, None)
        self._active_task_id = None
        self._cancel_event = None
        self._active_executor = None
        self.busy = False
        self._reset_task_runtime()
        self.cancel_button.configure(state=tk.DISABLED)
        self._set_task_ui_busy(False)
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
                    self._active_task_status_base = str(payload)
                    self._active_task_phase = "working"
                    self._active_task_phase_started_at = time.monotonic()
                    self._active_task_phase_payload = {}
                    self.status.set(self._active_task_status_base)
                elif kind == "ai_activity":
                    activity = dict(payload) if isinstance(payload, dict) else {}
                    state = str(activity.get("state", ""))
                    self._active_task_phase_started_at = time.monotonic()
                    self._active_task_phase_payload = activity
                    if state == "waiting":
                        self._active_task_phase = "waiting_llm"
                    elif state == "adaptive_retry":
                        self._active_task_phase = "adaptive_retry"
                    else:
                        self._active_task_phase = "working"
                        if state == "received":
                            self._active_task_status_base = self.i18n.t(
                                "ai_response_received",
                                current=int(activity.get("current", 1)),
                                total=int(activity.get("total", 1)),
                            )
                            self.status.set(self._active_task_status_base)
                elif kind == "maximum":
                    self._set_overall_progress(self.progress_value.get(), max(1, int(payload)))
                elif kind == "progress":
                    self._set_overall_progress(float(payload))
                elif kind == "log":
                    self._append_log(str(payload))
                elif kind == "import_item":
                    self.files.append(payload)
                elif kind == "preview_result":
                    index = int(payload["index"])
                    source = str(payload["source"])
                    if index < len(self.files) and self.files[index].active_text == source:
                        item = self.files[index]
                        if item.status == "pending":
                            item.status = "previewed"
                        self._cancel_scheduled_preview()
                        self._set_preview(
                            str(payload["before"]),
                            str(payload["after"]),
                            truncated=bool(payload["truncated"]),
                            before_start_line=int(payload["before_start_line"]),
                            after_start_line=int(payload["after_start_line"]),
                        )
                        self._preview_snapshot_identity = file_identity(item.path)
                        self._preview_snapshot_source = source
                        self.notebook.set(self.preview_tab_name)
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
                        rendered_parts = [self._format_ai_warning(part.strip()) for part in str(error).split(";") if part.strip()]
                        rendered_error = "; ".join(rendered_parts) or str(error)
                        self._task_failures.setdefault(task_id, []).append(f"{item.name}: {rendered_error}")
                        self._append_log(self.i18n.t("failed", name=item.name, error=rendered_error), level="warning")
                elif kind == "review_ready":
                    self._open_review_dialog(payload)
                elif kind == "done":
                    self._commit_pending_history(task_id)
                    failures = self._task_failures.pop(task_id, [])
                    self.busy = False
                    self._reset_task_runtime()
                    self._active_task_id = None
                    self._cancel_event = None
                    self._active_executor = None
                    self.cancel_button.configure(state=tk.DISABLED)
                    if not isinstance(payload, dict) or not bool(payload.get("cancelled", False)):
                        self._set_overall_progress(self._progress_maximum)
                    self._set_task_ui_busy(False)
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
                        processed = int(payload.get("processed", 0))
                        if failures and processed == 0:
                            details = "\n".join(f"• {failure}" for failure in failures)
                            message = self.i18n.t("processing_no_results", details=details)
                            self.status.set(message)
                            if not bool(payload.get("cancelled", False)):
                                messagebox.showwarning(self.i18n.t("app_title"), message, parent=self)
                        elif failures:
                            message = self.i18n.t("processing_partial_complete", processed=processed, failed=len(failures))
                            self.status.set(message)
                        else:
                            message = self.i18n.t("processing_complete_unsaved", count=processed)
                            self.status.set(message)
                    elif kind_name == "preview":
                        if not bool(payload.get("cancelled", False)):
                            llm_rule_count = int(payload.get("llm_rule_count", 0))
                            if llm_rule_count and not bool(payload.get("llm_completed", True)):
                                details = "\n".join(
                                    f"• {self._format_ai_warning(str(warning))}"
                                    for warning in payload.get("llm_warnings", [])
                                )
                                message = self.i18n.t("preview_llm_failed", details=details)
                                self.status.set(message)
                                messagebox.showwarning(self.i18n.t("app_title"), message, parent=self)
                            elif llm_rule_count:
                                self.status.set(self.i18n.t(
                                    "preview_llm_complete",
                                    rules=llm_rule_count,
                                    applied=int(payload.get("llm_applied", 0)),
                                    rejected=int(payload.get("llm_rejected", 0)),
                                    input_chars=int(payload.get("input_chars", 0)),
                                    result_chars=int(payload.get("result_chars", 0)),
                                ))
                            else:
                                self._set_local_preview_status(payload)
                    elif kind_name == "error":
                        error = str(payload.get("error", ""))
                        rendered_error = self.i18n.t("output_matches_source") if "output_path_matches_source" in error else error
                        self.status.set(self.i18n.t("task_failed", error=rendered_error))
                        messagebox.showerror(self.i18n.t("app_title"), rendered_error, parent=self)
                    elif kind_name not in {"merge", "save_as", "review"}:
                        self.status.set(self.i18n.t("finished", path=self.output_dir.get()))
                    if kind_name != "preview":
                        self.preview_selected()
        except queue.Empty:
            pass
        self.after(100, self._poll_worker_queue)

    def _set_local_preview_status(self, payload: dict[str, Any]) -> None:
        regex_enabled = int(payload.get("enabled_regex_count", 0))
        regex_matches = int(payload.get("regex_match_count", 0))
        if regex_enabled and regex_matches:
            self.status.set(self.i18n.t(
                "preview_regex_matches",
                rules=regex_enabled,
                matches=regex_matches,
                input_chars=int(payload.get("input_chars", 0)),
                result_chars=int(payload.get("result_chars", 0)),
            ))
        elif regex_enabled:
            key = "preview_regex_no_match_local" if bool(payload.get("local_changed", False)) else "preview_regex_no_match"
            self.status.set(self.i18n.t(key, rules=regex_enabled))
        elif bool(payload.get("changed", False)):
            key = "preview_complete_changed" if bool(payload.get("visible_change", False)) else "preview_complete_invisible"
            self.status.set(self.i18n.t(
                key,
                input_chars=int(payload.get("input_chars", 0)),
                result_chars=int(payload.get("result_chars", 0)),
                operations=int(payload.get("operations", 0)),
            ))
        else:
            self.status.set(self.i18n.t("preview_no_effect"))

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
            "log_status": "saved",
        }
        self._add_log_row(row)

    def _record_processing(
        self,
        operation: str,
        item: TextFile,
        input_chars: int,
        changes: list[str],
        warnings: list[str],
        history_entry: HistoryEntry | None = None,
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
            "log_status": "active",
        }
        self._add_log_row(row, history_entry=history_entry, undoable=True)

    def _add_log_row(
        self,
        row: dict[str, object],
        history_entry: HistoryEntry | None = None,
        undoable: bool = False,
    ) -> str:
        self._log_sequence += 1
        log_id = f"log-{self._log_sequence}"
        row.setdefault("time", datetime.now().isoformat(timespec="seconds"))
        row.setdefault("operation", "message")
        row.setdefault("source", "")
        row.setdefault("input_chars", "")
        row.setdefault("result_chars", "")
        row.setdefault("changes", "")
        row.setdefault("warnings", "")
        row.setdefault("log_status", "active" if undoable else "completed")
        row["_id"] = log_id
        row["_history_id"] = history_entry.entry_id if history_entry is not None else ""
        row["_undoable"] = bool(undoable and (history_entry is not None or self._active_task_id is not None))
        self.log_rows.append(row)
        if undoable and history_entry is None and self._active_task_id is not None:
            self._task_log_ids.setdefault(self._active_task_id, []).append(log_id)
        self._insert_log_tree_row(row)
        return log_id

    def _append_log(self, message: str, level: str = "info") -> None:
        self._add_log_row({
            "operation": "message",
            "details": message,
            "warnings": message if level == "warning" else "",
            "log_status": "warning" if level == "warning" else "completed",
        })

    def _attach_task_logs(self, task_id: int, entry: HistoryEntry | None) -> None:
        ids = set(self._task_log_ids.pop(task_id, []))
        if not ids:
            return
        for row in self.log_rows:
            if row.get("_id") not in ids:
                continue
            row["_history_id"] = entry.entry_id if entry is not None else ""
            row["_undoable"] = entry is not None
            if entry is None:
                row["log_status"] = "completed"
        self._refresh_log_tree()

    def _mark_history_logs(self, entry_id: int, status: str) -> None:
        for row in self.log_rows:
            if row.get("_history_id") == entry_id:
                row["log_status"] = status
                row["_undoable"] = False
        self._refresh_log_tree()

    def _log_details(self, row: dict[str, object]) -> str:
        values = [str(row.get(key, "")).strip() for key in ("details", "changes", "warnings", "output")]
        return " | ".join(value for value in values if value)

    def _refresh_log_tree(self) -> None:
        if not hasattr(self, "log_tree"):
            return
        selected = self.log_tree.selection()
        self.log_tree.delete(*self.log_tree.get_children())
        for row in self.log_rows:
            self._insert_log_tree_row(row, scroll=False)
        if selected and selected[0] in self.log_tree.get_children():
            self.log_tree.selection_set(selected[0])
        elif self.log_tree.get_children():
            self.log_tree.see(self.log_tree.get_children()[-1])

    def _insert_log_tree_row(self, row: dict[str, object], scroll: bool = True) -> None:
        if not hasattr(self, "log_tree"):
            return
        log_id = str(row.get("_id", ""))
        if not log_id:
            return
        if self.log_tree.exists(log_id):
            self.log_tree.delete(log_id)
        operation = str(row.get("operation", "message"))
        status = str(row.get("log_status", "completed"))
        source = Path(str(row.get("source", ""))).name if row.get("source") else ""
        tags = ("undone",) if status in {"undone", "redone"} else (("warning",) if status == "warning" else ())
        self.log_tree.insert(
            "",
            tk.END,
            iid=log_id,
            values=(
                row.get("time", ""), self.i18n.t(f"operation_{operation}"), source,
                row.get("input_chars", row.get("original_chars", "")), row.get("result_chars", ""),
                self.i18n.t(f"log_status_{status}"), self._log_details(row),
            ),
            tags=tags,
        )
        if scroll:
            self.log_tree.see(log_id)

    def _show_log_context_menu(self, event) -> str:
        iid = self.log_tree.identify_row(event.y)
        if iid:
            self.log_tree.selection_set(iid)
        menu = DpiAwareMenu(self, tearoff=False)
        menu.add_command(label=self.i18n.t("undo_selected_log"), command=self.undo_selected_log)
        menu.add_command(label=self.i18n.t("export_log"), command=self.export_log)
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def clear_log(self) -> None:
        self.log_rows.clear()
        self._log_sequence = 0
        self._task_log_ids.clear()
        self._refresh_log_tree()

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
        export_rows = [
            {key: value for key, value in row.items() if not key.startswith("_")}
            for row in self.log_rows
        ]
        if target.suffix.lower() == ".json":
            export_log_json(export_rows, target)
        else:
            export_log_csv(export_rows, target)
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
        dialog = EncodingSelectDialog(self, self.i18n, READ_ENCODINGS, item.encoding)
        self.wait_window(dialog)
        encoding = dialog.result
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

        def highlight_matches(spans: list[tuple[int, int]]) -> None:
            tag = "find_matches"
            self.after_text.tag_delete(tag)
            self.after_text.tag_configure(tag, background="#fff0a8", foreground="#332800")
            self.after_text.tag_remove(tk.SEL, "1.0", tk.END)
            for start, end in spans:
                if end <= start:
                    continue
                self.after_text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")
            if spans:
                start, end = spans[0]
                self.after_text.mark_set(tk.INSERT, f"1.0+{start}c")
                if end > start:
                    self.after_text.tag_add(tk.SEL, f"1.0+{start}c", f"1.0+{end}c")
                self.after_text.see(f"1.0+{start}c")
                gutter = self.line_number_gutters.get(self.after_text)
                if gutter is not None:
                    gutter.schedule_redraw()

        FindReplaceDialog(self, self.i18n, get_text, set_text, highlight_matches)

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
        self._commit_manual_history()
        self._cancel_scheduled_preview()
        # The token refers to widgets that are about to be destroyed. Keeping
        # it would make preview_selected() treat the new, empty editors as an
        # already rendered view when a rule library is saved.
        self._preview_token = None
        self._clear_preview_snapshot()
        self._preview_truncated = False
        selected_path = None
        index = self._selected_index(show_message=False) if hasattr(self, "file_tree") else None
        if index is not None:
            selected_path = self.files[index].path
        for child in self.winfo_children():
            child.destroy()
        self.editor_widgets = []
        self.line_number_gutters = {}
        self._diff_rows = {}
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
        unsaved_count = sum(1 for item in self.files if item.dirty)
        if unsaved_count and not messagebox.askyesno(
            self.i18n.t("app_title"),
            self.i18n.t("unsaved_exit_confirm", count=unsaved_count),
            parent=self,
            icon="warning",
        ):
            return
        self._capture_ui_settings()
        self._save_settings()
        self.destroy()


def main() -> None:
    app = ClearLensApp()
    app.mainloop()
