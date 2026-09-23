# -*- coding: utf-8 -*-
"""Browser and WebDriver discovery/management for BFSU WebLens.

This module is intentionally separate from the search collector.  It discovers
installed Chrome/Edge binaries, reads their versions, checks local driver
compatibility, and can download the matching WebDriver from the browser vendor's
official distribution endpoints.
"""
from __future__ import annotations

import ctypes
import io
import json
import os
import platform
import plistlib
import re
import shutil
import struct
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
import xml.etree.ElementTree as ET

import requests

from .platform_paths import resource_roots, user_data_root, user_cache_root

VERSION_RE = re.compile(r"(\d+\.\d+\.\d+\.\d+)")

CHROME_CFT_BUILD_JSON = "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build-with-downloads.json"
CHROME_CFT_MILESTONE_JSON = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
CHROME_CFT_LKG_JSON = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
CHROME_DRIVER_PAGE = "https://googlechromelabs.github.io/chrome-for-testing/"
CHROME_BROWSER_PAGE = "https://www.google.com/chrome/"
EDGE_DRIVER_BASE = "https://msedgedriver.microsoft.com"
EDGE_DRIVER_CATALOG = "https://msedgewebdriverstorage.blob.core.windows.net/edgewebdriver"
EDGE_DRIVER_PAGE = "https://developer.microsoft.com/microsoft-edge/tools/webdriver/"
EDGE_BROWSER_PAGE = "https://www.microsoft.com/edge/download"
EDGE_UPDATES_API = "https://edgeupdates.microsoft.com/api/products?view=enterprise"


@dataclass(frozen=True)
class BrowserInstallation:
    backend: str
    name: str
    channel: str
    path: str
    version: str


@dataclass
class BrowserInstallRecommendation:
    backend: str
    browser_name: str
    browser_version: str = ""
    browser_download_url: str = ""
    driver_version: str = ""
    driver_download_url: str = ""
    official_browser_url: str = ""
    official_driver_url: str = ""
    message: str = ""


@dataclass
class DriverPreparationResult:
    backend: str
    browser_path: str = ""
    browser_version: str = ""
    driver_path: str = ""
    driver_version: str = ""
    compatible: bool = False
    downloaded: bool = False
    message: str = ""
    official_driver_url: str = ""
    official_browser_url: str = ""


@dataclass
class BrowserPreparationResult:
    backend: str
    browser_path: str = ""
    browser_version: str = ""
    downloaded: bool = False
    source: str = ""
    message: str = ""


@dataclass
class PortableEnvironmentUpdateResult:
    backend: str
    browser_path: str = ""
    browser_version: str = ""
    driver_path: str = ""
    driver_version: str = ""
    browser_updated: bool = False
    driver_updated: bool = False
    fully_latest: bool = False
    latest_browser_version: str = ""
    message: str = ""


def _backend_key(backend: str) -> str:
    return "selenium_edge" if str(backend).lower() in {"edge", "selenium_edge", "msedge"} else "selenium_chrome"


def browser_family(backend: str) -> str:
    return "edge" if _backend_key(backend) == "selenium_edge" else "chrome"


def _browser_path_family_hint(path: str | Path) -> str:
    """Infer a Chromium browser family from an executable path.

    The hint is intentionally conservative: it only returns ``chrome`` or
    ``edge`` when the executable/file hierarchy makes the family unambiguous.
    Unknown custom Chromium builds return an empty string and are validated by
    their executable version instead of being rejected up front.
    """
    try:
        p = Path(str(path or "").strip().strip('"'))
    except Exception:
        return ""
    name = p.name.lower()
    if name in {"msedge.exe", "msedge"} or "microsoft edge" in str(p).lower():
        return "edge"
    if name in {"chrome.exe", "chrome", "google chrome", "chrome for testing", "chromium", "chromium-browser"}:
        return "chrome"
    low = str(p).replace("\\", "/").lower()
    if "/microsoft/edge" in low or "/edge beta/" in low or "/edge dev/" in low or "/edge sxs/" in low:
        return "edge"
    if "/google/chrome" in low or "/chrome for testing" in low or "/chromium" in low:
        return "chrome"
    return ""


def official_driver_url(backend: str) -> str:
    return EDGE_DRIVER_PAGE if browser_family(backend) == "edge" else CHROME_DRIVER_PAGE


def official_browser_url(backend: str) -> str:
    return EDGE_BROWSER_PAGE if browser_family(backend) == "edge" else CHROME_BROWSER_PAGE


def _version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(value).strip().split("."))
    except Exception:
        return tuple()


def _first_three(value: str) -> tuple[int, int, int] | tuple[()]:
    parts = _version_tuple(value)
    return parts[:3] if len(parts) >= 3 else tuple()


def versions_compatible(browser_version: str, driver_version: str, backend: str) -> bool:
    """Chrome/Edge drivers must match the browser major/minor/build triplet."""
    b = _first_three(browser_version)
    d = _first_three(driver_version)
    return bool(b and d and b == d)


def _read_file_version_windows(path: Path) -> str:
    """Read the Windows file version without requiring pywin32."""
    if os.name != "nt":
        return ""
    try:
        version = ctypes.windll.version
        version.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint)]
        version.GetFileVersionInfoSizeW.restype = ctypes.c_uint
        version.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        version.GetFileVersionInfoW.restype = ctypes.c_int
        version.VerQueryValueW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint)]
        version.VerQueryValueW.restype = ctypes.c_int
        dummy = ctypes.c_uint(0)
        size = version.GetFileVersionInfoSizeW(str(path), ctypes.byref(dummy))
        if not size:
            return ""
        buf = ctypes.create_string_buffer(size)
        if not version.GetFileVersionInfoW(str(path), 0, size, buf):
            return ""
        value_ptr = ctypes.c_void_p()
        value_len = ctypes.c_uint(0)
        if not version.VerQueryValueW(buf, "\\", ctypes.byref(value_ptr), ctypes.byref(value_len)):
            return ""

        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ("dwSignature", ctypes.c_uint32), ("dwStrucVersion", ctypes.c_uint32),
                ("dwFileVersionMS", ctypes.c_uint32), ("dwFileVersionLS", ctypes.c_uint32),
                ("dwProductVersionMS", ctypes.c_uint32), ("dwProductVersionLS", ctypes.c_uint32),
                ("dwFileFlagsMask", ctypes.c_uint32), ("dwFileFlags", ctypes.c_uint32),
                ("dwFileOS", ctypes.c_uint32), ("dwFileType", ctypes.c_uint32),
                ("dwFileSubtype", ctypes.c_uint32), ("dwFileDateMS", ctypes.c_uint32),
                ("dwFileDateLS", ctypes.c_uint32),
            ]

        ffi = ctypes.cast(value_ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        ms = ffi.dwProductVersionMS or ffi.dwFileVersionMS
        ls = ffi.dwProductVersionLS or ffi.dwFileVersionLS
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return ""


def executable_version(path: str | Path) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    if sys.platform == "darwin":
        # Reading the app bundle plist is faster and more reliable than
        # launching Chrome/Edge with --version, especially when the browser is
        # already running.
        try:
            app_root = next((parent for parent in p.parents if parent.suffix.lower() == ".app"), None)
            if app_root is not None:
                info = app_root / "Contents" / "Info.plist"
                if info.exists():
                    with info.open("rb") as fh:
                        payload = plistlib.load(fh)
                    value = str(payload.get("CFBundleShortVersionString") or payload.get("CFBundleVersion") or "")
                    match = VERSION_RE.search(value)
                    if match:
                        return match.group(1)
        except Exception:
            pass
    value = _read_file_version_windows(p)
    if VERSION_RE.fullmatch(value or ""):
        return value
    if os.name == "nt":
        # PowerShell is a reliable Windows fallback and reads file metadata
        # without launching the browser process itself.
        try:
            escaped = str(p).replace("'", "''")
            command = f"(Get-Item -LiteralPath '{escaped}').VersionInfo.ProductVersion"
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True, text=True, timeout=8, creationflags=flags,
            )
            m = VERSION_RE.search(f"{proc.stdout}\n{proc.stderr}")
            if m:
                return m.group(1)
        except Exception:
            return ""
        return ""
    try:
        proc = subprocess.run([str(p), "--version"], capture_output=True, text=True, timeout=8)
        text = f"{proc.stdout}\n{proc.stderr}"
        m = VERSION_RE.search(text)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _registry_app_paths(exe_name: str) -> list[Path]:
    if os.name != "nt":
        return []
    try:
        import winreg
    except Exception:
        return []
    out: list[Path] = []
    subkey = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
    roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
    views = [0]
    for flag_name in ("KEY_WOW64_64KEY", "KEY_WOW64_32KEY"):
        flag = getattr(winreg, flag_name, 0)
        if flag and flag not in views:
            views.append(flag)
    for root in roots:
        for view in views:
            try:
                with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | view) as key:
                    value, _ = winreg.QueryValueEx(key, None)
                if value:
                    out.append(Path(str(value).strip().strip('"')))
            except Exception:
                continue
    return out


def _browser_candidates(backend: str) -> list[tuple[str, str, Path]]:
    """Return likely Chrome/Edge executable locations on Windows, macOS and Linux."""
    backend = _backend_key(backend)
    entries: list[tuple[str, str, Path]] = []

    if os.name == "nt":
        env = os.environ
        pf = Path(env.get("PROGRAMFILES", r"C:\Program Files"))
        pfx86 = Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        local = Path(env.get("LOCALAPPDATA", "")) if env.get("LOCALAPPDATA") else None
        if backend == "selenium_edge":
            for base in (pfx86, pf):
                entries.extend([
                    ("Microsoft Edge", "stable", base / "Microsoft/Edge/Application/msedge.exe"),
                    ("Microsoft Edge Beta", "beta", base / "Microsoft/Edge Beta/Application/msedge.exe"),
                    ("Microsoft Edge Dev", "dev", base / "Microsoft/Edge Dev/Application/msedge.exe"),
                    ("Microsoft Edge Canary", "canary", base / "Microsoft/Edge SxS/Application/msedge.exe"),
                ])
            if local:
                entries.extend([
                    ("Microsoft Edge", "stable", local / "Microsoft/Edge/Application/msedge.exe"),
                    ("Microsoft Edge Beta", "beta", local / "Microsoft/Edge Beta/Application/msedge.exe"),
                    ("Microsoft Edge Dev", "dev", local / "Microsoft/Edge Dev/Application/msedge.exe"),
                    ("Microsoft Edge Canary", "canary", local / "Microsoft/Edge SxS/Application/msedge.exe"),
                ])
            for candidate in _registry_app_paths("msedge.exe"):
                entries.insert(0, ("Microsoft Edge", "stable", candidate))
            found = shutil.which("msedge") or shutil.which("msedge.exe")
            if found:
                entries.insert(0, ("Microsoft Edge", "stable", Path(found)))
        else:
            for base in (pf, pfx86):
                entries.extend([
                    ("Google Chrome", "stable", base / "Google/Chrome/Application/chrome.exe"),
                    ("Google Chrome Beta", "beta", base / "Google/Chrome Beta/Application/chrome.exe"),
                    ("Google Chrome Dev", "dev", base / "Google/Chrome Dev/Application/chrome.exe"),
                    ("Google Chrome Canary", "canary", base / "Google/Chrome SxS/Application/chrome.exe"),
                    ("Chrome for Testing", "testing", base / "Google/Chrome for Testing/Application/chrome.exe"),
                ])
            if local:
                entries.extend([
                    ("Google Chrome", "stable", local / "Google/Chrome/Application/chrome.exe"),
                    ("Google Chrome Beta", "beta", local / "Google/Chrome Beta/Application/chrome.exe"),
                    ("Google Chrome Dev", "dev", local / "Google/Chrome Dev/Application/chrome.exe"),
                    ("Google Chrome Canary", "canary", local / "Google/Chrome SxS/Application/chrome.exe"),
                    ("Chrome for Testing", "testing", local / "Google/Chrome for Testing/Application/chrome.exe"),
                ])
            for candidate in _registry_app_paths("chrome.exe"):
                entries.insert(0, ("Google Chrome", "stable", candidate))
            found = shutil.which("chrome") or shutil.which("chrome.exe") or shutil.which("google-chrome")
            if found:
                entries.insert(0, ("Google Chrome", "stable", Path(found)))
        return entries

    if sys.platform == "darwin":
        roots = [Path('/Applications'), Path.home() / 'Applications']
        if backend == "selenium_edge":
            apps = [
                ("Microsoft Edge", "stable", "Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                ("Microsoft Edge Beta", "beta", "Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta"),
                ("Microsoft Edge Dev", "dev", "Microsoft Edge Dev.app/Contents/MacOS/Microsoft Edge Dev"),
                ("Microsoft Edge Canary", "canary", "Microsoft Edge Canary.app/Contents/MacOS/Microsoft Edge Canary"),
            ]
        else:
            apps = [
                ("Google Chrome", "stable", "Google Chrome.app/Contents/MacOS/Google Chrome"),
                ("Google Chrome Beta", "beta", "Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta"),
                ("Google Chrome Dev", "dev", "Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev"),
                ("Google Chrome Canary", "canary", "Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"),
                ("Chrome for Testing", "testing", "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
            ]
        for root in roots:
            for name, channel, rel in apps:
                entries.append((name, channel, root / rel))
        commands = ("microsoft-edge", "microsoft-edge-stable") if backend == "selenium_edge" else ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
        for command in commands:
            found = shutil.which(command)
            if found:
                entries.insert(0, (("Microsoft Edge" if backend == "selenium_edge" else "Google Chrome"), "stable", Path(found)))
        return entries

    # Linux and other Unix-like systems.
    if backend == "selenium_edge":
        commands = ("microsoft-edge", "microsoft-edge-stable", "microsoft-edge-beta", "microsoft-edge-dev")
        names = {
            "microsoft-edge": ("Microsoft Edge", "stable"),
            "microsoft-edge-stable": ("Microsoft Edge", "stable"),
            "microsoft-edge-beta": ("Microsoft Edge Beta", "beta"),
            "microsoft-edge-dev": ("Microsoft Edge Dev", "dev"),
        }
    else:
        commands = ("google-chrome", "google-chrome-stable", "google-chrome-beta", "google-chrome-unstable", "chromium", "chromium-browser")
        names = {
            "google-chrome": ("Google Chrome", "stable"),
            "google-chrome-stable": ("Google Chrome", "stable"),
            "google-chrome-beta": ("Google Chrome Beta", "beta"),
            "google-chrome-unstable": ("Google Chrome Dev", "dev"),
            "chromium": ("Chromium", "stable"),
            "chromium-browser": ("Chromium", "stable"),
        }
    for command in commands:
        found = shutil.which(command)
        if found:
            name, channel = names[command]
            entries.append((name, channel, Path(found)))
    return entries


def _application_roots(app_root: str | Path | None = None) -> list[Path]:
    """Return likely WebLens roots for bundled/managed portable browsers."""
    roots: list[Path] = []
    if app_root:
        roots.append(Path(app_root))
    roots.append(user_data_root())
    roots.extend(resource_roots())
    roots.append(Path(__file__).resolve().parent.parent)
    roots.append(Path.cwd())
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            resolved = root.expanduser().resolve()
        except Exception:
            resolved = root.expanduser()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
    return out


def _portable_browser_candidates(backend: str, app_root: str | Path | None = None) -> list[tuple[str, str, Path]]:
    """Discover browser executables already bundled under WebLens ``tools``.

    Portable browsers are a normal discovery source and are deliberately
    preferred over system-installed browsers. This keeps WebLens collection
    isolated from the user's everyday browser installation and update cycle.
    """
    backend = _backend_key(backend)
    family = browser_family(backend)
    wanted_names: tuple[str, ...]
    if os.name == "nt":
        wanted_names = ("msedge.exe",) if family == "edge" else ("chrome.exe",)
    elif sys.platform == "darwin":
        wanted_names = ("Microsoft Edge",) if family == "edge" else ("Google Chrome", "Chrome for Testing")
    else:
        wanted_names = ("microsoft-edge", "msedge") if family == "edge" else ("chrome", "google-chrome", "chromium")

    entries: list[tuple[str, str, Path]] = []
    seen: set[str] = set()
    for root in _application_roots(app_root):
        tools = root / "tools"
        if not tools.exists():
            continue
        search_roots = [tools / "browser", tools / "browsers"]
        # Also accept a user-supplied portable browser anywhere below tools.
        search_roots.append(tools)
        for search_root in search_roots:
            if not search_root.exists():
                continue
            for wanted in wanted_names:
                try:
                    candidates = search_root.rglob(wanted)
                    for path in candidates:
                        if not path.is_file():
                            continue
                        # Avoid accidentally treating helper/driver paths as browsers.
                        low = str(path).replace("\\", "/").lower()
                        if "/drivers/" in low or "chromedriver" in path.name.lower() or "msedgedriver" in path.name.lower():
                            continue
                        try:
                            resolved = path.resolve()
                        except Exception:
                            resolved = path
                        key = os.path.normcase(str(resolved))
                        if key in seen:
                            continue
                        seen.add(key)
                        name = ("Microsoft Edge (WebLens portable)" if family == "edge" else "Chrome for Testing (WebLens portable)")
                        entries.append((name, "portable", resolved))
                except Exception:
                    continue
    return entries


def detect_browser_installations(backend: str | None = None, app_root: str | Path | None = None) -> list[BrowserInstallation]:
    backends = [_backend_key(backend)] if backend else ["selenium_chrome", "selenium_edge"]
    out: list[BrowserInstallation] = []
    seen: set[str] = set()
    for be in backends:
        # WebLens-managed portable browsers are preferred. System installations
        # remain available only as an explicit opt-in fallback in the UI.
        combined = list(_portable_browser_candidates(be, app_root=app_root)) + list(_browser_candidates(be))
        for name, channel, path in combined:
            try:
                resolved = path.expanduser().resolve()
            except Exception:
                resolved = path.expanduser()
            key = os.path.normcase(str(resolved))
            if key in seen:
                continue
            try:
                exists = resolved.exists() and resolved.is_file()
            except Exception:
                exists = False
            if not exists:
                continue
            seen.add(key)
            out.append(BrowserInstallation(be, name, channel, str(resolved), executable_version(resolved)))
    channel_rank = {"portable": 0, "stable": 1, "beta": 2, "dev": 3, "canary": 4, "testing": 5, "custom": 6}
    out.sort(key=lambda x: (0 if x.backend == "selenium_chrome" else 1, channel_rank.get(x.channel, 9), x.path.lower()))
    return out

def installation_for_path(path: str, backend: str) -> BrowserInstallation | None:
    p = str(path or "").strip().strip('"')
    if not p:
        return None
    expected_family = browser_family(backend)
    hinted_family = _browser_path_family_hint(p)
    if hinted_family and hinted_family != expected_family:
        return None
    target = os.path.normcase(os.path.abspath(p))
    for inst in detect_browser_installations(backend):
        if os.path.normcase(os.path.abspath(inst.path)) == target:
            return inst
    pp = Path(p)
    if pp.exists() and pp.is_file():
        fam = browser_family(backend)
        name = "Microsoft Edge" if fam == "edge" else "Google Chrome"
        return BrowserInstallation(_backend_key(backend), name, "custom", str(pp.resolve()), executable_version(pp))
    return None


def browser_source_key(source: str | None) -> str:
    return "system" if str(source or "").strip().lower() in {"system", "installed", "system_installed"} else "portable"


def browser_installations_for_source(
    backend: str,
    source: str = "portable",
    app_root: str | Path | None = None,
) -> list[BrowserInstallation]:
    """Return installations allowed by the selected browser-source policy."""
    wanted = browser_source_key(source)
    installs = detect_browser_installations(backend, app_root=app_root)
    if wanted == "portable":
        return [x for x in installs if x.channel == "portable"]
    return [x for x in installs if x.channel != "portable"]


def preferred_browser_path(
    backend: str,
    app_root: str | Path | None = None,
    source: str = "portable",
) -> str:
    """Return the preferred browser under the requested source policy.

    The caller chooses the source policy. WebLens defaults Chrome to a managed
    portable Chrome for Testing build, while Microsoft Edge defaults to the
    system-installed browser because Microsoft does not publish an equivalent
    portable Edge ZIP.
    """
    installs = browser_installations_for_source(backend, source=source, app_root=app_root)
    if not installs:
        return ""
    if browser_source_key(source) == "system":
        stable = next((x for x in installs if x.channel == "stable"), None)
        return (stable or installs[0]).path
    # Multiple WebLens-managed portable versions may coexist so a failed
    # update never destroys the last working environment. Always prefer the
    # newest detected portable browser instead of relying on path ordering.
    newest = max(installs, key=lambda x: _version_tuple(x.version or "0.0.0.0"))
    return newest.path

def driver_executable_name(backend: str) -> str:
    return "msedgedriver.exe" if browser_family(backend) == "edge" and os.name == "nt" else (
        "msedgedriver" if browser_family(backend) == "edge" else ("chromedriver.exe" if os.name == "nt" else "chromedriver")
    )


def driver_version(path: str | Path) -> str:
    return executable_version(path)


def _driver_search_roots(app_root: str | Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if app_root:
        roots.append(Path(app_root) / "tools")
    roots.append(user_data_root() / "tools")
    for base in resource_roots():
        roots.append(base / "tools")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "BFSU_WebLens" / "drivers")
    roots.append(user_cache_root() / "drivers")
    roots.append(Path.home() / ".cache" / "selenium")
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = os.path.normcase(str(root))
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def find_compatible_driver(backend: str, browser_version: str, candidates: Iterable[str | Path] = (), app_root: str | Path | None = None) -> tuple[str, str]:
    name = driver_executable_name(backend).lower()
    checked: set[str] = set()
    paths: list[Path] = [Path(p) for p in candidates if str(p or "").strip()]
    for root in _driver_search_roots(app_root):
        try:
            if root.exists():
                paths.extend(p for p in root.rglob("*") if p.is_file() and p.name.lower() == name)
        except Exception:
            continue
    found = shutil.which(driver_executable_name(backend))
    if found:
        paths.append(Path(found))
    best: tuple[tuple[int, ...], str, str] | None = None
    for p in paths:
        try:
            rp = p.expanduser().resolve()
        except Exception:
            rp = p.expanduser()
        key = os.path.normcase(str(rp))
        if key in checked:
            continue
        checked.add(key)
        if not rp.exists() or not rp.is_file():
            continue
        ver = driver_version(rp)
        if not versions_compatible(browser_version, ver, backend):
            continue
        vt = _version_tuple(ver)
        if best is None or vt > best[0]:
            best = (vt, str(rp), ver)
    return (best[1], best[2]) if best else ("", "")


def _requests_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "BFSU-WebLens/2 BrowserDriverManager"})
    return session


def _windows_driver_platform() -> str:
    return "win64" if struct.calcsize("P") * 8 >= 64 else "win32"


def _chrome_driver_asset(browser_version: str, timeout: int = 30) -> tuple[str, str]:
    parts = browser_version.split(".")
    if len(parts) < 3:
        raise RuntimeError(f"Cannot resolve ChromeDriver for browser version: {browser_version or 'unknown'}")
    build = ".".join(parts[:3])
    major = parts[0]
    session = _requests_session()
    entries: list[dict] = []
    try:
        resp = session.get(CHROME_CFT_BUILD_JSON, timeout=timeout)
        resp.raise_for_status()
        entry = (resp.json().get("builds") or {}).get(build)
        if entry:
            entries.append(entry)
    except Exception:
        pass
    if not entries:
        resp = session.get(CHROME_CFT_MILESTONE_JSON, timeout=timeout)
        resp.raise_for_status()
        entry = (resp.json().get("milestones") or {}).get(major)
        if entry:
            entries.append(entry)
    if not entries:
        raise RuntimeError(f"No ChromeDriver release was found for Chrome {browser_version}.")
    platform_key = _windows_driver_platform() if os.name == "nt" else ("mac-arm64" if sys.platform == "darwin" and platform.machine().lower() in {"arm64", "aarch64"} else "mac-x64" if sys.platform == "darwin" else "linux-arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "linux64")
    for entry in entries:
        version = str(entry.get("version") or "")
        downloads = (entry.get("downloads") or {}).get("chromedriver") or []
        for asset in downloads:
            if asset.get("platform") == platform_key and asset.get("url"):
                if versions_compatible(browser_version, version, "selenium_chrome"):
                    return version, str(asset["url"])
    raise RuntimeError(f"No compatible ChromeDriver {platform_key} download was found for Chrome {browser_version}.")


def _decode_text_response(content: bytes) -> str:
    for enc in ("utf-16", "utf-8-sig", "utf-8", "latin-1"):
        try:
            text = content.decode(enc).strip().strip("\ufeff\x00")
            m = VERSION_RE.search(text)
            if m:
                return m.group(1)
        except Exception:
            continue
    return ""


def _edge_driver_asset(browser_version: str, timeout: int = 30) -> tuple[str, str]:
    parts = browser_version.split(".")
    if len(parts) < 3:
        raise RuntimeError(f"Cannot resolve EdgeDriver for browser version: {browser_version or 'unknown'}")
    build_prefix = ".".join(parts[:3]) + "."
    if os.name == "nt":
        zip_name = "edgedriver_win64.zip" if _windows_driver_platform() == "win64" else "edgedriver_win32.zip"
    elif sys.platform == "darwin":
        zip_name = "edgedriver_mac64_m1.zip" if platform.machine().lower() in {"arm64", "aarch64"} else "edgedriver_mac64.zip"
    else:
        zip_name = "edgedriver_linux64.zip"
    session = _requests_session()

    # Microsoft publishes all EdgeDriver artifacts in an Azure blob catalogue.
    # Querying only the browser build prefix lets us choose the newest patch
    # whose first three version components match the installed Edge build.
    try:
        resp = session.get(EDGE_DRIVER_CATALOG, params={"restype": "container", "comp": "list", "prefix": build_prefix}, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        candidates: list[str] = []
        for node in root.findall(".//Blob/Name"):
            name = (node.text or "").strip()
            if not name.lower().endswith("/" + zip_name.lower()):
                continue
            ver = name.split("/", 1)[0]
            if versions_compatible(browser_version, ver, "selenium_edge"):
                candidates.append(ver)
        if candidates:
            version = max(candidates, key=_version_tuple)
            return version, f"{EDGE_DRIVER_BASE}/{version}/{zip_name}"
    except Exception:
        pass

    # Fallback used by Microsoft's driver CDN.  Only accept the response when
    # it still matches the installed browser build triplet.
    major = parts[0]
    suffixes = (f"LATEST_RELEASE_{major}_WINDOWS", f"LATEST_RELEASE_{major}") if os.name == "nt" else (f"LATEST_RELEASE_{major}",)
    for suffix in suffixes:
        try:
            resp = session.get(f"{EDGE_DRIVER_BASE}/{suffix}", timeout=timeout)
            resp.raise_for_status()
            version = _decode_text_response(resp.content)
            if version and versions_compatible(browser_version, version, "selenium_edge"):
                return version, f"{EDGE_DRIVER_BASE}/{version}/{zip_name}"
        except Exception:
            continue
    raise RuntimeError(f"No compatible Microsoft Edge WebDriver release was found for Edge {browser_version}.")


def resolve_driver_download(backend: str, browser_version: str, timeout: int = 30) -> tuple[str, str]:
    if browser_family(backend) == "edge":
        return _edge_driver_asset(browser_version, timeout=timeout)
    return _chrome_driver_asset(browser_version, timeout=timeout)



def _current_platform_key_for_chrome() -> str:
    if os.name == "nt":
        return _windows_driver_platform()
    if sys.platform == "darwin":
        return "mac-arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "mac-x64"
    return "linux-arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "linux64"


def latest_browser_recommendation(backend: str, timeout: int = 30) -> BrowserInstallRecommendation:
    """Resolve a current official browser/driver pair for an unconfigured machine."""
    backend = _backend_key(backend)
    family = browser_family(backend)
    result = BrowserInstallRecommendation(
        backend=backend,
        browser_name="Microsoft Edge" if family == "edge" else "Google Chrome",
        official_browser_url=official_browser_url(backend),
        official_driver_url=official_driver_url(backend),
    )
    session = _requests_session()
    try:
        if family == "chrome":
            resp = session.get(CHROME_CFT_LKG_JSON, timeout=timeout)
            resp.raise_for_status()
            stable = (resp.json().get("channels") or {}).get("Stable") or {}
            version = str(stable.get("version") or "")
            downloads = stable.get("downloads") or {}
            platform_key = _current_platform_key_for_chrome()
            browser_asset = next((x for x in downloads.get("chrome", []) if x.get("platform") == platform_key and x.get("url")), None)
            driver_asset = next((x for x in downloads.get("chromedriver", []) if x.get("platform") == platform_key and x.get("url")), None)
            result.browser_version = version
            result.driver_version = version
            result.browser_download_url = str((browser_asset or {}).get("url") or "")
            result.driver_download_url = str((driver_asset or {}).get("url") or "")
            result.message = f"Recommended Stable Chrome for Testing / ChromeDriver pair: {version}." if version else "Open the official Chrome download page."
            return result

        resp = session.get(EDGE_UPDATES_API, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        products = payload if isinstance(payload, list) else []
        stable = next((p for p in products if str(p.get("Product", "")).lower() == "stable"), None)
        releases = list((stable or {}).get("Releases") or [])
        if os.name == "nt":
            wanted_platform, wanted_arch = "Windows", "x64" if _windows_driver_platform() == "win64" else "x86"
        elif sys.platform == "darwin":
            wanted_platform, wanted_arch = "MacOS", "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "x64"
        else:
            wanted_platform, wanted_arch = "Linux", "x64"
        matching = [r for r in releases if str(r.get("Platform", "")).lower() == wanted_platform.lower() and str(r.get("Architecture", "")).lower() == wanted_arch.lower()]
        if not matching:
            matching = [r for r in releases if str(r.get("Platform", "")).lower() == wanted_platform.lower()]
        if matching:
            release = max(matching, key=lambda r: _version_tuple(str(r.get("Version") or "")))
            version = str(release.get("Version") or "")
            result.browser_version = version
            artifacts = list(release.get("Artifacts") or [])
            artifact = next((a for a in artifacts if str(a.get("Location") or a.get("location") or "").startswith("http")), None)
            if artifact:
                result.browser_download_url = str(artifact.get("Location") or artifact.get("location") or "")
            if version:
                try:
                    drv_ver, drv_url = _edge_driver_asset(version, timeout=timeout)
                    result.driver_version = drv_ver
                    result.driver_download_url = drv_url
                except Exception:
                    pass
            result.message = f"Recommended Microsoft Edge Stable: {version}." if version else "Open the official Microsoft Edge download page."
            return result
    except Exception as exc:
        result.message = f"Could not resolve a direct latest-version download automatically: {exc}"
    return result


def _extract_browser_archive(archive: zipfile.ZipFile, target_dir: Path) -> None:
    """Safely extract a browser ZIP while preserving Unix modes and symlinks.

    macOS Chrome bundles contain executable helper files and may contain
    symlinks. ``ZipFile.extractall`` does not reliably preserve those details,
    so a plain extraction can produce a browser that looks present but cannot
    launch.
    """
    base = target_dir.resolve()
    for member in archive.infolist():
        destination = (target_dir / member.filename).resolve()
        if base != destination and base not in destination.parents:
            raise RuntimeError("The browser archive contains an unsafe path.")
        mode = (member.external_attr >> 16) & 0xFFFF
        if member.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if mode and stat.S_ISLNK(mode):
            link_target = archive.read(member).decode("utf-8", errors="strict")
            if os.path.isabs(link_target):
                raise RuntimeError("The browser archive contains an unsafe absolute symlink.")
            resolved_target = (destination.parent / link_target).resolve()
            if base != resolved_target and base not in resolved_target.parents:
                raise RuntimeError("The browser archive contains a symlink outside the target folder.")
            try:
                destination.unlink(missing_ok=True)
            except Exception:
                pass
            os.symlink(link_target, destination)
            continue
        with archive.open(member, "r") as src, destination.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        permissions = stat.S_IMODE(mode)
        if permissions:
            try:
                destination.chmod(permissions)
            except Exception:
                pass


def _preferred_browser_root(app_root: str | Path | None = None) -> Path:
    """Choose a writable root for WebLens-managed portable browsers."""
    candidates: list[Path] = []
    if app_root:
        candidates.append(Path(app_root) / "tools" / "browser")
    for root in _application_roots(app_root):
        candidates.append(root / "tools" / "browser")
    # Fallback for read-only application bundles. Source/portable Windows
    # builds normally use the application-local tools folder above.
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "BFSU_WebLens" / "browser")
    candidates.append(user_data_root() / "tools" / "browser")
    candidates.append(user_cache_root() / "browser")
    seen: set[str] = set()
    for root in candidates:
        key = os.path.normcase(str(root))
        if key in seen:
            continue
        seen.add(key)
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return root
        except Exception:
            continue
    raise RuntimeError("No writable folder is available for portable browser downloads.")


def download_portable_browser(
    backend: str,
    app_root: str | Path | None = None,
    timeout: int = 180,
    progress: Callable[[int, str], None] | None = None,
) -> BrowserPreparationResult:
    """Download and configure an official non-install Chrome browser archive.

    Chrome for Testing is Google's official ZIP-distributed Chrome build and is
    suitable as a WebLens-managed portable browser. Microsoft Edge does not
    currently publish an equivalent official portable ZIP; bundled portable
    Edge copies under ``tools`` are still auto-detected, but automatic Edge
    browser download is therefore intentionally not faked from MSI/PKG files.
    """
    backend = _backend_key(backend)
    family = browser_family(backend)
    if family != "chrome":
        raise RuntimeError(
            "Microsoft does not publish an official portable Edge ZIP comparable to Chrome for Testing. "
            "Install Edge normally or place a portable Edge build under the WebLens tools folder; WebLens will detect it automatically."
        )

    def report(value: int, text: str) -> None:
        if progress:
            try:
                progress(max(0, min(100, int(value))), text)
            except Exception:
                pass

    report(2, "Resolving the recommended portable Chrome build…")
    recommendation = latest_browser_recommendation(backend, timeout=min(30, timeout))
    version = str(recommendation.browser_version or "").strip()
    url = str(recommendation.browser_download_url or "").strip()
    if not version or not url:
        raise RuntimeError("Could not resolve the official Chrome for Testing portable download.")

    root = _preferred_browser_root(app_root)
    target_dir = root / "chrome" / version
    exe_name = "chrome.exe" if os.name == "nt" else ("Google Chrome" if sys.platform == "darwin" else "chrome")
    if target_dir.exists():
        matches = [p for p in target_dir.rglob(exe_name) if p.is_file()]
        if matches:
            existing = matches[0]
            existing_version = executable_version(existing) or version
            report(100, f"Portable Chrome {existing_version} is already available.")
            return BrowserPreparationResult(
                backend=backend, browser_path=str(existing.resolve()), browser_version=existing_version,
                downloaded=False, source="tools", message=f"Portable Chrome {existing_version} is ready."
            )

    target_dir.mkdir(parents=True, exist_ok=True)
    tmp_zip = target_dir / ".browser_download.zip"
    report(5, f"Downloading portable Chrome {version}…")
    session = _requests_session()
    try:
        with session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            with tmp_zip.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        report(5 + int(70 * min(downloaded, total) / total), f"Downloading portable Chrome {version}…")
        report(78, "Extracting portable Chrome into the WebLens tools folder…")
        with zipfile.ZipFile(tmp_zip) as archive:
            _extract_browser_archive(archive, target_dir)
        report(92, "Detecting the extracted browser executable…")
        matches = [p for p in target_dir.rglob(exe_name) if p.is_file()]
        if not matches:
            # macOS bundle executable can have a different visible file name.
            if sys.platform == "darwin":
                matches = [p for p in target_dir.rglob("Chrome for Testing") if p.is_file()]
        if not matches:
            raise RuntimeError("The portable browser archive was extracted, but the Chrome executable could not be found.")
        browser_path = matches[0]
        if os.name != "nt":
            try:
                browser_path.chmod(browser_path.stat().st_mode | 0o111)
            except Exception:
                pass
        actual_version = executable_version(browser_path) or version
        report(100, f"Portable Chrome {actual_version} is configured.")
        return BrowserPreparationResult(
            backend=backend,
            browser_path=str(browser_path.resolve()),
            browser_version=actual_version,
            downloaded=True,
            source="tools",
            message=f"Portable Chrome {actual_version} was downloaded and configured automatically.",
        )
    finally:
        try:
            tmp_zip.unlink(missing_ok=True)
        except Exception:
            pass


def _preferred_driver_root(app_root: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if app_root:
        candidates.append(Path(app_root) / "tools" / "drivers")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "BFSU_WebLens" / "drivers")
    candidates.append(user_data_root() / "tools" / "drivers")
    candidates.append(user_cache_root() / "drivers")
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return root
        except Exception:
            continue
    raise RuntimeError("No writable folder is available for WebDriver downloads.")


def download_driver(
    backend: str,
    browser_version: str,
    app_root: str | Path | None = None,
    timeout: int = 60,
    progress: Callable[[int, str], None] | None = None,
) -> DriverPreparationResult:
    result = DriverPreparationResult(
        backend=_backend_key(backend), browser_version=browser_version,
        official_driver_url=official_driver_url(backend), official_browser_url=official_browser_url(backend),
    )

    def report(value: int, text: str) -> None:
        if progress:
            try:
                progress(max(0, min(100, int(value))), text)
            except Exception:
                pass

    family = browser_family(backend)
    report(3, f"Resolving the matching {family} WebDriver…")
    version, url = resolve_driver_download(backend, browser_version, timeout=min(timeout, 30))
    root = _preferred_driver_root(app_root)
    target_dir = root / family / version
    target_dir.mkdir(parents=True, exist_ok=True)
    exe_name = driver_executable_name(backend)
    target = target_dir / exe_name
    tmp_zip = target_dir / ".driver_download.zip"
    tmp_exe = target.with_suffix(target.suffix + ".tmp")

    report(8, f"Downloading {family} WebDriver {version}…")
    session = _requests_session()
    try:
        with session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            with tmp_zip.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        report(8 + int(72 * min(downloaded, total) / total), f"Downloading {family} WebDriver {version}…")
        report(83, f"Extracting {family} WebDriver {version}…")
        with zipfile.ZipFile(tmp_zip) as archive:
            member = next((n for n in archive.namelist() if Path(n).name.lower() == exe_name.lower()), None)
            if not member:
                raise RuntimeError(f"Downloaded archive does not contain {exe_name}.")
            tmp_exe.write_bytes(archive.read(member))
        if os.name != "nt":
            tmp_exe.chmod(0o755)
        os.replace(tmp_exe, target)
        report(94, "Checking browser/WebDriver version compatibility…")
        actual = driver_version(target)
        if not versions_compatible(browser_version, actual or version, backend):
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Downloaded driver {actual or version} does not match browser {browser_version}.")
        result.driver_path = str(target.resolve())
        result.driver_version = actual or version
        result.compatible = True
        result.downloaded = True
        result.message = f"Downloaded matching {family} driver {result.driver_version}."
        report(100, result.message)
        return result
    finally:
        try:
            tmp_zip.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            tmp_exe.unlink(missing_ok=True)
        except Exception:
            pass


def update_portable_environment(
    backend: str,
    app_root: str | Path | None = None,
    timeout: int = 180,
    progress: Callable[[int, str], None] | None = None,
) -> PortableEnvironmentUpdateResult:
    """Update the WebLens-managed portable browser environment safely.

    Chrome is updated to the current official Chrome for Testing Stable build
    and ChromeDriver is then downloaded for that exact browser version. Older
    WebLens-managed versions are deliberately kept so a failed update never
    removes the last working environment.

    Microsoft does not publish an equivalent official portable Edge ZIP. For
    a bundled portable Edge, WebLens therefore keeps the browser binary intact
    and refreshes EdgeDriver to the newest release compatible with that exact
    browser build. If the bundled Edge is older than Microsoft's current Stable
    release, the result explains that the browser itself cannot be updated
    automatically without replacing the portable Edge files manually.
    """
    backend = _backend_key(backend)
    family = browser_family(backend)

    def report(value: int, text: str) -> None:
        if progress:
            try:
                progress(max(0, min(100, int(value))), text)
            except Exception:
                pass

    result = PortableEnvironmentUpdateResult(backend=backend)
    current_path = preferred_browser_path(backend, app_root=app_root, source="portable")
    current_inst = installation_for_path(current_path, backend) if current_path else None
    current_browser_version = current_inst.version if current_inst else ""

    if family == "chrome":
        report(2, "Checking the latest official portable Chrome version…")
        browser_result = download_portable_browser(
            backend,
            app_root=app_root,
            timeout=timeout,
            progress=lambda value, message: report(3 + int(value * 0.55), message),
        )
        result.browser_path = browser_result.browser_path
        result.browser_version = browser_result.browser_version
        result.latest_browser_version = browser_result.browser_version
        result.browser_updated = bool(
            browser_result.downloaded
            or not current_browser_version
            or _version_tuple(result.browser_version) > _version_tuple(current_browser_version)
        )
        if not result.browser_path or not result.browser_version:
            raise RuntimeError("The latest portable Chrome was prepared, but its executable/version could not be resolved.")

        report(60, f"Updating ChromeDriver for Chrome {result.browser_version}…")
        driver_result = download_driver(
            backend,
            result.browser_version,
            app_root=app_root,
            timeout=min(timeout, 120),
            progress=lambda value, message: report(60 + int(value * 0.39), message),
        )
        result.driver_path = driver_result.driver_path
        result.driver_version = driver_result.driver_version
        result.driver_updated = bool(driver_result.downloaded)
        result.fully_latest = bool(
            driver_result.compatible
            and result.driver_path
            and versions_compatible(result.browser_version, result.driver_version, backend)
        )
        if not result.fully_latest:
            raise RuntimeError(
                f"The portable Chrome update finished, but ChromeDriver {result.driver_version or '?'} "
                f"does not match Chrome {result.browser_version}."
            )
        result.message = (
            f"WebLens portable Chrome {result.browser_version} and ChromeDriver "
            f"{result.driver_version} are current and matched."
        )
        report(100, result.message)
        return result

    # Edge portable binaries can be bundled/discovered, but there is no
    # official Edge portable ZIP that WebLens can safely replace automatically.
    if not current_inst or not current_inst.version:
        raise RuntimeError(
            "No WebLens-portable Edge browser is available under tools/browser. "
            "WebLens cannot download a portable Edge browser automatically because Microsoft "
            "does not publish an official portable Edge ZIP."
        )
    result.browser_path = current_inst.path
    result.browser_version = current_inst.version
    report(10, f"Checking current Microsoft Edge Stable against bundled Edge {result.browser_version}…")
    latest = latest_browser_recommendation(backend, timeout=min(timeout, 30))
    latest_edge_version = str(latest.browser_version or "").strip()
    result.latest_browser_version = latest_edge_version

    report(35, f"Updating EdgeDriver for bundled Edge {result.browser_version}…")
    driver_result = download_driver(
        backend,
        result.browser_version,
        app_root=app_root,
        timeout=min(timeout, 120),
        progress=lambda value, message: report(35 + int(value * 0.64), message),
    )
    result.driver_path = driver_result.driver_path
    result.driver_version = driver_result.driver_version
    result.driver_updated = bool(driver_result.downloaded)
    browser_is_latest = bool(
        latest_edge_version
        and _version_tuple(result.browser_version) >= _version_tuple(latest_edge_version)
    )
    result.fully_latest = bool(
        browser_is_latest
        and driver_result.compatible
        and versions_compatible(result.browser_version, result.driver_version, backend)
    )
    if browser_is_latest:
        result.message = (
            f"Bundled Edge {result.browser_version} is current and EdgeDriver "
            f"{result.driver_version} is the newest compatible release."
        )
    else:
        suffix = f" (current Microsoft Stable: {latest_edge_version})" if latest_edge_version else ""
        result.message = (
            f"EdgeDriver {result.driver_version} was updated for bundled Edge {result.browser_version}. "
            f"The Edge browser itself was not replaced automatically{suffix} because Microsoft does not "
            "publish an official portable Edge ZIP. Replace the bundled Edge files manually if you need the newest browser build."
        )
    report(100, result.message)
    return result


def ensure_driver(
    backend: str,
    browser_path: str,
    explicit_driver_path: str = "",
    app_root: str | Path | None = None,
    allow_download: bool = True,
    timeout: int = 60,
    progress: Callable[[int, str], None] | None = None,
) -> DriverPreparationResult:
    backend = _backend_key(backend)

    def report(value: int, text: str) -> None:
        if progress:
            try:
                progress(max(0, min(100, int(value))), text)
            except Exception:
                pass

    result = DriverPreparationResult(
        backend=backend, browser_path=str(browser_path or "").strip().strip('"'),
        official_driver_url=official_driver_url(backend), official_browser_url=official_browser_url(backend),
    )
    report(2, "Checking the selected browser…")
    inst = installation_for_path(result.browser_path, backend) if result.browser_path else None
    if not inst:
        preferred = preferred_browser_path(backend, app_root=app_root)
        inst = installation_for_path(preferred, backend) if preferred else None
    if not inst:
        result.message = "No usable browser was detected for the selected configuration."
        return result
    result.browser_path = inst.path
    result.browser_version = inst.version
    if not result.browser_version:
        result.message = f"Browser found at {inst.path}, but its version could not be detected."
        return result

    report(12, f"Browser {result.browser_version} detected. Looking for a compatible WebDriver…")
    candidates = [explicit_driver_path] if explicit_driver_path else []
    driver_path, drv_version = find_compatible_driver(backend, result.browser_version, candidates, app_root=app_root)
    if driver_path:
        result.driver_path = driver_path
        result.driver_version = drv_version
        result.compatible = True
        result.message = f"Matching driver {drv_version} is already available."
        report(100, result.message)
        return result
    if not allow_download:
        result.message = f"No matching driver was found for browser {result.browser_version}."
        return result
    try:
        downloaded = download_driver(
            backend, result.browser_version, app_root=app_root, timeout=timeout,
            progress=lambda value, text: report(18 + int(value * 0.82), text),
        )
        downloaded.browser_path = inst.path
        downloaded.browser_version = inst.version
        report(100, downloaded.message)
        return downloaded
    except Exception as exc:
        result.message = f"Automatic driver download failed: {exc}"
        return result

