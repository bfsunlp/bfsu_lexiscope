# -*- coding: utf-8 -*-
"""PySide6 main window for BFSU WebLens.

The interface is intentionally built from native Qt widgets and mirrors the
fixed warm-light visual language used by BFSU EditTrac.  Search collection and
full-text downloading remain background operations so the GUI stays responsive.
"""
from __future__ import annotations

import json
import os
import queue
import random
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PySide6.QtCore import QAbstractTableModel, QDate, QModelIndex, QObject, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTableView,
    QToolBar,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..collector import (
    BrowserStartupError,
    CollectorConfig,
    NetworkAccessError,
    StopCrawl,
    crawl,
    is_google_news_redirect_url,
    normalize_url_for_dedup,
    split_text_terms,
)
from ..browser_manager import (
    browser_installations_for_source,
    browser_source_key,
    detect_browser_installations,
    download_portable_browser,
    ensure_driver,
    update_portable_environment,
    find_compatible_driver,
    installation_for_path,
    official_browser_url,
    official_driver_url,
    latest_browser_recommendation,
    preferred_browser_path,
    driver_executable_name,
    driver_version,
    versions_compatible,
)
from ..content_downloader import (
    ContentDownloadSettings,
    DomainLockPool,
    content_result_from_manifest,
    download_one,
    ensure_content_dirs,
    load_successful_download_index,
    successful_manifest_for_record,
)
from ..date_utils import format_published_date, published_sort_key
from ..data import (
    APP_LANGS,
    BAIDU_SORT_OPTIONS,
    CONTENT_CLEANING_OPTIONS,
    CONTENT_FETCH_MODE_OPTIONS,
    COUNTRY_OPTIONS,
    FETCH_BACKEND_OPTIONS,
    LANGUAGE_OPTIONS,
    OUTPUT_FORMATS,
    QUERY_MODE_OPTIONS,
    VERTICAL_OPTIONS,
    label_for,
)
from ..exporter import export_import_template, export_records
from ..importer import import_records, import_urls_from_text
from ..manual_collection import generate_manual_search_tasks, parse_saved_search_page
from ..resources import apply_window_icon, resource_path
from ..timing_utils import milliseconds_to_ui_seconds, ui_seconds_to_milliseconds
from ..platform_paths import user_data_root
from ..maintenance import clear_web_components

APP_NAME = "BFSU WebLens"
APP_VERSION = __version__
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)


UI_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "google": "Google",
        "baidu": "Baidu",
        "search_engine": "Search engine",
        "file": "File",
        "edit": "Edit",
        "settings": "Settings",
        "help": "Help",
        "language": "Interface language",
        "browser_settings": "Browser && Selenium…",
        "browser_settings_title": "Browser and Selenium",
        "browser_detected": "Detected browser installations",
        "browser_driver": "WebDriver",
        "browser_type": "Browser",
        "browser_source": "Browser source",
        "browser_source_portable": "WebLens portable Chrome (Recommended)",
        "browser_source_system": "System-installed Chrome (Not recommended)",
        "browser_source_system_note": "For Chrome, the system-installed browser is an opt-in fallback and is not recommended because Chrome can auto-update independently of WebLens. Microsoft Edge is different: Edge uses the system-installed browser by default because Microsoft does not publish an equivalent portable Edge ZIP.",
        "browser_source_portable_note": "Recommended for Chrome: WebLens uses Chrome for Testing under tools/browser, isolated from your everyday Chrome installation. If it is missing, One-click configuration downloads and extracts the official archive automatically.",
        "browser_source_edge_system": "System-installed Microsoft Edge (Recommended)",
        "browser_source_edge_system_note": "Recommended for Edge: WebLens uses the system-installed Microsoft Edge browser and manages only the matching EdgeDriver. Microsoft does not publish an official portable Edge ZIP comparable to Chrome for Testing.",
        "detect_system_edge": "Detect system Edge",
        "edge_system_ready": "System-installed Microsoft Edge detected. WebLens will verify or prepare the matching EdgeDriver before collection.",
        "sort_by": "Sort by",
        "sort_none": "Original order",
        "start": "Start collection",
        "stop": "Stop",
        "export": "Export",
        "import": "Import links",
        "paste_links": "Paste links from text…",
        "paste_links_title": "Paste links from text",
        "paste_links_help": "Paste or type any text containing one or more HTTP/HTTPS links. WebLens extracts the links and appends new ones to the current Result Preview. You can add links repeatedly without replacing existing results.",
        "paste_links_add": "Parse and add links",
        "paste_links_clear": "Clear text",
        "paste_links_none": "No HTTP/HTTPS links were found in the pasted text.",
        "paste_links_result": "Found {found} link(s); added {added} new link(s); skipped {skipped} duplicate(s).",
        "manual_collection": "Manual collection…",
        "manual_collection_title": "Manual search-result collection",
        "manual_intro": "Use the current search parameters to generate search-engine URLs. Open them in your normal browser, page through results manually, and save each result page as an HTML file. Then import those saved pages here; WebLens extracts result links and appends them to the current Result Preview. This mode does not require Selenium or a WebDriver.",
        "manual_urls_group": "1. Generated search URLs",
        "manual_urls_note": "Each item is an initial search URL. For Baidu, multiple terms and multiple site/domain filters are expanded into separate term × domain tasks; enabled date slicing adds another task dimension. Pagination is manual: follow the search engine's own Next/next-page control in your browser.",
        "manual_copy_selected": "Copy selected URL",
        "manual_copy_all": "Copy all URLs",
        "manual_copied": "Copied {n} URL(s) to the clipboard.",
        "manual_html_group": "2. Import saved result pages",
        "manual_html_note": "Save every result page with the browser's Save Page As command (HTML only is sufficient). You can import many .html/.htm files at once or import a folder repeatedly. New unique result links are appended to the existing Result Preview.",
        "manual_import_html": "Import HTML files…",
        "manual_import_folder": "Import HTML folder…",
        "manual_parsing": "Parsing saved search-result pages…",
        "manual_parse_summary": "Parsed {files} file(s): {records} result record(s) found; {added} new unique link(s) added; {skipped} duplicate(s) skipped; {warnings} file(s) had warnings.",
        "manual_no_tasks": "No search URL could be generated. Check the current search parameters.",
        "manual_no_html": "No .html or .htm files were found.",
        "manual_wrong_engine": "Some saved pages belong to another search engine and were skipped. Switch to the matching Google/Baidu panel before importing them.",
        "clear": "Clear",
        "open_output": "Open output",
        "open_download": "Open download folder",
        "exit": "Exit",
        "undo": "Undo result edit",
        "redo": "Redo result edit",
        "reset_results": "Reset result preview",
        "reset_settings": "Reset settings",
        "clear_web_components": "Clear WebLens web components…",
        "confirm_clear_web_components": "Remove WebLens-managed portable browsers, WebDrivers and their WebLens-specific caches? System-installed Chrome/Edge and corpus output files will not be touched.",
        "clear_web_components_done": "WebLens-managed web components were cleared. Browser/Driver paths were reset; configure them again before automatic collection.",
        "clear_web_components_warning": "Web components were cleared with warnings:\n{message}",
        "user_guide": "User guide",
        "parameter_guide": "Parameter guide",
        "about": "About",
        "query_settings": "Query settings",
        "crawl_settings": "Collection settings",
        "limit_settings": "Language and region restrictions",
        "output_settings": "Collected-link output",
        "result_preview": "Result Preview",
        "log": "Log",
        "query_mode": "Query mode",
        "search_vertical": "Search vertical",
        "baidu_sort": "Baidu sort",
        "query_terms": "Search terms / phrases",
        "site_filters": "Site/domain filters\n(one per line)",
        "site_filters_baidu": "Site/domain filters\n(one per line; searched separately)",
        "safe": "SafeSearch",
        "disable_filter": "Disable Google duplicate filtering",
        "collection_browser": "Collection browser",
        "driver_path": "Browser driver path",
        "browser_binary": "Browser installation",
        "browser_refresh": "Detect",
        "driver_manage": "Detect / update driver",
        "one_click_setup": "One-click configure Chrome && Edge",
        "update_portable_environment": "Update selected portable browser && WebDriver",
        "portable_update_running": "Updating the WebLens portable browser and WebDriver…",
        "portable_update_done": "Portable environment updated: browser {browser}; WebDriver {driver}.",
        "portable_update_edge_partial": "EdgeDriver was updated for bundled Edge {browser}. Microsoft does not provide an official portable Edge ZIP, so WebLens cannot automatically replace the bundled Edge browser. Current Microsoft Edge Stable: {latest}.",
        "portable_update_failed": "Portable environment update failed: {message}",
        "portable_update_system_disabled": "Switch Browser source to WebLens portable browser (Recommended) to update the WebLens-managed environment.",
        "download_browser_now": "Download/configure browser",
        "setup_all_start": "Configuring Chrome and Edge browser environments…",
        "setup_all_done": "One-click configuration finished.",
        "setup_all_partial": "One-click configuration completed with issues. You can use the independent controls below to finish manual configuration.",
        "manual_browser_invalid": "The selected browser executable is not a valid {browser} browser, or its version could not be detected.",
        "manual_driver_invalid": "The selected WebDriver version ({driver}) does not match the selected browser version ({browser}).",
        "manual_driver_unknown": "WebLens could not read a WebDriver version from the selected file.",
        "edge_portable_unavailable": "No WebLens-portable Edge browser was found under tools/browser. Microsoft does not provide an official portable Edge ZIP comparable to Chrome for Testing. To keep WebLens isolated from your everyday browser, place a portable Edge copy under tools/browser; alternatively, explicitly choose System-installed browser (Not recommended).",
        "browser_version_unreadable": "The browser executable was found, but its version could not be detected.",
        "driver_prepare_failed_generic": "A compatible WebDriver could not be prepared.",
        "driver_auto": "Automatic driver management",
        "driver_ready": "Driver ready: {version}",
        "driver_missing": "No matching driver is ready yet.",
        "driver_downloading": "Checking browser and driver…",
        "driver_downloaded": "Matching driver is ready:\n{path}",
        "driver_failed": "Automatic driver preparation failed.\n\n{message}\n\nYou can open the official browser or WebDriver download page from the buttons below.",
        "browser_not_found": "No usable {browser} was found for the selected browser source.",
        "open_driver_page": "Open WebDriver page",
        "open_browser_page": "Open browser page",
        "browse": "Browse…",
        "browser_wait": "Page render wait (ms)",
        "hide_browser": "Do not show the collection browser window",
        "date_filter_enabled": "Restrict collection by date",
        "start_date": "Start date",
        "end_date": "End date",
        "day_step": "Date-slice step (days; 0 = no slicing)",
        "timeout": "Page-load timeout (seconds)",
        "page_delay": "Page-turn wait range (seconds)",
        "pagination_note": "Page size and page count are not set by WebLens. Each search begins with the engine's default result page and continues only through the engine-provided Next link. The same wait range is used between pages, date slices, and transient page-load retries.",
        "languages": "Result languages",
        "countries": "Country/region restrictions",
        "clear_selection": "Clear selection",
        "output_file": "Collected-link save location",
        "output_format": "Result file format",
        "content_folder": "Content folder",
        "content_threads": "Content download threads",
        "content_fetch_mode": "Content fetch mode",
        "content_delay": "Content request delay range (ms)",
        "content_wait": "Content receive/render wait (ms)",
        "content_cleaning": "Content cleaning scheme",
        "content_note": "Search-result collection is browser-only. The Requests options below apply only to downloading already collected destination webpages, not to Google/Baidu result-page collection.",
        "open_link": "Open link",
        "delete_selected": "Delete selected",
        "sort_time": "Sort by time",
        "sort_title": "Sort by title",
        "sort_source": "Sort by source",
        "restore_original_order": "Original order",
        "header_sort_hint": "Click a column header to sort; click the same header again to reverse the order.",
        "sample": "Sample",
        "sample_scheme": "Scheme",
        "sample_count": "N",
        "sample_simple": "Simple random",
        "sample_systematic": "Systematic",
        "sample_source": "By source (N per source)",
        "download_selected": "Download selected content",
        "download_all": "Download all content",
        "download_settings": "Download settings",
        "stop_download": "Stop download",
        "stopping_download": "Stopping download…",
        "download_stopped": "Download stopped.",
        "ready": "Ready.",
        "running": "Collecting…",
        "stopped": "Stopped.",
        "done": "Collection finished.",
        "exported": "Exported.",
        "no_records": "There are no result records.",
        "invalid_query": "Please enter search terms or a raw query.",
        "invalid_date": "Start date cannot be later than end date.",
        "invalid_number": "Please check the numeric settings.",
        "invalid_output": "Please choose an output file.",
        "verification_title": "Human verification required",
        "verification_message": "The collection browser is showing a human-verification page. WebLens has paused and will not refresh, paginate, restart the browser, or open another page while verification remains active. Complete the verification manually in the browser. You may then close this message. WebLens resumes automatically only after it detects that the real search-result page has finished rendering; simply returning to the search URL is not treated as completion.",
        "browser_start_error": "The collection browser could not be started.",
        "network_error": "Collection stopped because the browser could not load the result page.",
        "import_done": "Imported {n} new link(s).",
        "download_template": "Download import template",
        "template_saved": "Import template saved to:\n{path}",
        "browser_required": "Browser environment is not ready. Configure Chrome/Edge and a matching WebDriver before starting collection.",
        "configure_browser": "Configure browser && Selenium",
        "one_click_setup_short": "One-click setup Chrome && Edge",
        "advanced_browser_settings": "Browser && Selenium settings…",
        "browser_recommendation": "For Chrome, WebLens recommends its isolated Chrome for Testing copy under tools/browser. If it is missing, WebLens can download and configure the official archive automatically. Using a system-installed Chrome remains an explicit not-recommended option.",
        "browser_recommendation_edge": "For Microsoft Edge, WebLens uses the system-installed browser by default and manages a matching EdgeDriver. If Edge is not present, install Microsoft Edge from the official page, then return here and click Detect system Edge.",
        "download_recommended_browser": "Download/configure portable browser",
        "portable_browser_resolving": "Resolving the recommended portable browser…",
        "portable_browser_downloading": "Downloading the portable browser…",
        "portable_browser_extracting": "Extracting the portable browser into WebLens tools…",
        "portable_browser_detecting": "Detecting the extracted browser…",
        "portable_browser_ready": "Portable browser configured: {version}",
        "portable_browser_failed": "Portable browser configuration failed: {message}",
        "download_recommended_driver": "Download matching WebDriver",
        "export_done": "Exported {n} record(s) to:\n{path}",
        "confirm_reset_settings": "Reset browser/Selenium settings and both search-engine panels to the shipped defaults?",
        "content_retry": "Retry failed content N times",
        "content_task_timeout": "Single content task timeout (seconds)",
        "content_resume": "Resume: skip URLs already downloaded successfully",
        "content_domain_timeout": "Same-domain lock timeout (seconds)",
        "ok": "OK",
        "cancel": "Cancel",
        "close": "Close",
        "records_count": "{n} records; {s} selected",
    },
    "zh_sim": {
        "google": "Google",
        "baidu": "百度",
        "search_engine": "搜索引擎",
        "file": "文件",
        "edit": "编辑",
        "settings": "设置",
        "help": "帮助",
        "language": "界面语言",
        "browser_settings": "浏览器与 Selenium…",
        "browser_settings_title": "浏览器与 Selenium",
        "browser_detected": "已检测到的浏览器",
        "browser_driver": "WebDriver",
        "browser_type": "浏览器",
        "browser_source": "浏览器来源",
        "browser_source_portable": "WebLens 内置便携版 Chrome（推荐）",
        "browser_source_system": "使用系统已安装 Chrome（不推荐）",
        "browser_source_system_note": "对于 Chrome，系统已安装浏览器仅作为用户主动选择的备用方案，不推荐用于 WebLens 采集，因为 Chrome 可能独立自动升级。Microsoft Edge 采用不同策略：由于微软没有提供与 Chrome for Testing 对等的官方便携版 Edge ZIP，Edge 默认使用系统已安装版本。",
        "browser_source_portable_note": "Chrome 推荐使用 WebLens tools/browser 中的 Chrome for Testing，与用户日常 Chrome 相互独立。若不存在，一键配置会自动下载官方压缩包并解压到 WebLens 内部。",
        "browser_source_edge_system": "使用系统已安装 Microsoft Edge（推荐）",
        "browser_source_edge_system_note": "Edge 推荐直接使用系统已安装的 Microsoft Edge，WebLens 只负责检测并准备与其版本匹配的 EdgeDriver。微软目前没有提供与 Chrome for Testing 对等的官方便携版 Edge ZIP。",
        "detect_system_edge": "检测系统 Edge",
        "edge_system_ready": "已检测到系统 Microsoft Edge。开始采集前，WebLens 会继续核对或准备匹配的 EdgeDriver。",
        "sort_by": "排序",
        "sort_none": "原始顺序",
        "start": "开始采集",
        "stop": "停止",
        "export": "导出",
        "import": "导入链接",
        "paste_links": "粘贴文本解析链接…",
        "paste_links_title": "粘贴文本解析链接",
        "paste_links_help": "可直接粘贴或输入包含一个或多个 HTTP/HTTPS 链接的任意文本。WebLens 会自动解析链接，并把新链接追加到当前结果预览末尾；可以反复添加，不会覆盖已有结果。",
        "paste_links_add": "解析并加入结果",
        "paste_links_clear": "清空文本",
        "paste_links_none": "粘贴的文本中没有检测到 HTTP/HTTPS 链接。",
        "paste_links_result": "检测到 {found} 条链接；新增 {added} 条；跳过重复 {skipped} 条。",
        "manual_collection": "手动采集…",
        "manual_collection_title": "手动采集搜索结果",
        "manual_intro": "根据当前 Google/百度检索参数生成搜索引擎链接。请将链接复制到日常浏览器中打开，手动翻页，并把每个搜索结果页保存为 HTML 文件；随后在这里批量导入这些 HTML，WebLens 会解析其中的真实结果链接并追加到当前“结果预览”。该模式不依赖 Selenium 或 WebDriver。",
        "manual_urls_group": "1. 生成检索链接",
        "manual_urls_note": "每一项都是一个初始检索链接。百度会把多个检索词与多行站点/域名分别展开为“检索词 × 域名”任务；启用日期切片后再叠加日期任务。翻页完全由用户在浏览器中手动完成，只需使用搜索引擎自己的“下一页”。",
        "manual_copy_selected": "复制所选链接",
        "manual_copy_all": "复制全部链接",
        "manual_copied": "已复制 {n} 个检索链接到剪贴板。",
        "manual_html_group": "2. 导入保存的结果页",
        "manual_html_note": "请使用浏览器“网页另存为”保存每一页搜索结果（仅 HTML 即可）。可一次选择多个 .html/.htm 文件，也可以多次导入文件夹；解析出的新链接会追加到现有结果预览，不覆盖已有记录。",
        "manual_import_html": "导入 HTML 文件…",
        "manual_import_folder": "导入 HTML 文件夹…",
        "manual_parsing": "正在解析保存的搜索结果页……",
        "manual_parse_summary": "已解析 {files} 个文件：发现 {records} 条结果记录；新增 {added} 条唯一链接；跳过重复 {skipped} 条；{warnings} 个文件存在提示。",
        "manual_no_tasks": "无法生成检索链接，请检查当前检索参数。",
        "manual_no_html": "未找到 .html 或 .htm 文件。",
        "manual_wrong_engine": "部分保存页面属于另一搜索引擎，已跳过。请切换到对应的 Google/百度面板后再导入。",
        "clear": "清空",
        "open_output": "打开输出文件",
        "open_download": "打开下载文件夹",
        "exit": "退出",
        "undo": "撤销结果编辑",
        "redo": "重做结果编辑",
        "reset_results": "重置结果预览",
        "reset_settings": "重置默认设置",
        "clear_web_components": "清除 WebLens Web 组件…",
        "confirm_clear_web_components": "是否删除 WebLens 管理的便携浏览器、WebDriver 及其专用缓存？系统安装的 Chrome/Edge 和用户语料输出文件不会被删除。",
        "clear_web_components_done": "WebLens 管理的 Web 组件已清除，浏览器/Driver 路径已重置；再次自动采集前请重新配置。",
        "clear_web_components_warning": "Web 组件已清除，但存在以下提示：\n{message}",
        "user_guide": "使用说明",
        "parameter_guide": "参数说明",
        "about": "关于",
        "query_settings": "检索设置",
        "crawl_settings": "采集设置",
        "limit_settings": "语种与国家/地区限定",
        "output_settings": "采集链接保存",
        "result_preview": "结果预览",
        "log": "日志",
        "query_mode": "检索模式",
        "search_vertical": "检索类型",
        "baidu_sort": "百度排序",
        "query_terms": "检索词 / 短语",
        "site_filters": "站点/域名限定\n（每行一个）",
        "site_filters_baidu": "站点/域名限定\n（每行一个，逐项检索）",
        "safe": "安全搜索",
        "disable_filter": "关闭 Google 相似结果过滤",
        "collection_browser": "采集浏览器",
        "driver_path": "浏览器驱动路径",
        "browser_binary": "浏览器安装版本",
        "browser_refresh": "自动检测",
        "driver_manage": "检测 / 更新驱动",
        "one_click_setup": "一键配置 Chrome 与 Edge",
        "update_portable_environment": "更新当前内置便携版浏览器与 WebDriver",
        "portable_update_running": "正在更新 WebLens 内置便携版浏览器与 WebDriver……",
        "portable_update_done": "内置环境已更新：浏览器 {browser}；WebDriver {driver}。",
        "portable_update_edge_partial": "已为内置 Edge {browser} 更新 EdgeDriver。微软目前没有提供官方便携版 Edge ZIP，因此 WebLens 无法自动替换内置 Edge 浏览器。当前 Microsoft Edge Stable：{latest}。",
        "portable_update_failed": "内置环境更新失败：{message}",
        "portable_update_system_disabled": "请先将“浏览器来源”切换为“WebLens 内置便携版浏览器（推荐）”，再更新 WebLens 管理的环境。",
        "download_browser_now": "下载/配置浏览器",
        "setup_all_start": "正在配置 Chrome 与 Edge 浏览器环境……",
        "setup_all_done": "一键配置完成。",
        "setup_all_partial": "一键配置未全部完成。可使用下方独立控件继续手动配置。",
        "manual_browser_invalid": "所选程序不是有效的 {browser} 浏览器，或无法读取其版本。",
        "manual_driver_invalid": "所选 WebDriver 版本（{driver}）与浏览器版本（{browser}）不匹配。",
        "manual_driver_unknown": "无法从所选文件读取 WebDriver 版本。",
        "edge_portable_unavailable": "tools/browser 中未检测到 WebLens 便携版 Edge。微软目前没有提供与 Chrome for Testing 对等的官方便携版 Edge ZIP。为避免影响用户日常浏览器，建议将便携版 Edge 放入 tools/browser；也可以明确选择“使用系统已安装浏览器（不推荐）”。",
        "browser_version_unreadable": "已找到浏览器程序，但无法读取其版本号。",
        "driver_prepare_failed_generic": "无法准备与浏览器版本匹配的 WebDriver。",
        "driver_auto": "自动管理浏览器驱动",
        "driver_ready": "驱动已匹配：{version}",
        "driver_missing": "尚未准备好匹配的浏览器驱动。",
        "driver_downloading": "正在检测浏览器和驱动……",
        "driver_downloaded": "匹配的浏览器驱动已准备完成：\n{path}",
        "driver_failed": "自动准备浏览器驱动失败。\n\n{message}\n\n可以使用下面的按钮打开浏览器或 WebDriver 官方下载页面。",
        "browser_not_found": "当前所选浏览器来源中未检测到可用的 {browser}。",
        "open_driver_page": "打开 WebDriver 官网",
        "open_browser_page": "打开浏览器官网",
        "browse": "浏览…",
        "browser_wait": "页面渲染等待（毫秒）",
        "hide_browser": "不显示采集浏览器界面",
        "date_filter_enabled": "限定爬取日期",
        "start_date": "开始日期",
        "end_date": "结束日期",
        "day_step": "日期切片步长（天；0=不切片）",
        "timeout": "页面加载超时（秒）",
        "page_delay": "翻页等待范围（秒）",
        "pagination_note": "WebLens 不设置每页结果数，也不设置最大页数。每次检索从搜索引擎默认结果页开始，只跟随搜索引擎页面自身提供的“下一页”继续采集。翻页、日期切片之间以及临时页面加载错误后的等待统一使用这一等待范围。",
        "languages": "结果语种",
        "countries": "国家/地区限定",
        "clear_selection": "清除选择",
        "output_file": "爬取链接保存位置",
        "output_format": "结果文件格式",
        "content_folder": "正文下载文件夹",
        "content_threads": "正文下载线程数",
        "content_fetch_mode": "正文下载模式",
        "content_delay": "正文请求等待范围（毫秒）",
        "content_wait": "正文接收/渲染等待（毫秒）",
        "content_cleaning": "正文清洗方案",
        "content_note": "Google/百度搜索结果采集已经全面改为浏览器模式。下面正文下载中的 Requests 选项只用于已经获得链接后的目标网页下载，不参与搜索引擎结果页采集。",
        "open_link": "打开链接",
        "delete_selected": "删除所选",
        "sort_time": "按时间排序",
        "sort_title": "按标题排序",
        "sort_source": "按来源排序",
        "restore_original_order": "原始顺序",
        "header_sort_hint": "点击任一列表头即可排序；再次点击同一表头可在正序和逆序之间切换。",
        "sample": "抽样",
        "sample_scheme": "方案",
        "sample_count": "数量",
        "sample_simple": "简单随机",
        "sample_systematic": "系统抽样",
        "sample_source": "按来源分层（每来源 N 条）",
        "download_selected": "下载所选正文",
        "download_all": "下载全部正文",
        "download_settings": "下载设置",
        "stop_download": "停止下载",
        "stopping_download": "正在停止下载……",
        "download_stopped": "下载已停止。",
        "ready": "就绪。",
        "running": "正在采集……",
        "stopped": "已停止。",
        "done": "采集完成。",
        "exported": "已导出。",
        "no_records": "当前没有结果记录。",
        "invalid_query": "请输入检索词或原始检索式。",
        "invalid_date": "开始日期不能晚于结束日期。",
        "invalid_number": "请检查数值参数。",
        "invalid_output": "请选择输出文件。",
        "verification_title": "需要人工验证",
        "verification_message": "采集浏览器出现了人工验证页面。WebLens 已暂停，不会在验证期间刷新页面、翻页、重启浏览器或打开其他页面。请直接在浏览器中完成人工验证，完成后可以关闭本提示。WebLens 只有在检测到真实搜索结果页已经完成渲染后才会自动恢复；仅仅回到搜索页面 URL 不会被判定为验证完成。",
        "browser_start_error": "无法启动采集浏览器。",
        "network_error": "浏览器无法加载搜索结果页，采集已停止。",
        "import_done": "已导入 {n} 条新链接。",
        "download_template": "下载导入模板",
        "template_saved": "导入模板已保存：\n{path}",
        "browser_required": "自动采集所需的浏览器环境尚未准备好。请配置 Chrome/Edge 和匹配的 WebDriver 后再使用自动采集；手动采集无需 Selenium，仍可直接使用。",
        "configure_browser": "配置浏览器与 Selenium",
        "one_click_setup_short": "一键配置 Chrome 与 Edge",
        "advanced_browser_settings": "浏览器与 Selenium 设置…",
        "browser_recommendation": "对于 Chrome，WebLens 推荐使用 tools/browser 中与用户日常浏览器隔离的 Chrome for Testing。若不存在，可自动下载官方压缩包并完成配置；系统已安装 Chrome 仅作为用户主动选择的不推荐备用方案。",
        "browser_recommendation_edge": "对于 Microsoft Edge，WebLens 默认使用系统已安装的 Edge，并自动管理匹配的 EdgeDriver。若系统没有 Edge，请先从微软官方页面安装，随后返回本窗口点击“检测系统 Edge”。",
        "download_recommended_browser": "下载/配置便携版浏览器",
        "portable_browser_resolving": "正在解析推荐的便携版浏览器……",
        "portable_browser_downloading": "正在下载便携版浏览器……",
        "portable_browser_extracting": "正在解压便携版浏览器到 WebLens tools……",
        "portable_browser_detecting": "正在检测已解压的浏览器……",
        "portable_browser_ready": "便携版浏览器已配置：{version}",
        "portable_browser_failed": "便携版浏览器配置失败：{message}",
        "download_recommended_driver": "下载匹配的 WebDriver",
        "export_done": "已导出 {n} 条记录：\n{path}",
        "confirm_reset_settings": "是否将浏览器/Selenium 设置以及 Google、百度两个面板全部恢复为软件默认设置？",
        "content_retry": "正文失败重试次数",
        "content_task_timeout": "单个正文任务超时（秒）",
        "content_resume": "断点续传：跳过已成功下载的 URL",
        "content_domain_timeout": "同域名锁超时（秒）",
        "ok": "确定",
        "cancel": "取消",
        "close": "关闭",
        "records_count": "共 {n} 条；已选 {s} 条",
    },
    "zh_tra": {},
}
# Traditional Chinese defaults to the Simplified wording for any string not
# explicitly overridden, while option lists still retain their native labels.
UI_TEXTS["zh_tra"] = dict(UI_TEXTS["zh_sim"], **{
    "settings": "設定", "help": "幫助", "language": "介面語言", "search_engine": "搜尋引擎", "start": "開始採集",
    "stop": "停止", "export": "匯出", "import": "匯入連結", "paste_links": "貼上文字解析連結…", "paste_links_title": "貼上文字解析連結",
    "paste_links_help": "可直接貼上或輸入包含一個或多個 HTTP/HTTPS 連結的任意文字。WebLens 會自動解析連結，並把新連結追加到目前結果預覽末尾；可以反覆加入，不會覆蓋已有結果。",
    "paste_links_add": "解析並加入結果", "paste_links_clear": "清空文字", "paste_links_none": "貼上的文字中沒有偵測到 HTTP/HTTPS 連結。",
    "paste_links_result": "偵測到 {found} 條連結；新增 {added} 條；跳過重複 {skipped} 條。",
    "manual_collection": "手動採集…", "manual_collection_title": "手動採集搜尋結果",
    "manual_intro": "根據目前 Google/百度檢索參數產生搜尋引擎連結。請將連結複製到日常瀏覽器中開啟，手動翻頁，並把每個搜尋結果頁儲存為 HTML 檔；隨後在這裡批次匯入，WebLens 會解析真實結果連結並追加到目前結果預覽。此模式不依賴 Selenium 或 WebDriver。",
    "manual_urls_group": "1. 產生檢索連結", "manual_urls_note": "每一項都是初始檢索連結。百度會把多個檢索詞與多行站點/域名分別展開為「檢索詞 × 域名」任務；日期切片會再增加一個任務維度。翻頁由使用者在瀏覽器中手動完成。",
    "manual_copy_selected": "複製所選連結", "manual_copy_all": "複製全部連結", "manual_copied": "已複製 {n} 個檢索連結到剪貼簿。",
    "manual_html_group": "2. 匯入儲存的結果頁", "manual_html_note": "請使用瀏覽器「網頁另存為」儲存每一頁搜尋結果（僅 HTML 即可）。可一次選擇多個 .html/.htm 檔，也可多次匯入資料夾；新連結會追加到既有結果。",
    "manual_import_html": "匯入 HTML 檔…", "manual_import_folder": "匯入 HTML 資料夾…", "manual_parsing": "正在解析儲存的搜尋結果頁……",
    "manual_parse_summary": "已解析 {files} 個檔案：發現 {records} 條結果；新增 {added} 條唯一連結；跳過重複 {skipped} 條；{warnings} 個檔案有提示。",
    "manual_no_tasks": "無法產生檢索連結，請檢查目前參數。", "manual_no_html": "未找到 .html 或 .htm 檔。",
    "manual_wrong_engine": "部分頁面屬於另一搜尋引擎，已跳過。請切換到對應 Google/百度面板後再匯入。",
    "one_click_setup": "一鍵配置 Chrome 與 Edge", "update_portable_environment": "更新當前內置便攜版瀏覽器與 WebDriver",
    "portable_update_running": "正在更新 WebLens 內置便攜版瀏覽器與 WebDriver……",
    "portable_update_done": "內置環境已更新：瀏覽器 {browser}；WebDriver {driver}。",
    "portable_update_edge_partial": "已為內置 Edge {browser} 更新 EdgeDriver。微軟目前沒有提供官方便攜版 Edge ZIP，因此 WebLens 無法自動替換內置 Edge 瀏覽器。當前 Microsoft Edge Stable：{latest}。",
    "portable_update_failed": "內置環境更新失敗：{message}",
    "portable_update_system_disabled": "請先將「瀏覽器來源」切換為「WebLens 內置便攜版瀏覽器（推薦）」，再更新 WebLens 管理的環境。",
    "download_browser_now": "下載/配置瀏覽器",
    "browser_source": "瀏覽器來源", "browser_source_portable": "WebLens 內置便攜版 Chrome（推薦）", "browser_source_system": "使用系統已安裝 Chrome（不推薦）",
    "browser_source_edge_system": "使用系統已安裝 Microsoft Edge（推薦）",
    "browser_source_edge_system_note": "Edge 推薦直接使用系統已安裝的 Microsoft Edge，WebLens 只負責偵測並準備版本匹配的 EdgeDriver。微軟目前沒有提供與 Chrome for Testing 對等的官方便攜版 Edge ZIP。",
    "detect_system_edge": "偵測系統 Edge", "edge_system_ready": "已偵測到系統 Microsoft Edge。開始採集前，WebLens 會繼續核對或準備匹配的 EdgeDriver。",
    "setup_all_start": "正在配置 Chrome 與 Edge 瀏覽器環境……", "setup_all_done": "一鍵配置完成。",
    "setup_all_partial": "一鍵配置未全部完成。可使用下方獨立控制項繼續手動配置。",
    "one_click_setup_short": "一鍵配置 Chrome 與 Edge", "advanced_browser_settings": "瀏覽器與 Selenium 設定…",
    "restore_original_order": "原始順序", "header_sort_hint": "點擊任一列表頭即可排序；再次點擊同一表頭可在正序和逆序之間切換。",
    "manual_browser_invalid": "所選程式不是有效的 {browser} 瀏覽器，或無法讀取其版本。",
    "manual_driver_invalid": "所選 WebDriver 版本（{driver}）與瀏覽器版本（{browser}）不匹配。",
    "manual_driver_unknown": "無法從所選檔案讀取 WebDriver 版本。",
    "edge_portable_unavailable": "tools/browser 中未偵測到 WebLens 便攜版 Edge。微軟目前沒有提供與 Chrome for Testing 對等的官方便攜版 Edge ZIP；建議放入便攜版 Edge，或明確選擇「使用系統已安裝瀏覽器（不推薦）」。",
    "browser_version_unreadable": "已找到瀏覽器程式，但無法讀取其版本號。", "driver_prepare_failed_generic": "無法準備與瀏覽器版本匹配的 WebDriver。", "clear": "清空",
    "browser_recommendation_edge": "Microsoft Edge 預設使用系統已安裝版本，WebLens 自動管理匹配的 EdgeDriver。若系統沒有 Edge，請先從微軟官方頁面安裝，再回到本視窗偵測。",
    "query_settings": "檢索設定", "crawl_settings": "採集設定", "output_settings": "輸出",
    "site_filters_baidu": "站點/域名限定\n（每行一個，逐項檢索）",
    "browser_settings": "瀏覽器與 Selenium…", "browser_settings_title": "瀏覽器與 Selenium", "browser_detected": "已偵測到的瀏覽器", "browser_driver": "WebDriver", "browser_type": "瀏覽器", "sort_by": "排序", "sort_none": "原始順序",
    "result_preview": "結果預覽", "log": "日誌", "hide_browser": "不顯示採集瀏覽器介面",
    "page_delay": "翻頁等待範圍（秒）", "stop_download": "停止下載", "stopping_download": "正在停止下載……", "download_stopped": "下載已停止。", "ready": "就緒。", "running": "正在採集……",
    "done": "採集完成。", "stopped": "已停止。", "close": "關閉",
    "clear_web_components": "清除 WebLens Web 元件…",
    "confirm_clear_web_components": "是否刪除 WebLens 管理的便攜瀏覽器、WebDriver 及其專用快取？系統安裝的 Chrome/Edge 和使用者語料輸出檔不會被刪除。",
    "clear_web_components_done": "WebLens 管理的 Web 元件已清除，瀏覽器/Driver 路徑已重設；再次自動採集前請重新配置。",
})


def tr(lang: str, key: str, **kwargs) -> str:
    text = UI_TEXTS.get(lang, UI_TEXTS["en"]).get(key, UI_TEXTS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def app_base_dir() -> Path:
    """Return the writable WebLens data root for this platform."""
    return user_data_root()


def default_output_path(engine: str) -> str:
    name = "weblens_google_results.xlsx" if engine == "google" else "weblens_baidu_results.xlsx"
    return str(app_base_dir() / "output" / name)


def default_browser_source_for_backend(backend: str) -> str:
    """Recommended browser source for each Selenium backend.

    Chrome is isolated inside WebLens through Chrome for Testing. Microsoft
    Edge has no equivalent official portable ZIP, so Edge uses the
    system-installed browser by default.
    """
    return "system" if str(backend or "").strip().lower() == "selenium_edge" else "portable"


def browser_defaults() -> dict[str, Any]:
    # Browser and driver paths are resolved against the current machine when
    # settings are loaded. Never bake one computer's installation path into
    # the application defaults.
    return {
        "fetch_backend": "selenium_chrome",
        "browser_source": "portable",
        "browser_source_chrome": "portable",
        "browser_source_edge": "system",
        "browser_binary_path": "",
        "browser_driver_path": "",
        "browser_wait_ms": 5000,
        "browser_headless": False,
    }

def panel_defaults(engine: str) -> dict[str, Any]:
    today = date.today().isoformat()
    vertical = "baidu_news_media" if engine == "baidu" else "news"
    return {
        "query_mode": "single",
        "search_vertical": vertical,
        "baidu_sort": "focus",
        "query_terms": "",
        "site_filters": "",
        "safe": "",
        "disable_filter": False,
        "date_filter_enabled": False,
        "start_date": today,
        "end_date": today,
        "day_step": 0,
        "timeout": 20,
        "page_delay_min_ms": 30000,
        "page_delay_max_ms": 90000,
        "languages_lr": [],
        "countries_cr": [],
        "output_path": default_output_path(engine),
        "output_format": "xlsx",
        "content_download_dir": str(app_base_dir() / "content_downloads"),
        "content_threads": 3,
        "content_fetch_mode": "mixed",
        "content_delay_min_ms": 0,
        "content_delay_max_ms": 0,
        "content_receive_wait_ms": 5000,
        "content_cleaning_scheme": "auto",
        "content_retry_count": 1,
        "content_task_timeout_seconds": 300,
        "content_resume_enabled": True,
        "content_domain_lock_timeout_seconds": 300,
        "sample_scheme": "simple",
        "sample_count": 20,
        "user_agent": DEFAULT_USER_AGENT,
    }


def vertical_options_for_engine(engine: str) -> list[dict]:
    wanted = {"baidu_web", "baidu_news", "baidu_news_media"} if engine == "baidu" else {"news", "web"}
    return [o for o in VERTICAL_OPTIONS if o.get("key") in wanted]


def query_mode_options_for_engine(engine: str) -> list[dict]:
    if engine == "baidu":
        options: list[dict] = []
        for option in QUERY_MODE_OPTIONS:
            key = option.get("key")
            if key == "phrase_any":
                continue
            if key == "any":
                options.append({
                    "key": "any",
                    "labels": {
                        "en": "Multiple terms (search one by one)",
                        "zh_sim": "多个检索词（逐条检索）",
                        "zh_tra": "多個檢索詞（逐條檢索）",
                    },
                })
            else:
                options.append(option)
        return options
    return list(QUERY_MODE_OPTIONS)


def set_combo_options(combo: QComboBox, options: list[dict], lang: str, selected_key: str) -> None:
    combo.blockSignals(True)
    combo.clear()
    chosen = -1
    for i, opt in enumerate(options):
        combo.addItem(label_for(opt, lang), opt.get("key"))
        if opt.get("key") == selected_key:
            chosen = i
    if chosen < 0 and combo.count():
        chosen = 0
    if chosen >= 0:
        combo.setCurrentIndex(chosen)
    combo.blockSignals(False)


def combo_key(combo: QComboBox, default: str = "") -> str:
    value = combo.currentData(Qt.ItemDataRole.UserRole)
    return str(value if value is not None else default)


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def tinted_standard_icon(widget: QWidget, pixmap: QStyle.StandardPixmap, color: str = "#C96F32") -> QIcon:
    """Return a compact cross-platform Qt icon tinted to the WebLens accent."""
    source = widget.style().standardIcon(pixmap).pixmap(22, 22)
    if source.isNull():
        return widget.style().standardIcon(pixmap)
    tinted = QPixmap(source.size())
    tinted.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()
    return QIcon(tinted)


def fit_dialog_to_screen(dialog: QDialog, preferred_width: int, preferred_height: int | None = None) -> None:
    """Keep dialogs readable at high DPI without forcing them beyond the usable screen."""
    screen = dialog.screen() or QApplication.primaryScreen()
    available = screen.availableGeometry() if screen is not None else None
    if available is None:
        width = preferred_width
        height = preferred_height or dialog.sizeHint().height()
    else:
        width = min(preferred_width, max(480, int(available.width() * 0.92)))
        natural_h = preferred_height or dialog.sizeHint().height()
        height = min(natural_h, max(260, int(available.height() * 0.90)))
    dialog.resize(width, height)


def exec_action_dialog(
    parent: QWidget,
    title: str,
    message: str,
    actions: list[tuple[str, str]],
    *,
    close_text: str,
    warning: bool = False,
) -> str | None:
    """Responsive alternative to QMessageBox for long action labels.

    QMessageBox forces all custom buttons into one horizontal row, which clips
    labels on high-DPI or narrow logical desktops. This dialog uses a two-column
    action grid and gives each button the width it needs.
    """
    dialog = QDialog(parent)
    apply_window_icon(dialog)
    dialog.setWindowTitle(title)
    root = QVBoxLayout(dialog)
    root.setContentsMargins(18, 16, 18, 16)
    root.setSpacing(12)

    body = QHBoxLayout()
    body.setSpacing(14)
    icon_label = QLabel()
    pix = QStyle.StandardPixmap.SP_MessageBoxWarning if warning else QStyle.StandardPixmap.SP_MessageBoxInformation
    icon_label.setPixmap(dialog.style().standardIcon(pix).pixmap(44, 44))
    icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
    icon_label.setFixedWidth(54)
    body.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
    text_label = QLabel(message)
    text_label.setWordWrap(True)
    text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    body.addWidget(text_label, 1)
    root.addLayout(body)

    selected: dict[str, str | None] = {"key": None}
    action_grid = QGridLayout()
    action_grid.setHorizontalSpacing(8)
    action_grid.setVerticalSpacing(8)

    def choose(key: str) -> None:
        selected["key"] = key
        dialog.accept()

    for i, (key, label) in enumerate(actions):
        button = QPushButton(label)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setMinimumHeight(32)
        button.clicked.connect(lambda _checked=False, k=key: choose(k))
        action_grid.addWidget(button, i // 2, i % 2)
    close_button = QPushButton(close_text)
    close_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    close_button.setMinimumHeight(32)
    close_button.clicked.connect(dialog.reject)
    close_index = len(actions)
    action_grid.addWidget(close_button, close_index // 2, close_index % 2)
    action_grid.setColumnStretch(0, 1)
    action_grid.setColumnStretch(1, 1)
    root.addLayout(action_grid)

    dialog.adjustSize()
    fit_dialog_to_screen(dialog, 720, dialog.sizeHint().height())
    dialog.exec()
    return selected["key"]


class PanelSignals(QObject):
    crawl_event = Signal(object)
    crawl_error = Signal(str, str)
    crawl_finished = Signal()
    content_result = Signal(object, object)
    content_progress = Signal(int, int)
    content_error = Signal(str)
    content_finished = Signal(int, int, str)


class RecordTableModel(QAbstractTableModel):
    columns = ("link", "time", "title", "source", "published", "status", "words", "quality")

    def __init__(self, panel: "CollectorPanel") -> None:
        super().__init__(panel)
        self.panel = panel

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.panel.records)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.panel.records):
            return None
        rec = self.panel.records[index.row()]
        col = self.columns[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if col == "time":
                return str(getattr(rec, "collected_at", ""))
            if col == "title":
                return str(getattr(rec, "title", ""))
            if col == "source":
                return str(getattr(rec, "source", ""))
            if col == "published":
                return format_published_date(getattr(rec, "published_time", ""), getattr(rec, "collected_at", ""))
            if col == "status":
                return str(getattr(rec, "content_status", ""))
            if col == "words":
                value = getattr(rec, "content_word_count", "")
                return str(value) if value not in (None, "") else ""
            if col == "quality":
                value = getattr(rec, "content_quality_score", "")
                if value in (None, ""):
                    return ""
                try:
                    return f"{float(value):.0f}"
                except Exception:
                    return str(value)
            if col == "link":
                return str(getattr(rec, "link", ""))
        if role == Qt.ItemDataRole.ToolTipRole and col in {"title", "link", "published"}:
            if col == "published":
                raw = str(getattr(rec, "published_time", "") or "")
                shown = format_published_date(raw, getattr(rec, "collected_at", ""))
                return raw if not shown or shown == raw else f"{shown}  |  {raw}"
            return str(getattr(rec, "title" if col == "title" else "link", ""))
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        lang = self.panel.lang
        labels = {
            "en": ["Link", "Collected", "Title", "Source", "Published", "Content", "Words", "Quality"],
            "zh_sim": ["链接", "采集时间", "标题", "来源", "发布时间", "正文状态", "词数", "质量"],
            "zh_tra": ["連結", "採集時間", "標題", "來源", "發布時間", "正文狀態", "詞數", "品質"],
        }
        return labels.get(lang, labels["en"])[section]

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()


class CollectorPanel(QWidget):
    def __init__(self, window: "BFSUWebLensWindow", engine: str, settings: dict[str, Any]) -> None:
        super().__init__(window)
        self.window = window
        self.engine = engine
        self.records: list[Any] = []
        self.original_records: list[Any] = []
        self.undo_stack: list[list[Any]] = []
        self.redo_stack: list[list[Any]] = []
        self._header_sort_column: int | None = None
        self._header_sort_order = Qt.SortOrder.AscendingOrder
        self.worker: threading.Thread | None = None
        self.content_worker: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.content_stop_event = threading.Event()
        self.signals = PanelSignals()
        self.signals.crawl_event.connect(self._handle_crawl_event)
        self.signals.crawl_error.connect(self._handle_crawl_error)
        self.signals.crawl_finished.connect(self._on_crawl_finished)
        self.signals.content_result.connect(self._handle_content_result)
        self.signals.content_progress.connect(self._handle_content_progress)
        self.signals.content_error.connect(self._handle_content_error)
        self.signals.content_finished.connect(self._handle_content_finished)
        self._verification_dialog_shown = False
        self._crawl_terminal_kind = ""
        self._crawl_terminal_message = ""
        self._content_terminal_error = ""
        self._last_result_autosave_signature: tuple[Any, ...] | None = None
        self._settings = dict(panel_defaults(engine), **(settings or {}))
        self._build_ui()
        self.apply_settings(self._settings)
        self.retranslate_ui()

    @property
    def lang(self) -> str:
        return self.window.language

    def _configure_form(self, form: QFormLayout) -> None:
        """Use a DPI-safe form layout that wraps long labels when necessary."""
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

    @staticmethod
    def _prepare_form_label(label: QLabel) -> QLabel:
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        return label

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 9, 10, 10)
        root.setSpacing(8)

        # Task status and progress live exclusively in the main-window status
        # bar so the collector workspace remains available to search controls.
        self.status_label = self.window.task_status_label
        self.progress = self.window.task_progress

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(7)
        root.addWidget(self.main_splitter, 1)

        # Left settings panel -------------------------------------------------
        # Keep a real minimum width and use vertical scrolling rather than
        # compressing form controls when Windows display scaling is 125–200%.
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll.setMinimumWidth(450)
        self.left_scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_container = QWidget()
        left_container.setObjectName("leftSettingsContainer")
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.left_layout = QVBoxLayout(left_container)
        self.left_layout.setContentsMargins(4, 3, 9, 6)
        self.left_layout.setSpacing(10)
        self.left_scroll.setWidget(left_container)
        self.main_splitter.addWidget(self.left_scroll)

        self.query_group = QGroupBox()
        qform = QFormLayout(self.query_group)
        self._configure_form(qform)
        self.query_mode_combo = QComboBox()
        self.vertical_combo = QComboBox()
        self.baidu_sort_combo = QComboBox()
        self.query_text = QPlainTextEdit()
        self.site_text = QPlainTextEdit()
        three_line_height = self.fontMetrics().lineSpacing() * 3 + 18
        for editor in (self.query_text, self.site_text):
            editor.setFixedHeight(three_line_height)
            editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.safe_combo = QComboBox()
        self.safe_combo.addItem("", "")
        self.safe_combo.addItem("off", "off")
        self.safe_combo.addItem("medium", "medium")
        self.safe_combo.addItem("high", "high")
        self.disable_filter_check = QCheckBox()
        self.query_mode_label = self._prepare_form_label(QLabel())
        self.vertical_label = self._prepare_form_label(QLabel())
        self.baidu_sort_label = self._prepare_form_label(QLabel())
        self.query_terms_label = self._prepare_form_label(QLabel())
        self.site_filters_label = self._prepare_form_label(QLabel())
        self.safe_label = self._prepare_form_label(QLabel())
        qform.addRow(self.query_mode_label, self.query_mode_combo)
        qform.addRow(self.vertical_label, self.vertical_combo)
        if self.engine == "baidu":
            qform.addRow(self.baidu_sort_label, self.baidu_sort_combo)
        qform.addRow(self.query_terms_label, self.query_text)
        qform.addRow(self.site_filters_label, self.site_text)
        if self.engine == "google":
            qform.addRow(self.safe_label, self.safe_combo)
            qform.addRow(self.disable_filter_check)
        self.left_layout.addWidget(self.query_group)

        self.crawl_group = QGroupBox()
        cform = QFormLayout(self.crawl_group)
        self._configure_form(cform)
        self.date_filter_check = QCheckBox()
        self.start_date_edit = QDateEdit(); self.start_date_edit.setCalendarPopup(True); self.start_date_edit.setDisplayFormat("yyyy-MM-dd"); self.start_date_edit.setMinimumWidth(150)
        self.end_date_edit = QDateEdit(); self.end_date_edit.setCalendarPopup(True); self.end_date_edit.setDisplayFormat("yyyy-MM-dd"); self.end_date_edit.setMinimumWidth(150)
        for date_edit in (self.start_date_edit, self.end_date_edit):
            try:
                date_edit.calendarWidget().setMinimumSize(420, 300)
            except Exception:
                pass
        self.day_step_spin = QSpinBox(); self.day_step_spin.setRange(0, 3650)
        self.timeout_spin = QSpinBox(); self.timeout_spin.setRange(1, 600)
        self.page_delay_min = QSpinBox(); self.page_delay_min.setRange(0, 9999); self.page_delay_min.setSingleStep(1)
        self.page_delay_max = QSpinBox(); self.page_delay_max.setRange(0, 9999); self.page_delay_max.setSingleStep(1)
        delay_row = QWidget()
        delay_layout = QHBoxLayout(delay_row)
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.setSpacing(6)
        delay_layout.addWidget(self.page_delay_min, 1)
        delay_layout.addWidget(QLabel("–"))
        delay_layout.addWidget(self.page_delay_max, 1)
        self.start_date_label = self._prepare_form_label(QLabel())
        self.end_date_label = self._prepare_form_label(QLabel())
        self.day_step_label = self._prepare_form_label(QLabel())
        self.timeout_label = self._prepare_form_label(QLabel())
        self.page_delay_label = self._prepare_form_label(QLabel())
        cform.addRow(self.date_filter_check)
        cform.addRow(self.start_date_label, self.start_date_edit)
        cform.addRow(self.end_date_label, self.end_date_edit)
        cform.addRow(self.day_step_label, self.day_step_spin)
        cform.addRow(self.timeout_label, self.timeout_spin)
        cform.addRow(self.page_delay_label, delay_row)
        self.left_layout.addWidget(self.crawl_group)
        self.date_filter_check.toggled.connect(self._date_filter_toggled)
        self.start_date_edit.dateChanged.connect(self._start_date_changed)
        self.end_date_edit.dateChanged.connect(self._end_date_changed)

        self.limit_group = QGroupBox()
        lgrid = QGridLayout(self.limit_group)
        lgrid.setHorizontalSpacing(8)
        lgrid.setVerticalSpacing(7)
        self.languages_label = QLabel(); self.languages_label.setWordWrap(True)
        self.countries_label = QLabel(); self.countries_label.setWordWrap(True)
        self.languages_list = QListWidget(); self.languages_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.languages_list.setMinimumHeight(135)
        self.countries_list = QListWidget(); self.countries_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.countries_list.setMinimumHeight(160)
        self.clear_lang_btn = QPushButton(); self.clear_country_btn = QPushButton()
        lgrid.addWidget(self.languages_label, 0, 0)
        lgrid.addWidget(self.languages_list, 1, 0)
        lgrid.addWidget(self.clear_lang_btn, 2, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        lgrid.addWidget(self.countries_label, 3, 0)
        lgrid.addWidget(self.countries_list, 4, 0)
        lgrid.addWidget(self.clear_country_btn, 5, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        self.clear_lang_btn.clicked.connect(self.languages_list.clearSelection)
        self.clear_country_btn.clicked.connect(self.countries_list.clearSelection)
        if self.engine == "google":
            self.left_layout.addWidget(self.limit_group)
        else:
            self.limit_group.hide()

        self.output_group = QGroupBox()
        oform = QFormLayout(self.output_group)
        self._configure_form(oform)
        self.output_edit = QLineEdit()
        self.output_browse = QPushButton()
        out_row = QWidget()
        out_l = QHBoxLayout(out_row)
        out_l.setContentsMargins(0, 0, 0, 0)
        out_l.setSpacing(6)
        out_l.addWidget(self.output_edit, 1)
        out_l.addWidget(self.output_browse)
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(list(OUTPUT_FORMATS))
        self.output_format_combo.currentTextChanged.connect(self._output_format_changed)
        self.output_file_label = self._prepare_form_label(QLabel())
        self.output_format_label = self._prepare_form_label(QLabel())
        oform.addRow(self.output_file_label, out_row)
        oform.addRow(self.output_format_label, self.output_format_combo)
        self.left_layout.addWidget(self.output_group)
        self.left_layout.addStretch(1)
        self.output_browse.clicked.connect(self.browse_output)

        # Right results/log panel --------------------------------------------
        right = QWidget()
        right.setMinimumWidth(0)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(0)
        self.main_splitter.addWidget(right)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([480, 1060])

        self.result_group = QGroupBox()
        result_layout = QVBoxLayout(self.result_group)
        result_layout.setContentsMargins(9, 10, 9, 9)
        result_layout.setSpacing(7)

        # Result controls are split into short semantic rows so high DPI or a
        # narrow right pane never compresses them into unreadable buttons.
        row1 = QHBoxLayout(); row1.setSpacing(6)
        self.open_link_btn = QPushButton()
        self.delete_btn = QPushButton()
        self.restore_order_btn = QPushButton()
        self.count_label = QLabel(); self.count_label.setProperty("muted", True)
        row1.addWidget(self.open_link_btn)
        row1.addWidget(self.delete_btn)
        row1.addWidget(self.restore_order_btn)
        row1.addStretch(1)
        row1.addWidget(self.count_label)
        result_layout.addLayout(row1)

        row2 = QHBoxLayout(); row2.setSpacing(6)
        self.sample_scheme_label = QLabel()
        self.sample_scheme_combo = QComboBox(); self.sample_scheme_combo.setMinimumWidth(220)
        self.sample_count_label = QLabel()
        self.sample_count_spin = QSpinBox(); self.sample_count_spin.setRange(1, 1000000); self.sample_count_spin.setMaximumWidth(110)
        self.sample_btn = QPushButton()
        row2.addWidget(self.sample_scheme_label)
        row2.addWidget(self.sample_scheme_combo)
        row2.addWidget(self.sample_count_label)
        row2.addWidget(self.sample_count_spin)
        row2.addWidget(self.sample_btn)
        row2.addStretch(1)
        result_layout.addLayout(row2)

        row3 = QHBoxLayout(); row3.setSpacing(6)
        self.download_selected_btn = QPushButton()
        self.download_all_btn = QPushButton()
        self.download_settings_btn = QPushButton()
        self.stop_download_btn = QPushButton()
        self.stop_download_btn.setProperty("dangerAction", True)
        row3.addWidget(self.download_settings_btn)
        row3.addWidget(self.download_selected_btn)
        row3.addWidget(self.download_all_btn)
        row3.addWidget(self.stop_download_btn)
        row3.addStretch(1)
        result_layout.addLayout(row3)

        self.table_model = RecordTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setToolTip(tr(self.lang, "header_sort_hint"))
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.table.doubleClicked.connect(lambda _idx: self.open_selected_link())
        self.table.selectionModel().selectionChanged.connect(lambda *_: (self.update_count(), self.sync_download_button_states()))
        widths = [390, 145, 300, 130, 120, 105, 70, 70]
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(False)
        header.sectionClicked.connect(self._header_section_clicked)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(28)
        result_layout.addWidget(self.table, 1)

        self.log_group = QGroupBox()
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setContentsMargins(9, 10, 9, 9)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(5000)
        self.log_text.setMinimumHeight(90)
        log_layout.addWidget(self.log_text)

        self.results_splitter = QSplitter(Qt.Orientation.Vertical)
        self.results_splitter.setChildrenCollapsible(False)
        self.results_splitter.setHandleWidth(7)
        self.results_splitter.addWidget(self.result_group)
        self.results_splitter.addWidget(self.log_group)
        self.results_splitter.setStretchFactor(0, 1)
        self.results_splitter.setStretchFactor(1, 0)
        self.results_splitter.setSizes([650, 170])
        right_layout.addWidget(self.results_splitter, 1)

        self.open_link_btn.clicked.connect(self.open_selected_link)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.restore_order_btn.clicked.connect(self.restore_original_order)
        self.sample_btn.clicked.connect(self.sample_records)
        self.download_selected_btn.clicked.connect(self.download_selected_content)
        self.download_all_btn.clicked.connect(self.download_all_content)
        self.download_settings_btn.clicked.connect(self.open_content_settings)
        self.stop_download_btn.clicked.connect(self.stop_content_download)
        self.sync_download_button_states()

        for action_text_key, handler in (
            ("open_link", self.open_selected_link),
            ("download_selected", self.download_selected_content),
            ("download_all", self.download_all_content),
            ("delete_selected", self.delete_selected),
        ):
            action = QAction(self.table)
            action.setProperty("text_key", action_text_key)
            action.triggered.connect(handler)
            self.table.addAction(action)
        self.context_actions = self.table.actions()

    def set_initial_sidebar_width(self, total_width: int) -> None:
        """Choose a readable initial sidebar width in device-independent px."""
        total_width = max(760, int(total_width or 0))
        preferred = max(450, min(580, int(total_width * 0.35)))
        # Always leave a useful result area.  The result table can scroll
        # horizontally, but the settings controls must remain fully readable.
        if total_width - preferred < 400:
            preferred = max(450, total_width - 400)
        self.main_splitter.setSizes([preferred, max(400, total_width - preferred)])

    def retranslate_ui(self) -> None:
        lang = self.lang
        self.query_group.setTitle(tr(lang,"query_settings")); self.crawl_group.setTitle(tr(lang,"crawl_settings")); self.limit_group.setTitle(tr(lang,"limit_settings")); self.output_group.setTitle(tr(lang,"output_settings")); self.result_group.setTitle(tr(lang,"result_preview")); self.log_group.setTitle(tr(lang,"log"))
        self.query_mode_label.setText(tr(lang,"query_mode")); self.vertical_label.setText(tr(lang,"search_vertical")); self.baidu_sort_label.setText(tr(lang,"baidu_sort")); self.query_terms_label.setText(tr(lang,"query_terms")); self.site_filters_label.setText(tr(lang,"site_filters_baidu" if self.engine == "baidu" else "site_filters")); self.safe_label.setText(tr(lang,"safe")); self.disable_filter_check.setText(tr(lang,"disable_filter"))
        self.date_filter_check.setText(tr(lang,"date_filter_enabled")); self.start_date_label.setText(tr(lang,"start_date")); self.end_date_label.setText(tr(lang,"end_date")); self.day_step_label.setText(tr(lang,"day_step")); self.timeout_label.setText(tr(lang,"timeout")); self.page_delay_label.setText(tr(lang,"page_delay"))
        self.output_browse.setText(tr(lang,"browse"))
        self.languages_label.setText(tr(lang,"languages")); self.countries_label.setText(tr(lang,"countries")); self.clear_lang_btn.setText(tr(lang,"clear_selection")); self.clear_country_btn.setText(tr(lang,"clear_selection"))
        self.output_file_label.setText(tr(lang,"output_file")); self.output_format_label.setText(tr(lang,"output_format"))
        self.open_link_btn.setText(tr(lang,"open_link")); self.delete_btn.setText(tr(lang,"delete_selected")); self.restore_order_btn.setText(tr(lang,"restore_original_order")); self.table.setToolTip(tr(lang,"header_sort_hint"))
        self.sample_scheme_label.setText(tr(lang,"sample_scheme")); self.sample_count_label.setText(tr(lang,"sample_count")); self.sample_btn.setText(tr(lang,"sample"))
        self.download_selected_btn.setText(tr(lang,"download_selected")); self.download_all_btn.setText(tr(lang,"download_all")); self.download_settings_btn.setText(tr(lang,"download_settings")); self.stop_download_btn.setText(tr(lang,"stop_download"))
        for action in self.context_actions:
            action.setText(tr(lang, str(action.property("text_key"))))

        # Preserve option keys while changing labels.
        qkey = combo_key(self.query_mode_combo, self._settings.get("query_mode","single")); vkey = combo_key(self.vertical_combo, self._settings.get("search_vertical","news")); bkey = combo_key(self.baidu_sort_combo, self._settings.get("baidu_sort","focus"))
        set_combo_options(self.query_mode_combo, query_mode_options_for_engine(self.engine), lang, qkey)
        set_combo_options(self.vertical_combo, vertical_options_for_engine(self.engine), lang, vkey)
        set_combo_options(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, lang, bkey)
        sample_key = combo_key(self.sample_scheme_combo, self._settings.get("sample_scheme","simple"))
        sample_options = [
            {"key":"simple","labels":{"en":tr("en","sample_simple"),"zh_sim":tr("zh_sim","sample_simple"),"zh_tra":tr("zh_tra","sample_simple")}},
            {"key":"systematic","labels":{"en":tr("en","sample_systematic"),"zh_sim":tr("zh_sim","sample_systematic"),"zh_tra":tr("zh_tra","sample_systematic")}},
            {"key":"source","labels":{"en":tr("en","sample_source"),"zh_sim":tr("zh_sim","sample_source"),"zh_tra":tr("zh_tra","sample_source")}},
        ]
        set_combo_options(self.sample_scheme_combo, sample_options, lang, sample_key)
        self._populate_multiselect_lists()
        self.table_model.headerDataChanged.emit(Qt.Orientation.Horizontal,0,self.table_model.columnCount()-1)
        if self.status_label.text() in {"", tr("en","ready"), tr("zh_sim","ready"), tr("zh_tra","ready")}:
            self.status_label.setText(tr(lang,"ready"))
        self.update_count()

    def _populate_multiselect_lists(self) -> None:
        wanted_langs = set(self.selected_list_values(self.languages_list)) or set(self._settings.get("languages_lr", []))
        wanted_countries = set(self.selected_list_values(self.countries_list)) or set(self._settings.get("countries_cr", []))
        self.languages_list.clear()
        for opt in LANGUAGE_OPTIONS:
            if not opt.get("lr"):
                continue
            visible = label_for(opt, self.lang)
            if self.lang in {"zh_sim", "zh_tra"}:
                english = label_for(opt, "en")
                if english and english != visible:
                    visible = f"{visible} ({english})"
            item = QListWidgetItem(visible); item.setData(Qt.ItemDataRole.UserRole, opt.get("lr")); self.languages_list.addItem(item)
            if opt.get("lr") in wanted_langs: item.setSelected(True)
        self.countries_list.clear()
        for opt in COUNTRY_OPTIONS:
            if not opt.get("cr"):
                continue
            visible = label_for(opt, self.lang)
            if self.lang in {"zh_sim", "zh_tra"}:
                english = label_for(opt, "en")
                if english and english != visible:
                    visible = f"{visible} ({english})"
            item = QListWidgetItem(visible); item.setData(Qt.ItemDataRole.UserRole, opt.get("cr")); self.countries_list.addItem(item)
            if opt.get("cr") in wanted_countries: item.setSelected(True)

    @staticmethod
    def selected_list_values(widget: QListWidget) -> list[str]:
        return [str(i.data(Qt.ItemDataRole.UserRole)) for i in widget.selectedItems() if i.data(Qt.ItemDataRole.UserRole)]

    def _date_filter_toggled(self, enabled: bool) -> None:
        if enabled:
            self._normalize_date_controls()
        else:
            self._normalize_date_controls(reset_when_unfiltered=True)
        for widget in (self.start_date_edit, self.end_date_edit, self.day_step_spin):
            widget.setEnabled(bool(enabled))
        self.start_date_label.setEnabled(bool(enabled))
        self.end_date_label.setEnabled(bool(enabled))
        self.day_step_label.setEnabled(bool(enabled))

    def _normalize_date_controls(self, *, reset_when_unfiltered: bool = False) -> None:
        today = QDate.currentDate()
        if reset_when_unfiltered and not self.date_filter_check.isChecked():
            self.start_date_edit.blockSignals(True)
            self.end_date_edit.blockSignals(True)
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
            self.start_date_edit.blockSignals(False)
            self.end_date_edit.blockSignals(False)
            return
        if self.start_date_edit.date() > self.end_date_edit.date():
            self.start_date_edit.blockSignals(True)
            self.end_date_edit.blockSignals(True)
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
            self.start_date_edit.blockSignals(False)
            self.end_date_edit.blockSignals(False)

    def _start_date_changed(self, value: QDate) -> None:
        if value > self.end_date_edit.date():
            self.end_date_edit.setDate(value)

    def _end_date_changed(self, value: QDate) -> None:
        if value < self.start_date_edit.date():
            self.start_date_edit.setDate(value)

    def set_collection_enabled(self, enabled: bool) -> None:
        # Automatic collection requires a valid Selenium environment, but the
        # query controls must remain editable because Manual Collection 3.x
        # deliberately works without Selenium/WebDriver. The main-window Start
        # action is the only automatic-collection control locked by readiness.
        self._automatic_collection_ready = bool(enabled)
        self.query_group.setEnabled(True)
        self.crawl_group.setEnabled(True)
        if self.engine == "google":
            self.limit_group.setEnabled(True)

    def apply_settings(self, settings: dict[str, Any]) -> None:
        s = dict(panel_defaults(self.engine), **(settings or {}))
        self._settings = s
        set_combo_options(self.query_mode_combo, query_mode_options_for_engine(self.engine), self.lang, s["query_mode"])
        set_combo_options(self.vertical_combo, vertical_options_for_engine(self.engine), self.lang, s["search_vertical"])
        set_combo_options(self.baidu_sort_combo, BAIDU_SORT_OPTIONS, self.lang, s.get("baidu_sort","focus"))
        self.query_text.setPlainText(str(s.get("query_terms", ""))); self.site_text.setPlainText(str(s.get("site_filters", "")))
        safe = str(s.get("safe", "")); idx = self.safe_combo.findData(safe); self.safe_combo.setCurrentIndex(max(0,idx)); self.disable_filter_check.setChecked(bool(s.get("disable_filter",False)))
        self.date_filter_check.setChecked(bool(s.get("date_filter_enabled", False)))
        today_qdate = QDate.currentDate()
        start_qdate = QDate.fromString(str(s.get("start_date", date.today().isoformat())), "yyyy-MM-dd")
        end_qdate = QDate.fromString(str(s.get("end_date", date.today().isoformat())), "yyyy-MM-dd")
        if not start_qdate.isValid(): start_qdate = today_qdate
        if not end_qdate.isValid(): end_qdate = today_qdate
        if not self.date_filter_check.isChecked() or start_qdate > end_qdate:
            start_qdate = end_qdate = today_qdate
        self.start_date_edit.setDate(start_qdate); self.end_date_edit.setDate(end_qdate); self.day_step_spin.setValue(int(s.get("day_step",0))); self.timeout_spin.setValue(int(s.get("timeout",20))); self.page_delay_min.setValue(milliseconds_to_ui_seconds(s.get("page_delay_min_ms",30000), 30000)); self.page_delay_max.setValue(milliseconds_to_ui_seconds(s.get("page_delay_max_ms",90000), 90000))
        self._date_filter_toggled(self.date_filter_check.isChecked())
        self._normalize_date_controls(reset_when_unfiltered=True)
        self.output_edit.setText(str(s.get("output_path",default_output_path(self.engine)))); self.output_format_combo.setCurrentText(str(s.get("output_format","xlsx")))
        self.sample_count_spin.setValue(int(s.get("sample_count",20)))
        self._populate_multiselect_lists()
        self.retranslate_ui()

    def collect_settings(self) -> dict[str, Any]:
        data = dict(panel_defaults(self.engine))
        data.update({
            "query_mode": combo_key(self.query_mode_combo,"single"), "search_vertical": combo_key(self.vertical_combo,"news"), "baidu_sort": combo_key(self.baidu_sort_combo,"focus"),
            "query_terms": self.query_text.toPlainText().strip(), "site_filters": self.site_text.toPlainText().strip(), "safe": str(self.safe_combo.currentData() or ""), "disable_filter": self.disable_filter_check.isChecked(),
            "date_filter_enabled": self.date_filter_check.isChecked(), "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"), "end_date": self.end_date_edit.date().toString("yyyy-MM-dd"), "day_step": self.day_step_spin.value(), "timeout": self.timeout_spin.value(), "page_delay_min_ms": ui_seconds_to_milliseconds(self.page_delay_min.value()), "page_delay_max_ms": ui_seconds_to_milliseconds(self.page_delay_max.value()),
            "languages_lr": self.selected_list_values(self.languages_list) if self.engine == "google" else [], "countries_cr": self.selected_list_values(self.countries_list) if self.engine == "google" else [],
            "output_path": self.output_edit.text().strip(), "output_format": self.output_format_combo.currentText().strip().lower(), "content_download_dir": str(self._settings.get("content_download_dir", app_base_dir()/"content_downloads")), "content_threads": int(self._settings.get("content_threads",3)), "content_fetch_mode": str(self._settings.get("content_fetch_mode","mixed")), "content_delay_min_ms": int(self._settings.get("content_delay_min_ms",0)), "content_delay_max_ms": int(self._settings.get("content_delay_max_ms",0)), "content_receive_wait_ms": int(self._settings.get("content_receive_wait_ms",5000)), "content_cleaning_scheme": str(self._settings.get("content_cleaning_scheme","auto")),
            "sample_scheme": combo_key(self.sample_scheme_combo,"simple"), "sample_count": self.sample_count_spin.value(), "user_agent": self._settings.get("user_agent",DEFAULT_USER_AGENT),
            "content_retry_count": int(self._settings.get("content_retry_count",1)), "content_task_timeout_seconds": int(self._settings.get("content_task_timeout_seconds",300)), "content_resume_enabled": bool(self._settings.get("content_resume_enabled",True)), "content_domain_lock_timeout_seconds": int(self._settings.get("content_domain_lock_timeout_seconds",300)),
        })
        self._settings = dict(data)
        return data

    def browse_output(self) -> None:
        fmt=self.output_format_combo.currentText().lower() or "xlsx"; path,_=QFileDialog.getSaveFileName(self,tr(self.lang,"output_file"),self.output_edit.text() or default_output_path(self.engine),f"{fmt.upper()} (*.{fmt});;All files (*)")
        if path:
            if not path.lower().endswith("."+fmt): path += "."+fmt
            self.output_edit.setText(path)

    def _output_format_changed(self, fmt: str) -> None:
        if not fmt:return
        p=Path(self.output_edit.text().strip() or default_output_path(self.engine))
        if p.suffix.lower()!=f".{fmt.lower()}": self.output_edit.setText(str(p.with_suffix(f".{fmt.lower()}")))

    def build_config(self, *, allow_empty_query: bool = False) -> CollectorConfig:
        s=self.collect_settings(); browser=self.window.browser_settings; raw=s["query_terms"].strip()
        if not raw and not allow_empty_query: raise ValueError(tr(self.lang,"invalid_query"))
        sd=self.start_date_edit.date().toPython(); ed=self.end_date_edit.date().toPython()
        if s["date_filter_enabled"] and sd>ed: raise ValueError(tr(self.lang,"invalid_date"))
        if s["page_delay_min_ms"]<0 or s["page_delay_min_ms"]>s["page_delay_max_ms"] or s["timeout"]<1: raise ValueError(tr(self.lang,"invalid_number"))
        if not s["output_path"]: raise ValueError(tr(self.lang,"invalid_output"))
        terms=split_text_terms(raw)
        return CollectorConfig(
            query_mode=s["query_mode"], query_terms=terms, raw_query=raw if s["query_mode"]=="raw" else "", site_filters=split_text_terms(s["site_filters"]), search_vertical=s["search_vertical"], fetch_backend=str(browser.get("fetch_backend","selenium_chrome")),
            language_lr="|".join(s["languages_lr"]), country_cr="|".join(s["countries_cr"]), safe=s["safe"], disable_filter=bool(s["disable_filter"]), date_filter_enabled=bool(s["date_filter_enabled"]), start_date=sd, end_date=ed, day_step=int(s["day_step"]),
            page_delay_min_ms=int(s["page_delay_min_ms"]), page_delay_max_ms=int(s["page_delay_max_ms"]), timeout_seconds=int(s["timeout"]), user_agent=str(s.get("user_agent") or DEFAULT_USER_AGENT), browser_wait_ms=int(browser.get("browser_wait_ms",5000)), browser_headless=bool(browser.get("browser_headless",False)), browser_driver_path=str(browser.get("browser_driver_path", "")), browser_binary_path=str(browser.get("browser_binary_path", "")), baidu_sort=str(s.get("baidu_sort","focus")), debug_dir=str(app_base_dir() / "weblens_debug_html"),
        )

    def start_crawl(self) -> None:
        if self.worker and self.worker.is_alive(): return
        if not self.window.preflight_browser_environment():
            QMessageBox.warning(self, APP_NAME, tr(self.lang, "browser_required"))
            self.window.open_browser_settings()
            return
        try: cfg=self.build_config()
        except Exception as exc:
            QMessageBox.critical(self,APP_NAME,str(exc)); return
        self.window.save_settings()
        self.records=[]; self.original_records=[]; self.undo_stack=[]; self.redo_stack=[]; self._clear_header_sort_indicator(); self.table_model.refresh(); self.log_text.clear(); self.stop_event.clear(); self._verification_dialog_shown=False
        self._crawl_terminal_kind=""; self._crawl_terminal_message=""; self._last_result_autosave_signature=None
        self.progress.setRange(0,0); self.status_label.setText(tr(self.lang,"running")); self.update_count()
        def worker():
            try:
                for event in crawl(cfg, stop_checker=self.stop_event.is_set): self.signals.crawl_event.emit(event)
            except StopCrawl:
                self.signals.crawl_error.emit("stopped",tr(self.lang,"stopped"))
            except BrowserStartupError as exc:
                self.signals.crawl_error.emit("browser",str(exc))
            except NetworkAccessError as exc:
                self.signals.crawl_error.emit("network",str(exc))
            except Exception as exc:
                self.signals.crawl_error.emit("error",str(exc))
            finally:self.signals.crawl_finished.emit()
        self.worker=threading.Thread(target=worker,daemon=True); self.worker.start(); self.window.sync_action_states()

    def _handle_crawl_event(self,event: Any) -> None:
        et=getattr(event,"event_type","")
        if et=="slice" and getattr(event,"data",None):
            total=max(1,int(event.data.get("slice_total",1))); idx=max(1,int(event.data.get("slice_index",1))); self.progress.setRange(0,total); self.progress.setValue(idx-1); self.status_label.setText(event.message); self.log(event.message)
        elif et=="record" and getattr(event,"record",None):
            if self._header_sort_column is not None:
                self._clear_header_sort_indicator()
            self.records.append(event.record); self.original_records.append(event.record); self.table_model.refresh(); self.update_count()
        elif et=="verification_wait":
            self.log("[VERIFICATION WAIT] "+event.message); self.status_label.setText(tr(self.lang,"verification_title"))
            if not self._verification_dialog_shown:
                self._verification_dialog_shown=True; QMessageBox.warning(self,tr(self.lang,"verification_title"),tr(self.lang,"verification_message"))
        elif et=="verification_passed":
            self._verification_dialog_shown=False; self.log("[VERIFICATION PASSED] "+event.message); self.status_label.setText(tr(self.lang,"running"))
        elif et=="done":
            self.log(event.message)
        else:self.log(str(getattr(event,"message",event)))

    def _handle_crawl_error(self,kind: str,message: str) -> None:
        self._crawl_terminal_kind = str(kind or "error")
        self._crawl_terminal_message = str(message or "")
        # Save everything already delivered to Result Preview before opening any
        # modal error dialog.  The finalizer saves once more after the worker has
        # fully stopped, so late queued record events are not lost.
        self._autosave_results(f"collection {self._crawl_terminal_kind}")
        if kind=="stopped": self.log(message); self.status_label.setText(tr(self.lang,"stopped")); return
        self.log(f"[ERROR] {message}")
        if kind == "browser":
            self.window.show_driver_help(message)
            return
        title=tr(self.lang,"network_error") if kind=="network" else APP_NAME
        QMessageBox.warning(self,title,message)

    def _on_crawl_finished(self) -> None:
        self.worker = None
        self.window.sync_action_states()
        self.progress.setRange(0,100); self.progress.setValue(100 if self.records else 0)
        stopped = self.stop_event.is_set() or self._crawl_terminal_kind == "stopped"
        abnormal = bool(self._crawl_terminal_kind and self._crawl_terminal_kind != "stopped")
        if self.records:
            reason = "collection stopped" if stopped else ("collection exception" if abnormal else "collection completed")
            self._autosave_results(reason)
        if stopped:
            self.status_label.setText(tr(self.lang,"stopped"))
        elif abnormal:
            # Keep the error state rather than reporting a false normal completion.
            self.status_label.setText(tr(self.lang,"stopped"))
        elif self.records:
            self.status_label.setText(tr(self.lang,"done"))
        else:
            self.status_label.setText(tr(self.lang,"no_records"))

    def stop_crawl(self) -> None:
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            # Emergency save immediately on the user's click.  The worker may still
            # be inside a browser/network wait, so do not wait for thread shutdown
            # before protecting the records already collected.
            self._autosave_results("manual collection stop requested")
            self.status_label.setText(tr(self.lang,"stopped"))
            self.log(tr(self.lang,"stopped"))

    def stop_all(self) -> None:
        self.stop_event.set()
        self.content_stop_event.set()
        self._autosave_results("stop-all requested")
        self.status_label.setText(tr(self.lang,"stopped"))
        self.log(tr(self.lang,"stopped"))

    def log(self,msg: str) -> None:
        self.log_text.appendPlainText(str(msg)); sb=self.log_text.verticalScrollBar(); sb.setValue(sb.maximum())

    def update_count(self) -> None:
        sel=len(self.selected_rows()); self.count_label.setText(tr(self.lang,"records_count",n=len(self.records),s=sel))
        if hasattr(self, "stop_download_btn"):
            self.sync_download_button_states()

    def selected_rows(self) -> list[int]:
        if not self.table.selectionModel():return []
        return sorted({idx.row() for idx in self.table.selectionModel().selectedRows() if 0<=idx.row()<len(self.records)})

    def selected_records(self) -> list[Any]: return [self.records[i] for i in self.selected_rows()]

    def push_undo(self) -> None:
        self.undo_stack.append(list(self.records)); self.undo_stack=self.undo_stack[-50:]; self.redo_stack.clear()

    def undo_result_edit(self) -> None:
        if not self.undo_stack:return
        self.redo_stack.append(list(self.records)); self.records=self.undo_stack.pop(); self._clear_header_sort_indicator(); self.table_model.refresh(); self.update_count()

    def redo_result_edit(self) -> None:
        if not self.redo_stack:return
        self.undo_stack.append(list(self.records)); self.records=self.redo_stack.pop(); self._clear_header_sort_indicator(); self.table_model.refresh(); self.update_count()

    def reset_result_preview(self) -> None:
        if self.records==self.original_records:return
        self.push_undo(); self.records=list(self.original_records); self._clear_header_sort_indicator(); self.table_model.refresh(); self.update_count()

    def clear_results(self) -> None:
        self.records=[]; self.original_records=[]; self.undo_stack=[]; self.redo_stack=[]; self._last_result_autosave_signature=None; self._clear_header_sort_indicator(); self.table_model.refresh(); self.log_text.clear(); self.progress.setRange(0,100); self.progress.setValue(0); self.status_label.setText(tr(self.lang,"ready")); self.update_count()

    def open_selected_link(self) -> None:
        recs=self.selected_records()
        if recs:
            link=str(getattr(recs[0],"link","") or "")
            if link:webbrowser.open(link)

    def delete_selected(self) -> None:
        rows=self.selected_rows()
        if not rows:return
        self.push_undo(); doomed=set(rows); self.records=[r for i,r in enumerate(self.records) if i not in doomed]; self.table_model.refresh(); self.update_count()

    @staticmethod
    def _record_sort_value(record: Any, key: str) -> Any:
        """Return a predictable sort value for a Result Preview column."""
        if key == "link":
            return str(getattr(record, "link", "") or "").casefold()
        if key == "time":
            return str(getattr(record, "collected_at", "") or "").casefold()
        if key == "title":
            return str(getattr(record, "title", "") or "").casefold()
        if key == "source":
            return str(getattr(record, "source", "") or "").casefold()
        if key == "published":
            parsed = published_sort_key(
                getattr(record, "published_time", ""),
                getattr(record, "collected_at", ""),
            )
            return parsed if parsed is not None else (0, 0, 0, 0, 0, 0)
        if key == "status":
            return str(getattr(record, "content_status", "") or "").casefold()
        if key == "words":
            value = getattr(record, "content_word_count", None)
            try:
                return float(value)
            except (TypeError, ValueError):
                return float("-inf")
        if key == "quality":
            value = getattr(record, "content_quality_score", None)
            try:
                return float(value)
            except (TypeError, ValueError):
                return float("-inf")
        return ""

    def _clear_header_sort_indicator(self) -> None:
        self._header_sort_column = None
        self._header_sort_order = Qt.SortOrder.AscendingOrder
        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(False)

    def _header_section_clicked(self, section: int) -> None:
        if not self.records or not (0 <= section < len(self.table_model.columns)):
            return
        if self._header_sort_column == section:
            order = (
                Qt.SortOrder.DescendingOrder
                if self._header_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            order = Qt.SortOrder.AscendingOrder
        self._header_sort_column = section
        self._header_sort_order = order
        header = self.table.horizontalHeader()
        header.setSortIndicator(section, order)
        header.setSortIndicatorShown(True)
        self.sort_records(self.table_model.columns[section], descending=order == Qt.SortOrder.DescendingOrder)

    def restore_original_order(self) -> None:
        if not self.records:
            self._clear_header_sort_indicator()
            return
        self.sort_records("original", descending=False)
        self._clear_header_sort_indicator()

    def sort_records(self, key: str, *, descending: bool = False) -> None:
        if not self.records:
            return
        before = list(self.records)
        if key == "original":
            # Restore engine/import order only for records still present.
            # Deletions and sampling remain in effect.
            original_rank = {id(r): i for i, r in enumerate(self.original_records)}
            sorted_records = sorted(self.records, key=lambda r: original_rank.get(id(r), len(original_rank)))
        else:
            def has_value(record: Any) -> bool:
                attr = {
                    "link": "link",
                    "time": "collected_at",
                    "title": "title",
                    "source": "source",
                    "published": "published_time",
                    "status": "content_status",
                    "words": "content_word_count",
                    "quality": "content_quality_score",
                }.get(key, "")
                value = getattr(record, attr, None) if attr else None
                if key == "published":
                    return published_sort_key(value, getattr(record, "collected_at", "")) is not None
                return value not in (None, "")

            filled = [r for r in self.records if has_value(r)]
            blanks = [r for r in self.records if not has_value(r)]
            sorted_records = sorted(
                filled,
                key=lambda r: self._record_sort_value(r, key),
                reverse=bool(descending),
            ) + blanks
        if sorted_records == before:
            return
        self.push_undo()
        self.records = sorted_records
        self.table_model.refresh()
        self.update_count()

    def sample_records(self) -> None:
        if not self.records:return
        n=max(1,self.sample_count_spin.value()); scheme=combo_key(self.sample_scheme_combo,"simple")
        self.push_undo()
        if scheme=="source":
            groups: dict[str,list[Any]]={}
            for r in self.records: groups.setdefault(str(getattr(r,"source","") or "(unknown)"),[]).append(r)
            sampled=[]
            for group in groups.values(): sampled.extend(random.sample(group,min(n,len(group))))
        elif scheme=="systematic":
            if n>=len(self.records): sampled=list(self.records)
            else:
                step=len(self.records)/n; sampled=[self.records[min(len(self.records)-1,int(i*step))] for i in range(n)]
                ded=[]; seen=set()
                for r in sampled:
                    k=id(r)
                    if k not in seen:seen.add(k);ded.append(r)
                sampled=ded
        else: sampled=random.sample(self.records,min(n,len(self.records)))
        self.records=sampled; self._clear_header_sort_indicator(); self.table_model.refresh(); self.update_count()

    def _append_imported_records(self, imported: list[Any]) -> tuple[int, int]:
        """Append unique imported/pasted URLs without disturbing existing results."""
        if not imported:
            return 0, 0
        seen = {normalize_url_for_dedup(r.link) for r in self.records if getattr(r, "link", "")}
        added: list[Any] = []
        for rec in imported:
            key = normalize_url_for_dedup(getattr(rec, "link", ""))
            if key and key not in seen:
                seen.add(key)
                added.append(rec)
        if added:
            self.push_undo()
            self._clear_header_sort_indicator()
            self.records.extend(added)
            self.original_records.extend(added)
            self.table_model.refresh()
            self.update_count()
        return len(added), max(0, len(imported) - len(added))

    def import_links(self) -> None:
        path,_=QFileDialog.getOpenFileName(self,tr(self.lang,"import"),str(app_base_dir()),"WebLens/result files (*.xlsx *.csv *.tsv *.txt *.text *.xml *.docx);;Excel (*.xlsx);;Text/CSV (*.txt *.text *.csv *.tsv);;All files (*)")
        if not path:return
        try: imported=import_records(path)
        except Exception as exc: QMessageBox.critical(self,APP_NAME,str(exc));return
        if not imported: QMessageBox.information(self,APP_NAME,tr(self.lang,"no_records"));return
        added, _skipped = self._append_imported_records(imported)
        self.status_label.setText(tr(self.lang,"import_done",n=added)); self.log(tr(self.lang,"import_done",n=added))

    def paste_links_from_text(self) -> None:
        """Parse one or more URLs from arbitrary pasted text and append them."""
        dialog = QDialog(self)
        apply_window_icon(dialog)
        dialog.setWindowTitle(tr(self.lang, "paste_links_title"))
        root = QVBoxLayout(dialog)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)
        help_label = QLabel(tr(self.lang, "paste_links_help"))
        help_label.setWordWrap(True)
        help_label.setProperty("muted", True)
        root.addWidget(help_label)
        editor = QPlainTextEdit()
        editor.setPlaceholderText("https://example.com/article-1\nSome text https://example.org/article-2 …")
        editor.setMinimumHeight(240)
        root.addWidget(editor, 1)
        feedback = QLabel()
        feedback.setWordWrap(True)
        feedback.setProperty("muted", True)
        root.addWidget(feedback)
        row = QHBoxLayout()
        row.setSpacing(8)
        add_btn = QPushButton(tr(self.lang, "paste_links_add"))
        clear_btn = QPushButton(tr(self.lang, "paste_links_clear"))
        close_btn = QPushButton(tr(self.lang, "close"))
        row.addWidget(add_btn)
        row.addWidget(clear_btn)
        row.addStretch(1)
        row.addWidget(close_btn)
        root.addLayout(row)

        def add_now() -> None:
            imported = import_urls_from_text(editor.toPlainText())
            if not imported:
                feedback.setText(tr(self.lang, "paste_links_none"))
                return
            added, skipped = self._append_imported_records(imported)
            message = tr(self.lang, "paste_links_result", found=len(imported), added=added, skipped=skipped)
            feedback.setText(message)
            self.status_label.setText(message)
            self.log(message)
            if added:
                editor.clear()

        add_btn.clicked.connect(add_now)
        clear_btn.clicked.connect(editor.clear)
        close_btn.clicked.connect(dialog.accept)
        dialog.resize(760, 430)
        fit_dialog_to_screen(dialog, 760, 430)
        editor.setFocus()
        dialog.exec()

    def _result_export_signature(self) -> tuple[Any, ...]:
        """Fingerprint the current export-visible state for duplicate autosave suppression."""
        rows: list[tuple[Any, ...]] = []
        for rec in self.records:
            rows.append((
                str(getattr(rec,"link","") or ""),
                str(getattr(rec,"title","") or ""),
                str(getattr(rec,"source","") or ""),
                str(getattr(rec,"published_time","") or ""),
                str(getattr(rec,"content_status","") or ""),
                str(getattr(rec,"content_word_count","") or ""),
                str(getattr(rec,"content_quality_score","") or ""),
                str(getattr(rec,"content_error","") or ""),
                str(getattr(rec,"raw_html_path","") or ""),
                str(getattr(rec,"raw_text_path","") or ""),
                str(getattr(rec,"clean_text_path","") or ""),
                str(getattr(rec,"metadata_path","") or ""),
            ))
        return tuple(rows)

    def _write_result_file(self) -> tuple[int,str]:
        if not self.records:
            return 0,""
        fmt=self.output_format_combo.currentText().strip().lower(); path=self.output_edit.text().strip()
        if not path: raise ValueError(tr(self.lang,"invalid_output"))
        if not path.lower().endswith("."+fmt): path += "."+fmt; self.output_edit.setText(path)
        unique=[]; seen=set()
        for rec in self.records:
            k=normalize_url_for_dedup(rec.link)
            if k in seen:continue
            seen.add(k);unique.append(rec)
        export_records(unique,path,fmt)
        return len(unique),path

    def _autosave_results(self, reason: str) -> bool:
        """Persist the current Result Preview without showing a dialog.

        This is intentionally called on manual stop, abnormal termination and
        content-download termination.  It writes to the same configured result
        file used by normal export.
        """
        if not self.records:
            return True
        signature=(self.output_edit.text().strip(),self.output_format_combo.currentText().strip().lower(),self._result_export_signature())
        if signature == self._last_result_autosave_signature:
            return True
        try:
            count,path=self._write_result_file()
            self._last_result_autosave_signature=(self.output_edit.text().strip(),self.output_format_combo.currentText().strip().lower(),self._result_export_signature())
            self.log(f"[AUTO SAVE] {reason}: {count} record(s) -> {path}")
            return True
        except Exception as exc:
            self.log(f"[AUTO SAVE ERROR] {reason}: {exc}")
            return False

    def export_results(self,show_message: bool=True) -> None:
        if not self.records:
            if show_message: QMessageBox.information(self,APP_NAME,tr(self.lang,"no_records"))
            return
        count,path=self._write_result_file()
        self._last_result_autosave_signature=(self.output_edit.text().strip(),self.output_format_combo.currentText().strip().lower(),self._result_export_signature())
        self.status_label.setText(tr(self.lang,"exported")); self.log(tr(self.lang,"export_done",n=count,path=path))
        if show_message: QMessageBox.information(self,APP_NAME,tr(self.lang,"export_done",n=count,path=path))

    def open_output(self) -> None:
        p=Path(self.output_edit.text().strip())
        try:
            if p.exists():open_path(p)
            elif p.parent.exists():open_path(p.parent)
        except Exception as exc:QMessageBox.critical(self,APP_NAME,str(exc))

    def open_download_folder(self) -> None:
        p=Path(str(self._settings.get("content_download_dir", app_base_dir()/"content_downloads")))
        try:p.mkdir(parents=True,exist_ok=True);open_path(p)
        except Exception as exc:QMessageBox.critical(self,APP_NAME,str(exc))

    def open_content_settings(self) -> bool:
        dialog=QDialog(self); apply_window_icon(dialog); dialog.setWindowTitle(tr(self.lang,"download_settings")); dialog.setMinimumWidth(520)
        layout=QVBoxLayout(dialog); layout.setContentsMargins(16,14,16,14); layout.setSpacing(10)
        form=QFormLayout(); form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows); form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow); layout.addLayout(form)
        folder=QLineEdit(str(self._settings.get("content_download_dir", app_base_dir()/"content_downloads"))); browse=QPushButton(tr(self.lang,"browse")); fr=QWidget(); fl=QHBoxLayout(fr); fl.setContentsMargins(0,0,0,0);fl.addWidget(folder,1);fl.addWidget(browse); browse.clicked.connect(lambda: self._dialog_browse_dir(folder))
        threads=QSpinBox();threads.setRange(1,32);threads.setValue(int(self._settings.get("content_threads",3)))
        mode=QComboBox();set_combo_options(mode,CONTENT_FETCH_MODE_OPTIONS,self.lang,str(self._settings.get("content_fetch_mode","mixed")))
        dmin=QSpinBox();dmin.setRange(0,9999999);dmin.setValue(int(self._settings.get("content_delay_min_ms",0))); dmax=QSpinBox();dmax.setRange(0,9999999);dmax.setValue(int(self._settings.get("content_delay_max_ms",0))); dr=QWidget();dl=QHBoxLayout(dr);dl.setContentsMargins(0,0,0,0);dl.addWidget(dmin);dl.addWidget(QLabel("–"));dl.addWidget(dmax)
        wait=QSpinBox();wait.setRange(0,9999999);wait.setValue(int(self._settings.get("content_receive_wait_ms",5000)))
        clean=QComboBox();set_combo_options(clean,CONTENT_CLEANING_OPTIONS,self.lang,str(self._settings.get("content_cleaning_scheme","auto")))
        retry=QSpinBox();retry.setRange(0,10);retry.setValue(int(self._settings.get("content_retry_count",1)))
        task_timeout=QSpinBox();task_timeout.setRange(30,86400);task_timeout.setValue(int(self._settings.get("content_task_timeout_seconds",300)))
        resume=QCheckBox(tr(self.lang,"content_resume"));resume.setChecked(bool(self._settings.get("content_resume_enabled",True)))
        domain_timeout=QSpinBox();domain_timeout.setRange(1,86400);domain_timeout.setValue(int(self._settings.get("content_domain_lock_timeout_seconds",300)))
        form.addRow(tr(self.lang,"content_folder"),fr);form.addRow(tr(self.lang,"content_threads"),threads);form.addRow(tr(self.lang,"content_fetch_mode"),mode);form.addRow(tr(self.lang,"content_delay"),dr);form.addRow(tr(self.lang,"content_wait"),wait);form.addRow(tr(self.lang,"content_cleaning"),clean);form.addRow(tr(self.lang,"content_retry"),retry);form.addRow(tr(self.lang,"content_task_timeout"),task_timeout);form.addRow(resume);form.addRow(tr(self.lang,"content_domain_timeout"),domain_timeout)
        note=QLabel(tr(self.lang,"content_note")); note.setWordWrap(True); note.setProperty("muted", True); layout.addWidget(note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);layout.addWidget(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        dialog.adjustSize(); fit_dialog_to_screen(dialog, 760, dialog.sizeHint().height())
        if dialog.exec()!=QDialog.DialogCode.Accepted:return False
        if not folder.text().strip() or dmin.value()>dmax.value():QMessageBox.critical(self,APP_NAME,tr(self.lang,"invalid_number"));return False
        self._settings["content_download_dir"]=folder.text().strip();self._settings["content_threads"]=threads.value();self._settings["content_fetch_mode"]=combo_key(mode,"mixed");self._settings["content_delay_min_ms"]=dmin.value();self._settings["content_delay_max_ms"]=dmax.value();self._settings["content_receive_wait_ms"]=wait.value();self._settings["content_cleaning_scheme"]=combo_key(clean,"auto");self._settings["content_retry_count"]=retry.value();self._settings["content_task_timeout_seconds"]=task_timeout.value();self._settings["content_resume_enabled"]=resume.isChecked();self._settings["content_domain_lock_timeout_seconds"]=domain_timeout.value();self.window.save_settings();return True

    def _dialog_browse_dir(self,edit: QLineEdit) -> None:
        path=QFileDialog.getExistingDirectory(self,tr(self.lang,"content_folder"),edit.text() or str(app_base_dir()))
        if path:edit.setText(path)

    def content_settings(self,prompt: bool=True) -> ContentDownloadSettings|None:
        if prompt and not self.open_content_settings():return None
        s=self.collect_settings();folder=s["content_download_dir"]
        if not folder:return None
        try:ensure_content_dirs(folder)
        except Exception as exc:QMessageBox.critical(self,APP_NAME,str(exc));return None
        browser=self.window.browser_settings
        return ContentDownloadSettings(content_root=folder,max_workers=max(1,int(s["content_threads"])),timeout_seconds=max(1,int(s["timeout"])),user_agent=str(s.get("user_agent") or DEFAULT_USER_AGENT),min_delay_ms=int(s["content_delay_min_ms"]),max_delay_ms=int(s["content_delay_max_ms"]),fetch_mode=s["content_fetch_mode"],receive_wait_ms=int(s["content_receive_wait_ms"]),cleaning_scheme=s["content_cleaning_scheme"],selenium_fallback=(s["content_fetch_mode"]=="mixed"),selenium_backend=str(browser.get("fetch_backend","selenium_chrome")),selenium_driver_path=str(browser.get("browser_driver_path","")),selenium_binary_path=str(browser.get("browser_binary_path","")),selenium_wait_ms=int(s["content_receive_wait_ms"]),selenium_headless=bool(browser.get("browser_headless",False)),retry_count=int(s.get("content_retry_count",1)),task_timeout_seconds=int(s.get("content_task_timeout_seconds",300)),resume_enabled=bool(s.get("content_resume_enabled",True)),domain_lock_timeout_seconds=int(s.get("content_domain_lock_timeout_seconds",300)))

    def download_selected_content(self) -> None:self.start_content_download(self.selected_records())
    def download_all_content(self) -> None:self.start_content_download(list(self.records))

    def start_content_download(self,records: list[Any]) -> None:
        if not records:QMessageBox.information(self,APP_NAME,tr(self.lang,"no_records"));return
        if self.content_worker and self.content_worker.is_alive():return
        settings=self.content_settings(prompt=False)
        if not settings:return
        self.window.save_settings();self.content_stop_event.clear();self._content_terminal_error="";self.progress.setRange(0,max(1,len(records)));self.progress.setValue(0);self.status_label.setText("0/"+str(len(records)))
        self.content_worker=threading.Thread(target=self._content_worker,args=(records,settings),daemon=True);self.content_worker.start();self.sync_download_button_states();self.window.sync_action_states()

    def sync_download_button_states(self) -> None:
        running = bool(self.content_worker and self.content_worker.is_alive())
        has_records = bool(self.records)
        self.download_settings_btn.setEnabled(not running)
        self.download_selected_btn.setEnabled((not running) and bool(self.selected_records()))
        self.download_all_btn.setEnabled((not running) and has_records)
        self.stop_download_btn.setEnabled(running and not self.content_stop_event.is_set())

    def stop_content_download(self) -> None:
        if not (self.content_worker and self.content_worker.is_alive()):
            self.sync_download_button_states()
            return
        self.content_stop_event.set()
        # Save the result table immediately; completed content files and the
        # content manifest are already written item-by-item by the downloader.
        self._autosave_results("manual content-download stop requested")
        self.status_label.setText(tr(self.lang, "stopping_download"))
        self.log(tr(self.lang, "stopping_download"))
        self.sync_download_button_states()

    def _run_content_with_timeout(self,rec,settings,index,domain_locks,manifest_lock):
        timeout=max(30,int(settings.task_timeout_seconds));box={"done":False,"result":None,"error":""}
        def target():
            try:box["result"]=download_one(rec,settings,index,domain_locks,manifest_lock,self.content_stop_event.is_set)
            except Exception as exc:box["error"]=str(exc)
            finally:box["done"]=True
        th=threading.Thread(target=target,daemon=True);th.start();th.join(timeout)
        if th.is_alive():return {"ok":False,"error":f"Content task timed out after {timeout} seconds","url":getattr(rec,"link","")}
        if box["error"]:return {"ok":False,"error":box["error"],"url":getattr(rec,"link","")}
        return box["result"] or {"ok":False,"error":"Empty content task result","url":getattr(rec,"link","")}

    def _content_worker(self,records,settings):
        total=len(records);done=0;done_lock=threading.Lock();domain_locks=DomainLockPool();manifest_lock=threading.Lock();tasks=queue.Queue();max_retries=max(0,int(settings.retry_count))
        def publish(rec,result):
            nonlocal done
            with done_lock:done+=1;current=done
            self.signals.content_result.emit(rec,result);self.signals.content_progress.emit(current,total)
        try:
            success_index=load_successful_download_index(settings.content_root) if settings.resume_enabled else {}
            queued=0
            for i,rec in enumerate(records,1):
                if self.content_stop_event.is_set():break
                completed=successful_manifest_for_record(rec,success_index) if success_index else None
                if completed:
                    result=content_result_from_manifest(rec,completed);setattr(result,"skipped",True);publish(rec,result);continue
                tasks.put((i,rec));queued+=1
            def worker():
                try:
                    while not self.content_stop_event.is_set():
                        try:i,rec=tasks.get_nowait()
                        except queue.Empty:break
                        final=None
                        try:
                            for attempt in range(max_retries+1):
                                if self.content_stop_event.is_set():final={"ok":False,"error":"Stopped by user","url":getattr(rec,"link","")};break
                                result=self._run_content_with_timeout(rec,settings,i,domain_locks,manifest_lock);ok=bool(getattr(result,"ok",False) if not isinstance(result,dict) else result.get("ok"))
                                if ok or attempt>=max_retries:final=result;break
                                time.sleep(min(10.0,1.5*(attempt+1)))
                        finally:tasks.task_done()
                        publish(rec,final or {"ok":False,"error":"No result","url":getattr(rec,"link","")})
                except Exception as exc:
                    self.signals.content_error.emit(str(exc))
            workers=[]
            for _ in range(min(max(1,int(settings.max_workers)),max(1,queued)) if queued else 0):
                th=threading.Thread(target=worker,daemon=True);workers.append(th);th.start()
            while any(th.is_alive() for th in workers):time.sleep(.2)
        except Exception as exc:
            # Preserve all content already saved before an unexpected coordinator
            # failure.  Successful downloads remain resumable through the existing
            # manifest checkpoint mechanism.
            self.signals.content_error.emit(str(exc))
        finally:self.signals.content_finished.emit(done,total,settings.content_root)

    def _handle_content_result(self,rec,result) -> None:
        ok=bool(getattr(result,"ok",False) if not isinstance(result,dict) else result.get("ok"))
        def get(name,default=""):return getattr(result,name,default) if not isinstance(result,dict) else result.get(name,default)
        if ok:
            skipped=bool(getattr(result,"skipped",False) if not isinstance(result,dict) else result.get("skipped"));setattr(rec,"content_status","Skipped" if skipped else "Downloaded")
            # Current Google News may expose an opaque google.* /goto result URL.
            # Once destination-page downloading follows that redirect, replace
            # the preview/export link with the real final URL.
            final_url=str(get("final_url","") or "").strip()
            current_link=str(getattr(rec,"link","") or "")
            if final_url.startswith(("http://","https://")) and is_google_news_redirect_url(current_link) and not is_google_news_redirect_url(final_url):
                rec.link=final_url
                try: rec.actual_domain=(urlparse(final_url).netloc or "").lower().lstrip("www.")
                except Exception: rec.actual_domain=""
            if (not getattr(rec,"title","") or getattr(rec,"title","")==current_link) and get("title"):rec.title=str(get("title"))
            if not getattr(rec,"published_time","") and get("published_time"):rec.published_time=str(get("published_time"))
            for attr,key in (("content_word_count","word_count"),("content_quality_score","quality_score"),("content_extraction_method","extraction_method"),("content_cleaning_scheme","cleaning_scheme"),("metadata_excel_path","metadata_excel_path"),("raw_html_path","raw_html_path"),("raw_text_path","raw_text_path"),("clean_text_path","clean_text_path"),("metadata_path","metadata_path")):setattr(rec,attr,get(key,0 if "count" in key or "score" in key else ""))
            self.log(("Skipped" if skipped else "Downloaded")+": "+str(getattr(rec,"title",""))[:100])
        else:setattr(rec,"content_status","Failed");setattr(rec,"content_error",str(get("error","")));self.log("Content failed: "+str(get("error",""))[:180])
        self.table_model.refresh()

    def _handle_content_progress(self,done: int,total: int) -> None:self.progress.setRange(0,max(1,total));self.progress.setValue(done);self.status_label.setText(f"{done}/{total}")

    def _handle_content_error(self,message: str) -> None:
        self._content_terminal_error=str(message or "")
        self.content_stop_event.set()
        self.log(f"[CONTENT ERROR] {self._content_terminal_error}")
        # Save current Result Preview before the final completion signal.
        self._autosave_results("content-download exception")

    def _handle_content_finished(self,done: int,total: int,folder: str) -> None:
        self.content_worker = None
        stopped = self.content_stop_event.is_set() and done < total
        abnormal = bool(self._content_terminal_error)
        reason = "content download stopped" if stopped else ("content-download exception" if abnormal else "content download completed")
        # Result Preview contains the statuses/paths accumulated so far. Save it
        # on every terminal path. The downloader's per-item manifest/checkpoint
        # remains untouched, so Resume continues to skip only successful items.
        self._autosave_results(reason)
        if stopped:
            self.status_label.setText(tr(self.lang, "download_stopped"))
            self.log(f"{tr(self.lang, 'download_stopped')} {done}/{total}. {folder}")
        elif abnormal:
            self.status_label.setText(tr(self.lang, "download_stopped"))
            self.log(f"Content download stopped by error after {done}/{total}. {folder}")
        else:
            self.status_label.setText(f"{done}/{total}")
            self.log(f"Content download finished: {done}/{total}. {folder}")
        self.sync_download_button_states()
        self.window.sync_action_states()



class ManualCollectionSignals(QObject):
    progress = Signal(int, int, str)
    done = Signal(object)
    error = Signal(str)


class ManualCollectionDialog(QDialog):
    """Browser-independent workflow for manually saved search-result pages."""

    def __init__(self, panel: "CollectorPanel", cfg: CollectorConfig) -> None:
        super().__init__(panel)
        apply_window_icon(self)
        self.panel = panel
        self.window = panel.window
        self.lang = panel.lang
        self.cfg = cfg
        self.tasks = generate_manual_search_tasks(cfg)
        self.signals = ManualCollectionSignals(self)
        self.worker: threading.Thread | None = None
        self._build_ui()
        self._populate_tasks()
        self.signals.progress.connect(self._on_progress)
        self.signals.done.connect(self._on_done)
        self.signals.error.connect(self._on_error)
        QTimer.singleShot(0, lambda: fit_dialog_to_screen(self, 980, min(760, self.sizeHint().height())))

    def _build_ui(self) -> None:
        self.setWindowTitle(tr(self.lang, "manual_collection_title"))
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        intro = QLabel(tr(self.lang, "manual_intro"))
        intro.setWordWrap(True)
        root.addWidget(intro)

        url_group = QGroupBox(tr(self.lang, "manual_urls_group"))
        url_layout = QVBoxLayout(url_group)
        url_layout.setContentsMargins(12, 14, 12, 12)
        url_layout.setSpacing(8)
        note = QLabel(tr(self.lang, "manual_urls_note"))
        note.setWordWrap(True)
        note.setProperty("muted", True)
        url_layout.addWidget(note)
        self.url_list = QListWidget()
        self.url_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.url_list.setWordWrap(True)
        self.url_list.setMinimumHeight(180)
        url_layout.addWidget(self.url_list, 1)
        copy_row = QHBoxLayout()
        copy_row.setSpacing(7)
        self.copy_selected_btn = QPushButton(tr(self.lang, "manual_copy_selected"))
        self.copy_all_btn = QPushButton(tr(self.lang, "manual_copy_all"))
        self.copy_selected_btn.clicked.connect(self.copy_selected)
        self.copy_all_btn.clicked.connect(self.copy_all)
        copy_row.addWidget(self.copy_selected_btn)
        copy_row.addWidget(self.copy_all_btn)
        copy_row.addStretch(1)
        url_layout.addLayout(copy_row)
        root.addWidget(url_group)

        html_group = QGroupBox(tr(self.lang, "manual_html_group"))
        html_layout = QVBoxLayout(html_group)
        html_layout.setContentsMargins(12, 14, 12, 12)
        html_layout.setSpacing(8)
        html_note = QLabel(tr(self.lang, "manual_html_note"))
        html_note.setWordWrap(True)
        html_note.setProperty("muted", True)
        html_layout.addWidget(html_note)
        import_row = QHBoxLayout()
        import_row.setSpacing(7)
        self.import_files_btn = QPushButton(tr(self.lang, "manual_import_html"))
        self.import_folder_btn = QPushButton(tr(self.lang, "manual_import_folder"))
        self.import_files_btn.clicked.connect(self.import_files)
        self.import_folder_btn.clicked.connect(self.import_folder)
        import_row.addWidget(self.import_files_btn)
        import_row.addWidget(self.import_folder_btn)
        import_row.addStretch(1)
        html_layout.addLayout(import_row)
        self.parse_progress = QProgressBar()
        self.parse_progress.setRange(0, 100)
        self.parse_progress.setValue(0)
        self.parse_progress.setVisible(False)
        html_layout.addWidget(self.parse_progress)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setProperty("muted", True)
        html_layout.addWidget(self.summary_label)
        root.addWidget(html_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _populate_tasks(self) -> None:
        self.url_list.clear()
        for task in self.tasks:
            item = QListWidgetItem(f"{task.label}\n{task.url}")
            item.setData(Qt.ItemDataRole.UserRole, task.url)
            item.setToolTip(task.url)
            self.url_list.addItem(item)
        if self.url_list.count():
            self.url_list.setCurrentRow(0)
        else:
            self.summary_label.setText(tr(self.lang, "manual_no_tasks"))
        self.copy_selected_btn.setEnabled(bool(self.tasks))
        self.copy_all_btn.setEnabled(bool(self.tasks))

    def copy_selected(self) -> None:
        item = self.url_list.currentItem()
        if item is None:
            return
        url = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not url:
            return
        QApplication.clipboard().setText(url)
        self.summary_label.setText(tr(self.lang, "manual_copied", n=1))

    def copy_all(self) -> None:
        urls = [task.url for task in self.tasks if task.url]
        if not urls:
            return
        QApplication.clipboard().setText("\n".join(urls))
        self.summary_label.setText(tr(self.lang, "manual_copied", n=len(urls)))

    def import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr(self.lang, "manual_import_html"),
            str(app_base_dir()),
            "Saved search pages (*.html *.htm);;HTML (*.html *.htm);;All files (*)",
        )
        self._start_parse(paths)

    def import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr(self.lang, "manual_import_folder"), str(app_base_dir()))
        if not folder:
            return
        base = Path(folder)
        # Only parse HTML files directly in the selected folder. A browser's
        # "Webpage, complete" companion folder may contain iframe/resource HTML
        # files that are not result pages and must not be imported.
        paths = sorted(str(p) for p in base.iterdir() if p.is_file() and p.suffix.lower() in {".html", ".htm"})
        if not paths:
            QMessageBox.information(self, APP_NAME, tr(self.lang, "manual_no_html"))
            return
        self._start_parse(paths)

    def _set_busy(self, busy: bool) -> None:
        self.import_files_btn.setEnabled(not busy)
        self.import_folder_btn.setEnabled(not busy)
        self.copy_selected_btn.setEnabled((not busy) and bool(self.tasks))
        self.copy_all_btn.setEnabled((not busy) and bool(self.tasks))
        self.parse_progress.setVisible(busy)
        if hasattr(self, "close_button") and self.close_button is not None:
            self.close_button.setEnabled(not busy)
        if busy:
            self.parse_progress.setRange(0, 100)
            self.parse_progress.setValue(0)
            self.summary_label.setText(tr(self.lang, "manual_parsing"))

    def _start_parse(self, paths: list[str]) -> None:
        paths = [str(Path(p)) for p in paths if p and Path(p).is_file()]
        if not paths or (self.worker and self.worker.is_alive()):
            return
        self._set_busy(True)
        cfg = self.cfg

        def worker() -> None:
            try:
                results = []
                total = len(paths)
                for index, path in enumerate(paths, 1):
                    result = parse_saved_search_page(path, cfg, page_number=index)
                    results.append(result)
                    self.signals.progress.emit(index, total, Path(path).name)
                self.signals.done.emit(results)
            except Exception as exc:
                self.signals.error.emit(str(exc))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _on_progress(self, index: int, total: int, filename: str) -> None:
        self.parse_progress.setMaximum(max(1, total))
        self.parse_progress.setValue(max(0, min(index, total)))
        self.parse_progress.setFormat(f"{index}/{total} · {filename}")

    def _on_done(self, results: Any) -> None:
        self.worker = None
        self._set_busy(False)
        parsed = list(results or [])
        records: list[Any] = []
        warnings = 0
        wrong_engine = False
        for result in parsed:
            recs = list(getattr(result, "records", ()) or ())
            records.extend(recs)
            warning = str(getattr(result, "warning", "") or "")
            if warning:
                warnings += 1
                if "current panel" in warning:
                    wrong_engine = True
            self.panel.log(
                f"[MANUAL HTML] {Path(str(getattr(result, 'path', ''))).name}: "
                f"{len(recs)} record(s); source={getattr(result, 'source_url', '') or '(source URL unavailable)'}"
                + (f"; warning={warning}" if warning else "")
            )
        added, skipped = self.panel._append_imported_records(records)
        self.panel.status_label.setText(tr(self.lang, "import_done", n=added))
        summary = tr(
            self.lang,
            "manual_parse_summary",
            files=len(parsed),
            records=len(records),
            added=added,
            skipped=skipped,
            warnings=warnings,
        )
        if wrong_engine:
            summary += "\n" + tr(self.lang, "manual_wrong_engine")
        self.summary_label.setText(summary)
        self.panel.log(summary)

    def _on_error(self, message: str) -> None:
        self.worker = None
        self._set_busy(False)
        self.summary_label.setText(message)
        QMessageBox.critical(self, APP_NAME, message)

    def reject(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        super().reject()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.worker and self.worker.is_alive():
            event.ignore()
            return
        super().closeEvent(event)


class BrowserSettingsSignals(QObject):
    ready = Signal(object)
    error = Signal(str)
    browser_ready = Signal(object)
    browser_error = Signal(str)
    browser_progress = Signal(int, str)
    suite_ready = Signal(object)
    suite_error = Signal(str)
    portable_update_ready = Signal(object)
    portable_update_error = Signal(str)


class BrowserSettingsDialog(QDialog):
    """Application-wide browser/Selenium settings shared by every collector."""

    def __init__(self, parent: "BFSUWebLensWindow", settings: dict[str, Any], *, auto_setup: bool = False) -> None:
        super().__init__(parent)
        apply_window_icon(self)
        self.window = parent
        self.lang = parent.language
        self._settings = dict(browser_defaults(), **(settings or {}))
        self._worker: threading.Thread | None = None
        self._auto_setup_requested = bool(auto_setup)
        self.signals = BrowserSettingsSignals()
        self.signals.ready.connect(self._driver_ready)
        self.signals.error.connect(self._driver_error)
        self.signals.browser_ready.connect(self._browser_ready)
        self.signals.browser_error.connect(self._browser_error)
        self.signals.browser_progress.connect(self._browser_progress_changed)
        self.signals.suite_ready.connect(self._suite_ready)
        self.signals.suite_error.connect(self._suite_error)
        self.signals.portable_update_ready.connect(self._portable_update_ready)
        self.signals.portable_update_error.connect(self._portable_update_error)
        self.setWindowTitle(tr(self.lang, "browser_settings_title"))
        self.setMinimumWidth(560)
        self._build_ui()
        self._load_settings()
        QTimer.singleShot(0, self._resize_to_content)
        if self._auto_setup_requested:
            QTimer.singleShot(180, self.configure_all_browsers)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.one_click_btn = QPushButton(tr(self.lang, "one_click_setup"))
        self.one_click_btn.setMinimumHeight(34)
        self.one_click_btn.setProperty("accentAction", True)
        self.one_click_btn.clicked.connect(self.configure_all_browsers)
        layout.addWidget(self.one_click_btn)

        self.update_portable_btn = QPushButton(tr(self.lang, "update_portable_environment"))
        self.update_portable_btn.setMinimumHeight(32)
        self.update_portable_btn.clicked.connect(self.update_selected_portable_environment)
        layout.addWidget(self.update_portable_btn)

        form_widget = QWidget(self)
        form_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        grid = QGridLayout(form_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        self.backend_combo = QComboBox()
        set_combo_options(self.backend_combo, FETCH_BACKEND_OPTIONS, self.lang, "selenium_chrome")
        self.backend_combo.currentIndexChanged.connect(self._backend_changed)

        self.source_combo = QComboBox()
        self._populate_source_combo("portable")
        self.source_combo.currentIndexChanged.connect(self._source_changed)

        self.browser_combo = QComboBox()
        self.browser_combo.setEditable(True)
        self.browser_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.browser_combo.setMinimumWidth(340)
        self.detect_btn = QPushButton(tr(self.lang, "browser_refresh"))
        self.download_browser_btn = QPushButton(tr(self.lang, "download_browser_now"))
        self.browse_browser_btn = QPushButton(tr(self.lang, "browse"))
        browser_row = QWidget()
        browser_lay = QHBoxLayout(browser_row); browser_lay.setContentsMargins(0,0,0,0); browser_lay.setSpacing(6)
        browser_lay.addWidget(self.browser_combo, 1); browser_lay.addWidget(self.detect_btn); browser_lay.addWidget(self.download_browser_btn); browser_lay.addWidget(self.browse_browser_btn)

        self.driver_edit = QLineEdit()
        self.driver_btn = QPushButton(tr(self.lang, "driver_manage"))
        self.browse_driver_btn = QPushButton(tr(self.lang, "browse"))
        driver_row = QWidget()
        driver_lay = QHBoxLayout(driver_row); driver_lay.setContentsMargins(0,0,0,0); driver_lay.setSpacing(6)
        driver_lay.addWidget(self.driver_edit, 1); driver_lay.addWidget(self.driver_btn); driver_lay.addWidget(self.browse_driver_btn)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setProperty("muted", True)
        self.browser_progress = QProgressBar()
        self.browser_progress.setRange(0, 100)
        self.browser_progress.setValue(0)
        self.browser_progress.setTextVisible(True)
        self.browser_progress.setVisible(False)
        self.wait_spin = QSpinBox(); self.wait_spin.setRange(0, 9999999); self.wait_spin.setSuffix(" ms")
        self.headless_check = QCheckBox(tr(self.lang, "hide_browser"))

        labels = [
            QLabel(tr(self.lang, "browser_type")),
            QLabel(tr(self.lang, "browser_source")),
            QLabel(tr(self.lang, "browser_detected")),
            QLabel(tr(self.lang, "browser_driver")),
            QLabel(tr(self.lang, "browser_wait")),
        ]
        for label in labels:
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setWordWrap(False)
        grid.addWidget(labels[0], 0, 0); grid.addWidget(self.backend_combo, 0, 1)
        grid.addWidget(labels[1], 1, 0); grid.addWidget(self.source_combo, 1, 1)
        grid.addWidget(labels[2], 2, 0); grid.addWidget(browser_row, 2, 1)
        grid.addWidget(labels[3], 3, 0); grid.addWidget(driver_row, 3, 1)
        grid.addWidget(labels[4], 4, 0); grid.addWidget(self.wait_spin, 4, 1)
        grid.addWidget(QLabel(""), 5, 0); grid.addWidget(self.headless_check, 5, 1)
        layout.addWidget(form_widget, 0)

        # Status/progress live outside the form grid so long diagnostic text can
        # never steal row height from the controls below it or overlap them at
        # high Windows DPI settings.
        self.status_panel = QFrame(self)
        self.status_panel.setObjectName("browserStatusPanel")
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(6)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.browser_progress)
        layout.addWidget(self.status_panel, 0)

        self.detect_btn.clicked.connect(lambda: self.refresh_installations(silent=False))
        self.download_browser_btn.clicked.connect(self.download_recommended_browser)
        self.browse_browser_btn.clicked.connect(self.browse_browser)
        self.driver_btn.clicked.connect(self.prepare_driver)
        self.browse_driver_btn.clicked.connect(self.browse_driver)
        self.browser_combo.currentIndexChanged.connect(self.update_status)
        if self.browser_combo.lineEdit() is not None:
            self.browser_combo.lineEdit().editingFinished.connect(self._validate_typed_browser)
        self.driver_edit.editingFinished.connect(self._validate_typed_driver)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _resize_to_content(self) -> None:
        # Recompute the word-wrapped status height before asking Qt for the
        # natural dialog size. This prevents status text from overlapping the
        # following controls at 150%–250% Windows scaling.
        if hasattr(self, "status_label"):
            width = max(420, self.width() - 80)
            fm_height = self.status_label.heightForWidth(width) if self.status_label.wordWrap() else -1
            self.status_label.setMinimumHeight(max(24, fm_height if fm_height > 0 else self.status_label.sizeHint().height()))
        self.layout().activate()
        natural_height = max(300, self.sizeHint().height())
        fit_dialog_to_screen(self, 1040, natural_height)

    def _load_settings(self) -> None:
        backend = str(self._settings.get("fetch_backend", "selenium_chrome"))
        set_combo_options(self.backend_combo, FETCH_BACKEND_OPTIONS, self.lang, backend)
        legacy_source = browser_source_key(self._settings.get("browser_source", default_browser_source_for_backend(backend)))
        self._source_preferences = {
            "selenium_chrome": browser_source_key(self._settings.get("browser_source_chrome", legacy_source if backend == "selenium_chrome" else "portable")),
            # Edge intentionally defaults to the system-installed browser.
            "selenium_edge": "system",
        }
        self._populate_source_combo(self._source_preferences.get(self.backend(), default_browser_source_for_backend(self.backend())))
        self.driver_edit.setText(str(self._settings.get("browser_driver_path", "")))
        self.wait_spin.setValue(int(self._settings.get("browser_wait_ms", 5000)))
        self.headless_check.setChecked(bool(self._settings.get("browser_headless", False)))
        self.refresh_installations(preferred_path=str(self._settings.get("browser_binary_path", "")), silent=True)
        self._update_browser_source_controls()
        QTimer.singleShot(0, self._resize_to_content)

    def backend(self) -> str:
        return combo_key(self.backend_combo, "selenium_chrome")

    def _populate_source_combo(self, source: str | None = None) -> None:
        backend = self.backend()
        wanted = browser_source_key(source or default_browser_source_for_backend(backend))
        if backend == "selenium_edge":
            # Microsoft Edge is a Windows component and Microsoft does not
            # publish an official portable ZIP comparable to Chrome for Testing.
            # Keep the normal/default Edge path simple and unambiguous.
            wanted = "system"
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        if backend == "selenium_edge":
            self.source_combo.addItem(tr(self.lang, "browser_source_edge_system"), "system")
            self.source_combo.setCurrentIndex(0)
        else:
            self.source_combo.addItem(tr(self.lang, "browser_source_portable"), "portable")
            self.source_combo.addItem(tr(self.lang, "browser_source_system"), "system")
            self.source_combo.setCurrentIndex(1 if wanted == "system" else 0)
        self.source_combo.blockSignals(False)
        self._source_preferences = getattr(self, "_source_preferences", {})
        self._source_preferences[backend] = wanted
        self._update_browser_source_controls()

    def browser_source(self) -> str:
        if self.backend() == "selenium_edge":
            return "system"
        return browser_source_key(self.source_combo.currentData())

    def _update_browser_source_controls(self) -> None:
        if not hasattr(self, "source_combo"):
            return
        backend = self.backend()
        source = self.browser_source()
        if backend == "selenium_edge":
            self.source_combo.setEnabled(False)
            self.source_combo.setToolTip(tr(self.lang, "browser_source_edge_system_note"))
            if hasattr(self, "download_browser_btn"):
                self.download_browser_btn.setText(tr(self.lang, "detect_system_edge"))
            if hasattr(self, "update_portable_btn"):
                self.update_portable_btn.setEnabled(False)
        else:
            if not (self._worker and self._worker.is_alive()):
                self.source_combo.setEnabled(True)
            self.source_combo.setToolTip(tr(self.lang, "browser_source_system_note") if source == "system" else tr(self.lang, "browser_source_portable_note"))
            if hasattr(self, "download_browser_btn"):
                self.download_browser_btn.setText(tr(self.lang, "download_browser_now"))
            if hasattr(self, "update_portable_btn"):
                self.update_portable_btn.setEnabled(source == "portable" and not (self._worker and self._worker.is_alive()))

    def selected_browser_path(self) -> str:
        idx = self.browser_combo.currentIndex()
        text = self.browser_combo.currentText().strip()
        if idx >= 0 and text == self.browser_combo.itemText(idx):
            data = self.browser_combo.itemData(idx)
            if data:
                return str(data).strip()
        return text

    def refresh_installations(self, checked: bool = False, preferred_path: str = "", silent: bool = False) -> None:
        del checked
        backend = self.backend()
        current = preferred_path or self.selected_browser_path()
        current_inst = installation_for_path(current, backend) if current else None
        source = self.browser_source()
        if current_inst and ((source == "portable" and current_inst.channel != "portable") or (source == "system" and current_inst.channel == "portable")):
            current_inst = None
            current = ""
        if current and (not current_inst or not current_inst.version):
            current = ""
        installs = browser_installations_for_source(backend, source=source, app_root=app_base_dir())
        self.browser_combo.blockSignals(True)
        self.browser_combo.clear()
        chosen = -1
        for i, inst in enumerate(installs):
            label = f"{inst.name} {inst.version or '?'}  —  {inst.path}"
            self.browser_combo.addItem(label, inst.path)
            if current and os.path.normcase(os.path.abspath(inst.path)) == os.path.normcase(os.path.abspath(current)):
                chosen = i
        if chosen >= 0:
            self.browser_combo.setCurrentIndex(chosen)
        elif current_inst and current_inst.version:
            label = f"{current_inst.name} {current_inst.version}  —  {current_inst.path}"
            self.browser_combo.addItem(label, current_inst.path)
            self.browser_combo.setCurrentIndex(self.browser_combo.count() - 1)
        elif installs:
            self.browser_combo.setCurrentIndex(0)
        else:
            self.browser_combo.setEditText("")
        self.browser_combo.blockSignals(False)
        self.update_status()
        if not installs and not silent:
            self._show_no_browser_recommendation()

    def _offer_recommendation_if_missing(self) -> None:
        if not browser_installations_for_source(self.backend(), source=self.browser_source(), app_root=app_base_dir()):
            self._show_no_browser_recommendation()

    def _show_no_browser_recommendation(self) -> None:
        backend = self.backend()
        browser = "Edge" if backend == "selenium_edge" else "Chrome"
        recommendation = latest_browser_recommendation(backend, timeout=6)
        version_text = recommendation.browser_version or "latest"
        recommendation_key = "browser_recommendation_edge" if backend == "selenium_edge" else "browser_recommendation"
        detail = tr(self.lang, "browser_not_found", browser=browser) + "\n\n" + tr(self.lang, recommendation_key)
        if self.browser_source() == "system":
            detail += "\n\n" + tr(self.lang, "browser_source_edge_system_note" if backend == "selenium_edge" else "browser_source_system_note")
        if recommendation.browser_version:
            detail += f"\n\n{recommendation.browser_name}: {version_text}"
        if recommendation.driver_version:
            detail += f"\nWebDriver: {recommendation.driver_version}"
        actions = [("setup_all", tr(self.lang, "one_click_setup")),
                   ("browser", tr(self.lang, "open_browser_page") if backend == "selenium_edge" else tr(self.lang, "download_recommended_browser")),
                   ("driver", tr(self.lang, "download_recommended_driver"))]
        if backend != "selenium_edge":
            actions.append(("official", tr(self.lang, "open_browser_page")))
        choice = exec_action_dialog(
            self,
            APP_NAME,
            detail,
            actions,
            close_text=tr(self.lang, "close"),
        )
        if choice == "setup_all":
            self.configure_all_browsers()
        elif choice == "browser":
            if backend == "selenium_edge":
                webbrowser.open(recommendation.official_browser_url or official_browser_url(backend))
            else:
                self.download_recommended_browser()
        elif choice == "driver":
            webbrowser.open(recommendation.driver_download_url or recommendation.official_driver_url or official_driver_url(backend))
        elif choice == "official":
            webbrowser.open(recommendation.official_browser_url or official_browser_url(backend))

    def _backend_changed(self, *_args) -> None:
        backend = self.backend()
        source = getattr(self, "_source_preferences", {}).get(backend, default_browser_source_for_backend(backend))
        if backend == "selenium_edge":
            source = "system"
        self._populate_source_combo(source)
        self.driver_edit.clear()
        self.refresh_installations(
            preferred_path=preferred_browser_path(backend, app_root=app_base_dir(), source=source),
            silent=True,
        )
        self._update_browser_source_controls()
        QTimer.singleShot(0, self._resize_to_content)

    def _source_changed(self, *_args) -> None:
        source = self.browser_source()
        self._source_preferences = getattr(self, "_source_preferences", {})
        self._source_preferences[self.backend()] = source
        self.driver_edit.clear()
        self.refresh_installations(
            preferred_path=preferred_browser_path(self.backend(), app_root=app_base_dir(), source=source),
            silent=True,
        )
        self._update_browser_source_controls()
        if self.backend() == "selenium_edge":
            self.status_label.setText(tr(self.lang, "browser_source_edge_system_note"))
        elif source == "system":
            self.status_label.setText(tr(self.lang, "browser_source_system_note"))
        QTimer.singleShot(0, self._resize_to_content)

    def _set_browser_download_busy(self, busy: bool) -> None:
        for widget in (self.one_click_btn, self.update_portable_btn, self.backend_combo, self.source_combo, self.browser_combo, self.detect_btn, self.download_browser_btn, self.browse_browser_btn, self.driver_btn, self.browse_driver_btn):
            widget.setEnabled(not busy)
        if not busy:
            self._update_browser_source_controls()
        self.browser_progress.setVisible(bool(busy) or self.browser_progress.value() >= 100)
        QTimer.singleShot(0, self._resize_to_content)

    def _browser_progress_changed(self, value: int, message: str = "") -> None:
        value = max(0, min(100, int(value)))
        self.browser_progress.setVisible(True)
        self.browser_progress.setValue(value)
        if message:
            self.status_label.setText(message)
        elif value < 5:
            self.status_label.setText(tr(self.lang, "portable_browser_resolving"))
        elif value < 78:
            self.status_label.setText(tr(self.lang, "portable_browser_downloading"))
        elif value < 92:
            self.status_label.setText(tr(self.lang, "portable_browser_extracting"))
        elif value < 100:
            self.status_label.setText(tr(self.lang, "portable_browser_detecting"))

    def _validate_browser_path(self, path: str, *, show_message: bool = False) -> Any:
        path = str(path or "").strip().strip('"')
        if not path:
            return None
        inst = installation_for_path(path, self.backend())
        if inst and inst.version:
            return inst
        if show_message:
            browser = "Edge" if self.backend() == "selenium_edge" else "Chrome"
            QMessageBox.warning(self, APP_NAME, tr(self.lang, "manual_browser_invalid", browser=browser))
        return None

    def _validate_driver_path(self, path: str, *, show_message: bool = False) -> bool:
        path = str(path or "").strip().strip('"')
        if not path:
            return False
        inst = self._validate_browser_path(self.selected_browser_path(), show_message=show_message)
        if not inst:
            return False
        expected_name = driver_executable_name(self.backend()).lower()
        selected_name = Path(path).name.lower()
        # Reject the other browser family's driver even when build numbers
        # happen to coincide. Renamed custom driver binaries are still allowed
        # unless they are unmistakably the opposite family.
        if (expected_name.startswith("chromedriver") and "msedgedriver" in selected_name) or (expected_name.startswith("msedgedriver") and "chromedriver" in selected_name):
            if show_message:
                QMessageBox.warning(self, APP_NAME, tr(self.lang, "manual_driver_unknown"))
            return False
        dv = driver_version(path) if Path(path).exists() else ""
        if not dv:
            if show_message:
                QMessageBox.warning(self, APP_NAME, tr(self.lang, "manual_driver_unknown"))
            return False
        if not versions_compatible(inst.version, dv, self.backend()):
            if show_message:
                QMessageBox.warning(self, APP_NAME, tr(self.lang, "manual_driver_invalid", driver=dv, browser=inst.version))
            return False
        return True

    def _validate_typed_browser(self) -> None:
        path = self.selected_browser_path()
        if not path:
            return
        inst = self._validate_browser_path(path, show_message=True)
        if inst:
            source = "system" if self.backend() == "selenium_edge" else ("portable" if inst.channel == "portable" or "/tools/" in str(inst.path).replace("\\", "/").lower() else "system")
            self._populate_source_combo(source)
            self.refresh_installations(preferred_path=inst.path, silent=True)
            if source == "system":
                self.status_label.setText(tr(self.lang, "browser_source_edge_system_note" if self.backend() == "selenium_edge" else "browser_source_system_note"))
        else:
            self.refresh_installations(preferred_path="", silent=True)

    def _validate_typed_driver(self) -> None:
        path = self.driver_edit.text().strip()
        if not path:
            self.update_status()
            return
        if not self._validate_driver_path(path, show_message=True):
            self.driver_edit.clear()
        self.update_status()

    def configure_all_browsers(self) -> None:
        """One-click preparation of usable Chrome and Edge environments.

        Recommended policy is backend-specific: Chrome uses a WebLens-managed
        portable Chrome for Testing build, while Edge uses the system-installed
        Microsoft Edge browser. Matching WebDrivers are prepared for both.
        """
        if self._worker and self._worker.is_alive():
            return
        self.browser_progress.setRange(0, 100)
        self.browser_progress.setValue(0)
        self.browser_progress.setVisible(True)
        self._set_browser_download_busy(True)
        self.status_label.setText(tr(self.lang, "setup_all_start"))
        current_backend = self.backend()
        recommended_sources = {"selenium_chrome": "portable", "selenium_edge": "system"}

        def emit(value: int, message: str) -> None:
            self.signals.browser_progress.emit(max(0, min(100, int(value))), str(message))

        def worker() -> None:
            configured: dict[str, dict[str, str]] = {}
            failures: dict[str, str] = {}
            try:
                for index, (backend, browser_name) in enumerate((("selenium_chrome", "Chrome"), ("selenium_edge", "Edge"))):
                    base = index * 50
                    source = recommended_sources[backend]
                    emit(base + 1, f"{browser_name}: checking {source} browser source…")
                    browser_path = preferred_browser_path(backend, app_root=app_base_dir(), source=source)
                    inst = installation_for_path(browser_path, backend) if browser_path else None
                    if not inst or not inst.version:
                        if source == "portable" and backend == "selenium_chrome":
                            try:
                                browser_result = download_portable_browser(
                                    backend, app_root=app_base_dir(), timeout=180,
                                    progress=lambda value, message, b=base, n=browser_name: emit(b + 2 + int(value * 0.18), f"{n}: {message}"),
                                )
                                browser_path = browser_result.browser_path
                                inst = installation_for_path(browser_path, backend)
                            except Exception as exc:
                                failures[browser_name] = f"Browser preparation failed: {exc}"
                                emit(base + 48, f"{browser_name}: browser preparation failed.")
                                continue
                        else:
                            failures[browser_name] = tr(self.lang, "browser_not_found", browser=browser_name)
                            emit(base + 48, f"{browser_name}: no system-installed browser was found.")
                            continue
                    if not inst or not inst.version:
                        failures[browser_name] = tr(self.lang, "browser_version_unreadable")
                        emit(base + 48, f"{browser_name}: browser version detection failed.")
                        continue

                    emit(base + 21, f"{browser_name} {inst.version}: checking WebDriver…")
                    prep = ensure_driver(
                        backend, inst.path, explicit_driver_path="", app_root=app_base_dir(),
                        allow_download=True, timeout=120,
                        progress=lambda value, message, b=base, n=browser_name: emit(b + 21 + int(value * 0.27), f"{n}: {message}"),
                    )
                    if prep.compatible and prep.driver_path:
                        configured[backend] = {
                            "browser_path": prep.browser_path or inst.path,
                            "browser_version": prep.browser_version or inst.version,
                            "driver_path": prep.driver_path,
                            "driver_version": prep.driver_version,
                        }
                        emit(base + 49, f"{browser_name}: browser and WebDriver are ready.")
                    else:
                        failures[browser_name] = prep.message or tr(self.lang, "driver_prepare_failed_generic")
                        emit(base + 49, f"{browser_name}: WebDriver preparation failed.")
                emit(100, tr(self.lang, "setup_all_done") if not failures else tr(self.lang, "setup_all_partial"))
                self.signals.suite_ready.emit({
                    "configured": configured,
                    "failures": failures,
                    "current_backend": current_backend,
                    "browser_sources": recommended_sources,
                })
            except Exception as exc:
                self.signals.suite_error.emit(str(exc))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _suite_ready(self, payload: Any) -> None:
        self._set_browser_download_busy(False)
        data = payload if isinstance(payload, dict) else {}
        configured = data.get("configured") if isinstance(data.get("configured"), dict) else {}
        failures = data.get("failures") if isinstance(data.get("failures"), dict) else {}
        target_backend = self.backend()
        configured_sources = data.get("browser_sources") if isinstance(data.get("browser_sources"), dict) else {"selenium_chrome": "portable", "selenium_edge": "system"}
        self._source_preferences = getattr(self, "_source_preferences", {})
        self._source_preferences.update({k: browser_source_key(v) for k, v in configured_sources.items()})
        if target_backend not in configured:
            if "selenium_chrome" in configured:
                target_backend = "selenium_chrome"
            elif "selenium_edge" in configured:
                target_backend = "selenium_edge"
        set_combo_options(self.backend_combo, FETCH_BACKEND_OPTIONS, self.lang, target_backend)
        self._populate_source_combo(self._source_preferences.get(target_backend, default_browser_source_for_backend(target_backend)))
        selected = configured.get(target_backend) or {}
        if selected:
            self.refresh_installations(preferred_path=str(selected.get("browser_path", "")), silent=True)
            self.driver_edit.setText(str(selected.get("driver_path", "")))
            self.update_status()
        self.browser_progress.setValue(100)
        self.browser_progress.setVisible(True)

        success_lines = []
        for be, label in (("selenium_chrome", "Chrome"), ("selenium_edge", "Edge")):
            item = configured.get(be) or {}
            if item:
                success_lines.append(f"{label}: browser {item.get('browser_version', '?')} / WebDriver {item.get('driver_version', '?')} — ready")
        failure_lines = [f"{name}: {reason}" for name, reason in failures.items()]
        summary = "\n".join(success_lines + failure_lines) or tr(self.lang, "setup_all_partial")
        if failures:
            self.status_label.setText(tr(self.lang, "setup_all_partial"))
            QMessageBox.warning(self, APP_NAME, tr(self.lang, "setup_all_partial") + "\n\n" + summary)
        else:
            self.status_label.setText(tr(self.lang, "setup_all_done"))
            QMessageBox.information(self, APP_NAME, tr(self.lang, "setup_all_done") + "\n\n" + summary)
        if self._auto_setup_requested and selected:
            # The startup one-click path should finish by persisting the first
            # usable recommended environment instead of requiring a second
            # manual OK click in the settings dialog.
            self._auto_setup_requested = False
            QTimer.singleShot(0, self.accept)
            return
        QTimer.singleShot(0, self._resize_to_content)

    def _suite_error(self, message: str) -> None:
        self._set_browser_download_busy(False)
        self.browser_progress.setVisible(False)
        self.status_label.setText(message)
        QMessageBox.warning(self, APP_NAME, tr(self.lang, "setup_all_partial") + "\n\n" + message)

    def update_selected_portable_environment(self) -> None:
        """Update the selected WebLens-managed portable environment on demand."""
        if self._worker and self._worker.is_alive():
            return
        if self.browser_source() != "portable":
            QMessageBox.information(self, APP_NAME, tr(self.lang, "portable_update_system_disabled"))
            return
        backend = self.backend()
        self.browser_progress.setRange(0, 100)
        self.browser_progress.setValue(0)
        self.browser_progress.setVisible(True)
        self._set_browser_download_busy(True)
        self.status_label.setText(tr(self.lang, "portable_update_running"))

        def worker() -> None:
            try:
                result = update_portable_environment(
                    backend,
                    app_root=app_base_dir(),
                    timeout=180,
                    progress=lambda value, message: self.signals.browser_progress.emit(
                        int(value), f"{tr(self.lang, 'portable_update_running')} {int(value)}%"
                    ),
                )
                self.signals.portable_update_ready.emit(result)
            except Exception as exc:
                self.signals.portable_update_error.emit(str(exc))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _portable_update_ready(self, result: Any) -> None:
        self._set_browser_download_busy(False)
        self._populate_source_combo("portable")
        path = str(getattr(result, "browser_path", "") or "")
        driver_path = str(getattr(result, "driver_path", "") or "")
        browser_version = str(getattr(result, "browser_version", "") or "?")
        driver_version_text = str(getattr(result, "driver_version", "") or "?")
        latest_browser_version = str(getattr(result, "latest_browser_version", "") or "?")
        if path:
            self.refresh_installations(preferred_path=path, silent=True)
        if driver_path:
            self.driver_edit.setText(driver_path)
        self.browser_progress.setValue(100)
        self.browser_progress.setVisible(True)

        if getattr(result, "fully_latest", False):
            message = tr(
                self.lang,
                "portable_update_done",
                browser=browser_version,
                driver=driver_version_text,
            )
            self.status_label.setText(message)
            QMessageBox.information(self, APP_NAME, message)
        else:
            message = tr(
                self.lang,
                "portable_update_edge_partial",
                browser=browser_version,
                driver=driver_version_text,
                latest=latest_browser_version,
            )
            self.status_label.setText(message)
            QMessageBox.warning(self, APP_NAME, message)
        self.update_status()
        QTimer.singleShot(0, self._resize_to_content)

    def _portable_update_error(self, message: str) -> None:
        self._set_browser_download_busy(False)
        self.browser_progress.setVisible(False)
        text = tr(self.lang, "portable_update_failed", message=message)
        self.status_label.setText(text)
        QMessageBox.warning(self, APP_NAME, text)
        QTimer.singleShot(0, self._resize_to_content)

    def download_recommended_browser(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        backend = self.backend()
        if backend == "selenium_edge":
            # Edge defaults to the Windows/system installation. This button is
            # therefore a detect/configure action, not a portable download.
            self._populate_source_combo("system")
            self.refresh_installations(
                preferred_path=preferred_browser_path(backend, app_root=app_base_dir(), source="system"),
                silent=True,
            )
            if self.selected_browser_path():
                self.status_label.setText(tr(self.lang, "edge_system_ready"))
                self.update_status()
            else:
                self._show_no_browser_recommendation()
            QTimer.singleShot(0, self._resize_to_content)
            return
        # Chrome uses the WebLens-managed portable Chrome for Testing build.
        self._populate_source_combo("portable")
        self.browser_progress.setValue(0)
        self.browser_progress.setVisible(True)
        self._set_browser_download_busy(True)
        self.status_label.setText(tr(self.lang, "portable_browser_resolving"))

        def worker() -> None:
            try:
                result = download_portable_browser(
                    backend,
                    app_root=app_base_dir(),
                    timeout=180,
                    progress=lambda value, message: self.signals.browser_progress.emit(int(value), str(message)),
                )
                self.signals.browser_ready.emit(result)
            except Exception as exc:
                self.signals.browser_error.emit(str(exc))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _browser_ready(self, result: Any) -> None:
        self._set_browser_download_busy(False)
        path = str(getattr(result, "browser_path", "") or "")
        version = str(getattr(result, "browser_version", "") or "?")
        if path:
            self.refresh_installations(preferred_path=path, silent=True)
            self.browser_progress.setValue(100)
            self.browser_progress.setVisible(True)
            self.status_label.setText(tr(self.lang, "portable_browser_ready", version=version))
            # Re-run the existing driver detection against the *actual* version
            # of the newly selected portable browser. No driver download is
            # triggered here; the established driver workflow remains intact.
            QTimer.singleShot(0, self.update_status)
        else:
            self.browser_progress.setVisible(False)
            self.status_label.setText(tr(self.lang, "portable_browser_failed", message="No browser executable was returned."))
        QTimer.singleShot(0, self._resize_to_content)

    def _browser_error(self, message: str) -> None:
        self._set_browser_download_busy(False)
        self.browser_progress.setVisible(False)
        self.status_label.setText(tr(self.lang, "portable_browser_failed", message=message))
        QTimer.singleShot(0, self._resize_to_content)

    def update_status(self, *_args) -> None:
        QTimer.singleShot(0, self._resize_to_content)
        backend = self.backend()
        browser_path = self.selected_browser_path()
        inst = installation_for_path(browser_path, backend) if browser_path else None
        drv = self.driver_edit.text().strip()
        if inst and drv and Path(drv).exists():
            try:
                dv = driver_version(drv)
                if dv and versions_compatible(inst.version, dv, backend):
                    self.status_label.setText(tr(self.lang, "driver_ready", version=dv))
                    return
            except Exception:
                pass
        if inst and inst.version:
            # Automatically discover an already-compatible driver from WebLens'
            # cache, Selenium Manager cache or PATH. This is detection only; it
            # performs no network access.
            cached_path, cached_version = find_compatible_driver(
                backend, inst.version,
                candidates=[drv] if drv else (),
                app_root=app_base_dir(),
            )
            if cached_path:
                if cached_path != drv:
                    self.driver_edit.setText(cached_path)
                self.status_label.setText(tr(self.lang, "driver_ready", version=cached_version or "?"))
                return
            if drv:
                self.driver_edit.clear()
            self.status_label.setText(f"{inst.name} {inst.version or '?'} · {tr(self.lang, 'driver_missing')}")
        else:
            if drv:
                self.driver_edit.clear()
            self.status_label.setText(tr(self.lang, "driver_missing"))

    def browse_browser(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr(self.lang, "browser_binary"), self.selected_browser_path() or str(Path.home()), "All files (*)")
        if not path:
            return
        inst = self._validate_browser_path(path, show_message=True)
        if inst:
            # Manual browsing remains supported. Paths under WebLens tools are
            # treated as portable; all other manually selected browsers opt in
            # to the not-recommended system/custom source.
            source = "system" if self.backend() == "selenium_edge" else ("portable" if inst.channel == "portable" or "/tools/" in str(inst.path).replace("\\", "/").lower() else "system")
            self._populate_source_combo(source)
            self.refresh_installations(preferred_path=inst.path, silent=True)
            if source == "system":
                self.status_label.setText(tr(self.lang, "browser_source_edge_system_note" if self.backend() == "selenium_edge" else "browser_source_system_note"))

    def browse_driver(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr(self.lang, "driver_path"), self.driver_edit.text() or str(Path.home()), "All files (*)")
        if not path:
            return
        if self._validate_driver_path(path, show_message=True):
            self.driver_edit.setText(path)
            self.update_status()

    def prepare_driver(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        backend = self.backend()
        browser_path = self.selected_browser_path()
        explicit = self.driver_edit.text().strip()
        inst = self._validate_browser_path(browser_path, show_message=True) if browser_path else None
        if not inst:
            self._show_no_browser_recommendation()
            return
        if explicit and not self._validate_driver_path(explicit, show_message=False):
            # An incompatible manually-entered path must never be carried into
            # automatic preparation. Let the manager find/download the correct one.
            explicit = ""
            self.driver_edit.clear()
        self.browser_progress.setRange(0, 100)
        self.browser_progress.setValue(0)
        self.browser_progress.setVisible(True)
        self._set_browser_download_busy(True)
        self.status_label.setText(tr(self.lang, "driver_downloading"))

        def worker() -> None:
            try:
                result = ensure_driver(
                    backend, inst.path, explicit_driver_path=explicit, app_root=app_base_dir(),
                    allow_download=True, timeout=120,
                    progress=lambda value, message: self.signals.browser_progress.emit(int(value), f"{tr(self.lang, 'driver_downloading')} {int(value)}%"),
                )
                self.signals.ready.emit(result)
            except Exception as exc:
                self.signals.error.emit(str(exc))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _driver_ready(self, result: Any) -> None:
        self._set_browser_download_busy(False)
        if getattr(result, "browser_path", ""):
            self.refresh_installations(preferred_path=str(result.browser_path), silent=True)
        if getattr(result, "compatible", False) and getattr(result, "driver_path", ""):
            self.driver_edit.setText(str(result.driver_path))
            self.browser_progress.setValue(100)
            self.browser_progress.setVisible(True)
            self.status_label.setText(tr(self.lang, "driver_ready", version=str(result.driver_version or "?")))
            QTimer.singleShot(0, self._resize_to_content)
            return
        detail = str(getattr(result, "message", "") or tr(self.lang, "driver_missing"))
        self.browser_progress.setVisible(False)
        self.status_label.setText(detail)
        self.window.show_driver_help(detail, backend=self.backend(), parent=self)

    def _driver_error(self, message: str) -> None:
        self._set_browser_download_busy(False)
        self.browser_progress.setVisible(False)
        self.status_label.setText(message)
        self.window.show_driver_help(message, backend=self.backend(), parent=self)

    def accept(self) -> None:
        """Never persist an invalid browser/WebDriver pair."""
        browser_path = self.selected_browser_path()
        inst = self._validate_browser_path(browser_path, show_message=True) if browser_path else None
        if not inst:
            return
        driver_path = self.driver_edit.text().strip()
        if not driver_path or not self._validate_driver_path(driver_path, show_message=True):
            return
        super().accept()

    def values(self) -> dict[str, Any]:
        source_prefs = getattr(self, "_source_preferences", {})
        source_prefs[self.backend()] = self.browser_source()
        return {
            "fetch_backend": self.backend(),
            "browser_source": self.browser_source(),
            "browser_source_chrome": browser_source_key(source_prefs.get("selenium_chrome", "portable")),
            "browser_source_edge": "system",
            "browser_binary_path": self.selected_browser_path(),
            "browser_driver_path": self.driver_edit.text().strip(),
            "browser_wait_ms": self.wait_spin.value(),
            "browser_headless": self.headless_check.isChecked(),
        }


class BFSUWebLensWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        apply_window_icon(self)
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self._configure_window_geometry()
        self.settings_path = app_base_dir() / "weblens_settings.json"
        loaded = self._load_settings()
        self.language = str(loaded.get("ui_lang", "en"))
        self.browser_settings = dict(browser_defaults(), **(loaded.get("browser") or {}))
        self._create_status_bar()

        central = QWidget()
        central.setObjectName("centralRoot")
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(8)

        self.environment_banner = QFrame()
        self.environment_banner.setObjectName("environmentBanner")
        banner_layout = QHBoxLayout(self.environment_banner)
        banner_layout.setContentsMargins(10, 7, 10, 7)
        self.environment_label = QLabel()
        self.environment_label.setWordWrap(True)
        self.environment_one_click_btn = QPushButton()
        self.environment_one_click_btn.setProperty("accentAction", True)
        self.environment_one_click_btn.clicked.connect(lambda: self.open_browser_settings(auto_setup=True))
        self.environment_config_btn = QPushButton()
        self.environment_config_btn.clicked.connect(lambda: self.open_browser_settings(auto_setup=False))
        banner_layout.addWidget(self.environment_label, 1)
        banner_layout.addWidget(self.environment_one_click_btn)
        banner_layout.addWidget(self.environment_config_btn)
        central_layout.addWidget(self.environment_banner)

        selector = QFrame()
        selector.setObjectName("engineSelector")
        selector_layout = QHBoxLayout(selector)
        selector_layout.setContentsMargins(4, 4, 4, 4)
        selector_layout.setSpacing(0)
        selector_layout.addStretch(1)
        self.engine_selector_label = QLabel()
        self.engine_selector_label.setProperty("muted", True)
        selector_layout.addWidget(self.engine_selector_label)
        selector_layout.addSpacing(10)
        self.engine_group = QButtonGroup(self)
        self.engine_group.setExclusive(True)
        self.google_engine_btn = QPushButton()
        self.baidu_engine_btn = QPushButton()
        for idx, btn in enumerate((self.google_engine_btn, self.baidu_engine_btn)):
            btn.setCheckable(True)
            btn.setProperty("engineSelector", True)
            btn.setProperty("enginePosition", "first" if idx == 0 else "last")
            self.engine_group.addButton(btn, idx)
            selector_layout.addWidget(btn)
        selector_layout.addStretch(1)
        central_layout.addWidget(selector)

        self.engine_stack = QStackedWidget()
        self.google_panel = CollectorPanel(self, "google", loaded.get("google", {}))
        self.baidu_panel = CollectorPanel(self, "baidu", loaded.get("baidu", {}))
        self.engine_stack.addWidget(self.google_panel)
        self.engine_stack.addWidget(self.baidu_panel)
        central_layout.addWidget(self.engine_stack, 1)
        self.setCentralWidget(central)
        self.google_engine_btn.setChecked(True)
        self.engine_group.idClicked.connect(self._switch_engine)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self.retranslate_ui()
        self.refresh_browser_environment_state()
        self.sync_action_states()
        QTimer.singleShot(0, self._apply_initial_panel_sizes)

    def _create_status_bar(self) -> None:
        bar = self.statusBar()
        bar.setSizeGripEnabled(True)
        self.task_status_label = QLabel()
        self.task_status_label.setProperty("muted", True)
        self.task_status_label.setMinimumWidth(120)
        self.task_progress = QProgressBar()
        self.task_progress.setRange(0, 100)
        self.task_progress.setValue(0)
        self.task_progress.setTextVisible(True)
        self.task_progress.setMinimumWidth(170)
        self.task_progress.setMaximumWidth(260)
        bar.addWidget(self.task_status_label, 1)
        bar.addPermanentWidget(self.task_progress)
        self.task_status_label.setText(tr(self.language, "ready"))

    def _configure_window_geometry(self) -> None:
        """Size the window in Qt logical pixels so it remains usable at high DPI."""
        screen = QApplication.primaryScreen()
        if screen is None:
            self.setMinimumSize(840, 560)
            self.resize(1460, 880)
            return
        available = screen.availableGeometry()
        aw, ah = max(1, available.width()), max(1, available.height())
        minimum_w = min(aw, min(980, max(760, int(aw * 0.72))))
        minimum_h = min(ah, min(650, max(480, int(ah * 0.72))))
        target_w = min(1600, max(860, int(aw * 0.92)))
        target_h = min(980, max(560, int(ah * 0.90)))
        target_w = min(target_w, aw)
        target_h = min(target_h, ah)
        self.setMinimumSize(minimum_w, minimum_h)
        self.resize(target_w, target_h)
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def _apply_initial_panel_sizes(self) -> None:
        usable = max(760, self.engine_stack.width() - 24)
        self.google_panel.set_initial_sidebar_width(usable)
        self.baidu_panel.set_initial_sidebar_width(usable)

    def active_panel(self) -> CollectorPanel:
        return self.google_panel if self.engine_stack.currentIndex() == 0 else self.baidu_panel

    def _switch_engine(self, index: int) -> None:
        self.engine_stack.setCurrentIndex(0 if int(index) == 0 else 1)
        self.sync_action_states()

    def _resolve_browser_environment(self, *, save: bool = False) -> bool:
        """Resolve browser + matching driver against the current machine.

        Chrome prefers a WebLens-managed portable browser. Edge uses the
        system-installed Microsoft Edge browser by default because Microsoft
        does not publish an equivalent portable Edge ZIP. Browser and WebDriver
        versions are checked every
        time this method runs, so an internal portable browser never starts
        collection with a stale driver saved for another browser version.
        """
        backend = str(self.browser_settings.get("fetch_backend", "selenium_chrome"))
        if backend == "selenium_edge":
            source = "system"
        else:
            source = browser_source_key(self.browser_settings.get("browser_source_chrome", self.browser_settings.get("browser_source", "portable")))
        browser_path = str(self.browser_settings.get("browser_binary_path", "")).strip()
        inst = installation_for_path(browser_path, backend) if browser_path else None
        if inst and ((source == "portable" and inst.channel != "portable") or (source == "system" and inst.channel == "portable")):
            inst = None
        if not inst or not inst.version:
            preferred = preferred_browser_path(backend, app_root=app_base_dir(), source=source)
            inst = installation_for_path(preferred, backend) if preferred else None
            if not inst or not inst.version:
                return False
            if browser_path != inst.path:
                self.browser_settings["browser_binary_path"] = inst.path
                browser_path = inst.path

        driver_path = str(self.browser_settings.get("browser_driver_path", "")).strip()
        if driver_path and Path(driver_path).exists():
            try:
                if versions_compatible(inst.version, driver_version(driver_path), backend):
                    if save:
                        self.save_settings()
                    return True
            except Exception:
                pass

        # Re-resolve a compatible cached driver for the actual selected browser
        # version. This is detection only and performs no network download.
        cached_path, _cached_version = find_compatible_driver(
            backend,
            inst.version,
            candidates=[driver_path] if driver_path else (),
            app_root=app_base_dir(),
        )
        if cached_path:
            self.browser_settings["browser_driver_path"] = cached_path
            if save:
                self.save_settings()
            return True

        # Never retain a known-incompatible driver beside a newly discovered
        # portable browser. The existing Driver management button will prepare
        # the correct version when the user opens Browser & Selenium settings.
        if driver_path:
            self.browser_settings["browser_driver_path"] = ""
            if save:
                self.save_settings()
        return False

    def browser_environment_ready(self) -> bool:
        return self._resolve_browser_environment(save=False)

    def preflight_browser_environment(self) -> bool:
        """Mandatory browser/driver compatibility check immediately before crawl."""
        return self._resolve_browser_environment(save=True)

    def refresh_browser_environment_state(self) -> None:
        ready = self.browser_environment_ready()
        self.environment_banner.setVisible(not ready)
        self.google_panel.set_collection_enabled(ready)
        self.baidu_panel.set_collection_enabled(ready)
        if hasattr(self, "act_start"):
            self.sync_action_states()
        if not ready:
            self.task_status_label.setText(tr(self.language, "browser_required"))
        else:
            active = self.active_panel() if hasattr(self, "google_panel") else None
            if active is None or not ((active.worker and active.worker.is_alive()) or (active.content_worker and active.content_worker.is_alive())):
                self.task_status_label.setText(tr(self.language, "ready"))

    def _prompt_browser_setup_if_needed(self) -> None:
        if self.browser_environment_ready():
            return
        choice = exec_action_dialog(
            self,
            APP_NAME,
            tr(self.language, "browser_required"),
            [
                ("one_click", tr(self.language, "one_click_setup_short")),
                ("configure", tr(self.language, "advanced_browser_settings")),
            ],
            close_text=tr(self.language, "close"),
            warning=True,
        )
        if choice == "one_click":
            self.open_browser_settings(auto_setup=True)
        elif choice == "configure":
            self.open_browser_settings(auto_setup=False)

    def download_import_template(self) -> None:
        default_path = str(app_base_dir() / "WebLens_URL_import_template.xlsx")
        path, _ = QFileDialog.getSaveFileName(self, tr(self.language, "download_template"), default_path, "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            export_import_template(path)
            QMessageBox.information(self, APP_NAME, tr(self.language, "template_saved", path=path))
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, str(exc))

    @staticmethod
    def _panel_settings(engine: str, payload: Any) -> dict[str, Any]:
        defaults = panel_defaults(engine)
        source = payload if isinstance(payload, dict) else {}
        for key in tuple(defaults):
            if key in source:
                defaults[key] = source[key]
        return defaults

    def _load_settings(self) -> dict[str, Any]:
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8")) if self.settings_path.exists() else {}
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

        browser = browser_defaults()
        if isinstance(data.get("browser"), dict):
            browser.update(data["browser"])
        else:
            # v2.1 and older stored browser/Selenium settings separately inside
            # each engine panel. Migrate them once into the global browser block.
            legacy_sources = [data.get("google"), data.get("baidu"), data]
            for source in legacy_sources:
                if not isinstance(source, dict):
                    continue
                for key in browser:
                    if key in source and source[key] not in (None, ""):
                        browser[key] = source[key]
                if any(key in source for key in browser):
                    break
        if browser.get("fetch_backend") not in {"selenium_chrome", "selenium_edge"}:
            browser["fetch_backend"] = "selenium_chrome"
        backend = str(browser["fetch_backend"])
        saved_binary = str(browser.get("browser_binary_path", "")).strip()
        saved_installation = installation_for_path(saved_binary, backend) if saved_binary else None
        if not saved_installation:
            browser["browser_binary_path"] = preferred_browser_path(backend, app_root=app_base_dir())
            # A driver saved for another/missing browser should be re-resolved.
            if saved_binary:
                browser["browser_driver_path"] = ""

        if "google" in data or "baidu" in data:
            google = self._panel_settings("google", data.get("google", {}))
            baidu = self._panel_settings("baidu", data.get("baidu", {}))
        else:
            # Legacy flat settings migration. Removed page-size/page-limit/HTTP
            # collection controls are deliberately ignored.
            google = panel_defaults("google")
            baidu = panel_defaults("baidu")
            for key in tuple(google):
                if key in data:
                    google[key] = data[key]
            for key in tuple(baidu):
                if key in data:
                    baidu[key] = data[key]
            google["search_vertical"] = data.get("search_vertical") if data.get("search_vertical") in {"news", "web"} else "news"
            baidu["search_vertical"] = "baidu_news_media"
            baidu["day_step"] = 0
            baidu["output_path"] = default_output_path("baidu")

        # v2.3 migration: the page-render wait introduced in earlier builds
        # was 3500 ms.  Move those untouched legacy defaults to the new 5000-ms
        # baseline while preserving an explicitly customized value.
        if int(browser.get("browser_wait_ms", 5000) or 5000) == 3500:
            browser["browser_wait_ms"] = 5000
        for panel in (google, baidu):
            if int(panel.get("content_receive_wait_ms", 5000) or 5000) == 3500:
                panel["content_receive_wait_ms"] = 5000

        return {"ui_lang": data.get("ui_lang", "en"), "browser": browser, "google": google, "baidu": baidu}

    def save_settings(self) -> None:
        try:
            data = {
                "ui_lang": self.language,
                "browser": dict(self.browser_settings),
                "google": self.google_panel.collect_settings(),
                "baidu": self.baidu_panel.collect_settings(),
            }
            self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _create_actions(self) -> None:
        self.act_start = QAction(self); self.act_start.setShortcut(QKeySequence("Meta+Return" if sys.platform == "darwin" else "Ctrl+Return")); self.act_start.triggered.connect(lambda: self.active_panel().start_crawl())
        self.act_stop = QAction(self); self.act_stop.setShortcut(QKeySequence("Esc")); self.act_stop.triggered.connect(self.stop_collection)
        self.act_manual_collection = QAction(self); self.act_manual_collection.triggered.connect(self.open_manual_collection)
        self.act_export = QAction(self); self.act_export.setShortcut(QKeySequence.StandardKey.Save); self.act_export.triggered.connect(lambda: self.active_panel().export_results())
        self.act_import = QAction(self); self.act_import.triggered.connect(lambda: self.active_panel().import_links())
        self.act_paste_links = QAction(self); self.act_paste_links.triggered.connect(lambda: self.active_panel().paste_links_from_text())
        self.act_import_template = QAction(self); self.act_import_template.triggered.connect(self.download_import_template)
        self.act_open_output = QAction(self); self.act_open_output.triggered.connect(lambda: self.active_panel().open_output())
        self.act_open_download = QAction(self); self.act_open_download.triggered.connect(lambda: self.active_panel().open_download_folder())
        self.act_exit = QAction(self); self.act_exit.triggered.connect(self.close)
        self.act_undo = QAction(self); self.act_undo.setShortcut(QKeySequence.StandardKey.Undo); self.act_undo.triggered.connect(lambda: self.active_panel().undo_result_edit())
        self.act_redo = QAction(self); self.act_redo.setShortcut(QKeySequence.StandardKey.Redo); self.act_redo.triggered.connect(lambda: self.active_panel().redo_result_edit())
        self.act_reset_results = QAction(self); self.act_reset_results.triggered.connect(lambda: self.active_panel().reset_result_preview())
        self.act_clear = QAction(self); self.act_clear.triggered.connect(lambda: self.active_panel().clear_results())
        self.act_browser_settings = QAction(self); self.act_browser_settings.triggered.connect(self.open_browser_settings)
        self.act_clear_web_components = QAction(self); self.act_clear_web_components.triggered.connect(self.clear_managed_web_components)
        self.act_reset_settings = QAction(self); self.act_reset_settings.triggered.connect(self.reset_settings)
        self.act_guide = QAction(self); self.act_guide.triggered.connect(self.show_user_guide)
        self.act_params = QAction(self); self.act_params.triggered.connect(self.show_parameter_guide)
        self.act_about = QAction(self); self.act_about.triggered.connect(self.show_about)
        self.lang_group = QActionGroup(self); self.lang_group.setExclusive(True); self.lang_actions = {}
        for key, label in (("en", "English"), ("zh_sim", "简体中文"), ("zh_tra", "繁體中文")):
            act = QAction(label, self, checkable=True)
            act.setChecked(key == self.language)
            act.triggered.connect(lambda _checked=False, k=key: self.set_language(k))
            self.lang_group.addAction(act)
            self.lang_actions[key] = act

    def _create_menus(self) -> None:
        mb = self.menuBar()
        self.file_menu = mb.addMenu("")
        self.file_menu.addAction(self.act_start); self.file_menu.addAction(self.act_stop); self.file_menu.addAction(self.act_manual_collection); self.file_menu.addSeparator()
        self.file_menu.addAction(self.act_export); self.file_menu.addAction(self.act_import); self.file_menu.addAction(self.act_paste_links); self.file_menu.addAction(self.act_import_template); self.file_menu.addAction(self.act_open_output); self.file_menu.addAction(self.act_open_download); self.file_menu.addSeparator(); self.file_menu.addAction(self.act_exit)
        self.edit_menu = mb.addMenu("")
        self.edit_menu.addAction(self.act_undo); self.edit_menu.addAction(self.act_redo); self.edit_menu.addAction(self.act_reset_results); self.edit_menu.addAction(self.act_clear)
        self.settings_menu = mb.addMenu("")
        self.settings_menu.addAction(self.act_browser_settings)
        self.settings_menu.addAction(self.act_clear_web_components)
        self.settings_menu.addSeparator()
        self.language_menu = self.settings_menu.addMenu("")
        for key in ("en", "zh_sim", "zh_tra"):
            self.language_menu.addAction(self.lang_actions[key])
        self.settings_menu.addSeparator(); self.settings_menu.addAction(self.act_reset_settings)
        self.help_menu = mb.addMenu("")
        self.help_menu.addAction(self.act_guide); self.help_menu.addAction(self.act_params); self.help_menu.addSeparator(); self.help_menu.addAction(self.act_about)

    def _create_toolbar(self) -> None:
        self.main_toolbar = QToolBar(self)
        self.main_toolbar.setObjectName("mainToolbar")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setFloatable(False)
        self.main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.act_start.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_MediaPlay))
        self.act_stop.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_MediaStop))
        self.act_manual_collection.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_ComputerIcon))
        self.act_import.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_DialogOpenButton))
        self.act_paste_links.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.act_export.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_DialogSaveButton))
        self.act_open_output.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_FileIcon))
        self.act_open_download.setIcon(tinted_standard_icon(self, QStyle.StandardPixmap.SP_DirOpenIcon))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        for action in (self.act_start, self.act_stop, self.act_manual_collection):
            self.main_toolbar.addAction(action)
        start_widget = self.main_toolbar.widgetForAction(self.act_start)
        stop_widget = self.main_toolbar.widgetForAction(self.act_stop)
        if start_widget is not None:
            start_widget.setProperty("toolbarRole", "start")
            start_widget.style().unpolish(start_widget); start_widget.style().polish(start_widget)
        if stop_widget is not None:
            stop_widget.setProperty("toolbarRole", "stop")
            stop_widget.style().unpolish(stop_widget); stop_widget.style().polish(stop_widget)
        self.main_toolbar.addSeparator()
        for action in (self.act_import, self.act_paste_links, self.act_export):
            self.main_toolbar.addAction(action)
        self.main_toolbar.addSeparator()
        for action in (self.act_open_output, self.act_open_download):
            self.main_toolbar.addAction(action)

    def open_manual_collection(self) -> None:
        panel = self.active_panel()
        try:
            cfg = panel.build_config(allow_empty_query=True)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, str(exc))
            return
        self.save_settings()
        dialog = ManualCollectionDialog(panel, cfg)
        dialog.exec()

    def stop_collection(self) -> None:
        for panel in (self.google_panel, self.baidu_panel):
            if panel.worker and panel.worker.is_alive():
                panel.stop_crawl()
                break
        self.sync_action_states()

    def sync_action_states(self, *_args) -> None:
        if not hasattr(self, "act_start"):
            return
        panels = (self.google_panel, self.baidu_panel)
        collecting = any(bool(panel.worker and panel.worker.is_alive()) for panel in panels)
        downloading = any(bool(panel.content_worker and panel.content_worker.is_alive()) for panel in panels)
        busy = collecting or downloading
        ready = self.browser_environment_ready()
        self.act_start.setEnabled((not busy) and ready)
        self.act_stop.setEnabled(collecting)
        self.act_manual_collection.setEnabled(not busy)
        self.act_clear_web_components.setEnabled(not busy)
        self.google_engine_btn.setEnabled(not busy)
        self.baidu_engine_btn.setEnabled(not busy)
        for candidate in panels:
            candidate.sync_download_button_states()

    def retranslate_ui(self) -> None:
        l = self.language
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.google_engine_btn.setText(tr(l, "google")); self.baidu_engine_btn.setText(tr(l, "baidu")); self.engine_selector_label.setText(tr(l, "search_engine")); self.environment_label.setText(tr(l, "browser_required")); self.environment_one_click_btn.setText(tr(l, "one_click_setup_short")); self.environment_config_btn.setText(tr(l, "advanced_browser_settings"))
        self.file_menu.setTitle(tr(l, "file")); self.edit_menu.setTitle(tr(l, "edit")); self.settings_menu.setTitle(tr(l, "settings")); self.language_menu.setTitle(tr(l, "language")); self.help_menu.setTitle(tr(l, "help"))
        for act, key in ((self.act_start,"start"),(self.act_stop,"stop"),(self.act_manual_collection,"manual_collection"),(self.act_export,"export"),(self.act_import,"import"),(self.act_paste_links,"paste_links"),(self.act_import_template,"download_template"),(self.act_open_output,"open_output"),(self.act_open_download,"open_download"),(self.act_exit,"exit"),(self.act_undo,"undo"),(self.act_redo,"redo"),(self.act_reset_results,"reset_results"),(self.act_clear,"clear"),(self.act_browser_settings,"browser_settings"),(self.act_clear_web_components,"clear_web_components"),(self.act_reset_settings,"reset_settings"),(self.act_guide,"user_guide"),(self.act_params,"parameter_guide"),(self.act_about,"about")):
            act.setText(tr(l, key))
        self.google_panel.retranslate_ui(); self.baidu_panel.retranslate_ui()

    def set_language(self, lang: str) -> None:
        if lang not in UI_TEXTS:
            return
        self.language = lang
        self.lang_actions[lang].setChecked(True)
        self.retranslate_ui()
        self.save_settings()

    def open_browser_settings(self, *, auto_setup: bool = False) -> None:
        dialog = BrowserSettingsDialog(self, self.browser_settings, auto_setup=auto_setup)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.browser_settings = dict(browser_defaults(), **dialog.values())
        self.save_settings()
        self.refresh_browser_environment_state()

    def show_driver_help(self, message: str = "", backend: str | None = None, parent: QWidget | None = None) -> None:
        backend = backend or str(self.browser_settings.get("fetch_backend", "selenium_chrome"))
        choice = exec_action_dialog(
            parent or self,
            APP_NAME,
            tr(self.language, "driver_failed", message=message or tr(self.language, "driver_missing")),
            [
                ("driver", tr(self.language, "open_driver_page")),
                ("browser", tr(self.language, "open_browser_page")),
            ],
            close_text=tr(self.language, "close"),
            warning=True,
        )
        if choice == "driver":
            webbrowser.open(official_driver_url(backend))
        elif choice == "browser":
            webbrowser.open(official_browser_url(backend))

    def clear_managed_web_components(self) -> None:
        if QMessageBox.question(self, APP_NAME, tr(self.language, "confirm_clear_web_components")) != QMessageBox.StandardButton.Yes:
            return
        report = clear_web_components()
        self.browser_settings["browser_binary_path"] = ""
        self.browser_settings["browser_driver_path"] = ""
        self.save_settings()
        self.refresh_browser_environment_state()
        if report.warnings:
            QMessageBox.warning(self, APP_NAME, tr(self.language, "clear_web_components_warning", message="\n".join(report.warnings)))
        else:
            QMessageBox.information(self, APP_NAME, tr(self.language, "clear_web_components_done"))

    def reset_settings(self) -> None:
        if QMessageBox.question(self, APP_NAME, tr(self.language, "confirm_reset_settings")) != QMessageBox.StandardButton.Yes:
            return
        self.browser_settings = browser_defaults()
        self.browser_settings["browser_binary_path"] = preferred_browser_path(
            str(self.browser_settings["fetch_backend"]), app_root=app_base_dir()
        )
        self.google_panel.apply_settings(panel_defaults("google"))
        self.baidu_panel.apply_settings(panel_defaults("baidu"))
        self.save_settings()
        self.refresh_browser_environment_state()

    def _show_help_dialog(self, title: str, subtitle: str, html_body: str, *, identity: str = "", about: bool = False) -> None:
        """Show the styled help/about window in the currently selected UI language."""
        dialog = QDialog(self)
        apply_window_icon(dialog)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(560, 420)
        root = QVBoxLayout(dialog)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("helpHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 14, 14, 14)
        header_layout.setSpacing(16)

        logo = QLabel()
        logo_path = resource_path("assets/logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo.setPixmap(pixmap.scaled(112, 112, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setFixedSize(118, 118)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QVBoxLayout()
        title_box.setSpacing(5)
        heading = QLabel(title)
        heading.setObjectName("helpHeading")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setProperty("muted", True)
        title_box.addWidget(heading)
        title_box.addWidget(subtitle_label)
        if identity:
            identity_label = QLabel(identity)
            identity_label.setTextFormat(Qt.TextFormat.RichText)
            identity_label.setWordWrap(True)
            identity_label.setObjectName("aboutIdentity")
            title_box.addSpacing(5)
            title_box.addWidget(identity_label)
        title_box.addStretch(1)
        header_layout.addLayout(title_box, 1)
        root.addWidget(header)

        browser = QTextBrowser()
        browser.setObjectName("helpTextBrowser")
        browser.setOpenExternalLinks(True)
        browser.setHtml(html_body)
        root.addWidget(browser, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        close_button.setText(tr(self.language, "close"))
        close_button.setDefault(True)
        root.addWidget(buttons)
        fit_dialog_to_screen(dialog, 930, 760 if about else 720)
        dialog.exec()

    def show_user_guide(self) -> None:
        lang = self.language
        if lang == "en":
            title = "BFSU WebLens — User Guide"
            subtitle = "Corpus-oriented web and news collection workflow"
            html = f"""
            <h2>User Guide</h2>
            <p><b>BFSU WebLens {APP_VERSION}</b> supports corpus-oriented discovery, review, import/export and full-text downloading of web and news resources.</p>
            <ol>
              <li><b>Prepare the browser environment for automatic collection.</b> Under <i>Settings → Browser &amp; Selenium</i>, One-click configure checks both Chrome and Edge, uses an isolated portable Chrome by default and the system-installed Microsoft Edge by default, prepares matching WebDrivers and shows configuration progress. <i>Update selected portable browser &amp; WebDriver</i> checks the current official stable release and safely prepares a newer WebLens-managed version when available. Independent Detect/Download/Browse controls remain available for manual recovery. Automatic collection remains locked until the selected browser and Driver are compatible; Manual collection remains available without Selenium.</li>
              <li><b>Select a search engine.</b> Google and Baidu share the application-wide browser/Driver configuration while keeping separate search parameters and result lists.</li>
              <li><b>Use Manual collection when preferred.</b> WebLens generates one or more initial search URLs from the current parameters. Open them in your normal browser, turn pages manually, save every result page as HTML, then import those files in the Manual collection window. Parsed links are deduplicated and appended to Result Preview, after which the normal full-text download workflow applies.</li>
              <li><b>Enter search terms and optional site/domain filters.</b> Each line may contain one term or one domain. For Baidu, multiple terms and multiple domains are expanded into separate term × domain search tasks; WebLens never auto-joins those dimensions with OR.</li>
              <li><b>Use date restriction only when needed.</b> It is off by default, so no date parameter is sent. When enabled, Start date and End date become active and WebLens prevents the start date from being later than the end date.</li>
              <li><b>Collect links.</b> Start collection and Stop control search-engine collection only. WebLens does not set page size or a maximum page count and follows only the search engine's own Next link.</li>
              <li><b>Complete human verification in the browser.</b> WebLens pauses all navigation commands while a verification page is present. After verification, it waits for the real result DOM and resumes from the page already open.</li>
              <li><b>Import or paste existing links when needed.</b> TXT supports one URL per line; XLSX/CSV can place URLs in the first column; WebLens exports can be re-imported. <i>Paste links from text</i> extracts HTTP/HTTPS links from prose, HTML or Markdown and appends them to the current Result Preview. Imported links may have no title initially.</li>
              <li><b>Review results.</b> Open, delete, sort and sample records in Result Preview. The Published column is displayed as DD-MM-YYYY and sorted chronologically after parsing common absolute and relative search-engine date formats; the original publication-time text remains stored in the record. Google News may expose an opaque Google <code>/goto</code> result redirect. During automatic collection WebLens first asks Google for the redirect target and stores the direct external URL when available; unresolved redirects are retained as a safe fallback and can still be replaced after successful content downloading.</li>
              <li><b>Download content.</b> Configure download settings once, then use Download selected content or Download all content. Stop download is independent from Stop collection. Successful downloading can complete missing title, publication time and final URL information.</li>
            </ol>
            """
        elif lang == "zh_tra":
            title = "BFSU WebLens — 使用說明"
            subtitle = "面向語料庫建設的網頁與新聞採集工作流"
            html = f"""
            <h2>使用說明</h2>
            <p><b>BFSU WebLens {APP_VERSION}</b> 面向網頁語料庫和網路新聞語料庫建設，用於連結發現、結果整理、匯入匯出與正文下載。</p>
            <ol>
              <li><b>自動採集前配置瀏覽器環境。</b> 在「設定 → 瀏覽器與 Selenium」中預設使用 WebLens tools 內的便攜版瀏覽器；系統已安裝瀏覽器僅作為用戶主動選擇的「不推薦」備選。一鍵配置可準備瀏覽器與匹配的 WebDriver；「更新當前內置便攜版瀏覽器與 WebDriver」可主動檢查官方最新穩定版並安全更新。下方仍保留獨立的偵測、下載與瀏覽按鈕。瀏覽器與 Driver 未匹配時自動採集保持鎖定；手動採集不依賴 Selenium，仍可使用。</li>
              <li><b>選擇搜索引擎。</b> Google 和百度共用應用級瀏覽器/Driver 設定，但各自保留獨立的檢索參數和結果列表。</li>
              <li><b>可使用手動採集。</b> WebLens 依照目前參數產生一個或多個初始檢索連結；用戶在日常瀏覽器中開啟、手動翻頁並把每一頁儲存為 HTML，再回到「手動採集」視窗批次匯入。解析出的連結去重後追加到結果預覽，之後仍使用既有正文下載流程。</li>
              <li><b>填寫檢索詞和可選的站點/域名。</b> 每行可填一個檢索詞或一個域名。百度會把多個檢索詞和多行站點/域名展開為「檢索詞 × 域名」獨立任務逐項搜索，WebLens 不使用 OR 自動連接這兩個維度。</li>
              <li><b>按需限定日期。</b> 日期限定預設關閉，因此不向搜索引擎發送日期參數。啟用後才可設定開始/結束日期，且開始日期不會晚於結束日期。</li>
              <li><b>採集連結。</b>「開始採集」和「停止」只控制搜索結果採集。WebLens 不設定每頁結果數和最大頁數，只跟隨搜索引擎自身提供的「下一頁」。</li>
              <li><b>人工驗證。</b> 出現驗證頁時，WebLens 停止發送導航指令；用戶在瀏覽器中完成驗證後，軟體等待真實結果 DOM 穩定，再從當前頁面恢復。</li>
              <li><b>匯入或貼上已有連結。</b> TXT 可每行一個 URL；XLSX/CSV 可將 URL 放在首列；WebLens 自己匯出的檔案也可重新匯入。「貼上文字解析連結」可從普通文字、HTML 或 Markdown 中抽取 HTTP/HTTPS 連結並追加到當前結果列表。匯入時標題可以暫時為空。</li>
              <li><b>整理結果。</b> 可在結果預覽中開啟、刪除、排序和抽樣。Published/發布時間統一以 DD-MM-YYYY（日-月-年）顯示，排序時會先解析常見絕對日期與相對時間後按實際日期排序，原始時間文字仍保留在記錄中。Google 新聞有時會提供不透明的 Google <code>/goto</code> 跳轉連結；自動採集時 WebLens 會先向 Google 取得跳轉目標並直接保存外部 URL。若當次無法解析，仍保留 <code>/goto</code> 作為安全後備，正文下載成功後可再次替換為最終 URL。</li>
              <li><b>下載正文。</b> 下載參數只需設定一次；「停止下載」與「停止採集」彼此獨立。下載成功後可補全缺失的標題、發布時間和最終 URL。</li>
            </ol>
            """
        else:
            title = "BFSU WebLens — 使用说明"
            subtitle = "面向语料库建设的网页与新闻采集工作流"
            html = f"""
            <h2>使用说明</h2>
            <p><b>BFSU WebLens {APP_VERSION}</b> 面向网页语料库和网络新闻语料库建设，用于链接发现、结果整理、导入导出与正文下载。</p>
            <ol>
              <li><b>自动采集前配置浏览器环境。</b> 在“设置 → 浏览器与 Selenium”中默认使用 WebLens tools 内的便携版浏览器；系统已安装浏览器仅作为用户主动选择的“不推荐”备选。一键配置可准备浏览器与匹配的 WebDriver；“更新当前内置便携版浏览器与 WebDriver”可主动检查官方最新稳定版并安全更新。下方仍保留独立的检测、下载与浏览按钮。浏览器与 Driver 未匹配时，自动采集保持锁定；手动采集不依赖 Selenium，仍可使用。</li>
              <li><b>选择搜索引擎。</b> Google 和百度共用应用级浏览器/Driver 设置，但各自保留独立的检索参数和结果列表。</li>
              <li><b>可使用手动采集。</b> WebLens 根据当前参数生成一个或多个初始检索链接；用户在日常浏览器中打开、手动翻页并把每一页保存为 HTML，再回到“手动采集”窗口批量导入。解析出的链接去重后追加到结果预览，之后仍使用现有正文下载流程。</li>
              <li><b>填写检索词和可选的站点/域名。</b> 每行可填写一个检索词或一个域名。百度会把多个检索词和多行站点/域名展开为“检索词 × 域名”独立任务逐项搜索，WebLens 不使用 OR 自动连接这两个维度。</li>
              <li><b>按需限定日期。</b> 日期限定默认关闭，因此不会向搜索引擎发送日期参数。启用后才可设置开始/结束日期，并自动保证开始日期不晚于结束日期。</li>
              <li><b>采集链接。</b>“开始采集”和“停止”只控制搜索结果采集。WebLens 不设置每页结果数，也不设置最大页数，只跟随搜索引擎页面自身提供的“下一页”。</li>
              <li><b>人工验证。</b> 出现验证页时，WebLens 停止发送导航指令；用户在浏览器中完成验证后，软件等待真实结果 DOM 稳定，再从当前页面恢复采集。</li>
              <li><b>导入或粘贴已有链接。</b> TXT 支持每行一个 URL；XLSX/CSV 可把 URL 放在首列；WebLens 自己导出的文件也可重新导入。“粘贴文本解析链接”可从普通文字、HTML 或 Markdown 中抽取 HTTP/HTTPS 链接，并追加到当前结果列表。导入时标题可以暂时为空。</li>
              <li><b>整理结果。</b> 可在结果预览中打开、删除、排序和抽样。Published/发布时间统一以 DD-MM-YYYY（日-月-年）显示，排序时会先解析常见绝对日期与相对时间后按实际日期排序，原始时间文字仍保留在记录中。Google 新闻有时会提供不透明的 Google <code>/goto</code> 跳转链接；自动采集时 WebLens 会先向 Google 获取跳转目标并直接保存外部 URL。若当次无法解析，仍保留 <code>/goto</code> 作为安全回退，正文下载成功后还可再次替换为最终 URL。</li>
              <li><b>下载正文。</b> 下载参数只设置一次；“停止下载”与“停止采集”彼此独立。下载成功后可以补全缺失的标题、发布时间和最终 URL。</li>
            </ol>
            """
        self._show_help_dialog(title, subtitle, html)

    def show_parameter_guide(self) -> None:
        lang = self.language
        if lang == "en":
            title = "BFSU WebLens — Parameter Guide"
            subtitle = "Meaning and scope of collection parameters"
            html = """
            <h2>Parameter Guide</h2>
            <p><b>Search mode.</b> Google supports single term, OR, all terms, exact phrase, multiple exact phrases and raw queries. Baidu's multiple-term mode sends each non-empty line as a separate task. Multiple Baidu site/domain filters are also searched separately; the execution plan is term × domain × date slice, with no WebLens-generated OR between terms or domains.</p>
            <p><b>Search vertical.</b> Google supports Web and News. Baidu supports Web, News/Information and media-site News.</p>
            <p><b>Language and region.</b> Google language and country/region restrictions are optional.</p>
            <p><b>Date restriction.</b> Off by default. When disabled, no date-range parameter is sent. When enabled, the selected range can be split by Date-slice step; 0 keeps the entire range as one slice.</p>
            <p><b>Page-turn wait.</b> The range is entered in seconds for readability. WebLens converts the two endpoints to milliseconds internally and chooses a random wait at millisecond granularity between result pages, between date slices and before the one retry after a transient page-load error.</p>
            <p><b>Pagination.</b> WebLens has no page-size setting and no maximum-page setting. It loads the default first page and follows only the search engine's own Next link.</p>
            <p><b>Manual collection.</b> This mode uses the same query/date/language/region settings only to generate initial search URLs. It performs no automated navigation and needs no Selenium environment. Saved Google/Baidu result-page HTML files can be imported repeatedly; links are extracted, deduplicated and appended to Result Preview.</p>
            <p><b>Human verification.</b> While verification is present, WebLens sends no refresh, pagination, browser-restart or new-page navigation command. Collection resumes only after the live result DOM becomes stable.</p>
            <p><b>Google News redirect links.</b> Current Google News may expose story cards through an opaque Google <code>/goto?url=...</code> link. Automatic collection resolves that Google redirect without following the destination article and stores the external target directly when Google returns one. If resolution fails, the redirect remains a valid result-card fallback and the full-text downloader can still replace it later.</p>
            <p><b>Empty results.</b> Search-engine UI/navigation links are excluded. A genuine empty Baidu unit ends that unit and WebLens continues with the next date slice or term/domain task when available.</p>
            <p><b>Browser and WebDriver setup.</b> One-click configuration checks Chrome and Edge, uses an isolated portable Chrome by default and the system-installed Microsoft Edge by default, and prepares a version-compatible Driver with visible progress. The portable-update action applies to the WebLens-managed Chrome environment and can upgrade Chrome side-by-side with its exact matching ChromeDriver. Edge uses the system-installed Microsoft Edge browser and WebLens prepares an EdgeDriver matched to that installed version. Manual Browser/Driver paths are validated immediately, and collection preflight checks them again before every crawl.</p>
            <p><b>Browser rendering.</b> Page render wait is application-wide and defaults to 5000 ms.</p>
            <p><b>Content downloading.</b> This is separate from search-result collection. Requests/Selenium/Mixed options apply only to already collected destination pages; Google/Baidu result-page collection itself is browser-only.</p>
            """
        elif lang == "zh_tra":
            title = "BFSU WebLens — 參數說明"
            subtitle = "採集參數的含義與適用範圍"
            html = """
            <h2>參數說明</h2>
            <p><b>檢索模式。</b> Google 支援單個檢索詞、OR、多詞全部包含、嚴格短語、多個嚴格短語和原始檢索式。百度多檢索詞模式會將每個非空行作為獨立任務；多行站點/域名也會分別執行，因此完整任務為「檢索詞 × 域名 × 日期切片」，WebLens 不生成連接檢索詞或域名的 OR。</p>
            <p><b>檢索類型。</b> Google 支援網頁和新聞；百度支援網頁、資訊以及媒體網站資訊。</p>
            <p><b>語種與區域。</b> Google 的結果語種和國家/地區限定均為可選。</p>
            <p><b>日期限定。</b> 預設關閉。關閉時不發送日期範圍；開啟後才使用選定日期，切片步長為 0 時整個範圍作為一個切片。</p>
            <p><b>翻頁等待。</b> 界面以秒為單位設定範圍；WebLens 內部轉換為毫秒，並在兩個端點之間按毫秒粒度隨機取值。結果翻頁、日期切片之間以及臨時頁面載入錯誤後的單次重試均使用這一範圍。</p>
            <p><b>翻頁方式。</b> WebLens 不設定每頁結果數，也不設定最大頁數，只跟隨搜索引擎自身的「下一頁」。</p>
            <p><b>手動採集。</b> 此模式只使用相同的檢索詞、日期、語種與區域等參數來產生初始搜索連結，不進行任何自動導航，也不需要 Selenium。用戶可反覆匯入手動儲存的 Google/百度搜索結果 HTML，WebLens 解析、去重後追加到結果預覽。</p>
            <p><b>人工驗證。</b> 驗證期間不刷新、不翻頁、不重啟瀏覽器，也不開啟新搜索頁；只有實時結果 DOM 穩定後才恢復。</p>
            <p><b>Google 新聞跳轉連結。</b> 當前 Google 新聞可能使用不透明的 <code>/goto?url=...</code> 作為新聞卡片主連結。自動採集會先解析 Google 的 HTTP 跳轉而不下載目標文章，能取得目標時直接保存外部 URL；解析失敗時保留跳轉連結，正文下載流程仍可再次跟隨並替換。</p>
            <p><b>真實空結果。</b> 搜索引擎界面和導航連結不算結果。百度某個具體任務出現真實空頁時，只結束該任務，仍會繼續下一個日期切片或下一個檢索詞/域名任務。</p>
            <p><b>瀏覽器與 WebDriver 配置。</b> 預設使用 WebLens 便攜版瀏覽器，系統安裝版僅作為明確標示「不推薦」的用戶主動備選。一鍵配置會準備可用瀏覽器與版本匹配的 Driver；便攜版更新功能可檢查官方最新穩定版，Chrome 可與精確匹配的 ChromeDriver 一併更新；內置 Edge 可更新匹配的 EdgeDriver，但因微軟沒有官方便攜 Edge ZIP，WebLens 不會自動替換 Edge 瀏覽器本體。手動 Browser/Driver 路徑會立即驗證，開始採集前還會再次預檢。</p>
            <p><b>瀏覽器渲染。</b> 頁面渲染等待為應用級設定，預設 5000 ms。</p>
            <p><b>正文下載。</b> 正文下載與搜索結果採集分離；Requests/Selenium/Mixed 僅作用於已採集的目標頁面，Google/百度結果頁採集本身始終為瀏覽器模式。</p>
            """
        else:
            title = "BFSU WebLens — 参数说明"
            subtitle = "采集参数的含义与适用范围"
            html = """
            <h2>参数说明</h2>
            <p><b>检索模式。</b> Google 支持单个检索词、OR、多词全部包含、严格短语、多个严格短语和原始检索式。百度多检索词模式会把每个非空行作为独立任务；多行站点/域名也会分别执行，因此完整任务为“检索词 × 域名 × 日期切片”，WebLens 不生成连接检索词或域名的 OR。</p>
            <p><b>检索类型。</b> Google 支持网页和新闻；百度支持网页、资讯以及媒体网站资讯。</p>
            <p><b>语种与区域。</b> Google 的结果语种和国家/地区限定均为可选；中文界面的名称后附英文名称。</p>
            <p><b>日期限定。</b> 默认关闭。关闭时不发送日期范围；开启后才使用选定日期，日期切片步长为 0 时整个范围作为一个切片。</p>
            <p><b>翻页等待。</b> 界面以秒为单位设置范围；WebLens 内部转换为毫秒，并在两个端点之间按毫秒粒度随机取值。结果翻页、日期切片之间以及临时页面加载错误后的单次重试均使用这一范围。</p>
            <p><b>翻页方式。</b> WebLens 不设置每页结果数，也不设置最大页数，只跟随搜索引擎自身提供的“下一页”。</p>
            <p><b>手动采集。</b> 此模式只使用相同的检索词、日期、语种与区域等参数生成初始搜索链接，不进行任何自动导航，也不需要 Selenium。用户可反复导入手动保存的 Google/百度搜索结果 HTML，WebLens 解析、去重后追加到结果预览。</p>
            <p><b>人工验证。</b> 验证期间不刷新、不翻页、不重启浏览器，也不打开新的搜索页；只有实时结果 DOM 稳定后才恢复。</p>
            <p><b>Google 新闻跳转链接。</b> 当前 Google 新闻可能使用不透明的 <code>/goto?url=...</code> 作为新闻卡片主链接。自动采集会先解析 Google 的 HTTP 跳转而不下载目标文章，能取得目标时直接保存外部 URL；解析失败时保留跳转链接，正文下载流程仍可再次跟随并替换。</p>
            <p><b>真实空结果。</b> 搜索引擎界面和导航链接不算结果。百度某个具体任务出现真实空页时，只结束该任务，仍会继续下一个日期切片或下一个检索词/域名任务。</p>
            <p><b>浏览器与 WebDriver 配置。</b> 默认使用 WebLens 便携版浏览器，系统安装版仅作为明确标记“不推荐”的用户主动备选。一键配置会准备可用浏览器与版本匹配的 Driver；便携版更新功能可检查官方最新稳定版，Chrome 可与精确匹配的 ChromeDriver 一并更新；内置 Edge 可更新匹配的 EdgeDriver，但由于微软没有官方便携 Edge ZIP，WebLens 不会自动替换 Edge 浏览器本体。手动 Browser/Driver 路径会立即验证，开始采集前还会再次预检。</p>
            <p><b>浏览器渲染。</b> 页面渲染等待为应用级设置，默认 5000 ms。</p>
            <p><b>正文下载。</b> 正文下载与搜索结果采集分离；Requests/Selenium/Mixed 只作用于已经采集的目标页面，Google/百度结果页采集本身始终为浏览器模式。</p>
            """
        self._show_help_dialog(title, subtitle, html)

    def show_about(self) -> None:
        lang = self.language
        corpus_url = "https://corpus.bfsu.edu.cn/"
        github_url = "https://github.com/bfsunlp"
        lexiscope_url = "https://github.com/bfsunlp/bfsu_lexiscope"
        if lang == "en":
            title = "About BFSU WebLens"
            subtitle = "BFSU LexiScope · Web and news corpus collection"
            identity = "<b>Author:</b> Dr. Dingjia Liu"
            html = f"""
            <h2>About BFSU WebLens</h2>
            <p><b>Version:</b> {APP_VERSION}</p>
            <p><b>Author:</b> Dr. Dingjia Liu</p>
            <p><b>BFSU Corpus Research Group:</b> BFSU WebLens is developed by the BFSU Corpus Research Group as part of its corpus-tool development. The group's official website provides information on corpus research, corpora, tools, publications and related activities.</p>
            <p><a href="{corpus_url}">BFSU Corpus Research Group official website</a></p>
            <p><b>BFSUNLP on GitHub:</b> <a href="{github_url}">{github_url}</a></p>
            <p><b>BFSU LexiScope:</b> LexiScope is an open-source corpus toolkit for corpus construction, metadata management, concordancing, parallel-corpus processing and AI-assisted linguistic analysis. BFSU WebLens is its web/news collection component, supporting corpus-oriented link discovery, review, export and destination-page downloading.</p>
            <p><a href="{lexiscope_url}">BFSU LexiScope project on GitHub</a></p>
            <p><b>Implementation:</b> PySide6 / Qt desktop interface; application-wide Chrome/Edge and Selenium/WebDriver management; browser-rendered Google/Baidu automatic search collection; browser-independent manual HTML result-page collection; result review/import/export; destination-page content downloading and metadata completion.</p>
            <p><b>Research-use note:</b> Users should respect search-engine and website access rules, applicable law, copyright and research ethics.</p>
            """
        elif lang == "zh_tra":
            title = "關於 BFSU WebLens"
            subtitle = "BFSU LexiScope · 網頁與新聞語料採集"
            identity = "<b>作者：</b>劉鼎甲 博士"
            html = f"""
            <h2>關於 BFSU WebLens</h2>
            <p><b>版本：</b>{APP_VERSION}</p>
            <p><b>作者：</b>劉鼎甲 博士</p>
            <p><b>北外语料库团队：</b>WebLens 是北外语料库团队語料工具建設的一部分。團隊官方網站提供語料庫研究、語料庫資源、工具、成果與學術活動等資訊。</p>
            <p><a href="{corpus_url}">北外语料库团队官方網站</a></p>
            <p><b>BFSUNLP GitHub：</b><a href="{github_url}">{github_url}</a></p>
            <p><b>BFSU LexiScope：</b>LexiScope 是一套開源語料庫工具集，面向語料庫建設、元資料管理、語料檢索、平行語料處理與 AI 輔助語言分析。BFSU WebLens 是其中的網頁/新聞採集組件，用於面向語料庫建設的連結發現、結果整理、匯出與目標頁面下載。</p>
            <p><a href="{lexiscope_url}">BFSU LexiScope GitHub 專案首頁</a></p>
            <p><b>實現：</b>PySide6 / Qt 桌面介面；應用級 Chrome/Edge 與 Selenium/WebDriver 管理；瀏覽器渲染式 Google/百度搜索採集；結果整理與匯入匯出；目標頁面正文下載和元資料補全。</p>
            <p><b>科研使用：</b>使用者應遵守搜索引擎與目標網站的訪問規則、相關法律、版權規範和科研倫理。</p>
            """
        else:
            title = "关于 BFSU WebLens"
            subtitle = "BFSU LexiScope · 网页与新闻语料采集"
            identity = "<b>作者：</b>刘鼎甲 博士"
            html = f"""
            <h2>关于 BFSU WebLens</h2>
            <p><b>版本：</b>{APP_VERSION}</p>
            <p><b>作者：</b>刘鼎甲 博士</p>
            <p><b>北外语料库团队：</b>WebLens 是北外语料库团队语料工具建设的一部分。团队官方网站提供语料库研究、语料库资源、工具、成果与学术活动等信息。</p>
            <p><a href="{corpus_url}">北外语料库团队官方网站</a></p>
            <p><b>BFSUNLP GitHub：</b><a href="{github_url}">{github_url}</a></p>
            <p><b>BFSU LexiScope：</b>LexiScope 是一套开源语料库工具集，面向语料库建设、元数据管理、语料检索、平行语料处理与 AI 辅助语言分析。BFSU WebLens 是其中的网页/新闻采集组件，用于面向语料库建设的链接发现、结果整理、导出与目标页面下载。</p>
            <p><a href="{lexiscope_url}">BFSU LexiScope GitHub 项目主页</a></p>
            <p><b>实现：</b>PySide6 / Qt 桌面界面；应用级 Chrome/Edge 与 Selenium/WebDriver 管理；浏览器渲染式 Google/百度搜索采集；结果整理与导入导出；目标页面正文下载和元数据补全。</p>
            <p><b>科研使用：</b>使用者应遵守搜索引擎和目标网站访问规则、相关法律法规、版权规范和科研伦理。</p>
            """
        self._show_help_dialog(title, subtitle, html, identity=identity, about=True)

    def closeEvent(self,event) -> None:  # noqa: N802
        self.google_panel.stop_all();self.baidu_panel.stop_all();self.save_settings();event.accept()
