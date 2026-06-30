# -*- coding: utf-8 -*-
"""Settings dialog."""
from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any

from .i18n import I18N, LANGUAGE_LABELS, LANGUAGE_CODES_BY_LABEL, normalize_language_code
from .rapid_ocr_backend import LANGUAGE_PRESETS
from .utils import enable_mousewheel


class SettingsDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, config: dict[str, Any], i18n: I18N | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n or I18N(config.get("ui_language", "en"))
        t = self.i18n.t
        self.title(t("settings_title"))
        self.geometry("900x720")
        self.minsize(760, 520)
        self.transient(master)
        self.grab_set()
        self.result: dict[str, Any] | None = None
        self.config_data = copy.deepcopy(config)
        self.vars: dict[str, tk.Variable] = {}
        self.ui_language_display_var = tk.StringVar(value=LANGUAGE_LABELS.get(normalize_language_code(self.config_data.get("ui_language", "en")), "English"))
        self._build()

    def _v(self, key: str, var: tk.Variable) -> tk.Variable:
        self.vars[key] = var
        return var

    def _build(self) -> None:
        t = self.i18n.t
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        nb = ttk.Notebook(outer)
        nb.pack(fill=tk.BOTH, expand=True)
        self._build_basic(nb)
        self._build_ocr(nb)
        self._build_llm(nb)
        self._build_privacy(nb)
        btns = ttk.Frame(outer)
        btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btns, text=t("save"), command=self._save).pack(side=tk.RIGHT)
        ttk.Button(btns, text=t("cancel"), command=self.destroy).pack(side=tk.RIGHT, padx=8)

    def _row(self, parent: ttk.Frame, r: int, label: str, widget: tk.Widget, button: tk.Widget | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky=tk.W, padx=6, pady=5)
        widget.grid(row=r, column=1, sticky=tk.EW, padx=6, pady=5)
        if button:
            button.grid(row=r, column=2, sticky=tk.W, padx=6, pady=5)
        parent.columnconfigure(1, weight=1)

    def _scrollable_tab(self, nb: ttk.Notebook, title: str) -> ttk.Frame:
        """Create a notebook tab whose content can scroll vertically."""
        container = ttk.Frame(nb)
        nb.add(container, text=title)
        canvas = tk.Canvas(container, highlightthickness=0)
        ybar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=ybar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        frame = ttk.Frame(canvas, padding=12)
        window_id = canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        def _on_frame_configure(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        enable_mousewheel(canvas, canvas)
        enable_mousewheel(frame, canvas)
        return frame

    def _build_basic(self, nb: ttk.Notebook) -> None:
        t = self.i18n.t
        cfg = self.config_data
        frame = self._scrollable_tab(nb, t("basic"))
        self.vars["ui_language"] = self.ui_language_display_var
        self._row(frame, 0, t("ui_language"), ttk.Combobox(frame, textvariable=self.ui_language_display_var, values=list(LANGUAGE_LABELS.values()), state="readonly"))
        self._row(frame, 1, t("default_project_dir"), ttk.Entry(frame, textvariable=self._v("default_project_dir", tk.StringVar(value=cfg.get("default_project_dir", "projects")))), ttk.Button(frame, text=t("choose"), command=lambda: self._choose_dir("default_project_dir")))
        self._row(frame, 2, t("default_export_dir"), ttk.Entry(frame, textvariable=self._v("default_export_dir", tk.StringVar(value=cfg.get("default_export_dir", "output")))), ttk.Button(frame, text=t("choose"), command=lambda: self._choose_dir("default_export_dir")))
        self._row(frame, 3, t("autosave_interval"), ttk.Spinbox(frame, from_=0, to=120, textvariable=self._v("autosave_interval_minutes", tk.IntVar(value=int(cfg.get("autosave_interval_minutes", 5))))))
        ttk.Checkbutton(frame, text=t("restore_last_project"), variable=self._v("restore_last_project", tk.BooleanVar(value=bool(cfg.get("restore_last_project", False))))).grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)

    def _build_ocr(self, nb: ttk.Notebook) -> None:
        t = self.i18n.t
        ocr = self.config_data.get("ocr", {})
        frame = self._scrollable_tab(nb, t("ocr"))
        backend_value = str(ocr.get("backend", "rapidocr") or "rapidocr")
        if backend_value == ("paddle" + "ocr"):
            backend_value = "rapidocr"
        self._row(frame, 0, t("ocr_backend"), ttk.Combobox(frame, textvariable=self._v("ocr.backend", tk.StringVar(value=backend_value)), values=["rapidocr", "easyocr", "llm_ocr", "hybrid"], state="readonly"))
        preset_values = list(LANGUAGE_PRESETS.keys())
        language_preset = ocr.get("language_preset", "zh_en_mixed")
        old_tr_code = "zh_" + chr(116) + chr(119)
        if language_preset == old_tr_code:
            language_preset = "zh_tr"
        self._row(frame, 1, t("language_preset_setting"), ttk.Combobox(frame, textvariable=self._v("ocr.language_preset", tk.StringVar(value=language_preset)), values=preset_values, state="readonly"))
        langs_box = ttk.LabelFrame(frame, text=t("languages_hint"))
        langs_box.grid(row=2, column=0, columnspan=3, sticky=tk.EW, padx=6, pady=6)
        selected = set(ocr.get("selected_languages", ["zh", "en"]))
        if "zh_tra" in selected:
            selected.discard("zh_tra")
            selected.add("zh_tr")
        if old_tr_code in selected:
            selected.discard(old_tr_code)
            selected.add("zh_tr")
        all_langs = ["zh", "zh_tr", "en", "ja", "ko", "fr", "de", "es", "ru", "it", "pt", "ar", "latin"]
        lang_labels = {"zh": "zh 简体中文", "zh_tr": "zh_tr 繁體中文"}
        for i, lang in enumerate(all_langs):
            var = self._v(f"ocr.lang.{lang}", tk.BooleanVar(value=lang in selected))
            ttk.Checkbutton(langs_box, text=lang_labels.get(lang, lang), variable=var).grid(row=i//5, column=i%5, sticky=tk.W, padx=6, pady=4)
        ttk.Checkbutton(frame, text=t("mixed_language_mode"), variable=self._v("ocr.mixed_language_mode", tk.BooleanVar(value=bool(ocr.get("mixed_language_mode", True))))).grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 4, t("rapidocr_lang_profile"), ttk.Entry(frame, textvariable=self._v("ocr.rapid_lang", tk.StringVar(value=ocr.get("rapid_lang", ocr.get("rapid_lang", "ch"))))))
        ttk.Checkbutton(frame, text=t("enable_gpu"), variable=self._v("ocr.use_gpu", tk.BooleanVar(value=bool(ocr.get("use_gpu", False))))).grid(row=5, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("keep_coordinates"), variable=self._v("ocr.keep_coordinates", tk.BooleanVar(value=bool(ocr.get("keep_coordinates", True))))).grid(row=6, column=0, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("keep_confidence"), variable=self._v("ocr.keep_confidence", tk.BooleanVar(value=bool(ocr.get("keep_confidence", True))))).grid(row=6, column=1, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("use_angle_cls"), variable=self._v("ocr.use_angle_cls", tk.BooleanVar(value=bool(ocr.get("use_angle_cls", True))))).grid(row=7, column=0, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("prefer_pdf_text_layer"), variable=self._v("ocr.prefer_pdf_text_layer", tk.BooleanVar(value=bool(ocr.get("prefer_pdf_text_layer", True))))).grid(row=7, column=1, columnspan=2, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 8, t("ocr_text_layout"), ttk.Combobox(frame, textvariable=self._v("ocr.text_layout", tk.StringVar(value=ocr.get("text_layout", "paragraph"))), values=["paragraph", "line"], state="readonly"))
        self._row(frame, 9, t("pdf_dpi"), ttk.Spinbox(frame, from_=72, to=600, textvariable=self._v("ocr.pdf_dpi", tk.IntVar(value=int(ocr.get("pdf_dpi", 200))))))
        self._row(frame, 10, t("ocr_parallel_backend"), ttk.Combobox(frame, textvariable=self._v("ocr.parallel_backend", tk.StringVar(value=ocr.get("parallel_backend", "thread"))), values=["thread", "process"], state="readonly"))
        self._row(frame, 11, t("max_ocr_workers"), ttk.Spinbox(frame, from_=1, to=8, textvariable=self._v("ocr.max_workers", tk.IntVar(value=int(ocr.get("max_workers", 1))))))
        ttk.Label(frame, text=t("parallel_tip"), foreground="#666", wraplength=760).grid(row=12, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 13, t("rapidocr_model_dir"), ttk.Entry(frame, textvariable=self._v("ocr.rapidocr_model_dir", tk.StringVar(value=ocr.get("rapidocr_model_dir", ocr.get("model_dir", "models/rapidocr"))))), ttk.Button(frame, text=t("choose"), command=lambda: self._choose_dir("ocr.rapidocr_model_dir")))
        self._row(frame, 14, t("rapidocr_model_type"), ttk.Combobox(frame, textvariable=self._v("ocr.rapidocr_model_type", tk.StringVar(value=ocr.get("rapidocr_model_type", "small"))), values=["small", "medium"], state="readonly"))
        ttk.Checkbutton(frame, text=t("auto_fallback_to_easyocr"), variable=self._v("ocr.auto_fallback_to_easyocr", tk.BooleanVar(value=bool(ocr.get("auto_fallback_to_easyocr", True))))).grid(row=15, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 16, t("easyocr_model_dir"), ttk.Entry(frame, textvariable=self._v("ocr.easyocr_model_dir", tk.StringVar(value=ocr.get("easyocr_model_dir", "models/easyocr")))), ttk.Button(frame, text=t("choose"), command=lambda: self._choose_dir("ocr.easyocr_model_dir")))
        ttk.Checkbutton(frame, text=t("easyocr_light_mode"), variable=self._v("ocr.easyocr_light_mode", tk.BooleanVar(value=bool(ocr.get("easyocr_light_mode", True))))).grid(row=17, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 18, t("easyocr_canvas_size"), ttk.Spinbox(frame, from_=640, to=4096, increment=160, textvariable=self._v("ocr.easyocr_canvas_size", tk.IntVar(value=int(ocr.get("easyocr_canvas_size", 1280))))))
        self._row(frame, 19, t("easyocr_mag_ratio"), ttk.Spinbox(frame, from_=0.5, to=2.0, increment=0.1, textvariable=self._v("ocr.easyocr_mag_ratio", tk.DoubleVar(value=float(ocr.get("easyocr_mag_ratio", 1.0))))))
        ttk.Checkbutton(frame, text=t("easyocr_paragraph"), variable=self._v("ocr.easyocr_paragraph", tk.BooleanVar(value=bool(ocr.get("easyocr_paragraph", False))))).grid(row=20, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 21, t("model_download_policy"), ttk.Combobox(frame, textvariable=self._v("ocr.model_download_policy", tk.StringVar(value=ocr.get("model_download_policy", "ask"))), values=["ask", "auto", "manual"], state="readonly"))
        self._row(frame, 22, t("preview_max_side"), ttk.Spinbox(frame, from_=800, to=4096, increment=100, textvariable=self._v("ocr.preview_max_side", tk.IntVar(value=int(ocr.get("preview_max_side", 1400))))))
        ttk.Label(frame, text=t("model_download_tip"), foreground="#666", wraplength=760).grid(row=23, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        ttk.Label(frame, text=t("rapidocr_model_tip"), foreground="#9a3b00", wraplength=760).grid(row=24, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)

    def _build_llm(self, nb: ttk.Notebook) -> None:
        t = self.i18n.t
        llm = self.config_data.get("llm", {})
        frame = self._scrollable_tab(nb, t("llm"))
        ttk.Checkbutton(frame, text=t("enable_openai"), variable=self._v("llm.enabled", tk.BooleanVar(value=bool(llm.get("enabled", False))))).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)
        api_entry = ttk.Entry(frame, textvariable=self._v("llm.api_key", tk.StringVar(value=llm.get("api_key", ""))), show="*")
        self._row(frame, 1, "OpenAI API Key", api_entry)
        self._row(frame, 2, t("default_model"), ttk.Entry(frame, textvariable=self._v("llm.model", tk.StringVar(value=llm.get("model", "gpt-5.5")))))
        self._row(frame, 3, "Temperature", ttk.Spinbox(frame, from_=0, to=2, increment=0.1, textvariable=self._v("llm.temperature", tk.DoubleVar(value=float(llm.get("temperature", 0))))))
        self._row(frame, 4, t("max_output_tokens"), ttk.Spinbox(frame, from_=256, to=32768, increment=256, textvariable=self._v("llm.max_output_tokens", tk.IntVar(value=int(llm.get("max_output_tokens", 4096))))))
        ttk.Checkbutton(frame, text=t("structured_json"), variable=self._v("llm.structured_json", tk.BooleanVar(value=bool(llm.get("structured_json", True))))).grid(row=5, column=0, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("save_api_logs"), variable=self._v("llm.save_api_logs", tk.BooleanVar(value=bool(llm.get("save_api_logs", False))))).grid(row=5, column=1, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("confirm_before_send"), variable=self._v("llm.confirm_before_send", tk.BooleanVar(value=bool(llm.get("confirm_before_send", True))))).grid(row=6, column=0, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("allow_send_image"), variable=self._v("llm.allow_send_image", tk.BooleanVar(value=bool(llm.get("allow_send_image", True))))).grid(row=7, column=0, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("allow_send_text"), variable=self._v("llm.allow_send_text", tk.BooleanVar(value=bool(llm.get("allow_send_text", True))))).grid(row=7, column=1, sticky=tk.W, padx=6, pady=5)
        self._row(frame, 8, t("max_llm_workers"), ttk.Spinbox(frame, from_=1, to=4, textvariable=self._v("llm.max_concurrent_requests", tk.IntVar(value=int(llm.get("max_concurrent_requests", 1))))))
        ttk.Checkbutton(frame, text=t("auto_repair_non_json"), variable=self._v("llm.auto_repair_non_json", tk.BooleanVar(value=bool(llm.get("auto_repair_non_json", True))))).grid(row=9, column=0, columnspan=3, sticky=tk.W, padx=6, pady=5)

    def _build_privacy(self, nb: ttk.Notebook) -> None:
        t = self.i18n.t
        privacy = self.config_data.get("privacy", {})
        frame = self._scrollable_tab(nb, t("privacy"))
        ttk.Checkbutton(frame, text=t("local_only_mode"), variable=self._v("privacy.local_only", tk.BooleanVar(value=bool(privacy.get("local_only", True))))).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("remind_before_llm"), variable=self._v("privacy.remind_before_llm", tk.BooleanVar(value=bool(privacy.get("remind_before_llm", True))))).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=6, pady=5)
        ttk.Checkbutton(frame, text=t("do_not_save_api_key"), variable=self._v("privacy.do_not_save_api_key", tk.BooleanVar(value=bool(privacy.get("do_not_save_api_key", False))))).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=6, pady=5)
        ttk.Button(frame, text=t("clear_api_key"), command=lambda: self.vars["llm.api_key"].set("")).grid(row=3, column=0, sticky=tk.W, padx=6, pady=10)
        ttk.Label(frame, text=t("privacy_tip"), foreground="#9a3b00").grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=6, pady=8)

    def _choose_dir(self, key: str) -> None:
        d = filedialog.askdirectory(parent=self)
        if d and key in self.vars:
            self.vars[key].set(d)

    def _set_nested(self, target: dict[str, Any], dotted_key: str, value: Any) -> None:
        parts = dotted_key.split(".")
        cur = target
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value

    def _resolve_ui_language(self) -> str:
        value = self.ui_language_display_var.get()
        return LANGUAGE_CODES_BY_LABEL.get(value, "en")

    def _save(self) -> None:
        result = copy.deepcopy(self.config_data)
        for key, var in self.vars.items():
            if key.startswith("ocr.lang.") or key == "ui_language":
                continue
            self._set_nested(result, key, var.get())
        result["ui_language"] = self._resolve_ui_language()
        selected = []
        for key, var in self.vars.items():
            if key.startswith("ocr.lang.") and bool(var.get()):
                selected.append(key.split(".")[-1])
        if not selected:
            messagebox.showwarning(self.i18n.t("info"), self.i18n.t("at_least_one_language"), parent=self)
            return
        result.setdefault("ocr", {})["selected_languages"] = selected
        if result.setdefault("ocr", {}).get("backend") == ("paddle" + "ocr"):
            result["ocr"]["backend"] = "rapidocr"
        if "zh_tr" in selected:
            result["ocr"]["rapid_lang"] = "chinese_cht"
        if len(selected) > 1:
            result.setdefault("ocr", {})["mixed_language_mode"] = True
        self.result = result
        self.destroy()
