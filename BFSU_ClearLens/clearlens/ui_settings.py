from __future__ import annotations

import copy
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .config import load_default_settings
from .fileio import OUTPUT_ENCODINGS
from .i18n import I18n, LANGUAGE_LABELS
from .ui_common import IconToplevel


class SettingsDialog(IconToplevel):
    def __init__(self, master: tk.Misc, settings: dict[str, Any], i18n: I18n, initial_tab: str | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.data = copy.deepcopy(settings)
        self.result: dict[str, Any] | None = None
        self.vars: dict[str, tk.Variable] = {}
        self.initial_tab = initial_tab
        self.title(i18n.t("settings_title"))
        self.geometry("850x680")
        self.minsize(720, 500)
        self.transient(master)
        self.grab_set()
        self._build()

    def _var(self, key: str, variable: tk.Variable) -> tk.Variable:
        self.vars[key] = variable
        return variable

    def _row(self, parent: ttk.Frame, row: int, label: str, widget: tk.Widget, button: tk.Widget | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=8, pady=6)
        widget.grid(row=row, column=1, sticky=tk.EW, padx=8, pady=6)
        if button:
            button.grid(row=row, column=2, sticky=tk.W, padx=8, pady=6)
        parent.columnconfigure(1, weight=1)

    def _tab(self, notebook: ttk.Notebook, title: str) -> ttk.Frame:
        frame = ttk.Frame(notebook, padding=14)
        notebook.add(frame, text=title)
        return frame

    def _build(self) -> None:
        t = self.i18n.t
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        notebook = ttk.Notebook(outer)
        notebook.pack(fill=tk.BOTH, expand=True)

        general = self._tab(notebook, t("settings_general"))
        output = self.data.setdefault("output", {})
        imported = self.data.setdefault("import", {})
        language = str(self.data.get("language", "zh_sim"))
        language_var = tk.StringVar(value=LANGUAGE_LABELS.get(language, LANGUAGE_LABELS["zh_sim"]))
        self._var("language_display", language_var)
        self._row(general, 0, t("ui_language"), ttk.Combobox(general, textvariable=language_var, values=list(LANGUAGE_LABELS.values()), state="readonly"))
        output_dir_var = tk.StringVar(value=str(output.get("directory", "clearlens_output")))
        self._var("output.directory", output_dir_var)
        self._row(
            general,
            1,
            t("default_output_dir"),
            ttk.Entry(general, textvariable=output_dir_var),
            ttk.Button(general, text=t("browse"), command=self._choose_output_dir),
        )
        self._row(general, 2, t("clean_suffix"), ttk.Entry(general, textvariable=self._var("output.clean_suffix", tk.StringVar(value=str(output.get("clean_suffix", "_cleaned"))))))
        self._row(general, 3, t("converted_suffix"), ttk.Entry(general, textvariable=self._var("output.converted_suffix", tk.StringVar(value=str(output.get("converted_suffix", "_converted"))))))
        ttk.Checkbutton(general, text=t("preserve_folders"), variable=self._var("output.preserve_folders", tk.BooleanVar(value=bool(output.get("preserve_folders", True))))).grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        ttk.Checkbutton(general, text=t("overwrite_existing"), variable=self._var("output.overwrite_existing", tk.BooleanVar(value=bool(output.get("overwrite_existing", False))))).grid(row=5, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        ttk.Checkbutton(general, text=t("recursive_folder"), variable=self._var("import.recursive", tk.BooleanVar(value=bool(imported.get("recursive", True))))).grid(row=6, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        editor = self.data.setdefault("editor", {})
        self._row(
            general,
            7,
            t("editor_font_size"),
            ttk.Spinbox(
                general,
                from_=8,
                to=32,
                textvariable=self._var("editor.font_size", tk.IntVar(value=int(editor.get("font_size", 11)))),
            ),
        )

        processing = self._tab(notebook, t("settings_processing"))
        processing_data = self.data.setdefault("processing", {})
        ttk.Checkbutton(
            processing,
            text=t("parallel_enabled"),
            variable=self._var("processing.parallel_enabled", tk.BooleanVar(value=bool(processing_data.get("parallel_enabled", True)))),
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        ttk.Checkbutton(
            processing,
            text=t("use_multiprocessing"),
            variable=self._var("processing.use_multiprocessing", tk.BooleanVar(value=bool(processing_data.get("use_multiprocessing", True)))),
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        self._row(
            processing,
            2,
            t("max_workers"),
            ttk.Spinbox(
                processing,
                from_=1,
                to=256,
                textvariable=self._var("processing.max_workers", tk.IntVar(value=int(processing_data.get("max_workers", 1)))),
            ),
        )
        self._row(
            processing,
            3,
            t("preview_max_chars"),
            ttk.Spinbox(
                processing,
                from_=10000,
                to=5000000,
                increment=10000,
                textvariable=self._var("processing.preview_max_chars", tk.IntVar(value=int(processing_data.get("preview_max_chars", 200000)))),
            ),
        )
        ttk.Label(processing, text=t("processing_tip"), wraplength=720, foreground="#4b6972").grid(
            row=4, column=0, columnspan=3, sticky=tk.W, padx=8, pady=12
        )

        encoding = self._tab(notebook, t("settings_encoding"))
        self._row(encoding, 0, t("output_encoding"), ttk.Combobox(encoding, textvariable=self._var("output.encoding", tk.StringVar(value=str(output.get("encoding", "utf-8")))), values=OUTPUT_ENCODINGS, state="readonly"))
        self._row(encoding, 1, t("newline_style"), ttk.Combobox(encoding, textvariable=self._var("output.newline", tk.StringVar(value=str(output.get("newline", "lf")))), values=("lf", "crlf", "cr"), state="readonly"))

        ai = self._tab(notebook, t("settings_ai"))
        ai_data = self.data.setdefault("ai", {})
        ttk.Checkbutton(ai, text=t("enable_ai"), variable=self._var("ai.enabled", tk.BooleanVar(value=bool(ai_data.get("enabled", False))))).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        provider_labels = {"openai": "OpenAI / ChatGPT", "deepseek": "DeepSeek"}
        provider_code = str(ai_data.get("provider", "openai"))
        provider_display = tk.StringVar(value=provider_labels.get(provider_code, provider_labels["openai"]))
        self._var("ai.provider_display", provider_display)
        self._row(ai, 1, t("llm_provider"), ttk.Combobox(ai, textvariable=provider_display, values=tuple(provider_labels.values()), state="readonly"))

        openai_key = self._var("ai.openai_api_key", tk.StringVar(value=str(ai_data.get("openai_api_key", ""))))
        self._row(
            ai,
            2,
            t("openai_api_key"),
            ttk.Entry(ai, textvariable=openai_key, show="*"),
            ttk.Button(ai, text=t("clear_api_key"), command=lambda: self._clear_api_key("ai.openai_api_key")),
        )
        self._row(ai, 3, t("openai_model"), ttk.Entry(ai, textvariable=self._var("ai.openai_model", tk.StringVar(value=str(ai_data.get("openai_model", "gpt-5.4-mini"))))))
        deepseek_key = self._var("ai.deepseek_api_key", tk.StringVar(value=str(ai_data.get("deepseek_api_key", ""))))
        self._row(
            ai,
            4,
            t("deepseek_api_key"),
            ttk.Entry(ai, textvariable=deepseek_key, show="*"),
            ttk.Button(ai, text=t("clear_api_key"), command=lambda: self._clear_api_key("ai.deepseek_api_key")),
        )
        self._row(ai, 5, t("deepseek_model"), ttk.Entry(ai, textvariable=self._var("ai.deepseek_model", tk.StringVar(value=str(ai_data.get("deepseek_model", "deepseek-v4-flash"))))))
        effort_codes = ("none", "low", "medium", "high")
        effort_labels = tuple(t(f"effort_{code}") for code in effort_codes)
        effort_code = str(ai_data.get("reasoning_effort", "low"))
        effort_display = tk.StringVar(value=effort_labels[effort_codes.index(effort_code)] if effort_code in effort_codes else effort_labels[1])
        self._var("ai.reasoning_effort_display", effort_display)
        self._row(ai, 6, t("reasoning_effort"), ttk.Combobox(ai, textvariable=effort_display, values=effort_labels, state="readonly"))
        self._row(ai, 7, t("max_chars"), ttk.Spinbox(ai, from_=1000, to=1000000, increment=1000, textvariable=self._var("ai.max_chars_per_request", tk.IntVar(value=int(ai_data.get("max_chars_per_request", 30000))))))
        self._row(ai, 8, t("max_output_tokens"), ttk.Spinbox(ai, from_=512, to=32768, increment=512, textvariable=self._var("ai.max_output_tokens", tk.IntVar(value=int(ai_data.get("max_output_tokens", 8000))))))
        ttk.Checkbutton(ai, text=t("confirm_before_send"), variable=self._var("ai.confirm_before_send", tk.BooleanVar(value=bool(ai_data.get("confirm_before_send", True))))).grid(row=9, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        ttk.Checkbutton(ai, text=t("remember_api_key"), variable=self._var("ai.remember_api_key", tk.BooleanVar(value=bool(ai_data.get("remember_api_key", False))))).grid(row=10, column=0, columnspan=3, sticky=tk.W, padx=8, pady=6)
        ttk.Label(ai, text=t("api_privacy_tip"), foreground="#8a4b08", wraplength=720).grid(row=11, column=0, columnspan=3, sticky=tk.W, padx=8, pady=12)

        safety = self._tab(notebook, t("settings_safety"))
        thresholds = self.data.setdefault("thresholds", {})
        self._row(safety, 0, t("abnormal_ratio"), ttk.Spinbox(safety, from_=0.1, to=1.0, increment=0.05, textvariable=self._var("thresholds.abnormal_symbol_ratio", tk.DoubleVar(value=float(thresholds.get("abnormal_symbol_ratio", 0.65))))))
        self._row(safety, 1, t("min_symbol_line"), ttk.Spinbox(safety, from_=1, to=200, textvariable=self._var("thresholds.min_line_length_for_symbol_check", tk.IntVar(value=int(thresholds.get("min_line_length_for_symbol_check", 8))))))

        buttons = ttk.Frame(outer)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text=t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=8)
        ttk.Button(buttons, text=t("restore_defaults"), command=self._restore_defaults).pack(side=tk.LEFT)
        if self.initial_tab == "ai":
            notebook.select(ai)

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(parent=self)
        if path:
            self.vars["output.directory"].set(path)

    def _clear_api_key(self, key: str) -> None:
        variable = self.vars.get(key)
        if variable is not None:
            variable.set("")

    def _restore_defaults(self) -> None:
        if not messagebox.askyesno(
            self.i18n.t("settings_title"),
            self.i18n.t("restore_defaults_confirm"),
            parent=self,
        ):
            return
        defaults = load_default_settings()
        defaults_ai = defaults.setdefault("ai", {})
        defaults_ai["openai_api_key"] = str(self.vars["ai.openai_api_key"].get())
        defaults_ai["deepseek_api_key"] = str(self.vars["ai.deepseek_api_key"].get())
        self.result = defaults
        self.destroy()

    @staticmethod
    def _set_nested(target: dict[str, Any], dotted_key: str, value: Any) -> None:
        parts = dotted_key.split(".")
        current = target
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def _save(self) -> None:
        result = copy.deepcopy(self.data)
        language_label = str(self.vars["language_display"].get())
        result["language"] = next((code for code, label in LANGUAGE_LABELS.items() if label == language_label), "zh_sim")
        try:
            for key, variable in self.vars.items():
                if key in {"language_display", "ai.reasoning_effort_display", "ai.provider_display"}:
                    continue
                self._set_nested(result, key, variable.get())
        except (tk.TclError, ValueError) as exc:
            messagebox.showerror(self.i18n.t("settings_title"), str(exc), parent=self)
            return
        result["output"]["directory"] = str(Path(str(result["output"]["directory"])))
        effort_labels = {self.i18n.t(f"effort_{code}"): code for code in ("none", "low", "medium", "high")}
        result_ai = result.setdefault("ai", {})
        result_ai["reasoning_effort"] = effort_labels.get(str(self.vars["ai.reasoning_effort_display"].get()), "low")
        provider_labels = {"OpenAI / ChatGPT": "openai", "DeepSeek": "deepseek"}
        result_ai["provider"] = provider_labels.get(str(self.vars["ai.provider_display"].get()), "openai")
        result_ai.pop("api_key", None)
        result_ai.pop("model", None)
        self.result = result
        self.destroy()
