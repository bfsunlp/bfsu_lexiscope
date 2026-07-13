# -*- coding: utf-8 -*-
"""BFSU WebLens GUI entry point."""
from __future__ import annotations

import json
import os
import queue
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import threading
import time
import webbrowser
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from bfsu_weblens.collector import (
    CollectorConfig,
    BrowserStartupError,
    NetworkAccessError,
    StopCrawl,
    crawl,
    split_text_terms,
    normalize_url_for_dedup,
)
from bfsu_weblens.data import (
    APP_LANGS,
    COUNTRY_OPTIONS,
    LANGUAGE_OPTIONS,
    OUTPUT_FORMATS,
    CONTENT_CLEANING_OPTIONS,
    CONTENT_FETCH_MODE_OPTIONS,
    QUERY_MODE_OPTIONS,
    VERTICAL_OPTIONS,
    BAIDU_SORT_OPTIONS,
    FETCH_BACKEND_OPTIONS,
    label_for,
    labels_for,
    option_by_label,
)
from bfsu_weblens.date_picker import DateEntry
from bfsu_weblens.exporter import export_records
from bfsu_weblens.importer import import_records
from bfsu_weblens.content_downloader import (
    ContentDownloadSettings,
    ContentResult,
    DomainLockPool,
    download_one,
    ensure_content_dirs,
    load_successful_download_index,
    successful_manifest_for_record,
    content_result_from_manifest,
)
from bfsu_weblens.i18n import t

APP_NAME = "BFSU WebLens"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
 )


def vertical_options_for_engine(engine: str):
    """Return engine-specific vertical choices for the collector tab UI."""
    if (engine or "").lower() == "baidu":
        wanted = {"baidu_web", "baidu_news", "baidu_news_media"}
    else:
        wanted = {"news", "web"}
    return [opt for opt in VERTICAL_OPTIONS if opt.get("key") in wanted]


def default_vertical_for_engine(engine: str) -> str:
    return "baidu_news_media" if (engine or "").lower() == "baidu" else "news"


def query_mode_options_for_engine(engine: str):
    """Baidu does not expose Google-style Any/OR helper modes in the UI."""
    if (engine or "").lower() == "baidu":
        blocked = {"any", "phrase_any"}
        return [opt for opt in QUERY_MODE_OPTIONS if opt.get("key") not in blocked]
    return list(QUERY_MODE_OPTIONS)


COLLECTOR_CONTEXT_ATTRS = [
    "main_pane", "left_panel", "right_panel", "action_bar",
    "start_button", "stop_button", "export_button", "import_links_button", "clear_button", "open_button",
    "toolbar_progress_label", "toolbar_progress",
    "settings_scroll", "query_frame", "crawl_frame", "limit_frame", "output_frame",
    "query_mode_label", "query_mode_combo", "vertical_label", "vertical_combo",
    "baidu_sort_label", "baidu_sort_combo", "backend_label", "backend_combo",
    "driver_path_label", "driver_path_var", "driver_path_entry", "driver_browse_button",
    "browser_binary_label", "browser_binary_var", "browser_binary_entry", "binary_browse_button",
    "browser_wait_label", "browser_wait_var", "browser_headless_var", "browser_headless_check",
    "query_terms_label", "query_text", "query_help_btn",
    "site_label", "site_var", "site_entry", "site_help_btn",
    "safe_label", "safe_var", "safe_combo", "disable_filter_var", "filter_check",
    "start_date_label", "start_date_entry", "end_date_label", "end_date_entry",
    "spin_vars", "delay_vars", "max_pages_hint_label",
    "max_pages_label", "day_step_label", "per_page_label", "timeout_label",
    "post_fetch_wait_ms_label", "empty_page_retry_count_label", "empty_page_retry_wait_ms_label", "no_new_pages_limit_label",
    "selenium_restart_pages_label",
    "page_delay_label", "slice_delay_label", "error_delay_label",
    "language_label", "language_box", "language_list", "clear_lang_btn",
    "country_label", "country_box", "country_list", "clear_country_btn",
    "current_language_options", "current_country_options", "current_vertical_options", "current_query_mode_options",
    "output_file_label", "output_entry", "browse_button", "output_format_label", "output_format_combo",
    "content_folder_label", "content_dir_entry", "content_browse_button", "content_threads_label", "content_threads_spin",
    "content_fetch_mode_label", "content_fetch_mode_combo", "content_delay_label", "content_delay_min_var", "content_delay_max_var",
    "content_receive_wait_label", "content_receive_wait_var",
    "content_cleaning_label", "content_cleaning_combo", "content_selenium_fallback_check", "output_hint_label",
    "preview_frame", "preview_toolbar", "open_link_button", "delete_selected_button",
    "sort_label", "sort_time_button", "sort_title_button", "sort_source_button",
    "result_edit_menu", "result_edit_button", "preview_count_var", "preview_count_label",
    "sample_scheme_label", "sample_scheme_var", "sample_scheme_combo", "sample_count_label", "sample_count_var", "sample_count_spin",
    "sample_button", "download_content_button", "download_all_content_button", "download_settings_button",
    "tree", "result_menu", "log_frame", "log_text",
]


def app_base_dir() -> Path:
    """Return the folder used for local settings and user-visible side files."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_output_path() -> str:
    return str(app_base_dir() / "output" / "weblens_results.xlsx")


def default_settings_dict() -> dict:
    today = date.today().isoformat()
    return {
        "ui_lang": "en",
        "query_mode": "single",
        "search_vertical": "news",
        "baidu_sort": "focus",
        "fetch_backend": "requests",
        "browser_driver_path": str(Path(resource_path("tools/chromedriver.exe"))),
        "browser_binary_path": default_browser_binary_path(),
        "browser_wait_ms": 3500,
        "browser_headless": False,
        "query_terms": "",
        "site_filters": "",
        "safe": "",
        "disable_filter": False,
        "start_date": today,
        "end_date": today,
        "max_pages": 30,
        "day_step": 7,
        "per_page": 50,
        "timeout": 15,
        "post_fetch_wait_ms": 800,
        "empty_page_retry_count": 2,
        "empty_page_retry_wait_ms": 1500,
        "no_new_pages_limit": 1,
        "selenium_restart_pages": 4,
        "page_delay_min_ms": 30000,
        "page_delay_max_ms": 90000,
        "slice_delay_min_ms": 30000,
        "slice_delay_max_ms": 60000,
        "error_delay_min_ms": 60000,
        "error_delay_max_ms": 180000,
        "languages_lr": [],
        "countries_cr": [],
        "output_path": default_output_path(),
        "output_format": "xlsx",
        "content_download_dir": str(app_base_dir() / "content_downloads"),
        "content_threads": 3,
        "content_cleaning_scheme": "auto",
        "content_fetch_mode": "mixed",
        "content_delay_min_ms": 0,
        "content_delay_max_ms": 0,
        "content_receive_wait_ms": 3500,
        "content_selenium_fallback": True,
        "content_retry_count": 1,
        "content_task_timeout_seconds": 300,
        "content_resume_enabled": True,
        "content_domain_lock_timeout_seconds": 300,
        "sample_scheme": "simple",
        "sample_count": 20,
        "user_agent": DEFAULT_USER_AGENT,
    }


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base) / relative)


def default_browser_binary_path() -> str:
    """Return the first common Chrome/Edge browser executable path found on Windows."""
    env = os.environ
    candidates = [
        Path(env.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(env.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
        Path(env.get("LOCALAPPDATA", "")) / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome Beta" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome Beta" / "Application" / "chrome.exe",
        Path(env.get("LOCALAPPDATA", "")) / "Google" / "Chrome SxS" / "Application" / "chrome.exe",
        Path(env.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(env.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    for c in candidates:
        try:
            if c and c.exists() and c.is_file():
                return str(c)
        except Exception:
            pass
    return ""


class ScrollableFrame(ttk.Frame):
    """A reusable scrollable frame for dense settings panels."""

    def __init__(self, parent, style="Panel.TFrame", *args, **kwargs):
        super().__init__(parent, style=style, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, background="#F7FAFB")
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.inner = ttk.Frame(self.canvas, style=style)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.inner)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Fit the settings panel to the currently visible width.
        # Child widgets keep their own scrollbars where needed, so this avoids
        # forcing the left pane to stay overly wide after the user drags the sash.
        self.canvas.itemconfigure(self.inner_id, width=max(1, event.width))

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")
        widget.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"), add="+")
        widget.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"), add="+")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")


class BFSUWebLensApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ui_lang = "en"
        self.records = []
        self.original_records = []
        self.undo_stack = []
        self.redo_stack = []
        self.worker = None
        self.content_worker = None
        self.stop_event = threading.Event()
        self.content_stop_event = threading.Event()
        self.event_queue = queue.Queue()
        self.settings_path = app_base_dir() / "weblens_settings.json"
        self.defaults = default_settings_dict()
        self.settings = self._load_settings()
        self.output_path = tk.StringVar(value=self.settings.get("output_path", self.defaults["output_path"]))
        self.output_format = tk.StringVar(value=self.settings.get("output_format", self.defaults["output_format"]))
        self.content_dir_var = tk.StringVar(value=self.settings.get("content_download_dir", self.defaults["content_download_dir"]))
        self.content_threads_var = tk.IntVar(value=int(self.settings.get("content_threads", self.defaults["content_threads"])))
        self.content_cleaning_var = tk.StringVar()
        self.content_fetch_mode_var = tk.StringVar()
        self.content_delay_min_var = tk.IntVar(value=int(self.settings.get("content_delay_min_ms", self.defaults.get("content_delay_min_ms", 0))))
        self.content_delay_max_var = tk.IntVar(value=int(self.settings.get("content_delay_max_ms", self.defaults.get("content_delay_max_ms", 0))))
        self.content_receive_wait_var = tk.IntVar(value=int(self.settings.get("content_receive_wait_ms", self.defaults.get("content_receive_wait_ms", 3500))))
        self.content_selenium_fallback_var = tk.BooleanVar(value=bool(self.settings.get("content_selenium_fallback", self.defaults.get("content_selenium_fallback", True))))
        self.ui_lang_var = tk.StringVar(value=self.settings.get("ui_lang", self.defaults["ui_lang"]))
        self.user_agent_var = tk.StringVar(value=self.settings.get("user_agent", DEFAULT_USER_AGENT))
        self.tree_record_map = {}
        self.tree_iid_counter = 0
        self.sort_reverse = {"time": False, "title": False, "source": False}
        self.contexts = {}
        self.active_context_key = None
        self.worker_context_key = None
        self.content_worker_context_key = None
        self._building_context_key = "google"
        self.icon_path = resource_path("assets/app.ico")
        self.title(APP_NAME)
        self.geometry("1600x940")
        self.minsize(1280, 760)
        self._apply_icon(self)
        self._setup_style()
        self._build_ui()
        self._set_language(self.settings.get("ui_lang", self.defaults["ui_lang"]))
        self._apply_settings_to_widgets(self.settings)
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._poll_queue)

    def _load_settings(self):
        data = {}
        try:
            if self.settings_path.exists():
                loaded = json.loads(self.settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
        except Exception:
            data = {}
        # Upgrade old anti-captcha defaults from earlier WebLens builds while preserving
        # deliberate custom values that differ from the old defaults.
        if data.get("page_delay_min_ms") == 15000 and data.get("page_delay_max_ms") == 20000:
            data["page_delay_min_ms"] = 30000
            data["page_delay_max_ms"] = 90000
        # v1.2 default: stop a slice after one no-new page.  Migrate only the
        # previous default value so intentional custom values can still survive.
        if data.get("no_new_pages_limit") == 2:
            data["no_new_pages_limit"] = 1
        merged = dict(getattr(self, "defaults", default_settings_dict()))
        merged.update(data)
        return merged

    def _collect_current_settings(self):
        data = dict(self.defaults)
        try:
            data["ui_lang"] = self.ui_lang
        except Exception:
            data["ui_lang"] = self.ui_lang_var.get() or self.defaults["ui_lang"]
        try:
            data["query_mode"] = self._current_combo_key(self.query_mode_combo, getattr(self, "current_query_mode_options", QUERY_MODE_OPTIONS), self.ui_lang, self.defaults["query_mode"])
            data["search_vertical"] = self._current_combo_key(self.vertical_combo, getattr(self, "current_vertical_options", VERTICAL_OPTIONS), self.ui_lang, default_vertical_for_engine(getattr(self, "active_context_key", "google")))
            data["fetch_backend"] = self._current_combo_key(self.backend_combo, FETCH_BACKEND_OPTIONS, self.ui_lang, self.defaults["fetch_backend"])
            if hasattr(self, "baidu_sort_combo"):
                data["baidu_sort"] = self._current_combo_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, self.ui_lang, self.defaults.get("baidu_sort", "focus"))
            data["content_cleaning_scheme"] = self._current_combo_key(self.content_cleaning_combo, CONTENT_CLEANING_OPTIONS, self.ui_lang, self.defaults["content_cleaning_scheme"])
            data["content_fetch_mode"] = self._current_combo_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, self.ui_lang, self.defaults.get("content_fetch_mode", "mixed"))
        except Exception:
            pass
        for key, attr in [
            ("browser_driver_path", "driver_path_var"),
            ("browser_binary_path", "browser_binary_var"),
            ("output_path", "output_path"),
            ("output_format", "output_format"),
            ("content_download_dir", "content_dir_var"),
            ("content_download_dir", "content_dir_var"),
            ("safe", "safe_var"),
            ("site_filters", "site_var"),
            ("user_agent", "user_agent_var"),
        ]:
            try:
                data[key] = getattr(self, attr).get()
            except Exception:
                pass
        # site_entry is now a multi-line Text widget, so StringVar alone may be stale.
        data["site_filters"] = self._get_site_filters_text()
        try:
            data["browser_wait_ms"] = int(self.browser_wait_var.get())
            data["browser_headless"] = bool(self.browser_headless_var.get())
            data["disable_filter"] = bool(self.disable_filter_var.get())
            data["query_terms"] = self.query_text.get("1.0", "end").strip()
            data["start_date"] = self.start_date_entry.get_date().isoformat()
            data["end_date"] = self.end_date_entry.get_date().isoformat()
            data["sample_scheme"] = self._current_sample_scheme_key()
            data["sample_count"] = int(self.sample_count_var.get())
            data["content_threads"] = int(self.content_threads_var.get())
            data["content_selenium_fallback"] = bool(self.content_selenium_fallback_var.get())
            data["content_delay_min_ms"] = int(self.content_delay_min_var.get())
            data["content_delay_max_ms"] = int(self.content_delay_max_var.get())
            data["content_receive_wait_ms"] = int(self.content_receive_wait_var.get())
        except Exception:
            pass
        try:
            for name, var in self.spin_vars.items():
                data[name] = int(var.get())
            for name, (vmin, vmax) in self.delay_vars.items():
                data[f"{name}_min_ms"] = int(vmin.get())
                data[f"{name}_max_ms"] = int(vmax.get())
        except Exception:
            pass
        try:
            data["languages_lr"] = [
                self.current_language_options[i].get("lr")
                for i in self.language_list.curselection()
                if self.current_language_options[i].get("lr")
            ]
            data["countries_cr"] = [
                self.current_country_options[i].get("cr")
                for i in self.country_list.curselection()
                if self.current_country_options[i].get("cr")
            ]
        except Exception:
            pass
        data["user_agent"] = (data.get("user_agent") or DEFAULT_USER_AGENT).strip() or DEFAULT_USER_AGENT
        return data

    def _save_settings(self):
        try:
            data = self._collect_current_settings()
            self.settings = dict(data)
            self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _set_combo_by_key(self, combo, options, key):
        for opt in options:
            if opt.get("key") == key:
                combo.set(label_for(opt, self.ui_lang))
                return

    def _set_listbox_selection_by_values(self, listbox, options, value_key, values):
        wanted = set(values or [])
        listbox.selection_clear(0, tk.END)
        for i, opt in enumerate(options):
            if opt.get(value_key) in wanted:
                listbox.selection_set(i)

    def _apply_settings_to_widgets(self, settings: dict):
        settings = dict(self.defaults, **(settings or {}))
        try:
            self._set_combo_by_key(self.query_mode_combo, getattr(self, "current_query_mode_options", QUERY_MODE_OPTIONS), settings.get("query_mode", self.defaults["query_mode"]))
            self._set_combo_by_key(self.vertical_combo, getattr(self, "current_vertical_options", VERTICAL_OPTIONS), settings.get("search_vertical", default_vertical_for_engine(getattr(self, "active_context_key", "google"))))
            self._set_combo_by_key(self.backend_combo, FETCH_BACKEND_OPTIONS, settings.get("fetch_backend", self.defaults["fetch_backend"]))
            if hasattr(self, "baidu_sort_combo"):
                self._set_combo_by_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, settings.get("baidu_sort", self.defaults.get("baidu_sort", "focus")))
            self._set_combo_by_key(self.content_cleaning_combo, CONTENT_CLEANING_OPTIONS, settings.get("content_cleaning_scheme", self.defaults["content_cleaning_scheme"]))
            self._set_combo_by_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, settings.get("content_fetch_mode", self.defaults.get("content_fetch_mode", "mixed")))
        except Exception:
            pass
        for key, attr in [
            ("browser_driver_path", "driver_path_var"),
            ("browser_binary_path", "browser_binary_var"),
            ("output_path", "output_path"),
            ("output_format", "output_format"),
            ("content_download_dir", "content_dir_var"),
            ("content_download_dir", "content_dir_var"),
            ("safe", "safe_var"),
            ("site_filters", "site_var"),
            ("user_agent", "user_agent_var"),
        ]:
            try:
                getattr(self, attr).set(settings.get(key, self.defaults.get(key, "")))
            except Exception:
                pass
        self._set_site_filters_text(settings.get("site_filters", self.defaults.get("site_filters", "")))
        try:
            self.browser_wait_var.set(int(settings.get("browser_wait_ms", self.defaults["browser_wait_ms"])))
            self.browser_headless_var.set(bool(settings.get("browser_headless", self.defaults["browser_headless"])))
            self.disable_filter_var.set(bool(settings.get("disable_filter", self.defaults["disable_filter"])))
            self.query_text.delete("1.0", "end")
            self.query_text.insert("1.0", settings.get("query_terms", self.defaults["query_terms"]))
            self.start_date_entry.set_date(date.fromisoformat(settings.get("start_date", self.defaults["start_date"])))
            self.end_date_entry.set_date(date.fromisoformat(settings.get("end_date", self.defaults["end_date"])))
            self.sample_count_var.set(int(settings.get("sample_count", self.defaults["sample_count"])))
            self.content_threads_var.set(int(settings.get("content_threads", self.defaults["content_threads"])))
            self.content_selenium_fallback_var.set(bool(settings.get("content_selenium_fallback", self.defaults.get("content_selenium_fallback", True))))
            self.content_delay_min_var.set(int(settings.get("content_delay_min_ms", self.defaults.get("content_delay_min_ms", 0))))
            self.content_delay_max_var.set(int(settings.get("content_delay_max_ms", self.defaults.get("content_delay_max_ms", 0))))
            self.content_receive_wait_var.set(int(settings.get("content_receive_wait_ms", self.defaults.get("content_receive_wait_ms", 3500))))
        except Exception:
            pass
        try:
            for name, var in self.spin_vars.items():
                var.set(int(settings.get(name, self.defaults.get(name, var.get()))))
            for name, (vmin, vmax) in self.delay_vars.items():
                vmin.set(int(settings.get(f"{name}_min_ms", self.defaults.get(f"{name}_min_ms", vmin.get()))))
                vmax.set(int(settings.get(f"{name}_max_ms", self.defaults.get(f"{name}_max_ms", vmax.get()))))
        except Exception:
            pass
        try:
            self._set_listbox_selection_by_values(self.language_list, self.current_language_options, "lr", settings.get("languages_lr", []))
            self._set_listbox_selection_by_values(self.country_list, self.current_country_options, "cr", settings.get("countries_cr", []))
        except Exception:
            pass
        try:
            scheme_key = settings.get("sample_scheme", self.defaults["sample_scheme"])
            labels = {"simple": t(self.ui_lang, "sample_simple"), "systematic": t(self.ui_lang, "sample_systematic"), "source": t(self.ui_lang, "sample_by_source")}
            self.sample_scheme_combo.set(labels.get(scheme_key, labels["simple"]))
        except Exception:
            pass
        self._on_output_format_changed()

    def _reset_all_settings_to_defaults(self, close_window=None):
        self.settings = default_settings_dict()
        self.defaults = dict(self.settings)
        self._set_language(self.settings.get("ui_lang", "en"))
        self._apply_settings_to_widgets(self.settings)
        self._save_settings()
        self._log(t(self.ui_lang, "defaults_restored"))
        if close_window is not None:
            try:
                close_window.destroy()
            except Exception:
                pass

    def _on_close(self):
        self._save_settings()
        self.destroy()

    def _apply_icon(self, win):
        try:
            if os.path.exists(self.icon_path):
                win.iconbitmap(self.icon_path)
        except Exception:
            pass

    def _setup_style(self):
        self.configure(bg="#E8EEF1")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.colors = {
            "navy": "#17384A",
            "blue": "#1F4E5F",
            "blue2": "#2F6F7E",
            "gold": "#D5A84A",
            "bg": "#E8EEF1",
            "panel": "#F7FAFB",
            "text": "#1F2A30",
        }
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat")
        style.configure("Toolbar.TFrame", background="#D8E3E8")
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 9))
        style.configure("Toolbar.TLabel", background="#D8E3E8", foreground=self.colors["navy"], font=("Segoe UI", 9, "bold"))
        style.configure("TLabelframe", background=self.colors["panel"], bordercolor="#CAD6DB")
        style.configure("TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["blue"], font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background=self.colors["blue"], foreground="white", font=("Segoe UI", 9, "bold"), padding=(10, 5))
        style.map("Accent.TButton", background=[("active", self.colors["blue2"])])
        style.configure("Danger.TButton", background="#A94442", foreground="white", font=("Segoe UI", 9, "bold"), padding=(10, 5))
        style.configure("Link.TButton", background=self.colors["panel"], foreground=self.colors["blue"], font=("Segoe UI", 9, "underline"), borderwidth=0)
        style.configure("Preview.TButton", background=self.colors["panel"], foreground=self.colors["navy"], font=("Segoe UI", 8), padding=(6, 2))
        style.configure("Preview.TMenubutton", background=self.colors["panel"], foreground=self.colors["navy"], font=("Segoe UI", 8), padding=(6, 2))
        style.configure("Preview.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 8))
        style.configure("Treeview", rowheight=24, font=("Segoe UI", 9), fieldbackground="white", background="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#D8E3E8", foreground="#17384A")

    def _build_ui(self):
        self._build_menu()
        # No large title banner: preserve vertical space for functional widgets.
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self.google_tab = ttk.Frame(self.notebook, padding=6)
        self.baidu_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.google_tab, text="Google")
        self.notebook.add(self.baidu_tab, text="Baidu")

        self._build_collector_tab(self.google_tab, "google")
        self._build_collector_tab(self.baidu_tab, "baidu")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed, add="+")

        bottom = ttk.Frame(self, padding=(8, 2, 8, 8))
        bottom.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready.")
        self.progress = ttk.Progressbar(bottom, mode="determinate", maximum=100, value=0)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.status_label = ttk.Label(bottom, textvariable=self.status_var)
        self.status_label.pack(side="right")
        self._activate_context("google", sync_previous=False)

    def _build_menu(self):
        self.menu_bar = tk.Menu(self, tearoff=False)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.lang_menu = tk.Menu(self.view_menu, tearoff=False)
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.file_menu.add_command(label="Import links/results", command=self._import_links_file)
        self.file_menu.add_command(label="Export results", command=self._export_results)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._on_close)
        for opt in APP_LANGS:
            self.lang_menu.add_radiobutton(
                label=label_for(opt, "en"),
                variable=self.ui_lang_var,
                value=opt["key"],
                command=lambda k=opt["key"]: (self._set_language(k), self._save_settings()),
            )
        self.view_menu.add_cascade(label="Interface language", menu=self.lang_menu)
        self.tools_menu.add_command(label="Download selected content", command=self._download_selected_content)
        self.tools_menu.add_command(label="Download all content", command=self._download_all_content)
        self.tools_menu.add_command(label="Download settings", command=self._open_content_settings_dialog)
        self.tools_menu.add_command(label="Settings", accelerator="Ctrl+,", command=self._show_settings)
        self.help_menu.add_command(label="User guide", command=self._show_user_guide)
        self.help_menu.add_command(label="Parameter guide", command=self._show_parameter_guide)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.config(menu=self.menu_bar)

    def _make_collector_context(self, key: str):
        ctx = SimpleNamespace(key=key, engine=key)
        for name in COLLECTOR_CONTEXT_ATTRS:
            if hasattr(self, name):
                setattr(ctx, name, getattr(self, name))
        ctx.records = []
        ctx.original_records = []
        ctx.undo_stack = []
        ctx.redo_stack = []
        ctx.tree_record_map = {}
        ctx.tree_iid_counter = 0
        ctx.sort_reverse = {"time": False, "title": False, "source": False}
        ctx.current_vertical_options = vertical_options_for_engine(key)
        ctx.current_query_mode_options = query_mode_options_for_engine(key)
        return ctx

    def _sync_active_context_state(self):
        key = getattr(self, "active_context_key", None)
        ctx = self.contexts.get(key) if hasattr(self, "contexts") else None
        if not ctx:
            return
        for name in COLLECTOR_CONTEXT_ATTRS:
            if hasattr(self, name):
                setattr(ctx, name, getattr(self, name))
        ctx.records = getattr(self, "records", [])
        ctx.original_records = getattr(self, "original_records", [])
        ctx.undo_stack = getattr(self, "undo_stack", [])
        ctx.redo_stack = getattr(self, "redo_stack", [])
        ctx.tree_record_map = getattr(self, "tree_record_map", {})
        ctx.tree_iid_counter = getattr(self, "tree_iid_counter", 0)
        ctx.sort_reverse = getattr(self, "sort_reverse", {"time": False, "title": False, "source": False})

    def _activate_context(self, key: str, sync_previous: bool = True):
        if key not in getattr(self, "contexts", {}):
            return
        if sync_previous:
            self._sync_active_context_state()
        ctx = self.contexts[key]
        self.active_context_key = key
        for name in COLLECTOR_CONTEXT_ATTRS:
            if hasattr(ctx, name):
                setattr(self, name, getattr(ctx, name))
        self.current_vertical_options = getattr(ctx, "current_vertical_options", vertical_options_for_engine(key))
        self.current_query_mode_options = getattr(ctx, "current_query_mode_options", query_mode_options_for_engine(key))
        self.records = getattr(ctx, "records", [])
        self.original_records = getattr(ctx, "original_records", [])
        self.undo_stack = getattr(ctx, "undo_stack", [])
        self.redo_stack = getattr(ctx, "redo_stack", [])
        self.tree_record_map = getattr(ctx, "tree_record_map", {})
        self.tree_iid_counter = getattr(ctx, "tree_iid_counter", 0)
        self.sort_reverse = getattr(ctx, "sort_reverse", {"time": False, "title": False, "source": False})

    def _selected_context_key(self):
        try:
            current = self.notebook.select()
            if current == str(self.google_tab):
                return "google"
            if current == str(self.baidu_tab):
                return "baidu"
        except Exception:
            pass
        return getattr(self, "active_context_key", "google") or "google"

    def _ensure_active_context_from_tab(self):
        key = self._selected_context_key()
        if key in getattr(self, "contexts", {}) and key != getattr(self, "active_context_key", None):
            self._activate_context(key)
        return key

    def _on_tab_changed(self, _event=None):
        self._ensure_active_context_from_tab()
        try:
            self._update_preview_count()
        except Exception:
            pass

    def _build_collector_tab(self, tab, key: str):
        self._building_context_key = key
        self.current_vertical_options = vertical_options_for_engine(key)
        self.current_query_mode_options = query_mode_options_for_engine(key)
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)
        self._build_action_bar(tab)
        self.main_pane = ttk.PanedWindow(tab, orient="horizontal")
        self.main_pane.grid(row=1, column=0, sticky="nsew")
        self.left_panel = ttk.Frame(self.main_pane, style="Panel.TFrame")
        self.right_panel = ttk.Frame(self.main_pane, style="Panel.TFrame", padding=8)
        self.main_pane.add(self.left_panel, weight=1)
        self.main_pane.add(self.right_panel, weight=2)
        self._build_settings_panel(self.left_panel)
        self._build_results_panel(self.right_panel)
        self._initial_sash_done = False
        self.contexts[key] = self._make_collector_context(key)
        self.after(250, lambda k=key: self._set_initial_sash_for_context(k))
        tab.bind("<Configure>", lambda _e, k=key: self._maybe_reset_initial_sash_for_context(k), add="+")

    def _set_initial_sash_for_context(self, key: str):
        ctx = self.contexts.get(key)
        pane = getattr(ctx, "main_pane", None)
        if pane is None:
            return
        try:
            width = pane.winfo_width()
            if width > 300:
                pos = min(max(420, int(width * 0.36)), 620)
                pane.sashpos(0, pos)
                ctx._initial_sash_done = True
        except Exception:
            pass

    def _maybe_reset_initial_sash_for_context(self, key: str):
        ctx = self.contexts.get(key)
        if ctx and not getattr(ctx, "_initial_sash_done", False):
            self.after(80, lambda k=key: self._set_initial_sash_for_context(k))

    def _build_action_bar(self, parent):
        self.action_bar = ttk.Frame(parent, style="Toolbar.TFrame", padding=(8, 6))
        self.action_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.action_bar.columnconfigure(7, weight=1)
        self.start_button = ttk.Button(self.action_bar, text="", style="Accent.TButton", command=self._start_crawl)
        self.start_button.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.stop_button = ttk.Button(self.action_bar, text="", style="Danger.TButton", command=self._stop_crawl, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 6), sticky="w")
        self.export_button = ttk.Button(self.action_bar, text="", command=self._export_results)
        self.export_button.grid(row=0, column=2, padx=(0, 6), sticky="w")
        self.import_links_button = ttk.Button(self.action_bar, text="", command=self._import_links_file)
        self.import_links_button.grid(row=0, column=3, padx=(0, 6), sticky="w")
        self.clear_button = ttk.Button(self.action_bar, text="", command=self._clear_results)
        self.clear_button.grid(row=0, column=4, padx=(0, 6), sticky="w")
        self.open_button = ttk.Button(self.action_bar, text="", command=self._open_output)
        self.open_button.grid(row=0, column=5, padx=(0, 12), sticky="w")
        self.toolbar_progress_label = ttk.Label(self.action_bar, text="", style="Toolbar.TLabel")
        self.toolbar_progress_label.grid(row=0, column=6, padx=(0, 6), sticky="w")
        self.toolbar_progress = ttk.Progressbar(self.action_bar, mode="determinate", maximum=100, value=0, length=260)
        self.toolbar_progress.grid(row=0, column=7, sticky="w")

    def _build_settings_panel(self, parent):
        """Build a single-column, wide, scrollable settings area.

        v0.6 returns to a clean one-column layout.  Each settings group is
        stacked vertically, while the full settings panel remains scrollable in
        both directions.  The language and country/region multi-select boxes are
        deliberately kept as large, visible list boxes instead of compact
        comboboxes, because users often need to select several Google lr/cr
        values at once.
        """
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.settings_scroll = ScrollableFrame(parent)
        self.settings_scroll.grid(row=0, column=0, sticky="nsew")
        panel = self.settings_scroll.inner
        panel.columnconfigure(0, weight=1)

        self.query_frame = ttk.LabelFrame(panel, text="Query", padding=10)
        self.query_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 8))
        self.crawl_frame = ttk.LabelFrame(panel, text="Crawl", padding=10)
        self.crawl_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.limit_frame = ttk.LabelFrame(panel, text="Limit", padding=10)
        self.limit_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.output_frame = ttk.LabelFrame(panel, text="Output", padding=10)
        self.output_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))

        for frame in [self.query_frame, self.crawl_frame, self.limit_frame, self.output_frame]:
            frame.columnconfigure(0, weight=0, minsize=110)
            frame.columnconfigure(1, weight=1)

        # Query settings
        self.query_mode_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.query_mode_label.grid(row=0, column=0, sticky="w", pady=3)
        self.query_mode_combo = ttk.Combobox(self.query_frame, state="readonly", width=42)
        self.query_mode_combo.grid(row=0, column=1, sticky="ew", pady=3)

        self.vertical_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.vertical_label.grid(row=1, column=0, sticky="w", pady=3)
        self.vertical_combo = ttk.Combobox(self.query_frame, state="readonly", width=42)
        self.vertical_combo.grid(row=1, column=1, sticky="ew", pady=3)

        self.baidu_sort_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.baidu_sort_label.grid(row=2, column=0, sticky="w", pady=3)
        self.baidu_sort_combo = ttk.Combobox(self.query_frame, state="readonly", width=42)
        self.baidu_sort_combo.grid(row=2, column=1, sticky="ew", pady=3)
        if getattr(self, "_building_context_key", "google") != "baidu":
            self.baidu_sort_label.grid_remove()
            self.baidu_sort_combo.grid_remove()

        self.backend_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.backend_label.grid(row=3, column=0, sticky="w", pady=3)
        self.backend_combo = ttk.Combobox(self.query_frame, state="readonly", width=42)
        self.backend_combo.grid(row=3, column=1, sticky="ew", pady=3)

        self.driver_path_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.driver_path_label.grid(row=4, column=0, sticky="w", pady=3)
        self.driver_path_var = tk.StringVar(value=str(Path(resource_path("tools/chromedriver.exe"))))
        driver_path_frame = ttk.Frame(self.query_frame, style="Panel.TFrame")
        driver_path_frame.grid(row=4, column=1, sticky="ew", pady=3)
        driver_path_frame.columnconfigure(0, weight=1)
        self.driver_path_entry = ttk.Entry(driver_path_frame, textvariable=self.driver_path_var)
        self.driver_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.driver_browse_button = ttk.Button(driver_path_frame, text="", command=self._browse_driver)
        self.driver_browse_button.grid(row=0, column=1, sticky="e")

        self.browser_binary_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.browser_binary_label.grid(row=5, column=0, sticky="w", pady=3)
        self.browser_binary_var = tk.StringVar(value=default_browser_binary_path())
        browser_binary_frame = ttk.Frame(self.query_frame, style="Panel.TFrame")
        browser_binary_frame.grid(row=5, column=1, sticky="ew", pady=3)
        browser_binary_frame.columnconfigure(0, weight=1)
        self.browser_binary_entry = ttk.Entry(browser_binary_frame, textvariable=self.browser_binary_var)
        self.browser_binary_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.binary_browse_button = ttk.Button(browser_binary_frame, text="", command=self._browse_browser_binary)
        self.binary_browse_button.grid(row=0, column=1, sticky="e")

        self.browser_wait_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.browser_wait_label.grid(row=6, column=0, sticky="w", pady=3)
        self.browser_wait_var = tk.IntVar(value=3500)
        ttk.Spinbox(self.query_frame, from_=0, to=60000, textvariable=self.browser_wait_var, width=14).grid(row=6, column=1, sticky="w", pady=3)

        self.browser_headless_var = tk.BooleanVar(value=False)
        self.browser_headless_check = ttk.Checkbutton(self.query_frame, text="", variable=self.browser_headless_var)
        self.browser_headless_check.grid(row=7, column=0, columnspan=2, sticky="w", pady=3)

        self.query_terms_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.query_terms_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(10, 3))
        self.query_text = tk.Text(self.query_frame, height=6, wrap="word", font=("Segoe UI", 9))
        self.query_text.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 3))
        self.query_frame.rowconfigure(9, weight=0)

        self.query_help_btn = ttk.Button(self.query_frame, text="", style="Link.TButton", command=lambda: self._show_help("query"))
        self.query_help_btn.grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.site_label = ttk.Label(self.query_frame, text="", style="Panel.TLabel")
        self.site_label.grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 3))
        # Multi-line domain input.  The backend already accepts one item per line
        # or semicolon-separated values; a Text widget makes this usable for long
        # source lists such as people.com.cn, xinhuanet.com, .gov.cn, .edu.cn.
        self.site_var = tk.StringVar()
        site_box = ttk.Frame(self.query_frame, style="Panel.TFrame")
        site_box.grid(row=12, column=0, columnspan=2, sticky="ew", pady=3)
        site_box.columnconfigure(0, weight=1)
        self.site_entry = tk.Text(site_box, height=4, wrap="none", font=("Segoe UI", 9), undo=True)
        site_y = ttk.Scrollbar(site_box, orient="vertical", command=self.site_entry.yview)
        site_x = ttk.Scrollbar(site_box, orient="horizontal", command=self.site_entry.xview)
        self.site_entry.configure(yscrollcommand=site_y.set, xscrollcommand=site_x.set)
        self.site_entry.grid(row=0, column=0, sticky="ew")
        site_y.grid(row=0, column=1, sticky="ns")
        site_x.grid(row=1, column=0, sticky="ew")
        self.site_help_btn = ttk.Button(self.query_frame, text="", style="Link.TButton", command=lambda: self._show_help("site"))
        self.site_help_btn.grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 2))

        # Crawl settings
        self.safe_label = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel")
        self.safe_label.grid(row=0, column=0, sticky="w", pady=3)
        self.safe_var = tk.StringVar(value="")
        self.safe_combo = ttk.Combobox(self.crawl_frame, textvariable=self.safe_var, state="readonly", values=["", "off", "medium", "high"], width=16)
        self.safe_combo.grid(row=0, column=1, sticky="w", pady=3)

        self.disable_filter_var = tk.BooleanVar(value=False)
        self.filter_check = ttk.Checkbutton(self.crawl_frame, text="", variable=self.disable_filter_var)
        self.filter_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=3)

        self.start_date_label = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel")
        self.start_date_label.grid(row=2, column=0, sticky="w", pady=3)
        self.start_date_entry = DateEntry(self.crawl_frame, self._t, self.icon_path, date.today())
        self.start_date_entry.grid(row=2, column=1, sticky="w", pady=3)

        self.end_date_label = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel")
        self.end_date_label.grid(row=3, column=0, sticky="w", pady=3)
        self.end_date_entry = DateEntry(self.crawl_frame, self._t, self.icon_path, date.today())
        self.end_date_entry.grid(row=3, column=1, sticky="w", pady=3)

        self.spin_vars = {}
        # name, default, minimum, maximum.  Post-fetch wait and empty-page retry
        # are intentionally visible because Google sometimes returns a shell page
        # with no result cards to non-browser HTTP clients.
        engine_key = getattr(self, "_building_context_key", "google")
        restart_default = 0 if engine_key == "baidu" else 4
        max_pages_default = 100 if engine_key == "baidu" else 30
        day_step_default = 0 if engine_key == "baidu" else 7
        rows = [
            ("max_pages", max_pages_default, 1, 1000),
            ("day_step", day_step_default, 0, 3650),
            ("per_page", 50, 1, 100),
            ("timeout", 15, 1, 300),
            ("post_fetch_wait_ms", 800, 0, 60000),
            ("empty_page_retry_count", 2, 0, 10),
            ("empty_page_retry_wait_ms", 1500, 0, 60000),
            ("no_new_pages_limit", 1, 1, 10),
            ("selenium_restart_pages", restart_default, 0, 1000),
        ]
        base = 4
        for idx, (name, default, min_value, max_value) in enumerate(rows):
            lab = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel")
            lab.grid(row=base + idx, column=0, sticky="w", pady=3)
            setattr(self, f"{name}_label", lab)
            var = tk.IntVar(value=default)
            self.spin_vars[name] = var
            ttk.Spinbox(self.crawl_frame, from_=min_value, to=max_value, textvariable=var, width=14).grid(row=base + idx, column=1, sticky="w", pady=3)

        self.max_pages_hint_label = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel", wraplength=360, foreground="#526871")
        self.max_pages_hint_label.grid(row=base + len(rows), column=0, columnspan=2, sticky="ew", pady=(2, 8))

        self.delay_vars = {}
        delay_defs = [("page_delay", 30000, 90000), ("slice_delay", 30000, 60000), ("error_delay", 60000, 180000)]
        delay_base = base + len(rows) + 1
        for j, (name, mn, mx) in enumerate(delay_defs, start=delay_base):
            lab = ttk.Label(self.crawl_frame, text="", style="Panel.TLabel")
            lab.grid(row=j, column=0, sticky="w", pady=3)
            setattr(self, f"{name}_label", lab)
            box = ttk.Frame(self.crawl_frame, style="Panel.TFrame")
            box.grid(row=j, column=1, sticky="w", pady=3)
            vmin = tk.IntVar(value=mn)
            vmax = tk.IntVar(value=mx)
            self.delay_vars[name] = (vmin, vmax)
            ttk.Spinbox(box, from_=0, to=9999999, textvariable=vmin, width=10).pack(side="left")
            ttk.Label(box, text=" - ", style="Panel.TLabel").pack(side="left")
            ttk.Spinbox(box, from_=0, to=9999999, textvariable=vmax, width=10).pack(side="left")

        # Language/country multi-selects.  IMPORTANT: create the Listbox widgets
        # with the same parent frame that manages their grid.  Previous versions
        # created them under limit_frame but gridded them inside nested frames,
        # which could make only the Clear button appear on some Tk builds.
        self.limit_frame.columnconfigure(0, weight=1)
        self.language_label = ttk.Label(self.limit_frame, text="", style="Panel.TLabel")
        self.language_label.grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.language_box = ttk.Frame(self.limit_frame, style="Panel.TFrame")
        self.language_box.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        self.language_box.columnconfigure(0, weight=1)
        self.language_box.rowconfigure(0, weight=1)
        self.language_list = tk.Listbox(
            self.language_box,
            selectmode="extended",
            height=9,
            width=48,
            exportselection=False,
            activestyle="dotbox",
        )
        lang_sb_y = ttk.Scrollbar(self.language_box, orient="vertical", command=self.language_list.yview)
        lang_sb_x = ttk.Scrollbar(self.language_box, orient="horizontal", command=self.language_list.xview)
        self.language_list.configure(yscrollcommand=lang_sb_y.set, xscrollcommand=lang_sb_x.set)
        self.language_list.grid(row=0, column=0, sticky="nsew")
        lang_sb_y.grid(row=0, column=1, sticky="ns")
        lang_sb_x.grid(row=1, column=0, sticky="ew")
        self.clear_lang_btn = ttk.Button(self.limit_frame, text="", command=lambda: self.language_list.selection_clear(0, tk.END))
        self.clear_lang_btn.grid(row=2, column=0, sticky="w", pady=(0, 10))

        self.country_label = ttk.Label(self.limit_frame, text="", style="Panel.TLabel")
        self.country_label.grid(row=3, column=0, sticky="w", pady=(4, 3))
        self.country_box = ttk.Frame(self.limit_frame, style="Panel.TFrame")
        self.country_box.grid(row=4, column=0, sticky="nsew", pady=(0, 4))
        self.country_box.columnconfigure(0, weight=1)
        self.country_box.rowconfigure(0, weight=1)
        self.country_list = tk.Listbox(
            self.country_box,
            selectmode="extended",
            height=11,
            width=48,
            exportselection=False,
            activestyle="dotbox",
        )
        country_sb_y = ttk.Scrollbar(self.country_box, orient="vertical", command=self.country_list.yview)
        country_sb_x = ttk.Scrollbar(self.country_box, orient="horizontal", command=self.country_list.xview)
        self.country_list.configure(yscrollcommand=country_sb_y.set, xscrollcommand=country_sb_x.set)
        self.country_list.grid(row=0, column=0, sticky="nsew")
        country_sb_y.grid(row=0, column=1, sticky="ns")
        country_sb_x.grid(row=1, column=0, sticky="ew")
        self.clear_country_btn = ttk.Button(self.limit_frame, text="", command=lambda: self.country_list.selection_clear(0, tk.END))
        self.clear_country_btn.grid(row=5, column=0, sticky="w", pady=(0, 2))

        # Output settings
        self.output_frame.columnconfigure(0, weight=0, minsize=110)
        self.output_frame.columnconfigure(1, weight=1)
        self.output_file_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.output_file_label.grid(row=0, column=0, sticky="w", pady=3)
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_path)
        self.output_entry.grid(row=0, column=1, sticky="ew", pady=3)
        self.browse_button = ttk.Button(self.output_frame, text="", command=self._browse_output)
        self.browse_button.grid(row=1, column=1, sticky="w", pady=(2, 8))
        self.output_format_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.output_format_label.grid(row=2, column=0, sticky="w", pady=3)
        self.output_format_combo = ttk.Combobox(self.output_frame, textvariable=self.output_format, values=OUTPUT_FORMATS, state="readonly", width=14)
        self.output_format_combo.grid(row=2, column=1, sticky="w", pady=3)
        self.output_format_combo.bind("<<ComboboxSelected>>", self._on_output_format_changed, add="+")
        self.content_folder_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_folder_label.grid(row=3, column=0, sticky="w", pady=(10, 3))
        content_dir_frame = ttk.Frame(self.output_frame, style="Panel.TFrame")
        content_dir_frame.grid(row=3, column=1, sticky="ew", pady=(10, 3))
        content_dir_frame.columnconfigure(0, weight=1)
        self.content_dir_entry = ttk.Entry(content_dir_frame, textvariable=self.content_dir_var)
        self.content_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.content_browse_button = ttk.Button(content_dir_frame, text="", command=self._browse_content_dir)
        self.content_browse_button.grid(row=0, column=1, sticky="e")

        self.content_threads_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_threads_label.grid(row=4, column=0, sticky="w", pady=3)
        self.content_threads_spin = ttk.Spinbox(self.output_frame, from_=1, to=32, textvariable=self.content_threads_var, width=14)
        self.content_threads_spin.grid(row=4, column=1, sticky="w", pady=3)

        self.content_fetch_mode_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_fetch_mode_label.grid(row=5, column=0, sticky="w", pady=3)
        self.content_fetch_mode_combo = ttk.Combobox(self.output_frame, textvariable=self.content_fetch_mode_var, state="readonly", width=34)
        self.content_fetch_mode_combo.grid(row=5, column=1, sticky="w", pady=3)

        self.content_delay_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_delay_label.grid(row=6, column=0, sticky="w", pady=3)
        content_delay_box = ttk.Frame(self.output_frame, style="Panel.TFrame")
        content_delay_box.grid(row=6, column=1, sticky="w", pady=3)
        ttk.Spinbox(content_delay_box, from_=0, to=9999999, textvariable=self.content_delay_min_var, width=10).pack(side="left")
        ttk.Label(content_delay_box, text=" - ", style="Panel.TLabel").pack(side="left")
        ttk.Spinbox(content_delay_box, from_=0, to=9999999, textvariable=self.content_delay_max_var, width=10).pack(side="left")

        self.content_receive_wait_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_receive_wait_label.grid(row=7, column=0, sticky="w", pady=3)
        ttk.Spinbox(self.output_frame, from_=0, to=9999999, textvariable=self.content_receive_wait_var, width=14).grid(row=7, column=1, sticky="w", pady=3)

        self.content_cleaning_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel")
        self.content_cleaning_label.grid(row=8, column=0, sticky="w", pady=3)
        self.content_cleaning_combo = ttk.Combobox(self.output_frame, textvariable=self.content_cleaning_var, state="readonly", width=34)
        self.content_cleaning_combo.grid(row=8, column=1, sticky="w", pady=3)

        self.content_selenium_fallback_check = ttk.Checkbutton(self.output_frame, text="", variable=self.content_selenium_fallback_var)
        self.content_selenium_fallback_check.grid(row=9, column=0, columnspan=2, sticky="w", pady=3)
        self.content_selenium_fallback_check.grid_remove()

        self.output_hint_label = ttk.Label(self.output_frame, text="", style="Panel.TLabel", wraplength=360, foreground="#526871")
        self.output_hint_label.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(8, 2))

        if getattr(self, "_building_context_key", "google") == "baidu":
            # Baidu is designed for Chinese web/news discovery; Google-only language
            # and country/region restrictions are intentionally hidden here.
            self.limit_frame.grid_remove()

        for wheel_widget in (self.query_text, self.language_list, self.country_list):
            self._bind_mousewheel(wheel_widget)

    def _build_results_panel(self, parent):
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=2)
        parent.columnconfigure(0, weight=1)

        self.preview_frame = ttk.LabelFrame(parent, text="Preview", padding=6)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.preview_frame.rowconfigure(1, weight=1)
        self.preview_frame.columnconfigure(0, weight=1)

        self.preview_toolbar = ttk.Frame(self.preview_frame, style="Panel.TFrame")
        self.preview_toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        # Compact two-line toolbar: keep all result-preview commands visible on smaller screens.
        for col in range(10):
            self.preview_toolbar.columnconfigure(col, weight=0)
        self.preview_toolbar.columnconfigure(9, weight=1)

        self.open_link_button = ttk.Button(self.preview_toolbar, text="", command=self._open_selected_link, style="Preview.TButton")
        self.open_link_button.grid(row=0, column=0, padx=(0, 4), pady=(0, 2), sticky="w")
        self.delete_selected_button = ttk.Button(self.preview_toolbar, text="", command=self._delete_selected_records, style="Preview.TButton")
        self.delete_selected_button.grid(row=0, column=1, padx=(0, 8), pady=(0, 2), sticky="w")

        self.sort_label = ttk.Label(self.preview_toolbar, text="", style="Preview.TLabel")
        self.sort_label.grid(row=0, column=2, padx=(0, 4), pady=(0, 2), sticky="w")
        self.sort_time_button = ttk.Button(self.preview_toolbar, text="", command=lambda: self._sort_records("time"), style="Preview.TButton")
        self.sort_time_button.grid(row=0, column=3, padx=(0, 4), pady=(0, 2), sticky="w")
        self.sort_title_button = ttk.Button(self.preview_toolbar, text="", command=lambda: self._sort_records("title"), style="Preview.TButton")
        self.sort_title_button.grid(row=0, column=4, padx=(0, 4), pady=(0, 2), sticky="w")
        self.sort_source_button = ttk.Button(self.preview_toolbar, text="", command=lambda: self._sort_records("source"), style="Preview.TButton")
        self.sort_source_button.grid(row=0, column=5, padx=(0, 8), pady=(0, 2), sticky="w")

        self.result_edit_menu = tk.Menu(self, tearoff=False)
        self.result_edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo_result_edit)
        self.result_edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo_result_edit)
        self.result_edit_menu.add_separator()
        self.result_edit_menu.add_command(label="Reset", accelerator="Ctrl+Shift+R", command=self._reset_result_preview)
        self.result_edit_button = ttk.Menubutton(self.preview_toolbar, text="", menu=self.result_edit_menu, style="Preview.TMenubutton")
        self.result_edit_button.grid(row=0, column=6, padx=(0, 4), pady=(0, 2), sticky="w")
        self.preview_count_var = tk.StringVar(value="")
        self.preview_count_label = ttk.Label(self.preview_toolbar, textvariable=self.preview_count_var, style="Preview.TLabel")
        self.preview_count_label.grid(row=0, column=7, columnspan=3, padx=(10, 2), pady=(0, 2), sticky="e")

        self.sample_scheme_label = ttk.Label(self.preview_toolbar, text="", style="Preview.TLabel")
        self.sample_scheme_label.grid(row=1, column=0, padx=(0, 4), pady=(0, 0), sticky="w")
        self.sample_scheme_var = tk.StringVar()
        self.sample_scheme_combo = ttk.Combobox(self.preview_toolbar, textvariable=self.sample_scheme_var, state="readonly", width=14)
        self.sample_scheme_combo.grid(row=1, column=1, columnspan=2, padx=(0, 6), pady=(0, 0), sticky="w")
        self.sample_count_label = ttk.Label(self.preview_toolbar, text="", style="Preview.TLabel")
        self.sample_count_label.grid(row=1, column=3, padx=(0, 4), pady=(0, 0), sticky="w")
        self.sample_count_var = tk.IntVar(value=20)
        self.sample_count_spin = ttk.Spinbox(self.preview_toolbar, from_=1, to=1000000, textvariable=self.sample_count_var, width=7)
        self.sample_count_spin.grid(row=1, column=4, padx=(0, 6), pady=(0, 0), sticky="w")
        self.sample_button = ttk.Button(self.preview_toolbar, text="", command=self._sample_records, style="Preview.TButton")
        self.sample_button.grid(row=1, column=5, padx=(0, 6), pady=(0, 0), sticky="w")
        self.download_content_button = ttk.Button(self.preview_toolbar, text="", command=self._download_selected_content, style="Preview.TButton")
        self.download_content_button.grid(row=1, column=6, padx=(0, 6), pady=(0, 0), sticky="w")
        self.download_all_content_button = ttk.Button(self.preview_toolbar, text="", command=self._download_all_content, style="Preview.TButton")
        self.download_all_content_button.grid(row=1, column=7, padx=(0, 6), pady=(0, 0), sticky="w")
        self.download_settings_button = ttk.Button(self.preview_toolbar, text="", command=self._open_content_settings_dialog, style="Preview.TButton")
        self.download_settings_button.grid(row=1, column=8, padx=(0, 6), pady=(0, 0), sticky="w")

        columns = ("no", "time", "title", "source", "published", "status", "words", "quality", "link")
        self.tree = ttk.Treeview(self.preview_frame, columns=columns, show="headings", height=16, selectmode="extended")
        for col, width in [("no", 58), ("time", 140), ("title", 330), ("source", 120), ("published", 110), ("status", 95), ("words", 70), ("quality", 70), ("link", 420)]:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_records("time" if c in ("published", "no") else c if c in ("title", "source") else "time"))
            self.tree.column(col, width=width, stretch=(col not in {"no", "words", "quality"}))
        ysb = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(self.preview_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        ysb.grid(row=1, column=1, sticky="ns")
        xsb.grid(row=2, column=0, sticky="ew")
        self.tree.bind("<Double-1>", lambda _e: self._open_selected_link(), add="+")
        self.tree.bind("<Return>", lambda _e: self._open_selected_link(), add="+")
        self.tree.bind("<Delete>", lambda _e: self._delete_selected_records(), add="+")
        self.tree.bind("<Button-3>", self._show_result_context_menu, add="+")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_preview_count(), add="+")
        self._bind_mousewheel(self.tree)

        self.result_menu = tk.Menu(self, tearoff=False)
        self.result_menu.add_command(label="Open link", command=self._open_selected_link)
        self.result_menu.add_command(label="Download selected content", command=self._download_selected_content)
        self.result_menu.add_command(label="Download all content", command=self._download_all_content)
        self.result_menu.add_command(label="Download settings", command=self._open_content_settings_dialog)
        self.result_menu.add_command(label="Delete selected", command=self._delete_selected_records)
        self.result_menu.add_separator()
        self.result_menu.add_command(label="Sample current preview", command=self._sample_records)
        self.result_menu.add_command(label="Undo", command=self._undo_result_edit)
        self.result_menu.add_command(label="Redo", command=self._redo_result_edit)
        self.result_menu.add_command(label="Reset", command=self._reset_result_preview)
        self.result_menu.add_separator()
        self.result_menu.add_command(label="Sort by time", command=lambda: self._sort_records("time"))
        self.result_menu.add_command(label="Sort by title", command=lambda: self._sort_records("title"))
        self.result_menu.add_command(label="Sort by source", command=lambda: self._sort_records("source"))

        self.log_frame = ttk.LabelFrame(parent, text="Log", padding=6)
        self.log_frame.grid(row=1, column=0, sticky="nsew")
        self.log_frame.rowconfigure(0, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(self.log_frame, height=9, wrap="word", font=("Consolas", 9))
        log_sb = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_sb.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_sb.grid(row=0, column=1, sticky="ns")
        self._bind_mousewheel(self.log_text)

    def _t(self, key):
        return t(self.ui_lang, key)

    def _set_language(self, lang):
        old_lang = getattr(self, "ui_lang", lang)
        self.ui_lang = lang
        self.ui_lang_var.set(lang)
        try:
            self.notebook.tab(0, text=t(lang, "google_tab"))
            self.notebook.tab(1, text=t(lang, "baidu_tab"))
        except Exception:
            pass
        self._rebuild_menu_labels()
        active_key = getattr(self, "active_context_key", None) or "google"
        for key in ("google", "baidu"):
            if key in getattr(self, "contexts", {}):
                self._activate_context(key)
                self._apply_language_to_active_context(lang, old_lang)
        if active_key in getattr(self, "contexts", {}):
            self._activate_context(active_key)
        try:
            self.status_var.set(t(lang, "status_ready"))
        except Exception:
            pass

    def _apply_language_to_active_context(self, lang, old_lang=None):
        old_lang = old_lang or lang
        self._update_option_lists(old_lang)
        mapping = {
            self.query_frame: "query_settings",
            self.limit_frame: "limit_settings",
            self.crawl_frame: "crawl_settings",
            self.output_frame: "output_settings",
            self.preview_frame: "preview",
            self.log_frame: "log",
            self.query_mode_label: "query_mode",
            self.vertical_label: "search_vertical",
            self.baidu_sort_label: "baidu_sort",
            self.backend_label: "fetch_backend",
            self.driver_path_label: "browser_driver_path",
            self.driver_browse_button: "browse_driver",
            self.browser_binary_label: "browser_binary_path",
            self.binary_browse_button: "browse_binary",
            self.browser_wait_label: "browser_wait_ms",
            self.browser_headless_check: "browser_headless",
            self.query_terms_label: "query_terms",
            self.query_help_btn: "query_help_link",
            self.site_label: "site_filters",
            self.site_help_btn: "site_help_link",
            self.language_label: "result_languages",
            self.country_label: "country_regions",
            self.clear_lang_btn: "clear_selection",
            self.clear_country_btn: "clear_selection",
            self.safe_label: "safe",
            self.filter_check: "filter",
            self.start_date_label: "start_date",
            self.end_date_label: "end_date",
            self.max_pages_label: "max_pages",
            self.day_step_label: "day_step",
            self.per_page_label: "per_page",
            self.timeout_label: "timeout",
            self.post_fetch_wait_ms_label: "post_fetch_wait_ms",
            self.empty_page_retry_count_label: "empty_page_retry_count",
            self.empty_page_retry_wait_ms_label: "empty_page_retry_wait_ms",
            self.no_new_pages_limit_label: "no_new_pages_limit",
            self.selenium_restart_pages_label: "selenium_restart_pages",
            self.max_pages_hint_label: "max_pages_hint",
            self.page_delay_label: "page_delay",
            self.slice_delay_label: "slice_delay",
            self.error_delay_label: "error_delay",
            self.output_file_label: "output_file",
            self.output_format_label: "output_format",
            self.content_folder_label: "content_folder",
            self.content_browse_button: "browse",
            self.content_threads_label: "content_threads",
            self.content_fetch_mode_label: "content_fetch_mode",
            self.content_delay_label: "content_delay",
            self.content_receive_wait_label: "content_receive_wait",
            self.content_cleaning_label: "content_cleaning_scheme",
            self.content_selenium_fallback_check: "content_selenium_fallback",
            self.output_hint_label: "output_hint",
            self.browse_button: "browse",
            self.start_button: "start",
            self.stop_button: "stop",
            self.export_button: "export",
            self.import_links_button: "preview_import_short",
            self.clear_button: "clear",
            self.open_button: "open_output",
            self.open_link_button: "preview_open_short",
            self.delete_selected_button: "preview_delete_short",
            self.sort_label: "preview_sort_label",
            self.sort_time_button: "preview_sort_time_short",
            self.sort_title_button: "preview_sort_title_short",
            self.sort_source_button: "preview_sort_source_short",
            self.sample_scheme_label: "preview_sample_label",
            self.sample_count_label: "sample_count",
            self.sample_button: "preview_sample_short",
            self.download_content_button: "preview_download_selected_short",
            self.download_all_content_button: "preview_download_all_short",
            self.download_settings_button: "preview_download_settings_short",
            self.result_edit_button: "preview_edit_short",
        }
        for widget, key in mapping.items():
            try:
                widget.config(text=t(lang, key))
            except Exception:
                pass
        if lang == "zh_sim":
            heads = {"no": "序号", "time": "采集时间", "title": "标题", "source": "来源", "published": "页面时间", "status": "状态", "words": "词数", "quality": "质量", "link": "链接"}
            progress_text = "进度"
        elif lang == "zh_tra":
            heads = {"no": "序號", "time": "採集時間", "title": "標題", "source": "來源", "published": "頁面時間", "status": "狀態", "words": "詞數", "quality": "品質", "link": "連結"}
            progress_text = "進度"
        else:
            heads = {"no": "No.", "time": "Collected", "title": "Title", "source": "Source", "published": "Published", "status": "Status", "words": "Words", "quality": "Quality", "link": "Link"}
            progress_text = "Progress"
        try:
            for c, h in heads.items():
                self.tree.heading(c, text=h)
            self.toolbar_progress_label.config(text=progress_text)
        except Exception:
            pass
        self._update_preview_count()
        if hasattr(self, "sample_scheme_combo"):
            current_key = self._current_sample_scheme_key()
            self.sample_scheme_combo["values"] = [t(lang, k) for k in ("sample_simple", "sample_systematic", "sample_by_source")]
            key_to_label = {"simple": t(lang, "sample_simple"), "systematic": t(lang, "sample_systematic"), "source": t(lang, "sample_by_source")}
            self.sample_scheme_combo.set(key_to_label.get(current_key, t(lang, "sample_simple")))
        if hasattr(self, "result_edit_menu"):
            self.result_edit_menu.entryconfig(0, label=t(lang, "undo"))
            self.result_edit_menu.entryconfig(1, label=t(lang, "redo"))
            self.result_edit_menu.entryconfig(3, label=t(lang, "reset_preview"))

    def _rebuild_menu_labels(self):
        lang = self.ui_lang
        self.menu_bar.entryconfig(0, label=t(lang, "menu_file"))
        self.menu_bar.entryconfig(1, label=t(lang, "menu_view"))
        self.menu_bar.entryconfig(2, label=t(lang, "menu_tools"))
        self.menu_bar.entryconfig(3, label=t(lang, "menu_help"))
        self.file_menu.entryconfig(0, label=t(lang, "menu_import_links"))
        self.file_menu.entryconfig(1, label=t(lang, "menu_export"))
        self.file_menu.entryconfig(3, label=t(lang, "menu_exit"))
        self.view_menu.entryconfig(0, label=t(lang, "menu_language"))
        self.tools_menu.entryconfig(0, label=t(lang, "menu_download_selected"))
        self.tools_menu.entryconfig(1, label=t(lang, "download_all_content"))
        self.tools_menu.entryconfig(2, label=t(lang, "download_settings_title"))
        self.tools_menu.entryconfig(3, label=t(lang, "menu_settings"))
        self.help_menu.entryconfig(0, label=t(lang, "menu_user_guide"))
        self.help_menu.entryconfig(1, label=t(lang, "menu_parameter_guide"))
        self.help_menu.entryconfig(3, label=t(lang, "menu_about"))
        for idx, opt in enumerate(APP_LANGS):
            self.lang_menu.entryconfig(idx, label=label_for(opt, lang))
        if hasattr(self, "result_menu"):
            labels = [
                "open_link", "download_selected_content", "download_all_content", "download_settings_title", "delete_selected", None, "sample_current",
                "undo", "redo", "reset_preview", None,
                "sort_by_time", "sort_by_title", "sort_by_source",
            ]
            for idx, key in enumerate(labels):
                if key:
                    self.result_menu.entryconfig(idx, label=t(lang, key))
        if hasattr(self, "result_edit_menu"):
            self.result_edit_menu.entryconfig(0, label=t(lang, "undo"))
            self.result_edit_menu.entryconfig(1, label=t(lang, "redo"))
            self.result_edit_menu.entryconfig(3, label=t(lang, "reset_preview"))

    def _current_combo_key(self, combo, options, lang, default_key):
        label = combo.get()
        opt = option_by_label(options, label, lang)
        return opt.get("key") if opt else default_key

    def _sort_options_for_ui(self, options, lang, value_key=None):
        """Sort no-restriction first; then alphabetically, or by pinyin if available."""
        none_items = [o for o in options if not o.get(value_key or "") or o.get("key") == "none"]
        rest = [o for o in options if o not in none_items]

        def key_en(o):
            return (label_for(o, "en") or "").lower()

        if lang.startswith("zh"):
            try:
                from pypinyin import lazy_pinyin  # optional, not required

                def key_func(o):
                    label = label_for(o, lang)
                    return "".join(lazy_pinyin(label)).lower()
            except Exception:
                # Fallback: still alphabetic and stable by Google's English label.
                key_func = key_en
        else:
            key_func = key_en
        return none_items + sorted(rest, key=lambda o: (key_func(o), o.get(value_key or "key", "")))

    def _update_option_lists(self, previous_lang=None):
        previous_lang = previous_lang or self.ui_lang
        lang = self.ui_lang
        query_options = getattr(self, "current_query_mode_options", QUERY_MODE_OPTIONS)
        query_key = self._current_combo_key(self.query_mode_combo, query_options, previous_lang, "single") if hasattr(self, "query_mode_combo") else "single"
        vertical_options = getattr(self, "current_vertical_options", VERTICAL_OPTIONS)
        default_vertical = default_vertical_for_engine(getattr(self, "active_context_key", "google"))
        vertical_key = self._current_combo_key(self.vertical_combo, vertical_options, previous_lang, default_vertical) if hasattr(self, "vertical_combo") else default_vertical
        backend_key = self._current_combo_key(self.backend_combo, FETCH_BACKEND_OPTIONS, previous_lang, "selenium_chrome") if hasattr(self, "backend_combo") else "selenium_chrome"
        content_cleaning_key = self._current_combo_key(self.content_cleaning_combo, CONTENT_CLEANING_OPTIONS, previous_lang, self.defaults.get("content_cleaning_scheme", "auto")) if hasattr(self, "content_cleaning_combo") and self.content_cleaning_combo.get() else self.settings.get("content_cleaning_scheme", self.defaults.get("content_cleaning_scheme", "auto"))
        content_fetch_key = self._current_combo_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, previous_lang, self.defaults.get("content_fetch_mode", "mixed")) if hasattr(self, "content_fetch_mode_combo") and self.content_fetch_mode_combo.get() else self.settings.get("content_fetch_mode", self.defaults.get("content_fetch_mode", "mixed"))

        def selected_values(listbox, options, value_key, old_lang):
            values = []
            for idx in listbox.curselection():
                label = listbox.get(idx)
                opt = option_by_label(options, label, old_lang, value_key)
                if opt and opt.get(value_key):
                    values.append(opt.get(value_key))
            return values

        selected_lang_values = selected_values(self.language_list, LANGUAGE_OPTIONS, "lr", previous_lang) if hasattr(self, "language_list") else []
        selected_country_values = selected_values(self.country_list, COUNTRY_OPTIONS, "cr", previous_lang) if hasattr(self, "country_list") else []

        if query_key not in {opt.get("key") for opt in query_options}:
            query_key = "single"
        self.query_mode_combo["values"] = labels_for(query_options, lang)
        for opt in query_options:
            if opt.get("key") == query_key:
                self.query_mode_combo.set(label_for(opt, lang))
                break
        self.vertical_combo["values"] = labels_for(vertical_options, lang)
        if vertical_key not in {opt.get("key") for opt in vertical_options}:
            vertical_key = default_vertical
        for opt in vertical_options:
            if opt.get("key") == vertical_key:
                self.vertical_combo.set(label_for(opt, lang))
                break
        if hasattr(self, "baidu_sort_combo"):
            current_baidu_sort = self._current_combo_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, previous_lang or lang, self.settings.get("baidu_sort", self.defaults.get("baidu_sort", "focus"))) if self.baidu_sort_combo.get() else self.settings.get("baidu_sort", self.defaults.get("baidu_sort", "focus"))
            self.baidu_sort_combo["values"] = labels_for(BAIDU_SORT_OPTIONS, lang)
            self._set_combo_by_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, current_baidu_sort)
        self.backend_combo["values"] = labels_for(FETCH_BACKEND_OPTIONS, lang)
        for opt in FETCH_BACKEND_OPTIONS:
            if opt.get("key") == backend_key:
                self.backend_combo.set(label_for(opt, lang))
        if hasattr(self, "content_fetch_mode_combo"):
            self.content_fetch_mode_combo["values"] = labels_for(CONTENT_FETCH_MODE_OPTIONS, lang)
            self._set_combo_by_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, content_fetch_key)
        if hasattr(self, "content_cleaning_combo"):
            self.content_cleaning_combo["values"] = labels_for(CONTENT_CLEANING_OPTIONS, lang)
            self._set_combo_by_key(self.content_cleaning_combo, CONTENT_CLEANING_OPTIONS, content_cleaning_key)

        self.current_language_options = self._sort_options_for_ui(LANGUAGE_OPTIONS, lang, "lr")
        self.current_country_options = self._sort_options_for_ui(COUNTRY_OPTIONS, lang, "cr")
        self.language_list.delete(0, tk.END)
        self.country_list.delete(0, tk.END)
        for opt in self.current_language_options:
            self.language_list.insert(tk.END, label_for(opt, lang, True, "lr"))
        for opt in self.current_country_options:
            self.country_list.insert(tk.END, label_for(opt, lang, True, "cr"))
        for i, opt in enumerate(self.current_language_options):
            if opt.get("lr") in selected_lang_values:
                self.language_list.selection_set(i)
        for i, opt in enumerate(self.current_country_options):
            if opt.get("cr") in selected_country_values:
                self.country_list.selection_set(i)

    def _show_text_window(self, title, text, geometry="880x680"):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(geometry)
        win.transient(self)
        self._apply_icon(win)
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word", font=("Segoe UI", 10))
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        txt.insert("1.0", text)
        txt.config(state="disabled")

    def _show_about(self):
        win = tk.Toplevel(self)
        win.title(t(self.ui_lang, "menu_about"))
        win.geometry("800x600")
        win.transient(self)
        self._apply_icon(win)
        header = tk.Frame(win, bg=self.colors["navy"], padx=18, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="BFSU WebLens", bg=self.colors["navy"], fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(header, text=t(self.ui_lang, "subtitle"), bg=self.colors["navy"], fg="#D8E3E8", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        txt = tk.Text(body, wrap="word", font=("Segoe UI", 10), relief="flat", padx=8, pady=8)
        sb = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        txt.insert("1.0", t(self.ui_lang, "about"))
        txt.config(state="disabled")
        self._bind_mousewheel(txt)

    def _show_user_guide(self):
        self._show_text_window(t(self.ui_lang, "user_guide_title"), t(self.ui_lang, "user_guide_text"), "920x720")

    def _show_parameter_guide(self):
        self._show_text_window(t(self.ui_lang, "parameter_guide_title"), t(self.ui_lang, "parameter_guide_text"), "940x760")

    def _show_help(self, kind):
        title = t(self.ui_lang, "help_query_title" if kind == "query" else "help_site_title")
        text = t(self.ui_lang, "query_help_text" if kind == "query" else "site_help_text")
        self._show_text_window(title, text, "820x620")

    def _show_settings(self):
        win = tk.Toplevel(self)
        win.title(t(self.ui_lang, "settings_title"))
        win.geometry("820x420")
        win.transient(self)
        self._apply_icon(win)
        frame = ttk.Frame(win, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t(self.ui_lang, "settings_title"), font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(frame, text=t(self.ui_lang, "settings_saved_hint"), wraplength=760).pack(anchor="w", pady=(0, 10))
        ttk.Label(frame, text=t(self.ui_lang, "user_agent_label")).pack(anchor="w")
        txt = tk.Text(frame, height=5, wrap="word", font=("Consolas", 9))
        txt.pack(fill="both", expand=True, pady=(4, 8))
        txt.insert("1.0", self.user_agent_var.get())
        self._bind_mousewheel(txt)
        hint = ttk.Label(frame, text=t(self.ui_lang, "user_agent_hint"), wraplength=760)
        hint.pack(anchor="w", pady=(0, 8))
        path_hint = ttk.Label(frame, text=t(self.ui_lang, "settings_file_hint", path=str(self.settings_path)), wraplength=760)
        path_hint.pack(anchor="w", pady=(0, 8))
        btns = ttk.Frame(frame)
        btns.pack(fill="x")
        def apply_settings(close=False):
            value = txt.get("1.0", "end").strip() or DEFAULT_USER_AGENT
            self.user_agent_var.set(value)
            self._save_settings()
            self._log(t(self.ui_lang, "settings_saved"))
            if close:
                win.destroy()
        ttk.Button(btns, text=t(self.ui_lang, "reset_default"), command=lambda: (txt.delete("1.0", "end"), txt.insert("1.0", DEFAULT_USER_AGENT))).pack(side="left")
        ttk.Button(btns, text=t(self.ui_lang, "reset_all_defaults"), command=lambda: self._reset_all_settings_to_defaults(win)).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text=t(self.ui_lang, "apply"), command=lambda: apply_settings(False)).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text=t(self.ui_lang, "ok"), command=lambda: apply_settings(True)).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text=t(self.ui_lang, "close"), command=win.destroy).pack(side="right")

    def _bind_shortcuts(self):
        self.bind_all("<F5>", lambda _e: self._start_crawl())
        self.bind_all("<Control-Return>", lambda _e: self._start_crawl())
        self.bind_all("<Escape>", lambda _e: self._stop_crawl())
        self.bind_all("<Control-e>", lambda _e: self._export_results())
        self.bind_all("<Control-E>", lambda _e: self._export_results())
        self.bind_all("<Control-l>", lambda _e: self._clear_results())
        self.bind_all("<Control-L>", lambda _e: self._clear_results())
        self.bind_all("<Control-o>", lambda _e: self._open_output())
        self.bind_all("<Control-O>", lambda _e: self._open_output())
        self.bind_all("<Control-comma>", lambda _e: self._show_settings())
        self.bind_all("<Control-i>", lambda _e: self._import_links_file())
        self.bind_all("<Control-I>", lambda _e: self._import_links_file())
        self.bind_all("<Control-d>", lambda _e: self._download_selected_content())
        self.bind_all("<Control-D>", lambda _e: self._download_selected_content())
        self.bind_all("<Control-Shift-D>", lambda _e: self._download_all_content())
        self.bind_all("<Control-Shift-d>", lambda _e: self._download_all_content())
        self.bind_all("<Control-z>", lambda _e: self._undo_result_edit())
        self.bind_all("<Control-Z>", lambda _e: self._undo_result_edit())
        self.bind_all("<Control-y>", lambda _e: self._redo_result_edit())
        self.bind_all("<Control-Y>", lambda _e: self._redo_result_edit())
        self.bind_all("<Control-Shift-R>", lambda _e: self._reset_result_preview())
        self.bind_all("<Control-Shift-r>", lambda _e: self._reset_result_preview())

    def _bind_mousewheel(self, widget):
        def on_mousewheel(event):
            try:
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
            return "break"
        def on_shift_mousewheel(event):
            try:
                widget.xview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
            return "break"
        widget.bind("<MouseWheel>", on_mousewheel, add="+")
        widget.bind("<Shift-MouseWheel>", on_shift_mousewheel, add="+")
        widget.bind("<Button-4>", lambda e: (widget.yview_scroll(-1, "units"), "break"), add="+")
        widget.bind("<Button-5>", lambda e: (widget.yview_scroll(1, "units"), "break"), add="+")

    def _browse_driver(self):
        self._ensure_active_context_from_tab()
        path = filedialog.askopenfilename(
            title=t(self.ui_lang, "select_driver"),
            filetypes=[("WebDriver", "chromedriver.exe msedgedriver.exe *.exe"), ("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.driver_path_var.set(path)

    def _browse_browser_binary(self):
        self._ensure_active_context_from_tab()
        path = filedialog.askopenfilename(
            title=t(self.ui_lang, "select_browser_binary"),
            filetypes=[("Browser executable", "chrome.exe msedge.exe *.exe"), ("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.browser_binary_var.set(path)

    def _browse_output(self):
        self._ensure_active_context_from_tab()
        fmt = self.output_format.get() or "xlsx"
        filetypes = [(fmt.upper(), f"*.{fmt}"), ("All files", "*.*")]
        path = filedialog.asksaveasfilename(title=t(self.ui_lang, "select_output"), defaultextension=f".{fmt}", filetypes=filetypes)
        if path:
            self.output_path.set(self._replace_output_suffix(path, fmt))

    def _browse_content_dir(self):
        self._ensure_active_context_from_tab()
        path = filedialog.askdirectory(title=t(self.ui_lang, "select_content_folder"))
        if path:
            self.content_dir_var.set(path)

    def _replace_output_suffix(self, path, fmt):
        fmt = (fmt or "xlsx").strip().lower().lstrip(".")
        if not path:
            return path
        p = Path(path)
        known = {".xlsx", ".csv", ".txt", ".docx", ".xml"}
        if p.suffix.lower() in known or not p.suffix:
            return str(p.with_suffix("." + fmt))
        return str(p)

    def _on_output_format_changed(self, _event=None):
        fmt = self.output_format.get() or "xlsx"
        self.output_path.set(self._replace_output_suffix(self.output_path.get().strip(), fmt))

    def _get_site_filters_text(self) -> str:
        """Return the multi-line site/domain filter text from the active panel."""
        try:
            if isinstance(self.site_entry, tk.Text):
                text = self.site_entry.get("1.0", "end").strip()
                self.site_var.set(text)
                return text
        except Exception:
            pass
        try:
            return self.site_var.get().strip()
        except Exception:
            return ""

    def _set_site_filters_text(self, text: str) -> None:
        """Set the active panel's site/domain filter text safely."""
        text = text or ""
        try:
            self.site_var.set(text)
        except Exception:
            pass
        try:
            if isinstance(self.site_entry, tk.Text):
                self.site_entry.delete("1.0", "end")
                if text:
                    self.site_entry.insert("1.0", text)
        except Exception:
            pass

    def _selected_multi_values(self, listbox, options, value_key):
        vals = []
        for idx in listbox.curselection():
            label = listbox.get(idx)
            opt = option_by_label(options, label, self.ui_lang, value_key)
            if opt and opt.get(value_key):
                vals.append(opt[value_key])
        return vals

    def _build_config(self):
        self._ensure_active_context_from_tab()
        mode_label = self.query_mode_combo.get()
        mode_opt = option_by_label(getattr(self, "current_query_mode_options", QUERY_MODE_OPTIONS), mode_label, self.ui_lang)
        mode = mode_opt["key"] if mode_opt else "single"
        vertical_label = self.vertical_combo.get()
        vertical_options = getattr(self, "current_vertical_options", VERTICAL_OPTIONS)
        default_vertical = default_vertical_for_engine(getattr(self, "active_context_key", "google"))
        vert_opt = option_by_label(vertical_options, vertical_label, self.ui_lang)
        vertical = vert_opt["key"] if vert_opt else default_vertical
        backend_label = self.backend_combo.get()
        backend_opt = option_by_label(FETCH_BACKEND_OPTIONS, backend_label, self.ui_lang)
        fetch_backend = backend_opt["key"] if backend_opt else "requests"
        baidu_sort = self._current_combo_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, self.ui_lang, self.defaults.get("baidu_sort", "focus")) if hasattr(self, "baidu_sort_combo") else "focus"
        raw_text = self.query_text.get("1.0", "end").strip()
        terms = split_text_terms(raw_text)
        if not raw_text:
            raise ValueError(t(self.ui_lang, "invalid_query"))
        start_d = self.start_date_entry.get_date()
        end_d = self.end_date_entry.get_date()
        if start_d > end_d:
            raise ValueError(t(self.ui_lang, "invalid_date"))
        out = self.output_path.get().strip()
        if not out:
            raise ValueError(t(self.ui_lang, "invalid_output"))
        numbers = {k: v.get() for k, v in self.spin_vars.items()}
        delays = {k: (v[0].get(), v[1].get()) for k, v in self.delay_vars.items()}
        for mn, mx in delays.values():
            if mn < 0 or mx < 0 or mn > mx:
                raise ValueError(t(self.ui_lang, "invalid_numeric"))
        if numbers["max_pages"] < 1 or numbers["day_step"] < 0 or numbers["per_page"] < 1 or numbers["timeout"] < 1:
            raise ValueError(t(self.ui_lang, "invalid_numeric"))
        if numbers["post_fetch_wait_ms"] < 0 or numbers["empty_page_retry_count"] < 0 or numbers["empty_page_retry_wait_ms"] < 0 or numbers["no_new_pages_limit"] < 1 or self.browser_wait_var.get() < 0:
            raise ValueError(t(self.ui_lang, "invalid_numeric"))
        if int(self.content_threads_var.get()) < 1:
            raise ValueError(t(self.ui_lang, "invalid_numeric"))
        if getattr(self, "active_context_key", "google") == "baidu":
            lang_values = []
            country_values = []
        else:
            lang_values = self._selected_multi_values(self.language_list, getattr(self, "current_language_options", LANGUAGE_OPTIONS), "lr")
            country_values = self._selected_multi_values(self.country_list, getattr(self, "current_country_options", COUNTRY_OPTIONS), "cr")
        language_lr = "|".join(lang_values)
        country_cr = "|".join(country_values)
        site_filters = split_text_terms(self._get_site_filters_text())
        return CollectorConfig(
            query_mode=mode,
            query_terms=terms,
            raw_query=raw_text if mode == "raw" else "",
            site_filters=site_filters,
            search_vertical=vertical,
            fetch_backend=fetch_backend,
            language_lr=language_lr,
            country_cr=country_cr,
            safe=self.safe_var.get().strip(),
            disable_filter=self.disable_filter_var.get(),
            start_date=start_d,
            end_date=end_d,
            day_step=numbers["day_step"],
            max_pages=numbers["max_pages"],
            per_page=numbers["per_page"],
            page_delay_min_ms=delays["page_delay"][0],
            page_delay_max_ms=delays["page_delay"][1],
            slice_delay_min_ms=delays["slice_delay"][0],
            slice_delay_max_ms=delays["slice_delay"][1],
            error_delay_min_ms=delays["error_delay"][0],
            error_delay_max_ms=delays["error_delay"][1],
            timeout_seconds=numbers["timeout"],
            max_retries=2,
            user_agent=self.user_agent_var.get().strip() or DEFAULT_USER_AGENT,
            post_fetch_wait_ms=numbers["post_fetch_wait_ms"],
            browser_wait_ms=self.browser_wait_var.get(),
            browser_headless=self.browser_headless_var.get(),
            browser_driver_path=self.driver_path_var.get().strip(),
            browser_binary_path=self.browser_binary_var.get().strip(),
            empty_page_retry_count=numbers["empty_page_retry_count"],
            empty_page_retry_wait_ms=numbers["empty_page_retry_wait_ms"],
            no_new_pages_limit=numbers["no_new_pages_limit"],
            selenium_restart_pages=numbers.get("selenium_restart_pages", 4),
            baidu_sort=baidu_sort,
        )

    def _start_crawl(self):
        self._ensure_active_context_from_tab()
        if self.worker and self.worker.is_alive():
            return
        self._save_settings()
        try:
            cfg = self._build_config()
        except Exception as e:
            messagebox.showerror(t(self.ui_lang, "validation_error"), str(e))
            return
        self.records = []
        self.original_records = []
        self.undo_stack = []
        self.redo_stack = []
        self._clear_tree()
        self.log_text.delete("1.0", "end")
        self.stop_event.clear()
        self.progress.config(mode="determinate", maximum=100, value=0)
        self.toolbar_progress.config(maximum=100, value=0)
        self.status_var.set(t(self.ui_lang, "status_running"))
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self._sync_active_context_state()
        ctx_key = getattr(self, "active_context_key", "google")
        self.worker_context_key = ctx_key
        self.worker = threading.Thread(target=self._worker_run, args=(cfg, ctx_key), daemon=True)
        self.worker.start()

    def _worker_run(self, cfg, ctx_key):
        def put_ctx(payload):
            self.event_queue.put(("__context__", ctx_key, payload))
        try:
            for event in crawl(cfg, stop_checker=self.stop_event.is_set):
                put_ctx(event)
        except StopCrawl:
            put_ctx(("stopped", t(self.ui_lang, "status_stopped")))
        except BrowserStartupError as exc:
            put_ctx(("error", f"{t(self.ui_lang, 'browser_startup_hint')}\n{exc}"))
        except NetworkAccessError as exc:
            put_ctx(("network", f"{t(self.ui_lang, 'network_hint')}\n{exc}"))
        except Exception as exc:
            put_ctx(("error", str(exc)))
        finally:
            put_ctx(("finished", None))

    def _poll_queue(self):
        try:
            while True:
                item = self.event_queue.get_nowait()
                if isinstance(item, tuple) and len(item) == 3 and item[0] == "__context__":
                    _tag, ctx_key, payload = item
                    self._handle_context_event(ctx_key, payload)
                else:
                    self._handle_event(item)
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _handle_context_event(self, ctx_key, item):
        previous = getattr(self, "active_context_key", None)
        if ctx_key in getattr(self, "contexts", {}):
            self._activate_context(ctx_key)
        self._handle_event(item)
        self._sync_active_context_state()
        if previous in getattr(self, "contexts", {}) and previous != ctx_key:
            self._activate_context(previous)

    def _set_progress(self, value, maximum=100):
        value = max(0, min(value, maximum))
        self.progress.config(maximum=maximum, value=value)
        self.toolbar_progress.config(maximum=maximum, value=value)

    def _handle_event(self, item):
        if isinstance(item, tuple):
            kind, msg = item
            if kind == "content_result":
                rec, result = msg
                self._handle_content_result(rec, result)
            elif kind == "content_progress":
                self._handle_content_progress(msg)
            elif kind == "content_finished":
                self._handle_content_finished(msg)
            elif kind == "finished":
                self._on_finished()
            elif kind == "network":
                self._log(str(msg))
                messagebox.showwarning(APP_NAME, str(msg))
            elif kind == "error":
                self._log("[ERROR] " + str(msg))
                messagebox.showerror(APP_NAME, str(msg))
            elif kind == "stopped":
                self._log(str(msg))
                self.status_var.set(t(self.ui_lang, "status_stopped"))
            return
        event = item
        if event.event_type == "slice" and event.data:
            total = int(event.data.get("slice_total") or 100)
            index = int(event.data.get("slice_index") or 1)
            # Move to the start of this slice; final completion is set in _on_finished.
            self._set_progress(index - 1, total)
            self.status_var.set(event.message)
            self._log(event.message)
        elif event.event_type == "record" and event.record:
            self.records.append(event.record)
            self.original_records.append(event.record)
            self._add_record_to_tree(event.record)
        elif event.event_type == "checkpoint":
            self._log(event.message)
            if self.records:
                try:
                    self._export_results(show_message=False)
                    self._log(t(self.ui_lang, "checkpoint_saved", n=len(self.records), path=self.output_path.get().strip()))
                except Exception as e:
                    self._log("[CHECKPOINT EXPORT ERROR] " + str(e))
        elif event.event_type == "blocked":
            self._log("[BLOCKED] " + event.message)
            messagebox.showwarning(APP_NAME, event.message)
        elif event.event_type == "done":
            self._log(event.message)
            self._set_progress(100, 100)
        else:
            self._log(event.message)

    def _on_finished(self):
        if self.stop_event.is_set():
            self.status_var.set(t(self.ui_lang, "status_stopped"))
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            return
        self._set_progress(100, 100)
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.records:
            try:
                self._export_results(show_message=False)
                self.status_var.set(t(self.ui_lang, "status_done"))
            except Exception as e:
                self._log("[EXPORT ERROR] " + str(e))
        else:
            self.status_var.set(t(self.ui_lang, "no_records"))

    def _stop_crawl(self):
        self._ensure_active_context_from_tab()
        self.stop_event.set()
        self.content_stop_event.set()
        self.status_var.set(t(self.ui_lang, "confirm_stop"))
        self._log(t(self.ui_lang, "confirm_stop"))

    def _clear_results(self):
        self._ensure_active_context_from_tab()
        self.records = []
        self.original_records = []
        self.undo_stack = []
        self.redo_stack = []
        self._clear_tree()
        self.log_text.delete("1.0", "end")
        self._set_progress(0, 100)
        self.status_var.set(t(self.ui_lang, "status_ready"))

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_record_map = {}
        self.tree_iid_counter = 0
        self._update_preview_count()

    def _record_number_for(self, rec):
        try:
            for i, item in enumerate(self.records, start=1):
                if item is rec:
                    return i
        except Exception:
            pass
        return ""

    def _record_tree_values(self, rec):
        status = getattr(rec, "content_status", "") or ""
        words = getattr(rec, "content_word_count", "") or ""
        quality = getattr(rec, "content_quality_score", "") or ""
        if isinstance(quality, float):
            quality = f"{quality:.0f}"
        return (self._record_number_for(rec), rec.collected_at, rec.title[:120], rec.source, rec.published_time, status, words, quality, rec.link)

    def _update_preview_count(self):
        if not hasattr(self, "preview_count_var"):
            return
        total = len(getattr(self, "records", []) or [])
        try:
            selected = len(self.tree.selection())
        except Exception:
            selected = 0
        self.preview_count_var.set(t(self.ui_lang, "preview_count", n=total, selected=selected))

    def _add_record_to_tree(self, rec):
        iid = f"rec_{self.tree_iid_counter}"
        self.tree_iid_counter += 1
        self.tree_record_map[iid] = rec
        self.tree.insert("", "end", iid=iid, values=self._record_tree_values(rec))
        self._update_preview_count()

    def _update_record_in_tree(self, rec):
        for iid, mapped in list(self.tree_record_map.items()):
            if mapped is rec:
                self.tree.item(iid, values=self._record_tree_values(rec))
                return

    def _repopulate_tree(self):
        self._clear_tree()
        for rec in self.records:
            self._add_record_to_tree(rec)
        self._update_preview_count()

    def _snapshot_records(self):
        return list(self.records)

    def _push_undo_state(self):
        self.undo_stack.append(self._snapshot_records())
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _restore_records_snapshot(self, snapshot, status_key=None, **fmt):
        self.records = list(snapshot)
        self._repopulate_tree()
        if status_key:
            self.status_var.set(t(self.ui_lang, status_key, **fmt))

    def _undo_result_edit(self):
        if not self.undo_stack:
            self.status_var.set(t(self.ui_lang, "nothing_to_undo"))
            return
        self.redo_stack.append(self._snapshot_records())
        snapshot = self.undo_stack.pop()
        self._restore_records_snapshot(snapshot, "undo_done")

    def _redo_result_edit(self):
        if not self.redo_stack:
            self.status_var.set(t(self.ui_lang, "nothing_to_redo"))
            return
        self.undo_stack.append(self._snapshot_records())
        snapshot = self.redo_stack.pop()
        self._restore_records_snapshot(snapshot, "redo_done")

    def _reset_result_preview(self):
        if not self.original_records:
            self.status_var.set(t(self.ui_lang, "no_original_records"))
            return
        self._push_undo_state()
        self._restore_records_snapshot(self.original_records, "reset_done", n=len(self.original_records))

    def _current_sample_scheme_key(self):
        label = self.sample_scheme_combo.get() if hasattr(self, "sample_scheme_combo") else ""
        mapping = {
            t(self.ui_lang, "sample_simple"): "simple",
            t(self.ui_lang, "sample_systematic"): "systematic",
            t(self.ui_lang, "sample_by_source"): "source",
        }
        return mapping.get(label, "simple")

    def _sample_records(self):
        self._ensure_active_context_from_tab()
        if not self.records:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "no_records"))
            return
        try:
            n = int(self.sample_count_var.get())
        except Exception:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_sample_count"))
            return
        if n <= 0:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_sample_count"))
            return
        scheme = self._current_sample_scheme_key()
        current = list(self.records)
        if scheme == "source":
            by_source = {}
            unknown = t(self.ui_lang, "unknown_source")
            for rec in current:
                key = (rec.source or unknown).strip() or unknown
                by_source.setdefault(key, []).append(rec)
            picked_ids = set()
            for group in by_source.values():
                k = min(n, len(group))
                picked_ids.update(id(r) for r in random.sample(group, k))
            sampled = [r for r in current if id(r) in picked_ids]
            status_key = "sampled_by_source_done"
            status_fmt = {"n": len(sampled), "sources": len(by_source)}
        elif scheme == "systematic":
            k = min(n, len(current))
            if k >= len(current):
                sampled = current
            else:
                step = len(current) / k
                indices = []
                seen = set()
                for i in range(k):
                    idx = min(len(current) - 1, int(round(i * step)))
                    while idx in seen and idx + 1 < len(current):
                        idx += 1
                    if idx not in seen:
                        indices.append(idx)
                        seen.add(idx)
                sampled = [current[i] for i in sorted(indices)]
            status_key = "sampled_done"
            status_fmt = {"n": len(sampled)}
        else:
            k = min(n, len(current))
            picked_ids = set(id(r) for r in random.sample(current, k))
            sampled = [r for r in current if id(r) in picked_ids]
            status_key = "sampled_done"
            status_fmt = {"n": len(sampled)}
        self._push_undo_state()
        self._restore_records_snapshot(sampled, status_key, **status_fmt)

    def _selected_records(self):
        return [self.tree_record_map[iid] for iid in self.tree.selection() if iid in self.tree_record_map]

    def _open_selected_link(self):
        self._ensure_active_context_from_tab()
        selected = self._selected_records()
        if not selected:
            return
        link = selected[0].link
        if link:
            webbrowser.open(link)

    def _delete_selected_records(self):
        self._ensure_active_context_from_tab()
        selected = self._selected_records()
        if not selected:
            return
        self._push_undo_state()
        selected_ids = {id(r) for r in selected}
        self.records = [r for r in self.records if id(r) not in selected_ids]
        self._repopulate_tree()
        self.status_var.set(t(self.ui_lang, "deleted_selected", n=len(selected)))

    def _sort_records(self, key):
        self._ensure_active_context_from_tab()
        if not self.records:
            return
        self._push_undo_state()
        reverse = self.sort_reverse.get(key, False)
        self.sort_reverse[key] = not reverse
        if key == "title":
            fn = lambda r: (r.title or "").lower()
        elif key == "source":
            fn = lambda r: (r.source or "").lower()
        else:
            fn = lambda r: ((r.published_time or ""), (r.collected_at or ""))
        self.records.sort(key=fn, reverse=reverse)
        self._repopulate_tree()

    def _show_result_context_menu(self, event):
        self._ensure_active_context_from_tab()
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
                self._update_preview_count()
            try:
                self.result_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.result_menu.grab_release()

    def _content_scheme_key_from_label(self, label: str, default_key: str = "auto") -> str:
        opt = option_by_label(CONTENT_CLEANING_OPTIONS, label, self.ui_lang)
        return opt.get("key") if opt else default_key

    def _show_content_settings_dialog(self, *, title_key: str = "download_settings_title") -> bool:
        """Show a modal content-download settings dialog and persist choices."""
        lang = self.ui_lang
        dialog = tk.Toplevel(self)
        dialog.title(t(lang, title_key))
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        frm = ttk.Frame(dialog, padding=14)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(1, weight=1)

        folder_var = tk.StringVar(value=self.content_dir_var.get().strip())
        threads_var = tk.IntVar(value=max(1, int(self.content_threads_var.get() or 1)))
        fetch_mode_var = tk.StringVar()
        fetch_mode_labels = labels_for(CONTENT_FETCH_MODE_OPTIONS, lang)
        current_fetch_key = self._current_combo_key(
            self.content_fetch_mode_combo,
            CONTENT_FETCH_MODE_OPTIONS,
            lang,
            self.defaults.get("content_fetch_mode", "mixed"),
        ) if hasattr(self, "content_fetch_mode_combo") and self.content_fetch_mode_combo.get() else self.settings.get("content_fetch_mode", "mixed")
        fetch_mode_var.set(label_for(next((o for o in CONTENT_FETCH_MODE_OPTIONS if o.get("key") == current_fetch_key), CONTENT_FETCH_MODE_OPTIONS[0]), lang))

        delay_min_var = tk.IntVar(value=max(0, int(self.content_delay_min_var.get() if hasattr(self, "content_delay_min_var") else self.defaults.get("content_delay_min_ms", 0))))
        delay_max_var = tk.IntVar(value=max(0, int(self.content_delay_max_var.get() if hasattr(self, "content_delay_max_var") else self.defaults.get("content_delay_max_ms", 0))))
        receive_wait_var = tk.IntVar(value=max(0, int(self.content_receive_wait_var.get() if hasattr(self, "content_receive_wait_var") else self.defaults.get("content_receive_wait_ms", 3500))))
        retry_var = tk.IntVar(value=max(0, int(self.settings.get("content_retry_count", self.defaults.get("content_retry_count", 1)))))
        task_timeout_var = tk.IntVar(value=max(30, int(self.settings.get("content_task_timeout_seconds", self.defaults.get("content_task_timeout_seconds", 300)))))
        resume_var = tk.BooleanVar(value=bool(self.settings.get("content_resume_enabled", self.defaults.get("content_resume_enabled", True))))

        scheme_var = tk.StringVar()
        scheme_labels = labels_for(CONTENT_CLEANING_OPTIONS, lang)
        current_key = self._current_combo_key(
            self.content_cleaning_combo,
            CONTENT_CLEANING_OPTIONS,
            lang,
            self.defaults.get("content_cleaning_scheme", "auto"),
        ) if hasattr(self, "content_cleaning_combo") and self.content_cleaning_combo.get() else self.settings.get("content_cleaning_scheme", "auto")
        current_label = label_for(next((o for o in CONTENT_CLEANING_OPTIONS if o.get("key") == current_key), CONTENT_CLEANING_OPTIONS[0]), lang)
        scheme_var.set(current_label)

        ttk.Label(frm, text=t(lang, "content_folder"), style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        folder_frame = ttk.Frame(frm)
        folder_frame.grid(row=0, column=1, sticky="ew", pady=4)
        folder_frame.columnconfigure(0, weight=1)
        ttk.Entry(folder_frame, textvariable=folder_var, width=48).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        def browse_folder():
            selected = filedialog.askdirectory(title=t(lang, "select_content_folder"), initialdir=folder_var.get() or os.getcwd())
            if selected:
                folder_var.set(selected)

        ttk.Button(folder_frame, text=t(lang, "browse"), command=browse_folder).grid(row=0, column=1, sticky="e")

        ttk.Label(frm, text=t(lang, "content_threads"), style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(frm, from_=1, to=32, textvariable=threads_var, width=10).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frm, text=t(lang, "content_fetch_mode"), style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        fetch_combo = ttk.Combobox(frm, textvariable=fetch_mode_var, values=fetch_mode_labels, state="readonly", width=42)
        fetch_combo.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(frm, text=t(lang, "content_delay"), style="Panel.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        delay_box = ttk.Frame(frm)
        delay_box.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Spinbox(delay_box, from_=0, to=9999999, textvariable=delay_min_var, width=10).pack(side="left")
        ttk.Label(delay_box, text=" - ").pack(side="left")
        ttk.Spinbox(delay_box, from_=0, to=9999999, textvariable=delay_max_var, width=10).pack(side="left")

        ttk.Label(frm, text=t(lang, "content_receive_wait"), style="Panel.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(frm, from_=0, to=9999999, textvariable=receive_wait_var, width=10).grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(frm, text=t(lang, "content_retry_count"), style="Panel.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(frm, from_=0, to=10, textvariable=retry_var, width=10).grid(row=5, column=1, sticky="w", pady=4)

        ttk.Label(frm, text=t(lang, "content_task_timeout"), style="Panel.TLabel").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Spinbox(frm, from_=30, to=86400, textvariable=task_timeout_var, width=10).grid(row=6, column=1, sticky="w", pady=4)

        ttk.Checkbutton(frm, text=t(lang, "content_resume_enabled"), variable=resume_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(frm, text=t(lang, "content_cleaning_scheme"), style="Panel.TLabel").grid(row=8, column=0, sticky="w", padx=(0, 8), pady=4)
        scheme_combo = ttk.Combobox(frm, textvariable=scheme_var, values=scheme_labels, state="readonly", width=42)
        scheme_combo.grid(row=8, column=1, sticky="w", pady=4)

        desc = tk.Text(frm, width=72, height=11, wrap="word", relief="flat", borderwidth=0, background=dialog.cget("background"))
        desc.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        desc.insert("1.0", t(lang, "download_mode_help") + "\n\n" + t(lang, "cleaning_scheme_help"))
        desc.configure(state="disabled")

        result = {"ok": False}

        def ok():
            folder = folder_var.get().strip()
            if not folder:
                messagebox.showerror(t(lang, "validation_error"), t(lang, "select_content_folder_first"), parent=dialog)
                return
            try:
                threads = max(1, int(threads_var.get()))
                dmin = max(0, int(delay_min_var.get()))
                dmax = max(0, int(delay_max_var.get()))
                wait = max(0, int(receive_wait_var.get()))
                retry_count = max(0, int(retry_var.get()))
                task_timeout = max(30, int(task_timeout_var.get()))
            except Exception:
                messagebox.showerror(t(lang, "validation_error"), t(lang, "invalid_numeric"), parent=dialog)
                return
            if dmin > dmax:
                messagebox.showerror(t(lang, "validation_error"), t(lang, "invalid_numeric"), parent=dialog)
                return
            scheme_key = self._content_scheme_key_from_label(scheme_var.get(), self.defaults.get("content_cleaning_scheme", "auto"))
            fetch_opt = option_by_label(CONTENT_FETCH_MODE_OPTIONS, fetch_mode_var.get(), lang)
            fetch_key = fetch_opt.get("key") if fetch_opt else self.defaults.get("content_fetch_mode", "mixed")
            self.content_dir_var.set(folder)
            self.content_threads_var.set(threads)
            self.content_delay_min_var.set(dmin)
            self.content_delay_max_var.set(dmax)
            self.content_receive_wait_var.set(wait)
            self.content_selenium_fallback_var.set(fetch_key == "mixed")
            self._set_combo_by_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, fetch_key)
            self._set_combo_by_key(self.content_cleaning_combo, CONTENT_CLEANING_OPTIONS, scheme_key)
            self.settings["content_download_dir"] = folder
            self.settings["content_threads"] = threads
            self.settings["content_fetch_mode"] = fetch_key
            self.settings["content_delay_min_ms"] = dmin
            self.settings["content_delay_max_ms"] = dmax
            self.settings["content_receive_wait_ms"] = wait
            self.settings["content_cleaning_scheme"] = scheme_key
            self.settings["content_selenium_fallback"] = bool(fetch_key == "mixed")
            self.settings["content_retry_count"] = retry_count
            self.settings["content_task_timeout_seconds"] = task_timeout
            self.settings["content_resume_enabled"] = bool(resume_var.get())
            self._save_settings()
            result["ok"] = True
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btns = ttk.Frame(frm)
        btns.grid(row=10, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="OK", command=ok).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btns, text="Cancel", command=cancel).grid(row=0, column=1)

        dialog.bind("<Return>", lambda _e: ok())
        dialog.bind("<Escape>", lambda _e: cancel())
        dialog.update_idletasks()
        x = self.winfo_rootx() + max(20, (self.winfo_width() - dialog.winfo_width()) // 2)
        y = self.winfo_rooty() + max(20, (self.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
        return bool(result["ok"])

    def _open_content_settings_dialog(self):
        self._ensure_active_context_from_tab()
        self._show_content_settings_dialog()

    def _content_settings(self, prompt: bool = True):
        self._ensure_active_context_from_tab()
        if prompt:
            if not self._show_content_settings_dialog(title_key="download_settings_title"):
                return None
        folder = self.content_dir_var.get().strip()
        if not folder:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "select_content_folder_first"))
            return None
        try:
            workers = max(1, int(self.content_threads_var.get()))
        except Exception:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_numeric"))
            return None
        try:
            ensure_content_dirs(folder)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return None
        cleaning_scheme = self._current_combo_key(
            self.content_cleaning_combo,
            CONTENT_CLEANING_OPTIONS,
            self.ui_lang,
            self.defaults.get("content_cleaning_scheme", "auto"),
        ) if hasattr(self, "content_cleaning_combo") else self.defaults.get("content_cleaning_scheme", "auto")
        try:
            dmin = max(0, int(self.content_delay_min_var.get()))
            dmax = max(0, int(self.content_delay_max_var.get()))
            receive_wait = max(0, int(self.content_receive_wait_var.get()))
        except Exception:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_numeric"))
            return None
        if dmin > dmax:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_numeric"))
            return None
        fetch_mode = self._current_combo_key(
            self.content_fetch_mode_combo,
            CONTENT_FETCH_MODE_OPTIONS,
            self.ui_lang,
            self.defaults.get("content_fetch_mode", "mixed"),
        ) if hasattr(self, "content_fetch_mode_combo") else self.defaults.get("content_fetch_mode", "mixed")
        return ContentDownloadSettings(
            content_root=folder,
            max_workers=workers,
            timeout_seconds=max(1, int(self.spin_vars.get("timeout").get() if hasattr(self, "spin_vars") else 30)),
            user_agent=self.user_agent_var.get().strip() or DEFAULT_USER_AGENT,
            min_delay_ms=dmin,
            max_delay_ms=dmax,
            fetch_mode=fetch_mode,
            receive_wait_ms=receive_wait,
            cleaning_scheme=cleaning_scheme,
            selenium_fallback=(fetch_mode == "mixed"),
            selenium_backend=self._current_combo_key(self.backend_combo, FETCH_BACKEND_OPTIONS, self.ui_lang, self.defaults.get("fetch_backend", "selenium_chrome")) if hasattr(self, "backend_combo") else "selenium_chrome",
            selenium_driver_path=self.driver_path_var.get().strip() if hasattr(self, "driver_path_var") else "",
            selenium_binary_path=self.browser_binary_var.get().strip() if hasattr(self, "browser_binary_var") else "",
            selenium_wait_ms=receive_wait,
            selenium_headless=bool(self.browser_headless_var.get()) if hasattr(self, "browser_headless_var") else False,
            retry_count=max(0, int(self.settings.get("content_retry_count", self.defaults.get("content_retry_count", 1)))),
            task_timeout_seconds=max(30, int(self.settings.get("content_task_timeout_seconds", self.defaults.get("content_task_timeout_seconds", 300)))),
            resume_enabled=bool(self.settings.get("content_resume_enabled", self.defaults.get("content_resume_enabled", True))),
            domain_lock_timeout_seconds=max(1, int(self.settings.get("content_domain_lock_timeout_seconds", self.defaults.get("content_domain_lock_timeout_seconds", 300)))),
        )

    def _start_content_download_for_records(self, records):
        records = list(records or [])
        if not records:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "no_records"))
            return
        if self.content_worker and self.content_worker.is_alive():
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "content_download_running"))
            return
        settings = self._content_settings()
        if settings is None:
            return
        self._save_settings()
        self.content_stop_event.clear()
        self.stop_button.config(state="normal")
        for rec in records:
            setattr(rec, "content_status", t(self.ui_lang, "content_status_queued"))
            setattr(rec, "content_error", "")
            self._update_record_in_tree(rec)
        self._set_progress(0, len(records))
        self.status_var.set(t(self.ui_lang, "content_download_started", n=len(records), workers=settings.max_workers))
        self._log(t(self.ui_lang, "content_download_started", n=len(records), workers=settings.max_workers))
        self._sync_active_context_state()
        ctx_key = getattr(self, "active_context_key", "google")
        self.content_worker_context_key = ctx_key
        self.content_worker = threading.Thread(target=self._content_download_worker, args=(records, settings, ctx_key), daemon=True)
        self.content_worker.start()

    def _download_selected_content(self):
        self._ensure_active_context_from_tab()
        selected = self._selected_records()
        if not selected:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "select_rows_to_download"))
            return
        self._start_content_download_for_records(selected)

    def _download_all_content(self):
        self._ensure_active_context_from_tab()
        if not self.records:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "no_records"))
            return
        self._start_content_download_for_records(self.records)

    def _run_download_one_with_timeout(self, rec, settings, index, domain_locks, manifest_lock):
        """Run one content task with a GUI-level hard timeout.

        Python cannot safely kill arbitrary code running inside a thread.  To keep
        the GUI responsive, the actual download is executed in a daemon helper
        thread.  If it exceeds the configured timeout, WebLens records a timeout
        failure and moves on; the daemon helper will not block application exit.
        Network/Selenium timeouts inside content_downloader still provide the
        primary cleanup path.
        """
        timeout = max(30, int(getattr(settings, "task_timeout_seconds", 300) or 300))
        box = {"done": False, "result": None, "error": ""}

        def target():
            try:
                box["result"] = download_one(
                    rec, settings, index, domain_locks, manifest_lock, self.content_stop_event.is_set
                )
            except Exception as exc:
                box["error"] = str(exc)
            finally:
                box["done"] = True

        th = threading.Thread(target=target, daemon=True)
        th.start()
        th.join(timeout)
        if th.is_alive():
            return {"ok": False, "error": f"Content task timed out after {timeout} seconds", "url": getattr(rec, "link", "")}
        if box.get("error"):
            return {"ok": False, "error": box["error"], "url": getattr(rec, "link", "")}
        return box.get("result") or {"ok": False, "error": "Empty content task result", "url": getattr(rec, "link", "")}

    def _content_download_worker(self, records, settings, ctx_key):
        total = len(records)
        done = 0
        done_lock = threading.Lock()
        domain_locks = DomainLockPool()
        manifest_lock = threading.Lock()
        task_queue = queue.Queue()
        max_retries = max(0, int(getattr(settings, "retry_count", 1) or 0))

        def publish_result(rec, result):
            nonlocal done
            with done_lock:
                done += 1
                current_done = done
            self.event_queue.put(("__context__", ctx_key, ("content_result", (rec, result))))
            self.event_queue.put(("__context__", ctx_key, ("content_progress", {"done": current_done, "total": total})))

        try:
            success_index = {}
            if bool(getattr(settings, "resume_enabled", True)):
                try:
                    success_index = load_successful_download_index(settings.content_root)
                except Exception:
                    success_index = {}

            queued_count = 0
            for i, rec in enumerate(records, 1):
                if self.content_stop_event.is_set():
                    break
                completed = successful_manifest_for_record(rec, success_index) if success_index else None
                if completed:
                    result = content_result_from_manifest(rec, completed)
                    setattr(result, "skipped", True)
                    publish_result(rec, result)
                    continue
                task_queue.put((i, rec))
                queued_count += 1

            def worker():
                while not self.content_stop_event.is_set():
                    try:
                        i, rec = task_queue.get_nowait()
                    except queue.Empty:
                        break
                    final_result = None
                    try:
                        for attempt in range(max_retries + 1):
                            if self.content_stop_event.is_set():
                                final_result = {"ok": False, "error": "Stopped by user", "url": getattr(rec, "link", "")}
                                break
                            result = self._run_download_one_with_timeout(rec, settings, i, domain_locks, manifest_lock)
                            ok = bool(getattr(result, "ok", False) if not isinstance(result, dict) else result.get("ok"))
                            if ok or attempt >= max_retries:
                                final_result = result
                                if attempt > 0 and not ok:
                                    try:
                                        if isinstance(final_result, dict):
                                            final_result["error"] = f"{final_result.get('error', '')} (after {attempt + 1} attempts)".strip()
                                        else:
                                            final_result.error = f"{getattr(final_result, 'error', '')} (after {attempt + 1} attempts)".strip()
                                    except Exception:
                                        pass
                                break
                            # Backoff before retry, but keep Stop responsive.
                            wait_left = min(10.0, 1.5 * (attempt + 1))
                            while wait_left > 0 and not self.content_stop_event.is_set():
                                step = min(0.5, wait_left)
                                time.sleep(step)
                                wait_left -= step
                    finally:
                        task_queue.task_done()
                    if final_result is None:
                        final_result = {"ok": False, "error": "No result", "url": getattr(rec, "link", "")}
                    publish_result(rec, final_result)

            workers = []
            worker_count = min(max(1, int(settings.max_workers)), max(1, queued_count)) if queued_count else 0
            for _ in range(worker_count):
                th = threading.Thread(target=worker, daemon=True)
                workers.append(th)
                th.start()

            # Wait for queue workers, but keep Stop responsive.  Worker-level task
            # timeouts prevent a single URL from holding this loop indefinitely.
            while any(th.is_alive() for th in workers):
                if self.content_stop_event.is_set():
                    # Drain tasks that never started so the queue cannot keep the
                    # manager alive.  Running daemon tasks will end by timeout or app close.
                    try:
                        while True:
                            task_queue.get_nowait()
                            task_queue.task_done()
                    except queue.Empty:
                        pass
                time.sleep(0.2)
        finally:
            self.event_queue.put(("__context__", ctx_key, ("content_finished", {"done": done, "total": total, "folder": settings.content_root})))

    def _handle_content_result(self, rec, result):
        ok = bool(getattr(result, "ok", False) if not isinstance(result, dict) else result.get("ok"))
        def get(name, default=""):
            return getattr(result, name, default) if not isinstance(result, dict) else result.get(name, default)
        if ok:
            skipped = bool(getattr(result, "skipped", False) if not isinstance(result, dict) else result.get("skipped"))
            setattr(rec, "content_status", t(self.ui_lang, "content_status_skipped") if skipped else t(self.ui_lang, "content_status_downloaded"))
            if (not rec.title or rec.title == rec.link) and get("title"):
                rec.title = str(get("title"))
            if not rec.published_time and get("published_time"):
                rec.published_time = str(get("published_time"))
            setattr(rec, "content_word_count", int(get("word_count", 0) or 0))
            setattr(rec, "content_quality_score", float(get("quality_score", 0) or 0))
            setattr(rec, "content_extraction_method", str(get("extraction_method", "")))
            setattr(rec, "content_cleaning_scheme", str(get("cleaning_scheme", "")))
            setattr(rec, "metadata_excel_path", str(get("metadata_excel_path", "")))
            setattr(rec, "raw_html_path", str(get("raw_html_path", "")))
            setattr(rec, "raw_text_path", str(get("raw_text_path", "")))
            setattr(rec, "clean_text_path", str(get("clean_text_path", "")))
            setattr(rec, "metadata_path", str(get("metadata_path", "")))
            if skipped:
                self._log(t(self.ui_lang, "content_download_skipped", title=rec.title[:80]))
            else:
                self._log(t(self.ui_lang, "content_download_ok", title=rec.title[:80], words=get("word_count", 0), score=f"{float(get('quality_score', 0) or 0):.0f}"))
        else:
            setattr(rec, "content_status", t(self.ui_lang, "content_status_failed"))
            setattr(rec, "content_error", str(get("error", "")))
            if get("raw_html_path"):
                setattr(rec, "raw_html_path", str(get("raw_html_path")))
            if get("metadata_excel_path"):
                setattr(rec, "metadata_excel_path", str(get("metadata_excel_path")))
            self._log(t(self.ui_lang, "content_download_failed", url=rec.link, error=str(get("error", ""))[:180]))
        self._update_record_in_tree(rec)

    def _handle_content_progress(self, data):
        done = int(data.get("done") or 0)
        total = max(1, int(data.get("total") or 1))
        self._set_progress(done, total)
        self.status_var.set(t(self.ui_lang, "content_progress", done=done, total=total))

    def _handle_content_finished(self, data):
        folder = data.get("folder", "") if isinstance(data, dict) else ""
        done = int(data.get("done") or 0) if isinstance(data, dict) else 0
        total = int(data.get("total") or 0) if isinstance(data, dict) else 0
        self.status_var.set(t(self.ui_lang, "content_download_finished", done=done, total=total))
        self._log(t(self.ui_lang, "content_folder_hint", path=folder))
        if not (self.worker and self.worker.is_alive()):
            self.stop_button.config(state="disabled")

    def _import_links_file(self):
        self._ensure_active_context_from_tab()
        path = filedialog.askopenfilename(
            title=t(self.ui_lang, "select_import_file"),
            filetypes=[
                ("WebLens/result files", "*.xlsx *.csv *.txt *.xml *.docx"),
                ("Excel", "*.xlsx"),
                ("CSV", "*.csv"),
                ("Text", "*.txt"),
                ("XML", "*.xml"),
                ("Word", "*.docx"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            imported = import_records(path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        if not imported:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "no_imported_links"))
            return
        self._push_undo_state()
        seen = {normalize_url_for_dedup(r.link) for r in self.records}
        added = []
        for rec in imported:
            key = normalize_url_for_dedup(rec.link)
            if key and key not in seen:
                seen.add(key)
                added.append(rec)
        self.records.extend(added)
        self.original_records.extend(added)
        self._repopulate_tree()
        self.status_var.set(t(self.ui_lang, "import_done", n=len(added)))
        self._log(t(self.ui_lang, "import_done", n=len(added)))

    def _log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")

    def _export_results(self, show_message=True):
        self._ensure_active_context_from_tab()
        if not self.records:
            if show_message:
                messagebox.showinfo(APP_NAME, t(self.ui_lang, "no_records"))
            return
        fmt = self.output_format.get().strip().lower()
        path = self.output_path.get().strip()
        if not path:
            messagebox.showerror(t(self.ui_lang, "validation_error"), t(self.ui_lang, "invalid_output"))
            return
        if not path.lower().endswith("." + fmt):
            path += "." + fmt
            self.output_path.set(path)
        unique = []
        seen = set()
        for rec in self.records:
            key = normalize_url_for_dedup(rec.link)
            if key in seen:
                continue
            seen.add(key)
            unique.append(rec)
        export_records(unique, path, fmt)
        self.status_var.set(t(self.ui_lang, "status_exported"))
        self._log(t(self.ui_lang, "finished_export", n=len(unique), path=path))
        if show_message:
            messagebox.showinfo(APP_NAME, t(self.ui_lang, "finished_export", n=len(unique), path=path))

    def _open_output(self):
        self._ensure_active_context_from_tab()
        path = self.output_path.get().strip()
        if not path:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))


def main():
    app = BFSUWebLensApp()
    app.mainloop()


if __name__ == "__main__":
    main()
