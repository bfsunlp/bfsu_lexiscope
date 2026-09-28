# -*- coding: utf-8 -*-
"""Maintenance helpers for BFSU WebLens.

The routines in this module are intentionally conservative.  They only remove
WebLens-managed settings, browser/driver payloads and caches.  User corpus
outputs (``output`` and ``content_downloads``) are never deleted by these
functions.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .platform_paths import user_cache_root, user_data_root


@dataclass
class MaintenanceReport:
    action: str
    removed: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings


def settings_file() -> Path:
    return user_data_root(create=False) / "weblens_settings.json"


def _safe_remove_file(path: Path, report: MaintenanceReport) -> None:
    try:
        if path.exists() or path.is_symlink():
            path.unlink()
            report.removed.append(str(path))
    except Exception as exc:
        report.warnings.append(f"Could not remove {path}: {exc}")


def _safe_rmtree(path: Path, report: MaintenanceReport) -> None:
    try:
        if path.exists() or path.is_symlink():
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            report.removed.append(str(path))
    except Exception as exc:
        report.warnings.append(f"Could not remove {path}: {exc}")


def _clear_dynamic_children(path: Path, report: MaintenanceReport, preserve_names: Iterable[str] = ()) -> None:
    """Remove generated children of a managed directory, preserving docs."""
    if not path.exists() or not path.is_dir():
        return
    preserve = {name.lower() for name in preserve_names}
    for child in list(path.iterdir()):
        if child.name.lower() in preserve:
            report.preserved.append(str(child))
            continue
        _safe_rmtree(child, report) if child.is_dir() and not child.is_symlink() else _safe_remove_file(child, report)


def reset_user_settings() -> MaintenanceReport:
    """Remove the persisted WebLens settings file only."""
    report = MaintenanceReport("reset-settings")
    _safe_remove_file(settings_file(), report)
    return report


def _clear_browser_paths_from_settings(report: MaintenanceReport) -> None:
    path = settings_file()
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        browser = data.get("browser") or {}
        if isinstance(browser, dict):
            browser["browser_binary_path"] = ""
            browser["browser_driver_path"] = ""
            data["browser"] = browser
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        report.warnings.append(f"Could not clear saved browser/driver paths in {path}: {exc}")


def managed_web_component_paths() -> list[Path]:
    """Return WebLens-owned browser/driver locations only.

    The global Selenium cache (``~/.cache/selenium``) is deliberately excluded
    because it may be shared by other applications.
    """
    data = user_data_root(create=False)
    cache = user_cache_root(create=False)
    paths = [
        data / "tools" / "browser",
        data / "tools" / "drivers",
        cache / "browser",
        cache / "drivers",
    ]
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            base = Path(local) / "BFSU_WebLens"
            paths.extend([base / "browser", base / "drivers"])
    # Deduplicate without resolving non-existent paths through foreign mounts.
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = os.path.normcase(os.path.abspath(str(path)))
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def clear_web_components() -> MaintenanceReport:
    """Remove WebLens-managed portable browsers, drivers and their caches.

    System-installed Chrome/Edge and the global Selenium cache are never
    touched.  Static README/download-link files inside a source checkout's
    ``tools/browser`` folder are preserved.
    """
    report = MaintenanceReport("clear-web")
    data = user_data_root(create=False)
    source_browser = data / "tools" / "browser"
    source_drivers = data / "tools" / "drivers"

    # Preserve documentation files if the user is running from source or if a
    # release ships these helpers beside the managed payload folders.
    if source_browser.exists():
        _clear_dynamic_children(source_browser, report, preserve_names={"README.txt", "README.md"})
    if source_drivers.exists():
        _clear_dynamic_children(source_drivers, report, preserve_names={"README.txt", "README.md"})

    for path in managed_web_component_paths():
        if path in {source_browser, source_drivers}:
            continue
        _safe_rmtree(path, report)

    _clear_browser_paths_from_settings(report)
    return report


def purge_user_state() -> MaintenanceReport:
    """Remove WebLens settings, managed web components and disposable caches.

    User-generated corpus outputs are preserved.  This is the data-cleaning
    phase used by the packaged uninstall scripts before application files are
    removed.
    """
    report = MaintenanceReport("purge-user-state")

    settings_report = reset_user_settings()
    report.removed.extend(settings_report.removed)
    report.warnings.extend(settings_report.warnings)

    web_report = clear_web_components()
    report.removed.extend(web_report.removed)
    report.preserved.extend(web_report.preserved)
    report.warnings.extend(web_report.warnings)

    data = user_data_root(create=False)
    for path in (
        data / "weblens_debug_html",
        data / ".tmp",
        data / "tmp",
    ):
        _safe_rmtree(path, report)

    # The WebLens-specific cache root is disposable.  Do not touch output or
    # content_downloads in the data root.
    _safe_rmtree(user_cache_root(create=False), report)
    return report


def self_check() -> MaintenanceReport:
    """Return a no-op report proving the maintenance module can be imported."""
    report = MaintenanceReport("self-check")
    report.preserved.extend([
        str(user_data_root(create=False) / "output"),
        str(user_data_root(create=False) / "content_downloads"),
    ])
    return report


def run_maintenance(action: str) -> MaintenanceReport:
    key = str(action or "").strip().lower().replace("_", "-")
    if key == "reset-settings":
        return reset_user_settings()
    if key == "clear-web":
        return clear_web_components()
    if key in {"purge-user-state", "uninstall-data", "purge"}:
        return purge_user_state()
    if key in {"self-check", "check"}:
        return self_check()
    raise ValueError(f"Unknown maintenance action: {action}")


def report_text(report: MaintenanceReport) -> str:
    lines = [f"BFSU WebLens maintenance: {report.action}"]
    if report.removed:
        lines.append("Removed:")
        lines.extend(f"  - {item}" for item in report.removed)
    else:
        lines.append("Removed: nothing (already clean)")
    if report.preserved:
        lines.append("Preserved:")
        lines.extend(f"  - {item}" for item in report.preserved)
    if report.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {item}" for item in report.warnings)
    return "\n".join(lines)
