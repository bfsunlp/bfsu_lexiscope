# -*- coding: utf-8 -*-
"""Main Tkinter UI for BFSU ProofLens."""
from __future__ import annotations

import os
import queue
import threading
import traceback
import time
import multiprocessing
import importlib.util
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Any

from .config_manager import ConfigManager
from .export_utils import (
    export_to_docx, export_to_json, export_to_markdown, export_to_txt,
    export_to_xlsx, export_to_xml,
)
from .file_loader import load_file_to_pages
from .i18n import I18N, LANGUAGE_LABELS, normalize_language_code
from .import_workers import import_files_process_worker
from .llm_backend import LLMBackend
from .logger import logger
from .rapid_ocr_backend import RapidOCRBackend, LANGUAGE_PRESETS, prepare_rapidocr_models
from .parallel_workers import rapidocr_recognize_page, easyocr_recognize_page, llm_ocr_page, llm_proofread_page
from .project_manager import ProjectManager
from .ui_about import AboutDialog
from .ui_export import ExportDialog
from .ui_proofreading import SuggestionPanel
from .ui_settings import SettingsDialog
from .utils import APP_NAME, APP_VERSION, PROJECT_EXT, SUPPORTED_FILES, enable_mousewheel, install_global_mousewheel_support, now_iso, open_folder, resource_path, runtime_root, safe_filename, writable_path


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()
        self.config_data = self.config_manager.load()
        self.i18n = I18N(self.config_data.get("ui_language", "en"))
        self.project = ProjectManager(config=self.config_data)
        self.current_file_id: str = ""
        self.current_page_index: int = 0
        self.zoom: float = 1.0
        self.rotation: int = 0
        self._image_original = None
        self._image_photo = None
        self._privacy_confirmed_this_session = False
        self._model_download_confirmed_this_session: dict[str, bool] = {}
        self._task_queue: queue.Queue[tuple[str, int, Any]] = queue.Queue()
        self._preview_queue: queue.Queue[tuple[int, str, Any]] = queue.Queue()
        self._preview_counter: int = 0
        self._active_preview_id: int | None = None
        self._task_counter: int = 0
        self._active_task_id: int | None = None
        self._active_task_callbacks: dict[int, dict[str, Any]] = {}
        self._busy: bool = False
        self._suppress_tree_select: bool = False
        self.title(f"{APP_NAME} - Untitled")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self._set_icon()
        self._setup_style()
        install_global_mousewheel_support(self)
        self._build_ui()
        self._refresh_title()
        self._set_status(self.i18n.t("welcome_status"))
        logger.info("BFSU ProofLens started")

    # ---------- UI construction ----------
    def _set_icon(self) -> None:
        ico = Path(resource_path("assets/app.ico"))
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        default_font = ("Microsoft YaHei UI", 9)
        self.option_add("*Font", default_font)
        style.configure("TButton", padding=(8, 4))
        style.configure("Tool.TButton", padding=(6, 3))
        style.configure("Status.TLabel", anchor=tk.W)

    def _build_ui(self) -> None:
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()

    def _build_menu(self) -> None:
        t = self.i18n.t
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label=t("new_project"), command=self.new_project)
        file_menu.add_command(label=t("open_project"), command=self.open_project)
        file_menu.add_command(label=t("save_project"), command=self.save_project)
        file_menu.add_command(label=t("save_as"), command=self.save_project_as)
        file_menu.add_command(label=t("close_project"), command=self.close_project)
        file_menu.add_separator()
        file_menu.add_command(label=t("import_files"), command=self.import_files)
        file_menu.add_separator()
        export_menu = tk.Menu(file_menu, tearoff=False)
        for scope_key, scope in [("export_scope_current_page", "current_page"), ("export_scope_current_file", "current_file"), ("export_scope_project", "project")]:
            scope_label = t(scope_key)
            sub = tk.Menu(export_menu, tearoff=False)
            for fmt in ["TXT", "DOCX", "XLSX", "JSON", "XML", "Markdown"]:
                sub.add_command(label=t("export_as", scope=scope_label, fmt=fmt), command=lambda s=scope, f=fmt: self.quick_export(s, f))
            export_menu.add_cascade(label=scope_label, menu=sub)
        file_menu.add_cascade(label=t("export"), menu=export_menu)
        file_menu.add_separator()
        file_menu.add_command(label=t("exit"), command=self.on_exit)
        menubar.add_cascade(label=t("file"), menu=file_menu)

        ocr_menu = tk.Menu(menubar, tearoff=False)
        ocr_menu.add_command(label=t("run_ocr_current"), command=self.run_ocr_current)
        ocr_menu.add_command(label=t("run_ocr_current_file"), command=lambda: self.run_ocr_scope("current_file"))
        ocr_menu.add_command(label=t("run_ocr_project"), command=lambda: self.run_ocr_scope("project"))
        ocr_menu.add_separator()
        fast_menu = tk.Menu(ocr_menu, tearoff=False)
        fast_menu.add_command(label=t("run_fast_ocr_current"), command=lambda: self.run_ocr_scope("current_page", engine_override="easyocr"))
        fast_menu.add_command(label=t("run_fast_ocr_current_file"), command=lambda: self.run_ocr_scope("current_file", engine_override="easyocr"))
        fast_menu.add_command(label=t("run_fast_ocr_project"), command=lambda: self.run_ocr_scope("project", engine_override="easyocr"))
        ocr_menu.add_cascade(label=t("fast_ocr_easyocr"), menu=fast_menu)
        ocr_menu.add_separator()
        ocr_menu.add_command(label=t("restore_ocr"), command=self.restore_ocr_text)
        menubar.add_cascade(label=t("ocr"), menu=ocr_menu)

        llm_menu = tk.Menu(menubar, tearoff=False)
        llm_menu.add_command(label=t("llm_ocr_current"), command=self.run_llm_ocr_current)
        llm_menu.add_command(label=t("llm_ocr_current_file"), command=lambda: self.run_llm_ocr_scope("current_file"))
        llm_menu.add_separator()
        llm_menu.add_command(label=t("llm_proofread_current"), command=self.run_llm_proofread_current)
        llm_menu.add_command(label=t("llm_proofread_current_file"), command=lambda: self.run_llm_proofread_scope("current_file"))
        menubar.add_cascade(label=t("llm"), menu=llm_menu)

        project_menu = tk.Menu(menubar, tearoff=False)
        project_menu.add_command(label=t("save_project"), command=self.save_project)
        project_menu.add_command(label=t("save_as"), command=self.save_project_as)
        menubar.add_cascade(label=t("project"), menu=project_menu)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label=t("find_replace"), command=self.find_replace)
        menubar.add_cascade(label=t("tools"), menu=tools_menu)

        settings_menu = tk.Menu(menubar, tearoff=False)
        self.ui_language_var = tk.StringVar(value=self.i18n.language)
        language_menu = tk.Menu(settings_menu, tearoff=False)
        for _code, _label in LANGUAGE_LABELS.items():
            language_menu.add_radiobutton(label=_label, value=_code, variable=self.ui_language_var, command=lambda c=_code: self._set_ui_language(c))
        settings_menu.add_cascade(label=t("language"), menu=language_menu)
        settings_menu.add_separator()
        settings_menu.add_command(label=t("preferences"), command=self.open_settings)
        menubar.add_cascade(label=t("settings"), menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label=t("about"), command=self.show_about)
        menubar.add_cascade(label=t("help"), menu=help_menu)
        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        t = self.i18n.t
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(fill=tk.X)
        ttk.Button(bar, text=t("open_files"), style="Tool.TButton", command=self.import_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("batch_import"), style="Tool.TButton", command=self.import_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("run_ocr"), style="Tool.TButton", command=self.run_ocr_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("run_fast_ocr"), style="Tool.TButton", command=lambda: self.run_ocr_scope("current_page", engine_override="easyocr")).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("llm_ocr"), style="Tool.TButton", command=self.run_llm_ocr_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("llm_proofread"), style="Tool.TButton", command=self.run_llm_proofread_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("save"), style="Tool.TButton", command=self.save_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("export"), style="Tool.TButton", command=self.export_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Label(bar, text=t("language_preset")).pack(side=tk.LEFT)
        self.language_preset_var = tk.StringVar(value=self.config_data.get("ocr", {}).get("language_preset", "zh_en_mixed"))
        self.language_combo = ttk.Combobox(bar, textvariable=self.language_preset_var, width=18, values=list(LANGUAGE_PRESETS.keys()), state="readonly")
        self.language_combo.pack(side=tk.LEFT, padx=4)
        self.language_combo.bind("<<ComboboxSelected>>", lambda e: self._on_language_preset_changed())
        self.mixed_var = tk.BooleanVar(value=bool(self.config_data.get("ocr", {}).get("mixed_language_mode", True)))
        ttk.Checkbutton(bar, text=t("mixed_language"), variable=self.mixed_var, command=self._on_mixed_changed).pack(side=tk.LEFT, padx=4)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(bar, text=t("zoom_in"), style="Tool.TButton", command=lambda: self.change_zoom(1.2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("zoom_out"), style="Tool.TButton", command=lambda: self.change_zoom(1/1.2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("fit"), style="Tool.TButton", command=self.fit_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("rotate_90"), style="Tool.TButton", command=self.rotate_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text=t("prev_page"), style="Tool.TButton", command=lambda: self.move_page(-1)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bar, text=t("next_page"), style="Tool.TButton", command=lambda: self.move_page(1)).pack(side=tk.RIGHT, padx=2)

    def _build_workspace(self) -> None:
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        top_pane = ttk.PanedWindow(main_pane, orient=tk.HORIZONTAL)
        main_pane.add(top_pane, weight=4)

        left = ttk.Frame(top_pane, padding=4)
        top_pane.add(left, weight=1)
        ttk.Label(left, text=self.i18n.t("file_page_list"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)

        tree_area = ttk.Frame(left)
        tree_area.pack(fill=tk.BOTH, expand=True)
        self.tree_files = ttk.Treeview(tree_area, show="tree", selectmode="extended")
        y_left = ttk.Scrollbar(tree_area, orient=tk.VERTICAL, command=self.tree_files.yview)
        self.tree_files.configure(yscrollcommand=y_left.set)
        self.tree_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_left.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_files.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree_files.bind("<Button-3>", self.on_tree_context_menu)
        self.tree_files.bind("<Control-Button-1>", self.on_tree_context_menu)
        self.tree_files.bind("<Double-1>", lambda _event: self.open_selected_tree_item())
        self.tree_files.bind("<Delete>", self._on_tree_delete_key)
        self.tree_files.bind("<KP_Delete>", self._on_tree_delete_key)
        enable_mousewheel(self.tree_files)

        tree_buttons = ttk.Frame(left)
        tree_buttons.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(tree_buttons, text="+", width=3, command=self.add_files_or_pages).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tree_buttons, text="−", width=3, command=self.delete_selected_tree_item).pack(side=tk.LEFT)
        ttk.Label(tree_buttons, text=self.i18n.t("tree_select_or_manage_hint"), foreground="#666").pack(side=tk.LEFT, padx=8)

        middle = ttk.Frame(top_pane, padding=4)
        top_pane.add(middle, weight=3)
        ttk.Label(middle, text=self.i18n.t("image_preview"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        img_frame = ttk.Frame(middle)
        img_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(img_frame, bg="#f6f6f6", highlightthickness=0)
        self.canvas_x = ttk.Scrollbar(img_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas_y = ttk.Scrollbar(img_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.canvas_x.set, yscrollcommand=self.canvas_y.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        enable_mousewheel(self.canvas, self.canvas, self.canvas)
        self.canvas_y.grid(row=0, column=1, sticky="ns")
        self.canvas_x.grid(row=1, column=0, sticky="ew")
        img_frame.rowconfigure(0, weight=1)
        img_frame.columnconfigure(0, weight=1)

        right = ttk.Frame(top_pane, padding=4)
        top_pane.add(right, weight=3)
        hdr = ttk.Frame(right)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text=self.i18n.t("ocr_text_editor"), font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(hdr, text=self.i18n.t("copy"), command=self.copy_text).pack(side=tk.RIGHT, padx=2)
        ttk.Button(hdr, text=self.i18n.t("restore_ocr"), command=self.restore_ocr_text).pack(side=tk.RIGHT, padx=2)
        text_frame = ttk.Frame(right)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.text_editor = tk.Text(text_frame, undo=True, wrap=tk.WORD)
        y_text = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=y_text.set)
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_text.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_editor.bind("<<Modified>>", self.on_text_modified)
        enable_mousewheel(self.text_editor)

        bottom = ttk.Frame(main_pane, padding=6)
        main_pane.add(bottom, weight=1)
        self.suggestion_panel = SuggestionPanel(bottom, self.accept_suggestion, self.reject_suggestion, self.accept_all_suggestions, self.clear_suggestions, i18n=self.i18n)
        self.suggestion_panel.pack(fill=tk.BOTH, expand=True)

    def _build_statusbar(self) -> None:
        status_frame = ttk.Frame(self, relief=tk.SUNKEN, padding=(6, 3))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.task_var = tk.StringVar(value=self.i18n.t("task_idle"))
        self.current_file_var = tk.StringVar(value=self.i18n.t("current_file_none"))
        self.status_var = tk.StringVar(value=self.i18n.t("ready"))

        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, mode="determinate", length=180)
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(status_frame, textvariable=self.task_var, width=28, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(status_frame, textvariable=self.current_file_var, width=38, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.status = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ---------- state helpers ----------
    def _set_status(self, text: str) -> None:
        if hasattr(self, "status_var"):
            self.status_var.set(text)


    def _set_progress(self, value: float | None = None, task: str | None = None, file_name: str | None = None, *, indeterminate: bool = False) -> None:
        if not hasattr(self, "progress_bar"):
            return
        if task is not None:
            self.task_var.set(task)
        if file_name is not None:
            self.current_file_var.set(self.i18n.t("current_file_label", file=file_name or "-"))
        if indeterminate:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start(12)
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            if value is not None:
                self.progress_var.set(max(0.0, min(100.0, float(value))))


    def _reset_progress_later(self, delay_ms: int = 1800) -> None:
        def reset() -> None:
            if not self._busy and hasattr(self, "progress_bar"):
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.progress_var.set(0.0)
                self.task_var.set(self.i18n.t("task_idle"))
                self.current_file_var.set(self.i18n.t("current_file_none"))
        self.after(delay_ms, reset)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        try:
            self.configure(cursor="watch" if busy else "")
        except Exception:
            pass

    def _start_background_task(self, task_label: str, file_name: str, worker: Any, on_success: Any, on_error: Any | None = None) -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        self._task_counter += 1
        task_id = self._task_counter
        self._active_task_id = task_id
        self._active_task_callbacks[task_id] = {"success": on_success, "error": on_error}
        self._set_busy(True)
        self._set_progress(5, self.i18n.t("task_preparing", task=task_label), file_name)
        self._set_status(self.i18n.t("background_task_started", task=task_label, file=file_name))

        def post_progress(payload: dict[str, Any]) -> None:
            self._task_queue.put(("progress", task_id, payload))

        def runner() -> None:
            try:
                self._task_queue.put(("progress", task_id, {"value": 15, "task": self.i18n.t("task_running", task=task_label), "file": file_name, "indeterminate": True}))
                result = worker(post_progress)
                self._task_queue.put(("progress", task_id, {"value": 90, "task": self.i18n.t("task_finalizing", task=task_label), "file": file_name, "indeterminate": False}))
                self._task_queue.put(("success", task_id, result))
            except Exception as exc:
                self._task_queue.put(("error", task_id, {"exception": exc, "traceback": traceback.format_exc()}))

        threading.Thread(target=runner, name=f"BFSUProofLensTask-{task_id}", daemon=True).start()
        self.after(100, self._poll_task_queue)

    def _poll_task_queue(self) -> None:
        # Process the GUI task queue in small batches.  A PDF import can emit
        # many progress events; handling all of them in one callback may make
        # Windows mark the Tkinter window as "not responding" even though the
        # background process has already completed.
        processed_count = 0
        max_events_per_tick = 25
        while processed_count < max_events_per_tick:
            try:
                kind, task_id, payload = self._task_queue.get_nowait()
            except queue.Empty:
                break
            processed_count += 1
            if task_id != self._active_task_id:
                continue
            if kind == "progress":
                page_update = payload.get("page_update") if isinstance(payload, dict) else None
                if page_update:
                    self._apply_page_update(page_update)
                self._set_progress(payload.get("value"), payload.get("task"), payload.get("file"), indeterminate=bool(payload.get("indeterminate")))
            elif kind == "success":
                callbacks = self._active_task_callbacks.pop(task_id, {})
                try:
                    if callbacks.get("success"):
                        callbacks["success"](payload)
                finally:
                    self._set_progress(100, self.i18n.t("task_completed"), None, indeterminate=False)
                    self._set_busy(False)
                    self._active_task_id = None
                    self._reset_progress_later()
            elif kind == "error":
                callbacks = self._active_task_callbacks.pop(task_id, {})
                exc = payload.get("exception")
                tb = payload.get("traceback")
                logger.error("Background task failed: %s\n%s", exc, tb)
                try:
                    if callbacks.get("error"):
                        callbacks["error"](exc)
                    else:
                        messagebox.showerror(self.i18n.t("task_failed"), str(exc), parent=self)
                finally:
                    self._set_progress(0, self.i18n.t("task_failed"), None, indeterminate=False)
                    self._set_busy(False)
                    self._active_task_id = None
                    self._reset_progress_later(2600)
        if self._busy and self._active_task_id is not None:
            delay = 10 if processed_count >= max_events_per_tick else 100
            self.after(delay, self._poll_task_queue)

    def _apply_page_update(self, update: dict[str, Any]) -> None:
        target = self.project.find_page(update.get("file_id", ""), int(update.get("page_index", 0)))
        if target is None:
            return
        operation = update.get("operation", "")
        success = bool(update.get("success", False))
        result = update.get("result") or {}
        if success and operation in {"rapidocr", "easyocr"}:
            target["ocr_text"] = result.get("text", "")
            target["final_text"] = result.get("text", "")
            target["ocr_blocks"] = result.get("blocks", [])
            target["ocr_backend"] = result.get("engine", "rapidocr")
            target["ocr_time"] = float(result.get("elapsed_seconds") or 0.0)
            target["ocr_status"] = "text_layer" if result.get("engine") == "pdf_text_layer" else "done"
            target.pop("processing_task", None)
            if self.current_file_id == update.get("file_id") and self.current_page_index == int(update.get("page_index", 0)):
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", target.get("final_text", ""))
                self.text_editor.edit_modified(False)
        elif success and operation == "llm_ocr":
            text = result.get("text", "")
            target["ocr_text"] = text
            target["corrected_text"] = text
            target["final_text"] = text
            target["ocr_status"] = "done"
            target["ocr_backend"] = "llm_ocr"
            target["proofread_status"] = "llm_ocr_done"
            target["llm_time"] = float(result.get("elapsed_seconds") or 0.0)
            target["llm_model"] = update.get("llm_model", "")
            target.pop("processing_task", None)
            if self.current_file_id == update.get("file_id") and self.current_page_index == int(update.get("page_index", 0)):
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", text)
                self.text_editor.edit_modified(False)
        elif success and operation == "llm_proofread":
            edited = update.get("edited_text", target.get("final_text", ""))
            corrected = result.get("corrected_text", edited)
            suggestions = result.get("suggestions", []) or []
            warnings = result.get("warnings", []) or []
            layout_notes = result.get("layout_notes", "") or ""
            # Ensure the user sees something in the suggestion panel.  Some
            # models return a corrected_text but no granular suggestions; others
            # return a no-error verdict.  Surface both cases explicitly.
            if not suggestions and str(corrected).strip() and str(corrected).strip() != str(edited).strip():
                suggestions = [{
                    "line_no": "",
                    "original": edited,
                    "suggested": corrected,
                    "reason": self.i18n.t("whole_text_correction_reason"),
                    "confidence": 0.65,
                    "category": "whole_text_correction",
                    "status": "pending",
                }]
            elif not suggestions:
                reason_parts = []
                if warnings:
                    reason_parts.append("; ".join(str(x) for x in warnings))
                if layout_notes:
                    reason_parts.append(str(layout_notes))
                suggestions = [{
                    "line_no": "",
                    "original": "",
                    "suggested": "",
                    "reason": " ".join(reason_parts).strip() or self.i18n.t("no_specific_suggestions_reason"),
                    "confidence": "",
                    "category": "no_change_or_info",
                    "status": "info",
                }]
            target["corrected_text"] = corrected
            target["suggestions"] = suggestions
            target["uncertain_spans"] = result.get("uncertain_spans", [])
            target["warnings"] = warnings
            target["layout_notes"] = layout_notes
            target["proofread_status"] = "done"
            target["llm_time"] = float(result.get("elapsed_seconds") or 0.0)
            target["llm_model"] = update.get("llm_model", "")
            target.pop("processing_task", None)
            if self.current_file_id == update.get("file_id") and self.current_page_index == int(update.get("page_index", 0)):
                self.suggestion_panel.set_suggestions(target.get("suggestions", []))
        else:
            if operation in {"rapidocr", "easyocr", "llm_ocr"}:
                target["ocr_status"] = "failed"
            if operation in {"llm_ocr", "llm_proofread"}:
                target["proofread_status"] = "failed"
            target["last_error"] = str(update.get("error", ""))
            target.pop("processing_task", None)
        target["timestamp"] = now_iso()
        self.refresh_file_tree()

    def _refresh_title(self) -> None:
        name = self.project.data.get("project_name", "Untitled")
        self.title(f"{APP_NAME} - {name}")

    def _rebuild_ui(self, status: str | None = None) -> None:
        if hasattr(self, "text_editor"):
            self.save_current_text_to_page()
        for child in list(self.winfo_children()):
            child.destroy()
        self._build_ui()
        self.refresh_file_tree()
        page = self.get_current_page()
        if page:
            self.display_page(page)
        else:
            self.clear_view()
        self._refresh_title()
        if status:
            self._set_status(status)

    def _set_ui_language(self, language: str) -> None:
        if self._busy:
            if hasattr(self, "ui_language_var"):
                self.ui_language_var.set(self.i18n.language)
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        language = normalize_language_code(language)
        if language == self.i18n.language and normalize_language_code(self.config_data.get("ui_language")) == language:
            return
        self.config_data["ui_language"] = language
        self.project.data["settings"] = self.config_data
        self.config_manager.save(self.config_data)
        self.i18n.set_language(language)
        self._rebuild_ui(status=self.i18n.t("language_changed_status"))

    def _on_language_preset_changed(self) -> None:
        preset = self.language_preset_var.get()
        ocr = self.config_data.setdefault("ocr", {})
        ocr["language_preset"] = preset
        if preset in LANGUAGE_PRESETS:
            ocr["rapid_lang"] = LANGUAGE_PRESETS[preset]["rapid_lang"]
            ocr["selected_languages"] = LANGUAGE_PRESETS[preset]["languages"]
            ocr["mixed_language_mode"] = len(LANGUAGE_PRESETS[preset]["languages"]) > 1 or bool(self.mixed_var.get())
        self.project.data.setdefault("settings", self.config_data)["ocr"] = ocr
        self._set_status(self.i18n.t("ocr_language_preset_status", preset=preset))

    def _on_mixed_changed(self) -> None:
        self.config_data.setdefault("ocr", {})["mixed_language_mode"] = bool(self.mixed_var.get())

    def get_current_file(self) -> dict[str, Any] | None:
        return self.project.find_file(self.current_file_id) if self.current_file_id else None

    def get_current_page(self) -> dict[str, Any] | None:
        return self.project.find_page(self.current_file_id, self.current_page_index) if self.current_file_id else None

    def save_current_text_to_page(self) -> None:
        page = self.get_current_page()
        if page is not None:
            page["final_text"] = self.text_editor.get("1.0", tk.END).rstrip("\n")
            page["timestamp"] = now_iso()

    def on_text_modified(self, event=None) -> None:
        if self.text_editor.edit_modified():
            page = self.get_current_page()
            if page is not None:
                page["final_text"] = self.text_editor.get("1.0", tk.END).rstrip("\n")
            self.text_editor.edit_modified(False)

    # ---------- project operations ----------
    def new_project(self) -> None:
        name = simpledialog.askstring(self.i18n.t("new_project_title"), self.i18n.t("new_project_prompt"), initialvalue="BFSU_ProofLens_Project", parent=self)
        if not name:
            return
        self.project.new_project(project_name=name, config=self.config_data)
        self.current_file_id = ""
        self.current_page_index = 0
        self.refresh_file_tree()
        self.clear_view()
        self._refresh_title()
        self._set_status(self.i18n.t("new_project_status"))

    def open_project(self) -> None:
        path = filedialog.askopenfilename(title=self.i18n.t("open_project_title"), filetypes=[("BFSU ProofLens Project", f"*{PROJECT_EXT}"), (self.i18n.t("json"), "*.json"), (self.i18n.t("all_files"), "*.*")])
        if not path:
            return
        try:
            current_ui_language = self.i18n.language
            self.project.open_project(path)
            self.config_data = self.project.data.get("settings", self.config_data)
            # UI language is treated as a user preference rather than a project-specific setting.
            self.config_data["ui_language"] = current_ui_language
            self.project.data["settings"] = self.config_data
            self.refresh_file_tree()
            self._refresh_title()
            self._set_status(self.i18n.t("open_project_status", path=path))
            logger.info("Project opened: %s", path)
        except Exception as exc:
            logger.exception("Open project failed")
            messagebox.showerror(self.i18n.t("open_failed"), str(exc), parent=self)

    def save_project(self) -> None:
        self.save_current_text_to_page()
        if not self.project.project_path:
            self.save_project_as()
            return
        try:
            path = self.project.save_project()
            self.config_manager.save(self.config_data)
            self._set_status(self.i18n.t("save_project_status", path=path))
            logger.info("Project saved: %s", path)
        except Exception as exc:
            logger.exception("Save project failed")
            messagebox.showerror(self.i18n.t("save_failed"), str(exc), parent=self)

    def save_project_as(self) -> None:
        self.save_current_text_to_page()
        default_dir = self.config_data.get("default_project_dir") or str(runtime_root())
        Path(default_dir).mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(title=self.i18n.t("save_as_title"), initialdir=default_dir, defaultextension=PROJECT_EXT, filetypes=[("BFSU ProofLens Project", f"*{PROJECT_EXT}")])
        if not path:
            return
        try:
            saved = self.project.save_project(path)
            self.config_data["last_project_path"] = saved
            self.config_manager.save(self.config_data)
            self._refresh_title()
            self._set_status(self.i18n.t("save_project_status", path=saved))
        except Exception as exc:
            logger.exception("Save as failed")
            messagebox.showerror(self.i18n.t("save_failed"), str(exc), parent=self)

    def close_project(self) -> None:
        if messagebox.askyesno(self.i18n.t("close_project_confirm_title"), self.i18n.t("close_project_confirm_message"), parent=self):
            self.project.close_project()
            self.current_file_id = ""
            self.current_page_index = 0
            self.refresh_file_tree()
            self.clear_view()
            self._refresh_title()
            self._set_status(self.i18n.t("close_project_status"))

    def on_exit(self) -> None:
        self.save_current_text_to_page()
        self.destroy()

    # ---------- file/page operations ----------
    def _ask_import_paths(self, title_key: str = "import_files_title") -> list[str]:
        patterns = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_FILES))
        paths = filedialog.askopenfilenames(
            title=self.i18n.t(title_key),
            filetypes=[
                (self.i18n.t("supported_files"), patterns),
                ("PDF", "*.pdf"),
                (self.i18n.t("images"), "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"),
                (self.i18n.t("all_files"), "*.*"),
            ],
        )
        return [str(p) for p in paths]

    def import_files(self) -> None:
        if not self._ensure_project_for_import():
            return
        selected_paths = self._ask_import_paths()
        if selected_paths:
            self._start_import_paths(selected_paths, append_to_file_id=None)

    def _ensure_project_for_import(self) -> bool:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return False
        if not self.project.data.get("project_name"):
            self.new_project()
        return bool(self.project.data.get("project_name"))

    def add_files_or_pages(self) -> None:
        """Bottom + button: add new files, or append pages when a file is selected."""
        if not self._ensure_project_for_import():
            return
        info = self._selected_tree_info()
        append_to_file_id = info[1] if info and info[0] in {"file", "page"} else None
        if append_to_file_id:
            file_entry = self.project.find_file(append_to_file_id)
            file_name = file_entry.get("file_name", "") if file_entry else ""
            use_append = messagebox.askyesno(
                self.i18n.t("import_files_title"),
                self.i18n.t("tree_add_mode_question", file=file_name),
                parent=self,
            )
            if not use_append:
                append_to_file_id = None
        selected_paths = self._ask_import_paths()
        if selected_paths:
            self._start_import_paths(selected_paths, append_to_file_id=append_to_file_id)

    def add_pages_to_selected_file(self) -> None:
        if not self._ensure_project_for_import():
            return
        info = self._selected_tree_info()
        if not info or info[0] not in {"file", "page"}:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("tree_no_file_selected"), parent=self)
            return
        append_to_file_id = info[1]
        selected_paths = self._ask_import_paths()
        if selected_paths:
            self._start_import_paths(selected_paths, append_to_file_id=append_to_file_id)

    def _start_import_paths(self, selected_paths: list[str], append_to_file_id: str | None = None) -> None:
        temp_root = writable_path("temp")
        dpi = int(self.config_data.get("ocr", {}).get("pdf_dpi", 200))
        task_label = self.i18n.t("import_task_label")
        first_file = Path(selected_paths[0]).name if selected_paths else "-"

        def _format_import_progress(raw: dict[str, Any]) -> dict[str, Any]:
            file_name = str(raw.get("file") or raw.get("file_name") or "-")
            file_index = int(raw.get("file_index") or 1)
            file_total = int(raw.get("file_total") or max(1, len(selected_paths)))
            page = int(raw.get("page") or 0)
            page_total = int(raw.get("total") or 0)
            stage = str(raw.get("stage") or "")
            base_value = ((file_index - 1) / max(1, file_total)) * 90
            span = 90 / max(1, file_total)
            value = base_value
            if page_total > 0 and page > 0:
                value = base_value + (page / page_total) * span
            elif stage in {"file_done", "file_error"}:
                value = base_value + span

            if stage.startswith("render_page") and page_total > 0:
                task = self.i18n.t("import_task_rendering", file=file_name, page=page, total=page_total)
            elif stage.startswith("preview_page") and page_total > 0:
                task = self.i18n.t("import_task_rendering", file=file_name, page=page, total=page_total)
            elif stage == "file_error":
                task = self.i18n.t("import_task_failed_file", file=file_name, error=raw.get("error", ""))
            else:
                task = self.i18n.t("import_task_running", file=file_name, index=file_index, total=file_total)
            return {"value": value, "task": task, "file": file_name, "indeterminate": False}

        def worker(progress_cb: Any) -> dict[str, Any]:
            ctx = multiprocessing.get_context("spawn")
            progress_queue = ctx.Queue()
            payload = {
                "paths": selected_paths,
                "temp_root": str(temp_root),
                "dpi": dpi,
                "preview_max_side": int(self.config_data.get("ocr", {}).get("preview_max_side", 1800) or 1800),
            }
            process = ctx.Process(target=import_files_process_worker, args=(payload, progress_queue))
            process.start()
            result: dict[str, Any] | None = None
            try:
                while True:
                    try:
                        message = progress_queue.get(timeout=0.12)
                    except queue.Empty:
                        if not process.is_alive():
                            process.join(timeout=0.2)
                            if process.exitcode not in (0, None) and result is None:
                                raise RuntimeError(self.i18n.t("import_process_failed", code=process.exitcode))
                            if result is not None:
                                break
                        continue

                    kind = message.get("kind")
                    payload_msg = message.get("payload") or {}
                    if kind == "progress":
                        progress_cb(_format_import_progress(payload_msg))
                    elif kind == "result":
                        result = dict(payload_msg)
                        break
                    elif kind == "error":
                        detail = payload_msg.get("traceback") or payload_msg.get("exception") or "Unknown import error"
                        raise RuntimeError(str(detail))
                process.join(timeout=2.0)
                try:
                    progress_queue.close()
                    progress_queue.join_thread()
                except Exception:
                    pass
                return result or {"entries": [], "errors": [], "count": 0}
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2.0)
                try:
                    progress_queue.close()
                except Exception:
                    pass

        def on_success(result: dict[str, Any]) -> None:
            self.after(1, lambda r=result, target=append_to_file_id: self._finish_import_result(r, append_to_file_id=target))

        def on_error(exc: Exception) -> None:
            messagebox.showerror(self.i18n.t("open_failed"), str(exc), parent=self)
            self._set_status(str(exc))

        self._start_background_task(task_label, first_file, worker, on_success, on_error)

    def _finish_import_result(self, result: dict[str, Any], append_to_file_id: str | None = None) -> None:
        entries = result.get("entries", []) or []
        errors = result.get("errors", []) or []
        appended_count = 0
        selected_after: tuple[str, int] | None = None

        if append_to_file_id:
            target = self.project.find_file(append_to_file_id)
            if target is not None:
                pages = target.setdefault("pages", [])
                for entry in entries:
                    for page in entry.get("pages", []) or []:
                        new_page = dict(page)
                        new_page["source_file_name"] = entry.get("file_name", "")
                        new_page["source_file_path"] = entry.get("file_path", "")
                        pages.append(new_page)
                        appended_count += 1
                self._renumber_pages(target)
                if appended_count:
                    selected_after = (append_to_file_id, max(0, len(pages) - appended_count))
                msg = self.i18n.t("tree_add_page_status", count=appended_count, file=target.get("file_name", ""))
            else:
                append_to_file_id = None
                msg = self.i18n.t("import_done_status", count=len(entries))
        else:
            msg = self.i18n.t("import_done_status", count=len(entries))

        if not append_to_file_id:
            for entry in entries:
                self.project.add_file(entry)
            if entries and not self.current_file_id:
                selected_after = (self.project.data.get("files", [])[0].get("id"), 0)

        self.refresh_file_tree()
        if errors:
            msg += "\n\n" + "\n".join(str(x) for x in errors[:5])
            messagebox.showwarning(self.i18n.t("partial_import_failed"), msg, parent=self)
        self._set_status(msg)

        # Do not synchronously decode/render a PDF page inside the import
        # completion callback.  Select the first/new page shortly afterwards; the
        # preview itself is loaded asynchronously by show_image().
        if selected_after:
            def _select_imported_page() -> None:
                try:
                    self.select_page(selected_after[0], selected_after[1])
                except Exception as exc:
                    logger.exception("Auto-select imported page failed")
                    self._set_status(self.i18n.t("image_preview_failed", error=exc))
            self.after(120, _select_imported_page)

    def _page_status_label(self, page: dict[str, Any]) -> tuple[str, str]:
        ocr_status = page.get("ocr_status", "pending")
        llm_status = page.get("proofread_status", "pending")
        if ocr_status == "processing" or llm_status == "processing":
            return "⏳", self.i18n.t("status_processing")
        if ocr_status == "failed" or llm_status == "failed":
            return "❌", self.i18n.t("status_failed")
        if llm_status in {"done", "llm_ocr_done"}:
            return "✅", self.i18n.t("status_llm_done")
        if ocr_status == "done":
            return "✅", self.i18n.t("status_ocr_done")
        if ocr_status == "text_layer":
            return "✅", self.i18n.t("status_text_layer_done")
        return "○", self.i18n.t("status_pending")

    def _file_status_label(self, file_entry: dict[str, Any]) -> tuple[str, int, int]:
        pages = file_entry.get("pages", [])
        total = len(pages)
        done = sum(1 for page in pages if page.get("ocr_status") in {"done", "text_layer"} or page.get("proofread_status") in {"done", "llm_ocr_done"})
        has_processing = any(page.get("ocr_status") == "processing" or page.get("proofread_status") == "processing" for page in pages)
        has_failed = any(page.get("ocr_status") == "failed" or page.get("proofread_status") == "failed" for page in pages)
        if total and done == total:
            marker = "✅ "
        elif has_processing:
            marker = "⏳ "
        elif has_failed:
            marker = "⚠ "
        else:
            marker = ""
        return marker, done, total

    def refresh_file_tree(self) -> None:
        self.tree_files.delete(*self.tree_files.get_children())
        for f in self.project.data.get("files", []):
            fid = f.get("id")
            marker, done, total = self._file_status_label(f)
            file_text = self.i18n.t("file_tree_label", marker=marker, file=f.get("file_name", "Untitled"), done=done, total=total)
            # Expanding very large PDFs automatically can make Treeview updates
            # feel frozen. Keep large files collapsed until the user expands them.
            pages = f.get("pages", [])
            auto_open = (fid == self.current_file_id) or (len(pages) <= 120)
            node = self.tree_files.insert("", tk.END, iid=f"file:{fid}", text=file_text, open=auto_open)
            for i, p in enumerate(pages):
                marker, status = self._page_status_label(p)
                page_text = self.i18n.t("page_tree_label", marker=marker, page=p.get("page_no", i+1), status=status)
                self.tree_files.insert(node, tk.END, iid=f"page:{fid}:{i}", text=page_text)

    def _selected_tree_iid(self) -> str:
        sel = self.tree_files.selection() if hasattr(self, "tree_files") else ()
        return str(sel[0]) if sel else ""

    def _selected_tree_info(self, iid: str | None = None) -> tuple[str, str, int | None] | None:
        iid = iid or self._selected_tree_iid()
        if not iid:
            return None
        if iid.startswith("page:"):
            _, fid, idx = iid.split(":", 2)
            return "page", fid, int(idx)
        if iid.startswith("file:"):
            _, fid = iid.split(":", 1)
            return "file", fid, None
        return None

    def on_tree_context_menu(self, event) -> None:
        iid = self.tree_files.identify_row(event.y)
        if iid:
            # Preserve an existing multi-selection when the user right-clicks
            # inside it.  If the click is outside the current selection, make
            # the clicked item the single operation target.
            current_selection = set(self.tree_files.selection())
            if iid not in current_selection:
                self.tree_files.selection_set(iid)
            self.tree_files.focus(iid)
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label=self.i18n.t("tree_open"), command=self.open_selected_tree_item)
        menu.add_command(label=self.i18n.t("tree_open_source"), command=self.open_selected_source_location)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("tree_add_files"), command=self.import_files)
        menu.add_command(label=self.i18n.t("tree_add_pages"), command=self.add_pages_to_selected_file)
        menu.add_separator()
        menu.add_command(label=self.i18n.t("tree_delete"), command=self.delete_selected_tree_item)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def open_selected_tree_item(self) -> None:
        info = self._selected_tree_info()
        if not info:
            return
        kind, fid, page_idx = info
        self.select_page(fid, int(page_idx or 0))

    def open_selected_source_location(self) -> None:
        info = self._selected_tree_info()
        if not info:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("tree_no_file_selected"), parent=self)
            return
        _, fid, _page_idx = info
        file_entry = self.project.find_file(fid)
        if not file_entry:
            return
        source = file_entry.get("file_path") or ""
        if source and Path(source).exists():
            open_folder(source)
        else:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("tree_source_missing", path=source or "-"), parent=self)

    def _renumber_pages(self, file_entry: dict[str, Any]) -> None:
        for idx, page in enumerate(file_entry.get("pages", []) or [], start=1):
            page["page_no"] = idx

    def _on_tree_delete_key(self, event=None):
        self.delete_selected_tree_item()
        return "break"

    def delete_selected_tree_item(self) -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        selected_iids = list(self.tree_files.selection()) if hasattr(self, "tree_files") else []
        if not selected_iids:
            iid = self._selected_tree_iid()
            selected_iids = [iid] if iid else []
        if not selected_iids:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("tree_no_file_selected"), parent=self)
            return

        parsed: list[tuple[str, str, int | None]] = []
        selected_file_ids: set[str] = set()
        for iid in selected_iids:
            if not iid:
                continue
            parts = str(iid).split(":")
            if len(parts) >= 2 and parts[0] == "file":
                fid = parts[1]
                parsed.append(("file", fid, None))
                selected_file_ids.add(fid)
            elif len(parts) >= 3 and parts[0] == "page":
                try:
                    parsed.append(("page", parts[1], int(parts[2])))
                except Exception:
                    continue
        if not parsed:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("tree_no_file_selected"), parent=self)
            return

        # If a whole file and one of its pages are both selected, the file-level
        # deletion subsumes the page-level deletion.
        page_targets: dict[str, set[int]] = {}
        for kind, fid, page_idx in parsed:
            if kind == "page" and fid not in selected_file_ids and page_idx is not None:
                page_targets.setdefault(fid, set()).add(page_idx)

        files = self.project.data.setdefault("files", [])
        file_name_by_id = {f.get("id"): f.get("file_name", "") for f in files}
        file_count = sum(1 for fid in selected_file_ids if fid in file_name_by_id)
        page_count = 0
        for fid, idxs in page_targets.items():
            file_entry = self.project.find_file(fid)
            pages = file_entry.get("pages", []) if file_entry else []
            page_count += sum(1 for idx in idxs if 0 <= idx < len(pages))
        if file_count <= 0 and page_count <= 0:
            return

        if file_count == 1 and page_count == 0:
            fid = next(iter(selected_file_ids))
            if not messagebox.askyesno(self.i18n.t("tree_delete_file_title"), self.i18n.t("tree_delete_file_message", file=file_name_by_id.get(fid, "")), parent=self):
                return
        elif file_count == 0 and page_count == 1:
            fid, idxs = next(iter(page_targets.items()))
            idx = next(iter(idxs))
            file_entry = self.project.find_file(fid) or {}
            pages = file_entry.get("pages", []) or []
            page_no = pages[idx].get("page_no", idx + 1) if 0 <= idx < len(pages) else idx + 1
            if not messagebox.askyesno(self.i18n.t("tree_delete_page_title"), self.i18n.t("tree_delete_page_message", file=file_entry.get("file_name", ""), page=page_no), parent=self):
                return
        else:
            if not messagebox.askyesno(
                self.i18n.t("tree_delete_multiple_title"),
                self.i18n.t("tree_delete_multiple_message", files=file_count, pages=page_count),
                parent=self,
            ):
                return

        self.save_current_text_to_page()

        # Delete whole files first, from the tail of the list to keep indices stable.
        for pos in range(len(files) - 1, -1, -1):
            if files[pos].get("id") in selected_file_ids:
                del files[pos]

        # Then delete selected pages in remaining files.  Page indices are also
        # removed in descending order to avoid shifting later targets.
        for fid, indices in page_targets.items():
            file_entry = self.project.find_file(fid)
            if not file_entry:
                continue
            pages = file_entry.setdefault("pages", [])
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(pages):
                    del pages[idx]
            self._renumber_pages(file_entry)

        # Drop files that became empty after page-level deletion.
        files[:] = [f for f in files if f.get("pages")]

        if self.current_file_id in selected_file_ids or not self.project.find_file(self.current_file_id):
            self.current_file_id = ""
            self.current_page_index = 0
        elif self.current_file_id in page_targets:
            current_file = self.project.find_file(self.current_file_id)
            pages = current_file.get("pages", []) if current_file else []
            if pages:
                self.current_page_index = min(self.current_page_index, len(pages) - 1)
            else:
                self.current_file_id = ""
                self.current_page_index = 0

        self.project.data["updated_at"] = now_iso()
        self.refresh_file_tree()
        self._select_best_page_after_tree_change()
        self._set_status(self.i18n.t("tree_delete_status"))

    def _select_best_page_after_tree_change(self) -> None:
        files = self.project.data.get("files", [])
        if self.current_file_id:
            current = self.project.find_file(self.current_file_id)
            if current and current.get("pages"):
                self.select_page(self.current_file_id, min(self.current_page_index, len(current.get("pages", [])) - 1))
                return
        if files and files[0].get("pages"):
            self.select_page(files[0].get("id"), 0)
        else:
            self.current_file_id = ""
            self.current_page_index = 0
            self.clear_view()

    def on_tree_select(self, event=None) -> None:
        if getattr(self, "_suppress_tree_select", False):
            return
        sel = self.tree_files.selection()
        if not sel:
            return
        iid = sel[0]
        if iid.startswith("page:"):
            _, fid, idx = iid.split(":", 2)
            # The selection already came from the tree; do not rewrite it.
            # This keeps Ctrl/Shift multi-selection intact for batch deletion.
            self.select_page(fid, int(idx), sync_tree_selection=False)
        elif iid.startswith("file:"):
            _, fid = iid.split(":", 1)
            # Show the first page for preview, but keep the file node selected.
            # Otherwise deleting immediately after selecting a file would delete
            # page 1 rather than the whole file.
            self.select_page(fid, 0, sync_tree_selection=False)

    def select_page(self, file_id: str, page_index: int, *, sync_tree_selection: bool = True) -> None:
        self.save_current_text_to_page()
        page = self.project.find_page(file_id, page_index)
        if page is None:
            return
        self.current_file_id = file_id
        self.current_page_index = page_index
        iid = f"page:{file_id}:{page_index}"
        if sync_tree_selection and self.tree_files.exists(iid):
            self._suppress_tree_select = True
            try:
                self.tree_files.selection_set(iid)
                self.tree_files.focus(iid)
                self.tree_files.see(iid)
            finally:
                self.after_idle(lambda: setattr(self, "_suppress_tree_select", False))
        self.display_page(page)

    def display_page(self, page: dict[str, Any]) -> None:
        self.zoom = 1.0
        self.rotation = 0
        self.show_image(page.get("image_path", ""))
        self.text_editor.delete("1.0", tk.END)
        text = page.get("final_text") or page.get("corrected_text") or page.get("ocr_text") or ""
        self.text_editor.insert("1.0", text)
        self.text_editor.edit_modified(False)
        self.suggestion_panel.set_suggestions(page.get("suggestions", []))
        file_entry = self.get_current_file()
        file_name = file_entry.get("file_name", "") if file_entry else ""
        if hasattr(self, "current_file_var") and not self._busy:
            self.current_file_var.set(self.i18n.t("current_file_label", file=file_name or "-"))
        self._set_status(self.i18n.t("current_page_status", file=file_name, page=page.get("page_no", ""), ocr=page.get("ocr_status", ""), llm=page.get("proofread_status", "")))

    def clear_view(self) -> None:
        self.canvas.delete("all")
        self.text_editor.delete("1.0", tk.END)
        self.suggestion_panel.set_suggestions([])

    def show_image(self, path: str) -> None:
        self.canvas.delete("all")
        page = self.get_current_page()
        display_path = str((page or {}).get("preview_path") or path)
        if not display_path or not Path(display_path).exists():
            self.canvas.create_text(20, 20, anchor=tk.NW, text=self.i18n.t("no_preview"), fill="#666")
            return

        self._preview_counter += 1
        preview_id = self._preview_counter
        self._active_preview_id = preview_id
        zoom = float(self.zoom)
        rotation = int(self.rotation)
        max_side = int(self.config_data.get("ocr", {}).get("preview_max_side", 1800) or 1800)
        self.canvas.create_text(20, 20, anchor=tk.NW, text=self.i18n.t("preview_loading"), fill="#666")

        def runner() -> None:
            try:
                from PIL import Image  # type: ignore
                with Image.open(display_path) as img:
                    img = img.convert("RGB")
                    if rotation:
                        img = img.rotate(-rotation, expand=True)
                    if max(img.size) > max_side:
                        img.thumbnail((max_side, max_side))
                    w, h = img.size
                    target_size = (max(1, int(w * zoom)), max(1, int(h * zoom)))
                    if target_size != img.size:
                        img = img.resize(target_size)
                    result = img.copy()
                self._preview_queue.put((preview_id, "success", result))
            except Exception as exc:
                self._preview_queue.put((preview_id, "error", {"exception": exc, "traceback": traceback.format_exc()}))

        threading.Thread(target=runner, name=f"BFSUProofLensPreview-{preview_id}", daemon=True).start()
        self.after(50, self._poll_preview_queue)

    def _poll_preview_queue(self) -> None:
        handled = False
        while True:
            try:
                preview_id, kind, payload = self._preview_queue.get_nowait()
            except queue.Empty:
                break
            handled = True
            if preview_id != self._active_preview_id:
                continue
            if kind == "success":
                try:
                    from PIL import ImageTk  # type: ignore
                    img = payload
                    self._image_original = img.copy()
                    self._image_photo = ImageTk.PhotoImage(img)
                    self.canvas.delete("all")
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self._image_photo)
                    self.canvas.configure(scrollregion=(0, 0, img.width, img.height))
                except Exception as exc:
                    logger.exception("Image preview PhotoImage creation failed")
                    self.canvas.delete("all")
                    self.canvas.create_text(20, 20, anchor=tk.NW, text=self.i18n.t("image_preview_failed", error=exc), fill="red")
            else:
                exc = payload.get("exception") if isinstance(payload, dict) else payload
                tb = payload.get("traceback") if isinstance(payload, dict) else ""
                logger.error("Image preview failed: %s\n%s", exc, tb)
                self.canvas.delete("all")
                self.canvas.create_text(20, 20, anchor=tk.NW, text=self.i18n.t("image_preview_failed", error=exc), fill="red")
        if self._active_preview_id is not None and not handled:
            self.after(50, self._poll_preview_queue)

    def change_zoom(self, factor: float) -> None:
        page = self.get_current_page()
        if not page:
            return
        self.zoom = max(0.1, min(5.0, self.zoom * factor))
        self.show_image(page.get("image_path", ""))

    def fit_image(self) -> None:
        page = self.get_current_page()
        if not page or not page.get("image_path"):
            return
        try:
            from PIL import Image  # type: ignore
            display_path = page.get("preview_path") or page.get("image_path")
            img = Image.open(display_path)
            cw = max(1, self.canvas.winfo_width() - 20)
            ch = max(1, self.canvas.winfo_height() - 20)
            self.zoom = min(cw / img.width, ch / img.height, 1.0)
            self.show_image(page.get("image_path"))
        except Exception:
            pass

    def rotate_preview(self) -> None:
        page = self.get_current_page()
        if not page:
            return
        self.rotation = (self.rotation + 90) % 360
        self.show_image(page.get("image_path", ""))

    def move_page(self, delta: int) -> None:
        f = self.get_current_file()
        if not f:
            return
        pages = f.get("pages", [])
        new_idx = self.current_page_index + delta
        if 0 <= new_idx < len(pages):
            self.select_page(f.get("id"), new_idx)

    # ---------- OCR / LLM ----------
    def _language_hint(self) -> str:
        ocr = self.config_data.get("ocr", {})
        selected = ocr.get("selected_languages") or []
        preset = ocr.get("language_preset", "")
        mixed = ocr.get("mixed_language_mode", False)
        return f"preset={preset}; selected={','.join(selected)}; mixed={mixed}"

    def _collect_page_jobs(self, scope: str) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        files = self.project.data.get("files", [])
        if scope == "current_page":
            f = self.get_current_file()
            page = self.get_current_page()
            if f and page:
                jobs.append({
                    "file_id": f.get("id"),
                    "file_name": f.get("file_name", ""),
                    "page_index": self.current_page_index,
                    "page_no": page.get("page_no", self.current_page_index + 1),
                    "image_path": page.get("image_path", ""),
                    "page": page,
                })
            return jobs
        if scope == "current_file":
            f = self.get_current_file()
            files = [f] if f else []
        for f in files:
            if not f:
                continue
            for i, page in enumerate(f.get("pages", [])):
                jobs.append({
                    "file_id": f.get("id"),
                    "file_name": f.get("file_name", ""),
                    "page_index": i,
                    "page_no": page.get("page_no", i + 1),
                    "image_path": page.get("image_path", ""),
                    "page": page,
                })
        return jobs

    def _mark_jobs_processing(self, jobs: list[dict[str, Any]], operation: str) -> None:
        for job in jobs:
            page = job.get("page") or self.project.find_page(job.get("file_id", ""), int(job.get("page_index", 0)))
            if not page:
                continue
            if operation in {"rapidocr", "easyocr"}:
                page["ocr_status"] = "processing"
            elif operation == "llm_ocr":
                page["ocr_status"] = "processing"
                page["proofread_status"] = "processing"
            elif operation == "llm_proofread":
                page["proofread_status"] = "processing"
            page["processing_task"] = operation
            page["timestamp"] = now_iso()
        self.refresh_file_tree()

    def _scope_label(self, scope: str) -> str:
        if scope == "current_page":
            return self.i18n.t("export_scope_current_page")
        if scope == "current_file":
            return self.i18n.t("export_scope_current_file")
        return self.i18n.t("export_scope_project")

    def _normalise_worker_count(self, value: Any, job_count: int, maximum: int = 8) -> int:
        try:
            workers = int(value)
        except Exception:
            workers = 1
        workers = max(1, min(maximum, workers))
        return max(1, min(job_count or 1, workers))

    def _resolve_model_download_allowed(self, engine: str) -> bool:
        """Resolve whether an OCR backend may auto-download missing models."""
        ocr = self.config_data.setdefault("ocr", {})
        policy = str(ocr.get("model_download_policy", "ask") or "ask").lower()
        if policy == "auto":
            return True
        if policy == "manual":
            self._set_status(self.i18n.t("model_download_manual_status"))
            return False
        if engine in self._model_download_confirmed_this_session:
            return bool(self._model_download_confirmed_this_session[engine])
        ok = messagebox.askyesno(
            self.i18n.t("model_download_title"),
            self.i18n.t("model_download_ask", engine=engine),
            parent=self,
        )
        self._model_download_confirmed_this_session[engine] = bool(ok)
        return bool(ok)

    def _module_available(self, module_name: str) -> bool:
        try:
            return importlib.util.find_spec(module_name) is not None
        except Exception:
            return False

    def _preflight_ocr_engine(self, operation: str) -> bool:
        """Check optional OCR dependencies before launching a long batch."""
        if operation == "rapidocr":
            if not self._module_available("rapidocr") or not self._module_available("onnxruntime"):
                messagebox.showerror(
                    self.i18n.t("ocr_dependency_missing_title"),
                    self.i18n.t("rapidocr_dependency_missing_message"),
                    parent=self,
                )
                self._set_status(self.i18n.t("ocr_dependency_missing_status"))
                return False
        elif operation == "easyocr":
            if not self._module_available("easyocr"):
                messagebox.showerror(
                    self.i18n.t("ocr_dependency_missing_title"),
                    self.i18n.t("easyocr_dependency_missing_message"),
                    parent=self,
                )
                self._set_status(self.i18n.t("ocr_dependency_missing_status"))
                return False
        return True

    def _preflight_llm(self, mode: str) -> bool:
        """Check LLM configuration before starting threaded API calls."""
        llm = self.config_data.get("llm", {})
        api_key = (llm.get("api_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
        if not api_key:
            messagebox.showerror(self.i18n.t("llm_config_error_title"), self.i18n.t("llm_api_key_missing_message"), parent=self)
            self._set_status(self.i18n.t("llm_config_error_status"))
            return False
        if not str(llm.get("model") or "").strip():
            messagebox.showerror(self.i18n.t("llm_config_error_title"), self.i18n.t("llm_model_missing_message"), parent=self)
            self._set_status(self.i18n.t("llm_config_error_status"))
            return False
        if not self._module_available("openai"):
            messagebox.showerror(self.i18n.t("llm_config_error_title"), self.i18n.t("openai_dependency_missing_message"), parent=self)
            self._set_status(self.i18n.t("llm_config_error_status"))
            return False
        if mode == "llm_ocr" and not bool(llm.get("allow_send_image", True)):
            messagebox.showerror(self.i18n.t("llm_config_error_title"), self.i18n.t("llm_image_disabled_message"), parent=self)
            self._set_status(self.i18n.t("llm_config_error_status"))
            return False
        if mode == "llm_proofread" and not bool(llm.get("allow_send_text", True)):
            messagebox.showerror(self.i18n.t("llm_config_error_title"), self.i18n.t("llm_text_disabled_message"), parent=self)
            self._set_status(self.i18n.t("llm_config_error_status"))
            return False
        return True

    def _format_batch_error_details(self, result: dict[str, Any], max_items: int = 5) -> str:
        errors = result.get("errors") or []
        if not errors:
            return ""
        lines = []
        for item in errors[:max_items]:
            if isinstance(item, dict):
                file_name = item.get("file") or item.get("file_name") or "-"
                page = item.get("page") or item.get("page_no") or "-"
                error = item.get("error") or ""
                lines.append(f"- {file_name}, page {page}: {error}")
            else:
                lines.append(f"- {item}")
        if len(errors) > max_items:
            lines.append(self.i18n.t("batch_more_errors", count=len(errors) - max_items))
        return "\n".join(lines)

    def run_ocr_current(self) -> None:
        self.run_ocr_scope("current_page")

    def run_ocr_scope(self, scope: str = "current_page", engine_override: str | None = None) -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        if not self.project.data.get("files"):
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("select_page_first"), parent=self)
            return
        self.save_current_text_to_page()
        backend_mode = engine_override or self.config_data.get("ocr", {}).get("backend", "rapidocr")
        if backend_mode == "llm_ocr":
            self.run_llm_ocr_scope(scope)
            return
        if backend_mode == "hybrid":
            backend_mode = "rapidocr"
        if backend_mode == ("paddle" + "ocr"):
            backend_mode = "rapidocr"
        if backend_mode not in {"rapidocr", "easyocr"}:
            backend_mode = "rapidocr"
        operation = "easyocr" if backend_mode == "easyocr" else "rapidocr"
        jobs = self._collect_page_jobs(scope)
        if not jobs:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("batch_no_pages"), parent=self)
            return

        ocr_options = dict(self.config_data.get("ocr", {}))
        ocr_options["language_preset"] = self.language_preset_var.get()
        ocr_options["mixed_language_mode"] = bool(self.mixed_var.get())

        # For born-digital/text-based PDFs, use the embedded text layer by default.
        # This is much faster, avoids RapidOCR model downloads, and preserves
        # paragraphs better than re-OCRing a rendered page image. Users can turn
        # this off in Settings when they deliberately need image-based OCR.
        if bool(ocr_options.get("prefer_pdf_text_layer", True)):
            remaining_jobs: list[dict[str, Any]] = []
            text_layer_count = 0
            for job in jobs:
                page = job.get("page") or {}
                embedded_text = str(page.get("embedded_text") or "").strip()
                if embedded_text:
                    text_layer_count += 1
                    update = {
                        "operation": operation if 'operation' in locals() else "rapidocr",
                        "success": True,
                        "result": {
                            "text": embedded_text,
                            "blocks": [],
                            "engine": "pdf_text_layer",
                            "language": "embedded",
                            "elapsed_seconds": 0.0,
                        },
                        "file_id": job.get("file_id"),
                        "page_index": job.get("page_index"),
                    }
                    self._apply_page_update(update)
                else:
                    remaining_jobs.append(job)
            if text_layer_count and not remaining_jobs:
                msg = self.i18n.t("pdf_text_layer_used_status", count=text_layer_count)
                self._set_status(msg)
                messagebox.showinfo(self.i18n.t("ocr_done_title"), msg, parent=self)
                return
            if text_layer_count:
                jobs = remaining_jobs

        max_workers = self._normalise_worker_count(ocr_options.get("max_workers", 1), len(jobs))
        parallel_backend = str(ocr_options.get("parallel_backend", "thread")).lower()
        if not self._preflight_ocr_engine(operation):
            return
        ocr_options["download_enabled"] = self._resolve_model_download_allowed("EasyOCR" if operation == "easyocr" else "RapidOCR")
        if operation == "easyocr" and bool(ocr_options.get("easyocr_light_mode", True)):
            # EasyOCR light/demo mode deliberately keeps one cached Reader to reduce RAM/CPU load.
            max_workers = 1
            parallel_backend = "thread"
        if bool(ocr_options.get("use_gpu", False)) and parallel_backend == "process":
            # Avoid multiple GPU processes competing for the same device by default.
            parallel_backend = "thread"
        if operation == "easyocr" and parallel_backend == "process":
            # EasyOCR relies on PyTorch; process mode often increases model loading time and memory.
            parallel_backend = "thread"
        use_process = parallel_backend == "process" and max_workers > 1
        worker_func = easyocr_recognize_page if operation == "easyocr" else rapidocr_recognize_page
        self._mark_jobs_processing(jobs, operation)
        task_key = "task_easyocr_batch" if operation == "easyocr" else "task_rapidocr_batch"
        task_label = self.i18n.t(task_key, scope=self._scope_label(scope), count=len(jobs), workers=max_workers)
        first_file = jobs[0].get("file_name", "")

        def worker(progress_cb: Any) -> dict[str, Any]:
            started = time.perf_counter()
            completed = 0
            failed = 0
            errors: list[dict[str, Any]] = []
            executor_cls = ProcessPoolExecutor if use_process else ThreadPoolExecutor
            progress_cb({"value": 2, "task": self.i18n.t("task_batch_running", task=task_label), "file": first_file, "indeterminate": False})
            if operation == "rapidocr":
                def _rapid_progress(payload: dict[str, Any]) -> None:
                    progress_cb({
                        "value": float(payload.get("value", 3)),
                        "task": str(payload.get("message") or self.i18n.t("rapidocr_model_checking")),
                        "file": first_file,
                        "indeterminate": True,
                    })
                progress_cb({"value": 3, "task": self.i18n.t("rapidocr_model_checking"), "file": first_file, "indeterminate": True})
                prepare_rapidocr_models(ocr_options, progress_callback=_rapid_progress)
                progress_cb({"value": 5, "task": self.i18n.t("rapidocr_model_ready"), "file": first_file, "indeterminate": False})
            future_map = {}
            try:
                with executor_cls(max_workers=max_workers) as executor:
                    for job in jobs:
                        payload = {"image_path": job.get("image_path", ""), "options": ocr_options}
                        future = executor.submit(worker_func, payload)
                        future_map[future] = job
                    for future in as_completed(future_map):
                        job = future_map[future]
                        value = 5 + ((completed + failed + 1) / len(jobs)) * 85
                        try:
                            result = future.result()
                            completed += 1
                            update = {"operation": operation, "success": True, "result": result, "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                            status_text = self.i18n.t("task_batch_page_done", file=job.get("file_name", ""), page=job.get("page_no", ""))
                        except Exception as exc:
                            failed += 1
                            error_text = str(exc)
                            errors.append({"file": job.get("file_name", ""), "page": job.get("page_no", ""), "error": error_text})
                            update = {"operation": operation, "success": False, "error": error_text, "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                            status_text = self.i18n.t("task_batch_page_failed", file=job.get("file_name", ""), page=job.get("page_no", ""), error=error_text)
                        progress_cb({"value": value, "task": status_text, "file": job.get("file_name", ""), "page_update": update, "indeterminate": False})
            except Exception as exc:
                if use_process:
                    raise RuntimeError(self.i18n.t("process_pool_failed", error=exc)) from exc
                raise
            return {"operation": operation, "total": len(jobs), "completed": completed, "failed": failed, "errors": errors, "elapsed_seconds": time.perf_counter() - started, "workers": max_workers, "backend": ("process" if use_process else "thread"), "engine": operation}

        def on_success(result: dict[str, Any]) -> None:
            self.refresh_file_tree()
            msg = self.i18n.t("batch_task_done", completed=result.get("completed", 0), failed=result.get("failed", 0), total=result.get("total", 0), seconds=float(result.get("elapsed_seconds", 0.0)), workers=result.get("workers", 1), backend=result.get("backend", "thread"))
            self._set_status(msg)
            if int(result.get("failed", 0)) > 0:
                details = self._format_batch_error_details(result)
                if details:
                    msg = msg + "\n\n" + self.i18n.t("batch_error_details_header") + "\n" + details
                messagebox.showwarning(self.i18n.t("batch_finished_with_errors_title"), msg, parent=self)
            logger.info("Batch OCR completed: %s", result)

        def on_error(exc: Exception) -> None:
            for job in jobs:
                update = {"operation": operation, "success": False, "error": str(exc), "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                self._apply_page_update(update)
            messagebox.showerror(self.i18n.t("ocr_failed_title"), str(exc), parent=self)
            self._set_status(self.i18n.t("ocr_failed_status"))

        self._start_background_task(task_label, first_file, worker, on_success, on_error)

    def _confirm_llm_privacy(self) -> bool:
        privacy = self.config_data.get("privacy", {})
        llm = self.config_data.get("llm", {})
        if privacy.get("local_only", True):
            messagebox.showwarning(self.i18n.t("local_only_title"), self.i18n.t("local_only_message"), parent=self)
            return False
        if not llm.get("enabled", False):
            messagebox.showwarning(self.i18n.t("llm_not_enabled_title"), self.i18n.t("llm_not_enabled_message"), parent=self)
            return False
        if llm.get("confirm_before_send", True) and privacy.get("remind_before_llm", True) and not self._privacy_confirmed_this_session:
            ok = messagebox.askyesno(self.i18n.t("privacy_confirm_title"), self.i18n.t("privacy_confirm_message"), parent=self)
            if not ok:
                return False
            self._privacy_confirmed_this_session = True
        return True

    def run_llm_ocr_current(self) -> None:
        self.run_llm_ocr_scope("current_page")

    def run_llm_ocr_scope(self, scope: str = "current_page") -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        if not self._confirm_llm_privacy():
            return
        if not self._preflight_llm("llm_ocr"):
            return
        jobs = self._collect_page_jobs(scope)
        if not jobs:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("batch_no_pages"), parent=self)
            return
        language_hint = self._language_hint()
        llm_cfg = dict(self.config_data.get("llm", {}))
        max_workers = self._normalise_worker_count(llm_cfg.get("max_concurrent_requests", 1), len(jobs), maximum=4)
        self._mark_jobs_processing(jobs, "llm_ocr")
        task_label = self.i18n.t("task_llm_ocr_batch", scope=self._scope_label(scope), count=len(jobs), workers=max_workers)
        first_file = jobs[0].get("file_name", "")

        def worker(progress_cb: Any) -> dict[str, Any]:
            started = time.perf_counter()
            completed = 0
            failed = 0
            errors: list[dict[str, Any]] = []
            progress_cb({"value": 2, "task": self.i18n.t("task_batch_running", task=task_label), "file": first_file, "indeterminate": False})
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {}
                for job in jobs:
                    payload = {"image_path": job.get("image_path", ""), "language_hint": language_hint, "llm_cfg": llm_cfg}
                    future = executor.submit(llm_ocr_page, payload)
                    future_map[future] = job
                for future in as_completed(future_map):
                    job = future_map[future]
                    value = 5 + ((completed + failed + 1) / len(jobs)) * 85
                    try:
                        result = future.result()
                        completed += 1
                        update = {"operation": "llm_ocr", "success": True, "result": result, "file_id": job.get("file_id"), "page_index": job.get("page_index"), "llm_model": llm_cfg.get("model", "")}
                        status_text = self.i18n.t("task_batch_page_done", file=job.get("file_name", ""), page=job.get("page_no", ""))
                    except Exception as exc:
                        failed += 1
                        error_text = str(exc)
                        errors.append({"file": job.get("file_name", ""), "page": job.get("page_no", ""), "error": error_text})
                        update = {"operation": "llm_ocr", "success": False, "error": error_text, "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                        status_text = self.i18n.t("task_batch_page_failed", file=job.get("file_name", ""), page=job.get("page_no", ""), error=error_text)
                    progress_cb({"value": value, "task": status_text, "file": job.get("file_name", ""), "page_update": update, "indeterminate": False})
            return {"operation": "llm_ocr", "total": len(jobs), "completed": completed, "failed": failed, "errors": errors, "elapsed_seconds": time.perf_counter() - started, "workers": max_workers, "backend": "thread"}

        def on_success(result: dict[str, Any]) -> None:
            self.refresh_file_tree()
            msg = self.i18n.t("batch_task_done", completed=result.get("completed", 0), failed=result.get("failed", 0), total=result.get("total", 0), seconds=float(result.get("elapsed_seconds", 0.0)), workers=result.get("workers", 1), backend=result.get("backend", "thread"))
            self._set_status(msg)
            if int(result.get("failed", 0)) > 0:
                details = self._format_batch_error_details(result)
                if details:
                    msg = msg + "\n\n" + self.i18n.t("batch_error_details_header") + "\n" + details
                messagebox.showwarning(self.i18n.t("batch_finished_with_errors_title"), msg, parent=self)
            logger.info("Batch LLM OCR completed: %s", result)

        def on_error(exc: Exception) -> None:
            for job in jobs:
                update = {"operation": "llm_ocr", "success": False, "error": str(exc), "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                self._apply_page_update(update)
            messagebox.showerror(self.i18n.t("llm_ocr_failed_title"), str(exc), parent=self)
            self._set_status(self.i18n.t("llm_ocr_failed_status"))

        self._start_background_task(task_label, first_file, worker, on_success, on_error)

    def run_llm_proofread_current(self) -> None:
        self.run_llm_proofread_scope("current_page")

    def run_llm_proofread_scope(self, scope: str = "current_page") -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        if not self._confirm_llm_privacy():
            return
        if not self._preflight_llm("llm_proofread"):
            return
        self.save_current_text_to_page()
        jobs = self._collect_page_jobs(scope)
        if not jobs:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("batch_no_pages"), parent=self)
            return
        language_hint = self._language_hint()
        llm_cfg = dict(self.config_data.get("llm", {}))
        max_workers = self._normalise_worker_count(llm_cfg.get("max_concurrent_requests", 1), len(jobs), maximum=4)
        allow_send_image = bool(llm_cfg.get("allow_send_image", True))
        prepared_jobs: list[dict[str, Any]] = []
        for job in jobs:
            page = job.get("page") or {}
            edited_text = page.get("final_text") or page.get("corrected_text") or page.get("ocr_text") or ""
            if job.get("file_id") == self.current_file_id and int(job.get("page_index", 0)) == self.current_page_index:
                edited_text = self.text_editor.get("1.0", tk.END).rstrip("\n")
            if not edited_text.strip():
                edited_text = page.get("embedded_text") or page.get("ocr_text") or ""
            ocr_text_for_llm = page.get("ocr_text") or page.get("embedded_text") or edited_text
            prepared = dict(job)
            prepared["edited_text"] = edited_text
            prepared["ocr_text"] = ocr_text_for_llm
            prepared["proofread_image_path"] = job.get("image_path") if allow_send_image else None
            prepared_jobs.append(prepared)
        prepared_jobs = [j for j in prepared_jobs if str(j.get("edited_text") or j.get("ocr_text") or "").strip()]
        if not prepared_jobs:
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("llm_proofread_no_text_message"), parent=self)
            return
        self._mark_jobs_processing(prepared_jobs, "llm_proofread")
        task_label = self.i18n.t("task_llm_proofread_batch", scope=self._scope_label(scope), count=len(prepared_jobs), workers=max_workers)
        first_file = prepared_jobs[0].get("file_name", "")

        def worker(progress_cb: Any) -> dict[str, Any]:
            started = time.perf_counter()
            completed = 0
            failed = 0
            errors: list[dict[str, Any]] = []
            progress_cb({"value": 2, "task": self.i18n.t("task_batch_running", task=task_label), "file": first_file, "indeterminate": False})
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {}
                for job in prepared_jobs:
                    payload = {
                        "llm_cfg": llm_cfg,
                        "ocr_text": job.get("ocr_text", ""),
                        "edited_text": job.get("edited_text", ""),
                        "image_path": job.get("proofread_image_path"),
                        "language_hint": language_hint,
                    }
                    future = executor.submit(llm_proofread_page, payload)
                    future_map[future] = job
                for future in as_completed(future_map):
                    job = future_map[future]
                    value = 5 + ((completed + failed + 1) / len(prepared_jobs)) * 85
                    try:
                        result = future.result()
                        completed += 1
                        update = {"operation": "llm_proofread", "success": True, "result": result, "file_id": job.get("file_id"), "page_index": job.get("page_index"), "llm_model": llm_cfg.get("model", ""), "edited_text": job.get("edited_text", "")}
                        status_text = self.i18n.t("task_batch_page_done", file=job.get("file_name", ""), page=job.get("page_no", ""))
                    except Exception as exc:
                        failed += 1
                        error_text = str(exc)
                        errors.append({"file": job.get("file_name", ""), "page": job.get("page_no", ""), "error": error_text})
                        update = {"operation": "llm_proofread", "success": False, "error": error_text, "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                        status_text = self.i18n.t("task_batch_page_failed", file=job.get("file_name", ""), page=job.get("page_no", ""), error=error_text)
                    progress_cb({"value": value, "task": status_text, "file": job.get("file_name", ""), "page_update": update, "indeterminate": False})
            return {"operation": "llm_proofread", "total": len(prepared_jobs), "completed": completed, "failed": failed, "errors": errors, "elapsed_seconds": time.perf_counter() - started, "workers": max_workers, "backend": "thread"}

        def on_success(result: dict[str, Any]) -> None:
            self.refresh_file_tree()
            msg = self.i18n.t("batch_task_done", completed=result.get("completed", 0), failed=result.get("failed", 0), total=result.get("total", 0), seconds=float(result.get("elapsed_seconds", 0.0)), workers=result.get("workers", 1), backend=result.get("backend", "thread"))
            self._set_status(msg)
            if int(result.get("failed", 0)) > 0:
                details = self._format_batch_error_details(result)
                if details:
                    msg = msg + "\n\n" + self.i18n.t("batch_error_details_header") + "\n" + details
                messagebox.showwarning(self.i18n.t("batch_finished_with_errors_title"), msg, parent=self)
            logger.info("Batch LLM proofreading completed: %s", result)

        def on_error(exc: Exception) -> None:
            for job in prepared_jobs:
                update = {"operation": "llm_proofread", "success": False, "error": str(exc), "file_id": job.get("file_id"), "page_index": job.get("page_index")}
                self._apply_page_update(update)
            messagebox.showerror(self.i18n.t("llm_proofread_failed_title"), str(exc), parent=self)
            self._set_status(self.i18n.t("llm_proofread_failed_status"))

        self._start_background_task(task_label, first_file, worker, on_success, on_error)

    # ---------- suggestions ----------
    def accept_suggestion(self, idx: int) -> None:
        page = self.get_current_page()
        if not page:
            return
        suggestions = page.get("suggestions", [])
        if idx < 0 or idx >= len(suggestions):
            return
        s = suggestions[idx]
        original = str(s.get("original", ""))
        suggested = str(s.get("suggested", ""))
        if not original:
            return
        content = self.text_editor.get("1.0", tk.END)
        pos = content.find(original)
        if pos >= 0:
            start = f"1.0+{pos}c"
            end = f"1.0+{pos + len(original)}c"
            self.text_editor.delete(start, end)
            self.text_editor.insert(start, suggested)
            s["status"] = "accepted"
        else:
            s["status"] = "not_found"
            messagebox.showwarning(self.i18n.t("text_not_found_title"), self.i18n.t("text_not_found_message"), parent=self)
        page["final_text"] = self.text_editor.get("1.0", tk.END).rstrip("\n")
        self.suggestion_panel.set_suggestions(suggestions)

    def reject_suggestion(self, idx: int) -> None:
        page = self.get_current_page()
        if not page:
            return
        suggestions = page.get("suggestions", [])
        if 0 <= idx < len(suggestions):
            suggestions[idx]["status"] = "rejected"
            self.suggestion_panel.set_suggestions(suggestions)

    def accept_all_suggestions(self) -> None:
        page = self.get_current_page()
        if not page:
            return
        for i, s in enumerate(page.get("suggestions", [])):
            if s.get("status") not in {"accepted", "rejected"}:
                self.accept_suggestion(i)
        page["final_text"] = self.text_editor.get("1.0", tk.END).rstrip("\n")

    def clear_suggestions(self) -> None:
        page = self.get_current_page()
        if page:
            page["suggestions"] = []
        self.suggestion_panel.set_suggestions([])

    def restore_ocr_text(self) -> None:
        page = self.get_current_page()
        if not page:
            return
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", page.get("ocr_text", ""))
        page["final_text"] = page.get("ocr_text", "")
        self.text_editor.edit_modified(False)

    # ---------- text tools ----------
    def copy_text(self) -> None:
        text = self.text_editor.get("1.0", tk.END).rstrip("\n")
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status(self.i18n.t("copied_status"))

    def find_replace(self) -> None:
        find = simpledialog.askstring(self.i18n.t("find_title"), self.i18n.t("find_prompt"), parent=self)
        if find is None:
            return
        repl = simpledialog.askstring(self.i18n.t("replace_title"), self.i18n.t("replace_prompt"), parent=self)
        if repl is None:
            return
        content = self.text_editor.get("1.0", tk.END)
        count = content.count(find)
        content = content.replace(find, repl)
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", content.rstrip("\n"))
        self.save_current_text_to_page()
        self._set_status(self.i18n.t("replace_status", count=count))

    # ---------- export ----------
    def _export_options(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        opts = dict(self.config_data.get("export", {}))
        opts.update(extra or {})
        opts["current_file_id"] = self.current_file_id
        opts["current_page_index"] = self.current_page_index
        return opts

    def _call_exporter(self, fmt: str, path: str, scope: str, options: dict[str, Any]) -> str:
        fmt_key = fmt.lower()
        if fmt_key == "markdown":
            return export_to_markdown(self.project.data, path, scope, options)
        if fmt_key == "txt":
            return export_to_txt(self.project.data, path, scope, options)
        if fmt_key == "docx":
            return export_to_docx(self.project.data, path, scope, options)
        if fmt_key == "xlsx":
            return export_to_xlsx(self.project.data, path, scope, options)
        if fmt_key == "json":
            return export_to_json(self.project.data, path, scope, options)
        if fmt_key == "xml":
            return export_to_xml(self.project.data, path, scope, options)
        raise ValueError(self.i18n.t("unsupported_export_format", fmt=fmt))

    def _export_ext_for_format(self, fmt: str) -> str:
        fmt_key = fmt.lower()
        return ".md" if fmt_key == "markdown" else f".{fmt_key}"

    def _files_for_export_scope(self, scope: str) -> list[dict[str, Any]]:
        files = list(self.project.data.get("files", []))
        if scope in {"current_file", "current_page", "file", "page"}:
            files = [f for f in files if f.get("id") == self.current_file_id]
        return [f for f in files if f.get("pages")]

    def _unique_export_path(self, folder: Path, filename: str, used: set[str]) -> Path:
        base = Path(filename)
        stem = base.stem
        suffix = base.suffix
        candidate = folder / filename
        counter = 2
        while str(candidate).lower() in used or candidate.exists():
            candidate = folder / f"{stem}_{counter}{suffix}"
            counter += 1
        used.add(str(candidate).lower())
        return candidate

    def _call_split_exporter(self, fmt: str, folder: str, scope: str, options: dict[str, Any]) -> str:
        target_dir = Path(folder)
        target_dir.mkdir(parents=True, exist_ok=True)
        files = self._files_for_export_scope(scope)
        if not files:
            raise ValueError(self.i18n.t("no_exportable_pages"))
        ext = self._export_ext_for_format(fmt)
        saved_paths: list[str] = []
        used: set[str] = set()
        for file_entry in files:
            file_name = file_entry.get("file_name") or file_entry.get("id") or "untitled"
            stem = safe_filename(Path(str(file_name)).stem)
            if not stem:
                stem = "untitled"
            out_path = self._unique_export_path(target_dir, f"{stem}_ocr{ext}", used)
            file_options = dict(options)
            file_options["current_file_id"] = file_entry.get("id", "")
            # In current-page scope, keep the selected page; otherwise export the whole source file.
            file_scope = "current_page" if scope in {"current_page", "page"} else "current_file"
            saved_paths.append(self._call_exporter(fmt, str(out_path), file_scope, file_options))
        return str(target_dir) if len(saved_paths) > 1 else saved_paths[0]

    def export_dialog(self) -> None:
        self.save_current_text_to_page()
        stem = safe_filename(self.project.data.get("project_name", "prooflens_export"))
        default_dir = self.config_data.get("default_export_dir") or str(writable_path("output"))
        dialog = ExportDialog(self, default_dir=default_dir, current_file_stem=stem, i18n=self.i18n)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            result = dialog.result
            options = self._export_options(result.get("options"))
            if options.get("split_by_source_file"):
                path = self._call_split_exporter(result["format"], result["path"], result["scope"], options)
            else:
                path = self._call_exporter(result["format"], result["path"], result["scope"], options)
            if result.get("open_folder"):
                open_folder(path)
            self._set_status(self.i18n.t("export_complete_status", path=path))
            messagebox.showinfo(self.i18n.t("export_complete_title"), self.i18n.t("export_complete_message", path=path), parent=self)
        except Exception as exc:
            logger.exception("Export failed")
            messagebox.showerror(self.i18n.t("export_failed_title"), str(exc), parent=self)

    def quick_export(self, scope: str, fmt: str) -> None:
        self.save_current_text_to_page()
        if not self.project.data.get("files"):
            messagebox.showinfo(self.i18n.t("info"), self.i18n.t("no_exportable_pages"), parent=self)
            return
        ext = ".md" if fmt.lower() == "markdown" else f".{fmt.lower()}"
        stem = safe_filename(self.project.data.get("project_name", "prooflens_export"))
        default_dir = Path(self.config_data.get("default_export_dir") or writable_path("output"))
        default_dir.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(title=self.i18n.t("export_title"), initialdir=default_dir, initialfile=f"{stem}{ext}", defaultextension=ext, filetypes=[(fmt, f"*{ext}"), (self.i18n.t("all_files"), "*.*")])
        if not path:
            return
        try:
            saved = self._call_exporter(fmt, path, scope, self._export_options())
            self._set_status(self.i18n.t("export_complete_status", path=saved))
        except Exception as exc:
            logger.exception("Quick export failed")
            messagebox.showerror(self.i18n.t("export_failed_title"), str(exc), parent=self)

    # ---------- settings/about ----------
    def open_settings(self) -> None:
        if self._busy:
            messagebox.showinfo(self.i18n.t("another_task_running_title"), self.i18n.t("another_task_running_message"), parent=self)
            return
        dialog = SettingsDialog(self, self.config_data, i18n=self.i18n)
        self.wait_window(dialog)
        if dialog.result:
            self.config_data = dialog.result
            self.project.data["settings"] = self.config_data
            self.config_manager.save(self.config_data)
            self.i18n.set_language(self.config_data.get("ui_language", "en"))
            self.language_preset_var.set(self.config_data.get("ocr", {}).get("language_preset", "zh_en_mixed"))
            self.mixed_var.set(bool(self.config_data.get("ocr", {}).get("mixed_language_mode", True)))
            self._rebuild_ui(status=self.i18n.t("settings_saved_status"))

    def show_about(self) -> None:
        AboutDialog(self, i18n=self.i18n)
