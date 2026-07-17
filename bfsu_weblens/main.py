# -*- coding: utf-8 -*-
"""BFSU WebLens GUI entry point."""
from __future__ import annotations

import ctypes
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
from tkinter import font as tkfont

import customtkinter as ctk
from PIL import Image

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
from bfsu_weblens.ui_common import (
    FONT_FAMILY, COLOR_BG, COLOR_PANEL, COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT, COLOR_MUTED,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_LLM, COLOR_LLM_HOVER, COLOR_DANGER,
    COLOR_DANGER_HOVER, COLOR_TOOLBAR, CTkSection, HoverScrollableFrame, CTkSpinbox,
    CompatProgressBar, CTkSplitPane, DpiAwareMenu, DpiAwareTreeview, apply_window_icon,
    button_colors, fit_window_to_screen,
)

APP_NAME = "BFSU WebLens"

def enable_windows_dpi_awareness() -> None:
    """Make Tk/CustomTkinter respect Windows 10/11 per-monitor DPI scaling."""
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def configure_customtkinter_theme() -> None:
    """Load the same light CustomTkinter theme family used by ClearLens."""
    try:
        ctk.set_appearance_mode("light")
    except Exception:
        pass
    try:
        theme_path = Path(resource_path("assets/clearlens_theme.json"))
        if theme_path.exists():
            ctk.set_default_color_theme(str(theme_path))
        else:
            ctk.set_default_color_theme("blue")
    except Exception:
        try:
            ctk.set_default_color_theme("blue")
        except Exception:
            pass


def ctk_button_colors(kind: str = "normal") -> dict[str, object]:
    return button_colors(kind)


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
    "start_button", "stop_button", "export_button", "import_links_button", "clear_button", "open_button", "open_download_button",
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
    "preview_frame", "preview_toolbar", "record_group_label", "sort_group_label", "sample_group_label", "download_group_label", "open_link_button", "delete_selected_button",
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
    defaults = {
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
        "per_page": 10,
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
    # A release-level default configuration file is kept outside the code so
    # maintainers can audit and adjust defaults without editing main.py.
    candidates = [
        app_base_dir() / "config" / "default_settings.json",
        Path(resource_path("config/default_settings.json")),
    ]
    for config_path in candidates:
        try:
            if config_path.exists():
                overrides = json.loads(config_path.read_text(encoding="utf-8"))
                if isinstance(overrides, dict):
                    for key, value in overrides.items():
                        if key in defaults:
                            defaults[key] = value
                break
        except Exception:
            continue
    return defaults


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


ScrollableFrame = HoverScrollableFrame


class BFSUWebLensApp(ctk.CTk):
    def __init__(self):
        enable_windows_dpi_awareness()
        configure_customtkinter_theme()
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
        self._main_window_fit_done = False
        self.worker_context_key = None
        self.content_worker_context_key = None
        self._building_context_key = "google"
        self.icon_path = resource_path("assets/app.ico")
        self.icon_png_path = resource_path("assets/app.png")
        self.title(APP_NAME)
        self.geometry("1680x940")
        self.minsize(1080, 680)
        self._apply_icon(self)
        self.after(250, lambda: self._apply_icon(self))
        self._setup_style()
        self._build_ui()
        self._set_language(self.settings.get("ui_lang", self.defaults["ui_lang"]))
        self._apply_settings_to_widgets(self.settings)
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._poll_queue)
        self._fit_main_window_once()

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
        # v1.2.8 changes Google's shipped Results per page default from 50 to 10.
        # Migrate the previous default value so existing installations receive the new stable pagination setting.
        if data.get("per_page") == 50:
            data["per_page"] = 10
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
        """Apply the WebLens icon at multiple sizes for crisp Windows taskbar rendering."""
        apply_window_icon(win, self.icon_png_path, self.icon_path, default=(win is self))

    def _fit_main_window_once(self):
        """Fit the main window exactly once during startup.

        Re-running the positioning routine from the queue poller prevents users
        from moving the window because every mouse drag is overwritten on the
        next poll cycle.  The one-shot guard keeps startup clamping while leaving
        all later window movement entirely under user control.
        """
        if self._main_window_fit_done:
            return
        self._main_window_fit_done = True
        self._fit_main_window()

    def _fit_main_window(self):
        fit_window_to_screen(
            self,
            requested_width=1680,
            requested_height=940,
            parent=None,
            margin=32,
            min_width=1180,
            min_height=680,
        )

    def _setup_style(self):
        self.configure(fg_color=COLOR_BG)
        try:
            self._default_tk_font = tkfont.Font(family=FONT_FAMILY, size=10)
            self.option_add("*Font", self._default_tk_font)
        except Exception:
            pass
        # Native controls remain only where CustomTkinter has no equivalent:
        # menu bars, Treeview and multi-select Listbox widgets.
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.colors = {
            "navy": COLOR_ACCENT,
            "blue": COLOR_ACCENT,
            "blue2": COLOR_ACCENT_HOVER,
            "gold": "#c6922d",
            "bg": COLOR_BG,
            "panel": COLOR_PANEL,
            "surface": COLOR_SURFACE,
            "text": COLOR_TEXT,
            "muted": COLOR_MUTED,
            "border": COLOR_BORDER,
            "danger": COLOR_DANGER,
        }
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Treeview", background=COLOR_SURFACE, fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT)
        style.configure("Treeview.Heading", background="#d9e8eb", foreground=COLOR_TEXT, font=(FONT_FAMILY, 10, "bold"))
        style.map("Treeview", background=[("selected", "#b7dfe3")], foreground=[("selected", COLOR_TEXT)])

    def _build_ui(self):
        self._build_menu()
        self.notebook = ctk.CTkTabview(
            self,
            fg_color=COLOR_BG,
            segmented_button_fg_color="#d9e8eb",
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            segmented_button_unselected_color="#d9e8eb",
            segmented_button_unselected_hover_color="#c9dde0",
            text_color=COLOR_TEXT,
            command=self._on_tab_changed,
            anchor="nw",
            corner_radius=6,
        )
        # CTkTabview defaults center the selector and reserve a tall header.
        # Keep the engine selector compact and aligned to the upper-left so the
        # crawler/result workspace receives more vertical room.
        try:
            self.notebook._button_height = 25
            self.notebook._outer_spacing = 2
            self.notebook._outer_button_overhang = 1
            self.notebook._segmented_button.configure(
                height=25,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                dynamic_resizing=False,
            )
            self.notebook._configure_grid()
            self.notebook._set_grid_canvas()
        except Exception:
            pass
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(4, 4))
        self.notebook.add("Google")
        self.notebook.add("Baidu")
        self.google_tab = self.notebook.tab("Google")
        self.baidu_tab = self.notebook.tab("Baidu")

        self._build_collector_tab(self.google_tab, "google")
        self._build_collector_tab(self.baidu_tab, "baidu")

        bottom = ctk.CTkFrame(self, fg_color=COLOR_TOOLBAR, corner_radius=0, height=38)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        bottom.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready.")
        self.progress = CompatProgressBar(bottom, maximum=100, value=0, height=12)
        self.progress.pack(side="left", fill="x", expand=True, padx=(10, 12), pady=13)
        self.status_label = ctk.CTkLabel(
            bottom,
            textvariable=self.status_var,
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.status_label.pack(side="right", padx=(0, 10))
        self._activate_context("google", sync_previous=False)

    def _build_menu(self):
        self.menu_bar = DpiAwareMenu(self, tearoff=False)
        self.file_menu = DpiAwareMenu(self.menu_bar, tearoff=False)
        self.view_menu = DpiAwareMenu(self.menu_bar, tearoff=False)
        self.lang_menu = DpiAwareMenu(self.view_menu, tearoff=False)
        self.tools_menu = DpiAwareMenu(self.menu_bar, tearoff=False)
        self.help_menu = DpiAwareMenu(self.menu_bar, tearoff=False)
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
        try:
            self.configure(menu=self.menu_bar)
        except Exception:
            self.tk.call(self._w, "configure", "-menu", self.menu_bar)

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
            current = self.notebook.get()
            if current == "Baidu":
                return "baidu"
            return "google"
        except Exception:
            return getattr(self, "active_context_key", "google") or "google"

    def _ensure_active_context_from_tab(self):
        key = self._selected_context_key()
        if key in getattr(self, "contexts", {}) and key != getattr(self, "active_context_key", None):
            self._activate_context(key)
        return key

    def _on_tab_changed(self, _value=None):
        self._ensure_active_context_from_tab()
        try:
            self._update_preview_count()
        except Exception:
            pass

    def _build_collector_tab(self, tab, key: str):
        self._building_context_key = key
        self.current_vertical_options = vertical_options_for_engine(key)
        self.current_query_mode_options = query_mode_options_for_engine(key)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        self._build_action_bar(tab)
        self.main_pane = CTkSplitPane(
            tab,
            orientation="horizontal",
            initial_ratio=0.41,
            min_first=500,
            min_second=650,
            separator_width=8,
            first_color=COLOR_PANEL,
            second_color="transparent",
        )
        self.main_pane.grid(row=1, column=0, sticky="nsew", pady=(0, 2))
        self.left_panel = self.main_pane.first
        self.right_panel = self.main_pane.second
        self._build_settings_panel(self.left_panel)
        self._build_results_panel(self.right_panel)
        self._initial_sash_done = True
        self.contexts[key] = self._make_collector_context(key)

    def _set_initial_sash_for_context(self, key: str):
        ctx = self.contexts.get(key)
        pane = getattr(ctx, "main_pane", None)
        if pane is None:
            return
        try:
            if hasattr(pane, "set_ratio"):
                pane.set_ratio(0.41)
            else:
                width = pane.winfo_width()
                if width > 300:
                    pane.sashpos(0, min(max(500, int(width * 0.41)), 720))
            ctx._initial_sash_done = True
        except Exception:
            pass

    def _maybe_reset_initial_sash_for_context(self, key: str):
        ctx = self.contexts.get(key)
        if ctx and not getattr(ctx, "_initial_sash_done", False):
            self.after(80, lambda k=key: self._set_initial_sash_for_context(k))

    def _build_action_bar(self, parent):
        self.action_bar = ctk.CTkFrame(parent, fg_color=COLOR_TOOLBAR, corner_radius=0, height=48)
        self.action_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.action_bar.grid_propagate(False)
        self.action_bar.grid_columnconfigure(8, weight=1)

        font = ctk.CTkFont(family=FONT_FAMILY, size=12)
        def button(column, command, kind="normal", width=92):
            widget = ctk.CTkButton(
                self.action_bar,
                text="",
                command=command,
                width=width,
                height=32,
                font=font,
                **ctk_button_colors(kind),
            )
            widget.grid(row=0, column=column, padx=(6 if column == 0 else 2, 2), pady=8, sticky="w")
            return widget

        self.start_button = button(0, self._start_crawl, "accent", 100)
        self.stop_button = button(1, self._stop_crawl, "danger", 100)
        self.stop_button.configure(state="disabled")
        self.export_button = button(2, self._export_results)
        self.import_links_button = button(3, self._import_links_file, width=106)
        self.clear_button = button(4, self._clear_results)
        self.open_button = button(5, self._open_output, width=106)
        self.open_download_button = button(6, self._open_download_folder, width=128)
        self.toolbar_progress_label = ctk.CTkLabel(
            self.action_bar,
            text="",
            text_color=COLOR_ACCENT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        )
        self.toolbar_progress_label.grid(row=0, column=7, padx=(12, 6), sticky="e")
        self.toolbar_progress = CompatProgressBar(self.action_bar, maximum=100, value=0, height=12)
        self.toolbar_progress.grid(row=0, column=8, sticky="ew", padx=(0, 12))

    def _build_settings_panel(self, parent):
        """Build the original single-column settings layout with CTk controls."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        self.settings_scroll = ScrollableFrame(parent)
        self.settings_scroll.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        panel = self.settings_scroll.inner
        panel.grid_columnconfigure(0, weight=1)

        self.query_frame = CTkSection(panel, text="Query")
        self.query_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 7))
        self.crawl_frame = CTkSection(panel, text="Crawl")
        self.crawl_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=7)
        self.limit_frame = CTkSection(panel, text="Limit")
        self.limit_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=7)
        self.output_frame = CTkSection(panel, text="Output")
        self.output_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=(7, 12))

        label_font = ctk.CTkFont(family=FONT_FAMILY, size=12)
        input_font = ctk.CTkFont(family=FONT_FAMILY, size=12)
        for frame in (self.query_frame, self.crawl_frame, self.limit_frame, self.output_frame):
            frame.grid_columnconfigure(0, weight=0, minsize=138)
            frame.grid_columnconfigure(1, weight=1)

        def label(master, row, *, column=0, columnspan=1, pady=5, sticky="w", wraplength=0):
            widget = ctk.CTkLabel(
                master,
                text="",
                font=label_font,
                text_color=COLOR_TEXT,
                anchor="w",
                justify="left",
                wraplength=wraplength,
            )
            widget.grid(row=row, column=column, columnspan=columnspan, sticky=sticky, padx=(12, 8), pady=pady)
            return widget

        def combo(master, row, *, variable=None, values=None, column=1, width=250):
            widget = ctk.CTkComboBox(
                master,
                variable=variable,
                values=list(values or [""]),
                state="readonly",
                height=32,
                width=width,
                font=input_font,
                dropdown_font=input_font,
            )
            widget.grid(row=row, column=column, sticky="ew", padx=(4, 12), pady=5)
            return widget

        def normal_button(master, text, command, *, width=82, height=30, kind="normal"):
            return ctk.CTkButton(
                master,
                text=text,
                command=command,
                width=width,
                height=height,
                font=input_font,
                **ctk_button_colors(kind),
            )

        def link_button(master, row, command):
            widget = ctk.CTkButton(
                master,
                text="",
                command=command,
                height=26,
                width=90,
                anchor="w",
                fg_color="transparent",
                hover_color="#d7e7e9",
                text_color=COLOR_ACCENT,
                border_width=0,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, underline=True),
            )
            widget.grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 7))
            return widget

        # Query settings. Row 0 is reserved for each section heading.
        self.query_mode_label = label(self.query_frame, 1)
        self.query_mode_combo = combo(self.query_frame, 1)
        self.vertical_label = label(self.query_frame, 2)
        self.vertical_combo = combo(self.query_frame, 2)
        self.baidu_sort_label = label(self.query_frame, 3)
        self.baidu_sort_combo = combo(self.query_frame, 3)
        if getattr(self, "_building_context_key", "google") != "baidu":
            self.baidu_sort_label.grid_remove()
            self.baidu_sort_combo.grid_remove()

        self.backend_label = label(self.query_frame, 4)
        self.backend_combo = combo(self.query_frame, 4)

        self.driver_path_label = label(self.query_frame, 5)
        self.driver_path_var = tk.StringVar(value=str(Path(resource_path("tools/chromedriver.exe"))))
        driver_path_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        driver_path_frame.grid(row=5, column=1, sticky="ew", padx=(4, 12), pady=5)
        driver_path_frame.grid_columnconfigure(0, weight=1)
        self.driver_path_entry = ctk.CTkEntry(driver_path_frame, textvariable=self.driver_path_var, height=32, font=input_font)
        self.driver_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.driver_browse_button = normal_button(driver_path_frame, "", self._browse_driver, width=78)
        self.driver_browse_button.grid(row=0, column=1)

        self.browser_binary_label = label(self.query_frame, 6)
        self.browser_binary_var = tk.StringVar(value=default_browser_binary_path())
        browser_binary_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        browser_binary_frame.grid(row=6, column=1, sticky="ew", padx=(4, 12), pady=5)
        browser_binary_frame.grid_columnconfigure(0, weight=1)
        self.browser_binary_entry = ctk.CTkEntry(browser_binary_frame, textvariable=self.browser_binary_var, height=32, font=input_font)
        self.browser_binary_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.binary_browse_button = normal_button(browser_binary_frame, "", self._browse_browser_binary, width=78)
        self.binary_browse_button.grid(row=0, column=1)

        self.browser_wait_label = label(self.query_frame, 7)
        self.browser_wait_var = tk.IntVar(value=3500)
        CTkSpinbox(self.query_frame, from_=0, to=60000, textvariable=self.browser_wait_var, width=170).grid(
            row=7, column=1, sticky="w", padx=(4, 12), pady=5
        )

        self.browser_headless_var = tk.BooleanVar(value=False)
        self.browser_headless_check = ctk.CTkCheckBox(
            self.query_frame,
            text="",
            variable=self.browser_headless_var,
            height=26,
            checkbox_width=19,
            checkbox_height=19,
            font=label_font,
        )
        self.browser_headless_check.grid(row=8, column=0, columnspan=2, sticky="w", padx=12, pady=5)

        self.query_terms_label = label(self.query_frame, 9, columnspan=2, pady=(10, 4))
        self.query_text = ctk.CTkTextbox(
            self.query_frame,
            height=132,
            wrap="word",
            font=input_font,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        self.query_text.grid(row=10, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))
        self.query_help_btn = link_button(self.query_frame, 11, lambda: self._show_help("query"))

        self.site_label = label(self.query_frame, 12, columnspan=2, pady=(8, 4))
        self.site_var = tk.StringVar()
        self.site_entry = ctk.CTkTextbox(
            self.query_frame,
            height=100,
            wrap="none",
            font=input_font,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        self.site_entry.grid(row=13, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))
        self.site_help_btn = link_button(self.query_frame, 14, lambda: self._show_help("site"))

        # Crawl settings.
        self.safe_label = label(self.crawl_frame, 1)
        self.safe_var = tk.StringVar(value="")
        self.safe_combo = combo(self.crawl_frame, 1, variable=self.safe_var, values=["", "off", "medium", "high"], width=180)

        self.disable_filter_var = tk.BooleanVar(value=False)
        self.filter_check = ctk.CTkCheckBox(
            self.crawl_frame,
            text="",
            variable=self.disable_filter_var,
            height=26,
            checkbox_width=19,
            checkbox_height=19,
            font=label_font,
        )
        self.filter_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=5)

        self.start_date_label = label(self.crawl_frame, 3)
        self.start_date_entry = DateEntry(self.crawl_frame, self._t, self.icon_path, date.today())
        self.start_date_entry.grid(row=3, column=1, sticky="w", padx=(4, 12), pady=5)
        self.end_date_label = label(self.crawl_frame, 4)
        self.end_date_entry = DateEntry(self.crawl_frame, self._t, self.icon_path, date.today())
        self.end_date_entry.grid(row=4, column=1, sticky="w", padx=(4, 12), pady=5)

        self.spin_vars = {}
        engine_key = getattr(self, "_building_context_key", "google")
        restart_default = 0 if engine_key == "baidu" else 4
        max_pages_default = 100 if engine_key == "baidu" else 30
        day_step_default = 0 if engine_key == "baidu" else 7
        per_page_default = 50 if engine_key == "baidu" else 10
        rows = [
            ("max_pages", max_pages_default, 1, 1000),
            ("day_step", day_step_default, 0, 3650),
            ("per_page", per_page_default, 1, 100),
            ("timeout", 15, 1, 300),
            ("post_fetch_wait_ms", 800, 0, 60000),
            ("empty_page_retry_count", 2, 0, 10),
            ("empty_page_retry_wait_ms", 1500, 0, 60000),
            ("no_new_pages_limit", 1, 1, 10),
            ("selenium_restart_pages", restart_default, 0, 1000),
        ]
        base = 5
        for idx, (name, default, min_value, max_value) in enumerate(rows):
            row = base + idx
            lab = label(self.crawl_frame, row)
            setattr(self, f"{name}_label", lab)
            var = tk.IntVar(value=default)
            self.spin_vars[name] = var
            CTkSpinbox(self.crawl_frame, from_=min_value, to=max_value, textvariable=var, width=170).grid(
                row=row, column=1, sticky="w", padx=(4, 12), pady=5
            )

        self.max_pages_hint_label = ctk.CTkLabel(
            self.crawl_frame,
            text="",
            wraplength=390,
            justify="left",
            anchor="w",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.max_pages_hint_label.grid(row=base + len(rows), column=0, columnspan=2, sticky="ew", padx=12, pady=(2, 8))

        self.delay_vars = {}
        delay_defs = [("page_delay", 30000, 90000), ("slice_delay", 30000, 60000), ("error_delay", 60000, 180000)]
        delay_base = base + len(rows) + 1
        for offset, (name, mn, mx) in enumerate(delay_defs):
            row = delay_base + offset
            lab = label(self.crawl_frame, row)
            setattr(self, f"{name}_label", lab)
            box = ctk.CTkFrame(self.crawl_frame, fg_color="transparent")
            box.grid(row=row, column=1, sticky="w", padx=(4, 12), pady=5)
            vmin = tk.IntVar(value=mn)
            vmax = tk.IntVar(value=mx)
            self.delay_vars[name] = (vmin, vmax)
            CTkSpinbox(box, from_=0, to=9999999, textvariable=vmin, width=132).pack(side="left")
            ctk.CTkLabel(box, text="–", width=24, font=label_font, text_color=COLOR_MUTED).pack(side="left")
            CTkSpinbox(box, from_=0, to=9999999, textvariable=vmax, width=132).pack(side="left")

        # Google-only language/country multi-selects use native Listbox because CTk has no equivalent.
        self.limit_frame.grid_columnconfigure(0, weight=1)
        self.language_label = label(self.limit_frame, 1, columnspan=2, pady=(4, 4))
        self.language_box = ctk.CTkFrame(self.limit_frame, fg_color="transparent")
        self.language_box.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 5))
        self.language_box.grid_columnconfigure(0, weight=1)
        self.language_box.grid_rowconfigure(0, weight=1)
        self.language_list = tk.Listbox(
            self.language_box,
            selectmode="extended",
            height=9,
            width=48,
            exportselection=False,
            activestyle="dotbox",
            font=(FONT_FAMILY, 11),
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            selectbackground="#b7dfe3",
            selectforeground=COLOR_TEXT,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            relief="flat",
        )
        lang_sb_y = ctk.CTkScrollbar(self.language_box, orientation="vertical", command=self.language_list.yview)
        lang_sb_x = ctk.CTkScrollbar(self.language_box, orientation="horizontal", command=self.language_list.xview)
        self.language_list.configure(yscrollcommand=lang_sb_y.set, xscrollcommand=lang_sb_x.set)
        self.language_list.grid(row=0, column=0, sticky="nsew")
        lang_sb_y.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        lang_sb_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.clear_lang_btn = normal_button(self.limit_frame, "", lambda: self.language_list.selection_clear(0, tk.END), width=112)
        self.clear_lang_btn.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 10))

        self.country_label = label(self.limit_frame, 4, columnspan=2, pady=(4, 4))
        self.country_box = ctk.CTkFrame(self.limit_frame, fg_color="transparent")
        self.country_box.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 5))
        self.country_box.grid_columnconfigure(0, weight=1)
        self.country_box.grid_rowconfigure(0, weight=1)
        self.country_list = tk.Listbox(
            self.country_box,
            selectmode="extended",
            height=11,
            width=48,
            exportselection=False,
            activestyle="dotbox",
            font=(FONT_FAMILY, 11),
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            selectbackground="#b7dfe3",
            selectforeground=COLOR_TEXT,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            relief="flat",
        )
        country_sb_y = ctk.CTkScrollbar(self.country_box, orientation="vertical", command=self.country_list.yview)
        country_sb_x = ctk.CTkScrollbar(self.country_box, orientation="horizontal", command=self.country_list.xview)
        self.country_list.configure(yscrollcommand=country_sb_y.set, xscrollcommand=country_sb_x.set)
        self.country_list.grid(row=0, column=0, sticky="nsew")
        country_sb_y.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        country_sb_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.clear_country_btn = normal_button(self.limit_frame, "", lambda: self.country_list.selection_clear(0, tk.END), width=112)
        self.clear_country_btn.grid(row=6, column=0, sticky="w", padx=12, pady=(0, 10))

        # Output settings.
        self.output_file_label = label(self.output_frame, 1)
        self.output_entry = ctk.CTkEntry(self.output_frame, textvariable=self.output_path, height=32, font=input_font)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=(4, 12), pady=5)
        self.browse_button = normal_button(self.output_frame, "", self._browse_output, width=90)
        self.browse_button.grid(row=2, column=1, sticky="w", padx=(4, 12), pady=(0, 8))

        self.output_format_label = label(self.output_frame, 3)
        self.output_format_combo = ctk.CTkComboBox(
            self.output_frame,
            variable=self.output_format,
            values=list(OUTPUT_FORMATS),
            state="readonly",
            height=32,
            width=180,
            font=input_font,
            dropdown_font=input_font,
            command=lambda _value: self._on_output_format_changed(),
        )
        self.output_format_combo.grid(row=3, column=1, sticky="w", padx=(4, 12), pady=5)

        self.content_folder_label = label(self.output_frame, 4, pady=(11, 5))
        content_dir_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        content_dir_frame.grid(row=4, column=1, sticky="ew", padx=(4, 12), pady=(11, 5))
        content_dir_frame.grid_columnconfigure(0, weight=1)
        self.content_dir_entry = ctk.CTkEntry(content_dir_frame, textvariable=self.content_dir_var, height=32, font=input_font)
        self.content_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.content_browse_button = normal_button(content_dir_frame, "", self._browse_content_dir, width=78)
        self.content_browse_button.grid(row=0, column=1)

        self.content_threads_label = label(self.output_frame, 5)
        self.content_threads_spin = CTkSpinbox(self.output_frame, from_=1, to=32, textvariable=self.content_threads_var, width=170)
        self.content_threads_spin.grid(row=5, column=1, sticky="w", padx=(4, 12), pady=5)

        self.content_fetch_mode_label = label(self.output_frame, 6)
        self.content_fetch_mode_combo = combo(self.output_frame, 6, variable=self.content_fetch_mode_var, width=260)

        self.content_delay_label = label(self.output_frame, 7)
        content_delay_box = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        content_delay_box.grid(row=7, column=1, sticky="w", padx=(4, 12), pady=5)
        CTkSpinbox(content_delay_box, from_=0, to=9999999, textvariable=self.content_delay_min_var, width=132).pack(side="left")
        ctk.CTkLabel(content_delay_box, text="–", width=24, font=label_font, text_color=COLOR_MUTED).pack(side="left")
        CTkSpinbox(content_delay_box, from_=0, to=9999999, textvariable=self.content_delay_max_var, width=132).pack(side="left")

        self.content_receive_wait_label = label(self.output_frame, 8)
        CTkSpinbox(self.output_frame, from_=0, to=9999999, textvariable=self.content_receive_wait_var, width=170).grid(
            row=8, column=1, sticky="w", padx=(4, 12), pady=5
        )

        self.content_cleaning_label = label(self.output_frame, 9)
        self.content_cleaning_combo = combo(self.output_frame, 9, variable=self.content_cleaning_var, width=260)

        self.content_selenium_fallback_check = ctk.CTkCheckBox(
            self.output_frame,
            text="",
            variable=self.content_selenium_fallback_var,
            height=26,
            checkbox_width=19,
            checkbox_height=19,
            font=label_font,
        )
        self.content_selenium_fallback_check.grid(row=10, column=0, columnspan=2, sticky="w", padx=12, pady=5)
        self.content_selenium_fallback_check.grid_remove()

        self.output_hint_label = ctk.CTkLabel(
            self.output_frame,
            text="",
            wraplength=390,
            justify="left",
            anchor="w",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.output_hint_label.grid(row=11, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 11))

        if getattr(self, "_building_context_key", "google") == "baidu":
            self.limit_frame.grid_remove()

        self.settings_scroll.bind_mousewheel_to_descendants()

    def _build_results_panel(self, parent):
        parent.grid_rowconfigure(0, weight=3)
        parent.grid_rowconfigure(1, weight=2)
        parent.grid_columnconfigure(0, weight=1)

        self.preview_frame = CTkSection(parent, text="Preview")
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 2), pady=(0, 8))
        self.preview_frame.grid_rowconfigure(2, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_toolbar = ctk.CTkFrame(self.preview_frame, fg_color="#eef5f6", corner_radius=7)
        self.preview_toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 7))
        self.preview_toolbar.grid_columnconfigure(0, weight=0)
        self.preview_toolbar.grid_columnconfigure(1, weight=0)
        self.preview_toolbar.grid_columnconfigure(2, weight=1)

        toolbar_font = ctk.CTkFont(family=FONT_FAMILY, size=11)
        group_font = ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")

        def toolbar_group(row, column, *, columnspan=1, sticky="w"):
            frame = ctk.CTkFrame(
                self.preview_toolbar,
                fg_color=COLOR_SURFACE,
                border_color=COLOR_BORDER,
                border_width=1,
                corner_radius=6,
            )
            frame.grid(row=row, column=column, columnspan=columnspan, padx=5, pady=4, sticky=sticky)
            return frame

        def small_button(master, command, *, width=72):
            return ctk.CTkButton(
                master,
                text="",
                command=command,
                width=width,
                height=28,
                font=toolbar_font,
                **ctk_button_colors(),
            )

        # Row 1: selection/editing and sorting are separate visual groups.
        record_group = toolbar_group(0, 0)
        self.record_group_label = ctk.CTkLabel(record_group, text="", font=group_font, text_color=COLOR_ACCENT)
        self.record_group_label.grid(row=0, column=0, padx=(8, 5), pady=5)
        self.open_link_button = small_button(record_group, self._open_selected_link, width=68)
        self.open_link_button.grid(row=0, column=1, padx=2, pady=4)
        self.delete_selected_button = small_button(record_group, self._delete_selected_records, width=72)
        self.delete_selected_button.grid(row=0, column=2, padx=2, pady=4)

        self.result_edit_menu = DpiAwareMenu(self, tearoff=False)
        self.result_edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo_result_edit)
        self.result_edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo_result_edit)
        self.result_edit_menu.add_separator()
        self.result_edit_menu.add_command(label="Reset", accelerator="Ctrl+Shift+R", command=self._reset_result_preview)
        self.result_edit_button = small_button(record_group, self._popup_result_edit_menu, width=68)
        self.result_edit_button.grid(row=0, column=3, padx=(2, 6), pady=4)

        sort_group = toolbar_group(0, 1)
        self.sort_group_label = ctk.CTkLabel(sort_group, text="", font=group_font, text_color=COLOR_ACCENT)
        self.sort_group_label.grid(row=0, column=0, padx=(8, 5), pady=5)
        self.sort_label = ctk.CTkLabel(sort_group, text="", font=toolbar_font, text_color=COLOR_MUTED)
        self.sort_label.grid(row=0, column=4, padx=0, pady=0)
        self.sort_label.grid_remove()
        self.sort_time_button = small_button(sort_group, lambda: self._sort_records("time"), width=60)
        self.sort_time_button.grid(row=0, column=1, padx=2, pady=4)
        self.sort_title_button = small_button(sort_group, lambda: self._sort_records("title"), width=60)
        self.sort_title_button.grid(row=0, column=2, padx=2, pady=4)
        self.sort_source_button = small_button(sort_group, lambda: self._sort_records("source"), width=68)
        self.sort_source_button.grid(row=0, column=3, padx=(2, 6), pady=4)

        self.preview_count_var = tk.StringVar(value="")
        self.preview_count_label = ctk.CTkLabel(
            self.preview_toolbar,
            textvariable=self.preview_count_var,
            font=toolbar_font,
            text_color=COLOR_MUTED,
        )
        self.preview_count_label.grid(row=0, column=2, padx=(8, 10), pady=5, sticky="e")

        # Row 2: sampling is isolated from ordinary row actions.
        sample_group = toolbar_group(1, 0, columnspan=3, sticky="w")
        self.sample_group_label = ctk.CTkLabel(sample_group, text="", font=group_font, text_color=COLOR_ACCENT)
        self.sample_group_label.grid(row=0, column=0, padx=(8, 5), pady=5)
        self.sample_scheme_label = ctk.CTkLabel(sample_group, text="", font=toolbar_font, text_color=COLOR_MUTED)
        self.sample_scheme_label.grid(row=0, column=1, padx=(2, 3), pady=5)
        self.sample_scheme_var = tk.StringVar()
        self.sample_scheme_combo = ctk.CTkComboBox(
            sample_group,
            variable=self.sample_scheme_var,
            values=[""],
            state="readonly",
            width=165,
            height=28,
            font=toolbar_font,
            dropdown_font=toolbar_font,
        )
        self.sample_scheme_combo.grid(row=0, column=2, padx=3, pady=4)
        self.sample_count_label = ctk.CTkLabel(sample_group, text="", font=toolbar_font, text_color=COLOR_MUTED)
        self.sample_count_label.grid(row=0, column=3, padx=(8, 3), pady=5)
        self.sample_count_var = tk.IntVar(value=20)
        self.sample_count_spin = CTkSpinbox(sample_group, from_=1, to=1000000, textvariable=self.sample_count_var, width=100)
        self.sample_count_spin.grid(row=0, column=4, padx=3, pady=4)
        self.sample_button = small_button(sample_group, self._sample_records, width=68)
        self.sample_button.grid(row=0, column=5, padx=(3, 6), pady=4)

        # Row 3: all full-text download actions share a dedicated group.
        download_group = toolbar_group(2, 0, columnspan=3, sticky="w")
        self.download_group_label = ctk.CTkLabel(download_group, text="", font=group_font, text_color=COLOR_ACCENT)
        self.download_group_label.grid(row=0, column=0, padx=(8, 5), pady=5)
        self.download_content_button = small_button(download_group, self._download_selected_content, width=112)
        self.download_content_button.grid(row=0, column=1, padx=2, pady=4)
        self.download_all_content_button = small_button(download_group, self._download_all_content, width=102)
        self.download_all_content_button.grid(row=0, column=2, padx=2, pady=4)
        self.download_settings_button = small_button(download_group, self._open_content_settings_dialog, width=108)
        self.download_settings_button.grid(row=0, column=3, padx=(2, 6), pady=4)

        columns = ("no", "time", "title", "source", "published", "status", "words", "quality", "link")
        self.tree = DpiAwareTreeview(self.preview_frame, columns=columns, show="headings", height=16, selectmode="extended")
        for col, width in [("no", 58), ("time", 140), ("title", 330), ("source", 120), ("published", 110), ("status", 95), ("words", 70), ("quality", 70), ("link", 420)]:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_records("time" if c in ("published", "no") else c if c in ("title", "source") else "time"))
            self.tree.logical_column(col, width=width, minwidth=48, stretch=(col not in {"no", "words", "quality"}))
        ysb = ctk.CTkScrollbar(self.preview_frame, orientation="vertical", command=self.tree.yview)
        xsb = ctk.CTkScrollbar(self.preview_frame, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=2, column=0, sticky="nsew", padx=(8, 3), pady=(0, 3))
        ysb.grid(row=2, column=1, sticky="ns", padx=(0, 6), pady=(0, 3))
        xsb.grid(row=3, column=0, sticky="ew", padx=(8, 3), pady=(0, 7))
        self.tree.bind("<Double-1>", lambda _e: self._open_selected_link(), add="+")
        self.tree.bind("<Return>", lambda _e: self._open_selected_link(), add="+")
        self.tree.bind("<Delete>", lambda _e: self._delete_selected_records(), add="+")
        self.tree.bind("<Button-3>", self._show_result_context_menu, add="+")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_preview_count(), add="+")
        self._bind_mousewheel(self.tree)

        self.result_menu = DpiAwareMenu(self, tearoff=False)
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

        self.log_frame = CTkSection(parent, text="Log")
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=(6, 2), pady=(0, 2))
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            height=150,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _popup_result_edit_menu(self):
        try:
            x = self.result_edit_button.winfo_rootx()
            y = self.result_edit_button.winfo_rooty() + self.result_edit_button.winfo_height()
            self.result_edit_menu.tk_popup(x, y)
        finally:
            try:
                self.result_edit_menu.grab_release()
            except Exception:
                pass

    def _t(self, key):
        return t(self.ui_lang, key)

    def _set_language(self, lang):
        old_lang = getattr(self, "ui_lang", lang)
        self.ui_lang = lang
        self.ui_lang_var.set(lang)
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
            self.open_download_button: "open_download_folder",
            self.record_group_label: "preview_records_group",
            self.sort_group_label: "preview_sort_group",
            self.sample_group_label: "preview_sample_group",
            self.download_group_label: "preview_download_group",
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
                widget.configure(text=t(lang, key))
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
            self.toolbar_progress_label.configure(text=progress_text)
        except Exception:
            pass
        self._update_preview_count()
        if hasattr(self, "sample_scheme_combo"):
            current_key = self._current_sample_scheme_key()
            self.sample_scheme_combo.configure(values=[t(lang, k) for k in ("sample_simple", "sample_systematic", "sample_by_source")])
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
        self.query_mode_combo.configure(values=labels_for(query_options, lang))
        for opt in query_options:
            if opt.get("key") == query_key:
                self.query_mode_combo.set(label_for(opt, lang))
                break
        self.vertical_combo.configure(values=labels_for(vertical_options, lang))
        if vertical_key not in {opt.get("key") for opt in vertical_options}:
            vertical_key = default_vertical
        for opt in vertical_options:
            if opt.get("key") == vertical_key:
                self.vertical_combo.set(label_for(opt, lang))
                break
        if hasattr(self, "baidu_sort_combo"):
            current_baidu_sort = self._current_combo_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, previous_lang or lang, self.settings.get("baidu_sort", self.defaults.get("baidu_sort", "focus"))) if self.baidu_sort_combo.get() else self.settings.get("baidu_sort", self.defaults.get("baidu_sort", "focus"))
            self.baidu_sort_combo.configure(values=labels_for(BAIDU_SORT_OPTIONS, lang))
            self._set_combo_by_key(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, current_baidu_sort)
        self.backend_combo.configure(values=labels_for(FETCH_BACKEND_OPTIONS, lang))
        for opt in FETCH_BACKEND_OPTIONS:
            if opt.get("key") == backend_key:
                self.backend_combo.set(label_for(opt, lang))
        if hasattr(self, "content_fetch_mode_combo"):
            self.content_fetch_mode_combo.configure(values=labels_for(CONTENT_FETCH_MODE_OPTIONS, lang))
            self._set_combo_by_key(self.content_fetch_mode_combo, CONTENT_FETCH_MODE_OPTIONS, content_fetch_key)
        if hasattr(self, "content_cleaning_combo"):
            self.content_cleaning_combo.configure(values=labels_for(CONTENT_CLEANING_OPTIONS, lang))
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
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.transient(self)
        win.resizable(True, True)
        self._apply_icon(win)
        root = ctk.CTkFrame(win, fg_color=COLOR_BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=14, pady=14)
        txt = ctk.CTkTextbox(
            root,
            wrap="word",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        ctk.CTkButton(
            root,
            text=t(self.ui_lang, "close"),
            command=win.destroy,
            width=96,
            height=32,
            **ctk_button_colors(),
        ).pack(anchor="e", pady=(10, 0))
        try:
            width, height = (int(value) for value in geometry.lower().split("x", 1))
        except Exception:
            width, height = 880, 680
        fit_window_to_screen(win, requested_width=width, requested_height=height, parent=self, min_width=620, min_height=440)
        win.lift()
        win.focus_force()

    def _show_about(self):
        win = ctk.CTkToplevel(self)
        win.title(t(self.ui_lang, "menu_about"))
        win.transient(self)
        win.resizable(True, True)
        self._apply_icon(win)
        root = ctk.CTkFrame(win, fg_color=COLOR_BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=18, pady=18)

        top = ctk.CTkFrame(root, fg_color="transparent")
        top.pack(fill="x", pady=(0, 12))
        self._about_logo_image = None
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                self._about_logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(118, 118))
                ctk.CTkLabel(top, image=self._about_logo_image, text="").pack(side="left", padx=(0, 16))
            except Exception:
                self._about_logo_image = None
        heading = ctk.CTkFrame(top, fg_color="transparent")
        heading.pack(side="left", fill="x", expand=True, anchor="w")
        ctk.CTkLabel(
            heading,
            text="BFSU WebLens",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=COLOR_ACCENT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            heading,
            text=t(self.ui_lang, "subtitle"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLOR_MUTED,
            justify="left",
            wraplength=560,
        ).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(
            heading,
            text="Dr. Liu Dingjia / 刘鼎甲 博士  ·  djliu@bfsu.edu.cn",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", pady=(8, 0))

        txt = ctk.CTkTextbox(
            root,
            wrap="word",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        txt.pack(fill="both", expand=True, pady=(0, 12))
        txt.insert("1.0", t(self.ui_lang, "about"))
        txt.configure(state="disabled")
        ctk.CTkButton(
            root,
            text=t(self.ui_lang, "close"),
            command=win.destroy,
            width=100,
            height=32,
            **ctk_button_colors(),
        ).pack(anchor="e")
        fit_window_to_screen(win, requested_width=900, requested_height=760, parent=self, min_width=700, min_height=560)
        win.lift()
        win.focus_force()

    def _show_user_guide(self):
        self._show_text_window(t(self.ui_lang, "user_guide_title"), t(self.ui_lang, "user_guide_text"), "920x720")

    def _show_parameter_guide(self):
        self._show_text_window(t(self.ui_lang, "parameter_guide_title"), t(self.ui_lang, "parameter_guide_text"), "940x760")

    def _show_help(self, kind):
        title = t(self.ui_lang, "help_query_title" if kind == "query" else "help_site_title")
        text = t(self.ui_lang, "query_help_text" if kind == "query" else "site_help_text")
        self._show_text_window(title, text, "820x620")

    def _show_settings(self):
        win = ctk.CTkToplevel(self)
        win.title(t(self.ui_lang, "settings_title"))
        win.transient(self)
        win.resizable(True, True)
        win.grab_set()
        self._apply_icon(win)

        root = ctk.CTkFrame(win, fg_color=COLOR_BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=16, pady=16)
        body = ctk.CTkScrollableFrame(root, fg_color=COLOR_PANEL, corner_radius=7)
        body.pack(fill="both", expand=True)
        ctk.CTkLabel(
            body,
            text=t(self.ui_lang, "settings_title"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLOR_ACCENT,
        ).pack(anchor="w", padx=12, pady=(12, 5))
        ctk.CTkLabel(
            body,
            text=t(self.ui_lang, "settings_saved_hint"),
            wraplength=790,
            justify="left",
            anchor="w",
            text_color=COLOR_MUTED,
        ).pack(fill="x", padx=12, pady=(0, 12))
        section = CTkSection(body, text=t(self.ui_lang, "user_agent_label"))
        section.pack(fill="x", padx=8, pady=(0, 10))
        txt = ctk.CTkTextbox(
            section,
            height=170,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        txt.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        section.grid_columnconfigure(0, weight=1)
        txt.insert("1.0", self.user_agent_var.get())
        ctk.CTkLabel(
            section,
            text=t(self.ui_lang, "user_agent_hint"),
            wraplength=760,
            justify="left",
            anchor="w",
            text_color=COLOR_MUTED,
        ).grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        ctk.CTkLabel(
            section,
            text=t(self.ui_lang, "settings_file_hint", path=str(self.settings_path)),
            wraplength=760,
            justify="left",
            anchor="w",
            text_color=COLOR_MUTED,
        ).grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

        def apply_settings(close=False):
            value = txt.get("1.0", "end").strip() or DEFAULT_USER_AGENT
            self.user_agent_var.set(value)
            self._save_settings()
            self._log(t(self.ui_lang, "settings_saved"))
            if close:
                win.destroy()

        btns = ctk.CTkFrame(root, fg_color="transparent")
        btns.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            btns,
            text=t(self.ui_lang, "reset_default"),
            command=lambda: (txt.delete("1.0", "end"), txt.insert("1.0", DEFAULT_USER_AGENT)),
            height=32,
            **ctk_button_colors(),
        ).pack(side="left")
        ctk.CTkButton(
            btns,
            text=t(self.ui_lang, "reset_all_defaults"),
            command=lambda: self._reset_all_settings_to_defaults(win),
            height=32,
            **ctk_button_colors("danger"),
        ).pack(side="left", padx=(8, 0))
        ctk.CTkButton(btns, text=t(self.ui_lang, "close"), command=win.destroy, width=88, height=32, **ctk_button_colors()).pack(side="right")
        ctk.CTkButton(btns, text=t(self.ui_lang, "ok"), command=lambda: apply_settings(True), width=88, height=32, **ctk_button_colors("accent")).pack(side="right", padx=(0, 8))
        ctk.CTkButton(btns, text=t(self.ui_lang, "apply"), command=lambda: apply_settings(False), width=88, height=32, **ctk_button_colors()).pack(side="right", padx=(0, 8))
        fit_window_to_screen(win, requested_width=920, requested_height=620, parent=self, min_width=700, min_height=480)
        win.bind("<Escape>", lambda _e: win.destroy())
        win.lift()
        win.focus_force()

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
            if isinstance(self.site_entry, (tk.Text, ctk.CTkTextbox)):
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
            if isinstance(self.site_entry, (tk.Text, ctk.CTkTextbox)):
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
        self.progress.configure(mode="determinate", maximum=100, value=0)
        self.toolbar_progress.configure(maximum=100, value=0)
        self.status_var.set(t(self.ui_lang, "status_running"))
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
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
        self.progress.configure(maximum=maximum, value=value)
        self.toolbar_progress.configure(maximum=maximum, value=value)

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
        elif event.event_type == "verification_wait":
            self._log("[VERIFICATION WAIT] " + event.message)
            self.status_var.set(t(self.ui_lang, "verification_wait_status"))
            messagebox.showwarning(
                t(self.ui_lang, "verification_wait_title"),
                t(self.ui_lang, "verification_wait_message"),
            )
        elif event.event_type == "verification_passed":
            self._log("[VERIFICATION PASSED] " + event.message)
            self.status_var.set(t(self.ui_lang, "status_running"))
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
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return
        self._set_progress(100, 100)
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
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
        """Show a complete, DPI-safe CTk content-download settings dialog."""
        lang = self.ui_lang
        dialog = ctk.CTkToplevel(self)
        dialog.title(t(lang, title_key))
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        self._apply_icon(dialog)

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
        scheme_var.set(label_for(next((o for o in CONTENT_CLEANING_OPTIONS if o.get("key") == current_key), CONTENT_CLEANING_OPTIONS[0]), lang))

        root = ctk.CTkFrame(dialog, fg_color=COLOR_BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=16, pady=16)
        body = ctk.CTkScrollableFrame(root, fg_color=COLOR_PANEL, corner_radius=7)
        body.pack(fill="both", expand=True)
        section = CTkSection(body, text=t(lang, title_key))
        section.pack(fill="x", padx=8, pady=8)
        section.grid_columnconfigure(0, weight=0, minsize=205)
        section.grid_columnconfigure(1, weight=1)
        font = ctk.CTkFont(family=FONT_FAMILY, size=12)

        def add_label(row, key):
            ctk.CTkLabel(section, text=t(lang, key), font=font, anchor="w", justify="left").grid(
                row=row, column=0, sticky="w", padx=(12, 10), pady=6
            )

        add_label(1, "content_folder")
        folder_frame = ctk.CTkFrame(section, fg_color="transparent")
        folder_frame.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=6)
        folder_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(folder_frame, textvariable=folder_var, height=32, font=font).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        def browse_folder():
            selected = filedialog.askdirectory(title=t(lang, "select_content_folder"), initialdir=folder_var.get() or os.getcwd())
            if selected:
                folder_var.set(selected)

        ctk.CTkButton(folder_frame, text=t(lang, "browse"), command=browse_folder, width=82, height=32, **ctk_button_colors()).grid(row=0, column=1)

        add_label(2, "content_threads")
        CTkSpinbox(section, from_=1, to=32, textvariable=threads_var, width=170).grid(row=2, column=1, sticky="w", padx=(0, 12), pady=6)
        add_label(3, "content_fetch_mode")
        ctk.CTkComboBox(section, variable=fetch_mode_var, values=fetch_mode_labels, state="readonly", height=32, font=font, dropdown_font=font).grid(row=3, column=1, sticky="ew", padx=(0, 12), pady=6)
        add_label(4, "content_delay")
        delay_box = ctk.CTkFrame(section, fg_color="transparent")
        delay_box.grid(row=4, column=1, sticky="w", padx=(0, 12), pady=6)
        CTkSpinbox(delay_box, from_=0, to=9999999, textvariable=delay_min_var, width=145).pack(side="left")
        ctk.CTkLabel(delay_box, text="–", width=26, text_color=COLOR_MUTED).pack(side="left")
        CTkSpinbox(delay_box, from_=0, to=9999999, textvariable=delay_max_var, width=145).pack(side="left")
        add_label(5, "content_receive_wait")
        CTkSpinbox(section, from_=0, to=9999999, textvariable=receive_wait_var, width=170).grid(row=5, column=1, sticky="w", padx=(0, 12), pady=6)
        add_label(6, "content_retry_count")
        CTkSpinbox(section, from_=0, to=10, textvariable=retry_var, width=170).grid(row=6, column=1, sticky="w", padx=(0, 12), pady=6)
        add_label(7, "content_task_timeout")
        CTkSpinbox(section, from_=30, to=86400, textvariable=task_timeout_var, width=170).grid(row=7, column=1, sticky="w", padx=(0, 12), pady=6)
        ctk.CTkCheckBox(
            section,
            text=t(lang, "content_resume_enabled"),
            variable=resume_var,
            height=26,
            checkbox_width=19,
            checkbox_height=19,
            font=font,
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=12, pady=7)
        add_label(9, "content_cleaning_scheme")
        ctk.CTkComboBox(section, variable=scheme_var, values=scheme_labels, state="readonly", height=32, font=font, dropdown_font=font).grid(row=9, column=1, sticky="ew", padx=(0, 12), pady=6)

        desc = ctk.CTkTextbox(
            section,
            height=220,
            wrap="word",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
        )
        desc.grid(row=10, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 12))
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

        btns = ctk.CTkFrame(root, fg_color="transparent")
        btns.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btns, text=t(lang, "cancel"), command=dialog.destroy, width=96, height=32, **ctk_button_colors()).pack(side="right")
        ctk.CTkButton(btns, text=t(lang, "ok"), command=ok, width=96, height=32, **ctk_button_colors("accent")).pack(side="right", padx=(0, 8))

        dialog.bind("<Return>", lambda _e: ok())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        fit_window_to_screen(dialog, requested_width=900, requested_height=790, parent=self, min_width=700, min_height=560)
        dialog.lift()
        dialog.focus_force()
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
        self.stop_button.configure(state="normal")
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
            self.stop_button.configure(state="disabled")

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

    def _open_download_folder(self):
        """Create and open the active panel's configured content-download folder."""
        self._ensure_active_context_from_tab()
        raw_path = self.content_dir_var.get().strip() if hasattr(self, "content_dir_var") else ""
        path = Path(raw_path or self.defaults.get("content_download_dir", str(app_base_dir() / "content_downloads")))
        try:
            path.mkdir(parents=True, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

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
