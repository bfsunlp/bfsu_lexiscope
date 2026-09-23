# -*- coding: utf-8 -*-
"""Build-time diagnostics shared by Windows and macOS release scripts.

Windows support deliberately understands both PyPI-wheel and Conda Qt layouts.
The runtime probe prepares the DLL search path *before* importing QtCore.
For private release builds it must never re-add the outer activated Conda
environment; package-local DLLs and the private prefix are authoritative.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import platform
import struct
import subprocess
import sys
from pathlib import Path


def norm_arch(value: str) -> str:
    value = (value or "").lower()
    if value in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value


def read_version() -> str:
    namespace: dict[str, object] = {}
    init_py = Path(__file__).resolve().parent / "bfsu_weblens" / "__init__.py"
    exec(init_py.read_text(encoding="utf-8"), namespace)
    return str(namespace.get("__version__", "0.0.0"))


def _unique_existing(paths: list[Path | str | None]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for raw in paths:
        if not raw:
            continue
        try:
            path = Path(raw).expanduser().resolve()
        except Exception:
            continue
        key = os.path.normcase(str(path))
        if key in seen or not path.exists():
            continue
        seen.add(key)
        result.append(path)
    return result


def _package_dir(name: str) -> Path | None:
    try:
        spec = importlib.util.find_spec(name)
    except Exception:
        spec = None
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin).resolve().parent


def candidate_prefixes() -> list[Path]:
    candidates: list[Path | str | None] = [Path(sys.prefix), Path(sys.base_prefix)]
    # Reusing an outer runtime is opt-in only.  A private build launched from
    # an activated Conda environment must not pull <outer>/Library/bin back
    # into DLL resolution, otherwise the wrong Qt6Core.dll can win.
    if os.environ.get("BFSU_WEBLENS_USE_BASE_DLLS") == "1" and not os.environ.get("BFSU_WEBLENS_PRIVATE_BUILD"):
        candidates.append(os.environ.get("BFSU_WEBLENS_BASE_PREFIX"))
    return _unique_existing(candidates)


def candidate_dll_dirs() -> list[Path]:
    if os.name != "nt":
        return []
    candidates: list[Path | str | None] = []
    pyside = _package_dir("PySide6")
    shiboken = _package_dir("shiboken6")
    if pyside:
        candidates.extend([pyside, pyside / "Qt" / "bin"])
    if shiboken:
        candidates.append(shiboken)
    for prefix in candidate_prefixes():
        candidates.extend(
            [
                prefix,
                prefix / "DLLs",
                prefix / "Scripts",
                prefix / "Library" / "bin",
                prefix / "Library" / "usr" / "bin",
            ]
        )
    return _unique_existing(candidates)


def prepare_windows_dll_search() -> list[Path]:
    """Prepare a deterministic Qt/Python DLL search path on Windows.

    PySide6 wheels keep Qt DLLs beside the package while Conda keeps them under
    <prefix>/Library/bin.  Put package-local DLLs first, then the selected
    source environment's native directories.  This prevents an unrelated
    Anaconda base environment from winning DLL resolution through PATH.
    """
    if os.name != "nt":
        return []
    dirs = candidate_dll_dirs()
    if dirs:
        os.environ["PATH"] = os.pathsep.join(str(p) for p in dirs) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        # Keep the handles alive for the lifetime of the process.
        handles = []
        for directory in dirs:
            try:
                handles.append(os.add_dll_directory(str(directory)))
            except OSError:
                pass
        globals()["_DLL_DIRECTORY_HANDLES"] = handles
    return dirs


def _qt_diagnostics() -> list[str]:
    lines: list[str] = []
    pyside = _package_dir("PySide6")
    lines.append(f"PySide6Dir={pyside}")
    for directory in candidate_dll_dirs():
        for name in ("Qt6Core.dll", "shiboken6.abi3.dll", "pyside6.abi3.dll"):
            candidate = directory / name
            if candidate.exists():
                lines.append(f"DLL {name}={candidate}")
    return lines


def cmd_check_base(args: argparse.Namespace) -> int:
    major, minor = sys.version_info[:2]
    bits = struct.calcsize("P") * 8
    machine = norm_arch(platform.machine())
    print(f"Python={sys.version.splitlines()[0]}")
    print(f"Executable={sys.executable}")
    print(f"Prefix={sys.prefix}")
    print(f"BasePrefix={sys.base_prefix}")
    print(f"Platform={sys.platform}")
    print(f"Architecture={machine}")
    print(f"Bits={bits}")
    if bits != 64:
        print("ERROR: A 64-bit Python interpreter is required.", file=sys.stderr)
        return 2
    if not ((major, minor) >= (3, 10) and (major, minor) < (3, 14)):
        print("ERROR: Use Python 3.10, 3.11, 3.12, or 3.13.", file=sys.stderr)
        return 3
    if args.platform == "windows" and os.name != "nt":
        print("ERROR: The Windows package must be built on Windows.", file=sys.stderr)
        return 4
    if args.platform == "macos" and sys.platform != "darwin":
        print("ERROR: The macOS package must be built on macOS.", file=sys.stderr)
        return 5
    if args.arch and norm_arch(args.arch) != machine:
        target = norm_arch(args.arch)
        supported = {machine}
        if sys.platform == "darwin":
            try:
                proc = subprocess.run(["lipo", "-archs", sys.executable], capture_output=True, text=True, timeout=5)
                supported.update(norm_arch(x) for x in proc.stdout.split())
            except Exception:
                pass
        if target not in supported:
            print(f"ERROR: This build needs Python support for {target}; available architecture(s): {sorted(supported)}.", file=sys.stderr)
            print("Use a matching single-architecture Python, a universal2 Python, or Rosetta for an Intel build on Apple Silicon.", file=sys.stderr)
            return 6
    return 0


def cmd_runtime_check(_args: argparse.Namespace) -> int:
    dll_dirs = prepare_windows_dll_search()
    modules = [
        "PySide6", "bs4", "charset_normalizer", "lxml_html_clean", "newspaper",
        "openpyxl", "docx", "requests", "selenium",
    ]
    failed = False
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"OK {name}")
        except Exception as exc:
            failed = True
            print(f"ERROR {name}: {exc}", file=sys.stderr)
    if failed:
        return 10
    try:
        import PySide6
        from PySide6.QtCore import QLibraryInfo, qVersion
        from PySide6.QtWidgets import QApplication
        print(f"PySide6={PySide6.__version__}")
        print(f"Qt={qVersion()}")
        print(f"QtPlugins={QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)}")
        print(f"QApplication={QApplication.__module__}.{QApplication.__name__}")
        if dll_dirs:
            print("DLLSearchDirs=")
            for directory in dll_dirs:
                print(f"  {directory}")
    except Exception as exc:
        print(f"ERROR Qt runtime probe: {exc}", file=sys.stderr)
        for line in _qt_diagnostics():
            print(line, file=sys.stderr)
        return 11
    return 0


def cmd_prefix(_args: argparse.Namespace) -> int:
    print(sys.prefix)
    return 0


def cmd_qt_plugins(_args: argparse.Namespace) -> int:
    try:
        prepare_windows_dll_search()
        from PySide6.QtCore import QLibraryInfo
        path = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)).resolve()
    except Exception as exc:
        print(f"ERROR Qt plugin probe: {exc}", file=sys.stderr)
        return 12
    platform_name = "qwindows.dll" if os.name == "nt" else ("libqcocoa.dylib" if sys.platform == "darwin" else "libqxcb.so")
    if not (path / "platforms" / platform_name).exists():
        print(f"ERROR: Qt platform plugin was not found under {path}", file=sys.stderr)
        return 13
    print(path)
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(read_version())
    return 0


def cmd_write_version_info(args: argparse.Namespace) -> int:
    version = read_version()
    parts = [int(x) if x.isdigit() else 0 for x in version.split(".")[:4]]
    while len(parts) < 4:
        parts.append(0)
    filevers = tuple(parts)
    target = Path(args.output)
    text = (
        "# UTF-8\n"
        "VSVersionInfo(\n"
        f"  ffi=FixedFileInfo(filevers={filevers}, prodvers={filevers}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),\n"
        "  kids=[StringFileInfo([StringTable('040904B0', [\n"
        "    StringStruct('CompanyName', 'Beijing Foreign Studies University Corpus Research Group'),\n"
        "    StringStruct('FileDescription', 'BFSU WebLens'),\n"
        f"    StringStruct('FileVersion', '{version}'),\n"
        "    StringStruct('InternalName', 'BFSU_WebLens'),\n"
        "    StringStruct('OriginalFilename', 'BFSU_WebLens.exe'),\n"
        "    StringStruct('ProductName', 'BFSU WebLens'),\n"
        f"    StringStruct('ProductVersion', '{version}')\n"
        "  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])])\n"
    )
    target.write_text(text, encoding="utf-8")
    print(target)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check-base")
    p.add_argument("--platform", choices=["windows", "macos"], required=True)
    p.add_argument("--arch", default="")
    sub.add_parser("runtime-check")
    sub.add_parser("prefix")
    sub.add_parser("qt-plugins")
    sub.add_parser("version")
    p = sub.add_parser("write-version-info")
    p.add_argument("output")
    args = parser.parse_args()
    commands = {
        "check-base": cmd_check_base,
        "runtime-check": cmd_runtime_check,
        "prefix": cmd_prefix,
        "qt-plugins": cmd_qt_plugins,
        "version": cmd_version,
        "write-version-info": cmd_write_version_info,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
