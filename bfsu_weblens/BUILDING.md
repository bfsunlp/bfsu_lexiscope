# BFSU WebLens 3.1.4 release builds

BFSU WebLens release builds must be created on the target operating system. Windows packages are built on Windows; macOS packages are built on macOS.

## Windows x64

Run `build_exe.bat` from the project directory. The BAT file is deliberately small and BOM-free; it starts `build_launcher.py`, which chooses a safe build Python before the real build begins.

The launcher prefers, in order: an explicit `BFSU_WEBLENS_PYTHON`, the active `VIRTUAL_ENV`, the active `CONDA_PREFIX`, a nearby project/Conda environment (including the normal BFSU LexiScope layout), discovered Conda environments, Python 3.12/3.11 from the Windows Python launcher, then the bootstrap/PATH Python. Every candidate is probed for 64-bit Windows compatibility and for the complete WebLens/PySide6 runtime.

### Why v3.1.4 changed the strategy

A real v3.1.1 build showed that Anaconda Base Python 3.13 could create `.venv_build_windows` and install PySide6 6.11, but `from PySide6.QtCore import ...` failed with `DLL load failed ... The specified procedure could not be found`. This is a native DLL/runtime conflict, not a missing Python package and not a PyInstaller failure. Therefore v3.1.4 no longer installs a second PySide6/Qt runtime on top of a bare Conda interpreter.

If the selected source environment already runs all WebLens dependencies and Qt correctly, the private build venv is created with `--system-site-packages`; PySide6/Qt are reused read-only from that verified environment and only `requirements-build.txt` is installed in the build venv. This is the preferred Conda mode and mirrors the successful BFSU EditTrac packaging strategy.

If the source runtime is incomplete, a fully isolated installation is allowed only when the source is a non-Conda CPython/venv 3.10–3.12. A bare Conda environment with a failing Qt runtime is intentionally rejected instead of spending time downloading a second Qt that may not load. Python 3.13 is accepted for Windows packaging only when its existing WebLens/PySide6 runtime already passes the probe.

The release remains PyInstaller ONEDIR:

```text
BFSU_WebLens/
├─ BFSU_WebLens.exe
└─ _internal/
   ├─ assets/
   ├─ config/
   └─ ...runtime files...
```

The builder verifies `qwindows.dll`; if PyInstaller does not expose it in a standard `_internal` location, the plugin is copied from the verified runtime into `_internal/qt_plugins`. The frozen EXE is then executed with external Python/Conda/Qt environment variables removed.

ZIP creation uses Python `zipfile` and validates the resulting archive. A successful build produces:

`release/BFSU_WebLens_v<version>_windows_x64.zip`

Logs are always written to:

`build_logs/build_launcher.log`

`build_logs/build_windows.log`

If automatic selection is not desired, explicitly select a known-working environment before running the BAT:

```text
set BFSU_WEBLENS_PYTHON=C:\path\to\python.exe && build_exe.bat
```

`clean_build.bat` removes the private venv, `build`, `dist`, spec/version files and build logs while keeping `release/`.

## macOS Apple Silicon

On an Apple Silicon Mac with an arm64-capable Python/Conda environment:

```bash
./build_macos_arm64.sh --fresh
```

The release is:

`release/BFSU_WebLens_v<version>_macos_arm64.zip`

## macOS Intel

On an Intel Mac, or on Apple Silicon using an x86_64/Rosetta or suitable universal2 Python environment:

```bash
./build_macos_intel.sh --fresh
```

The release is:

`release/BFSU_WebLens_v<version>_macos_x86_64.zip`

Both macOS scripts choose Python in this order: `BFSU_WEBLENS_PYTHON`, active `VIRTUAL_ENV`, active `CONDA_PREFIX`, `python3`, then `python`. They create architecture-specific isolated build venvs, generate a native `.icns`, build a windowed `.app`, verify the Cocoa Qt platform plugin, ad-hoc sign the app, run a frozen smoke test in a clean environment, and preserve macOS metadata when creating the ZIP with `ditto`.

`clean_build.sh` deletes build intermediates but keeps `release/`.

## Writable data on macOS

A signed `.app` bundle is not used as writable application storage. Frozen macOS builds store settings, managed browser/driver files, output data, downloaded content, and debug HTML under:

`~/Library/Application Support/BFSU WebLens`

Cache files use:

`~/Library/Caches/BFSU WebLens`

This keeps runtime data outside the application bundle and avoids invalidating the bundle after packaging.

## macOS distribution note

The supplied scripts use ad-hoc signing so the local `.app` bundle has a coherent signature after PyInstaller packaging. Ad-hoc signing is not Apple notarization. For broad public distribution without Gatekeeper warnings, sign the final app with an Apple Developer ID Application certificate and submit it for Apple notarization before creating the release ZIP.

## Windows slim build (v3.1.4)

The Windows release builder now uses a private minimal build environment and never exposes the whole development Conda environment through `--system-site-packages`. WebLens installs `PySide6-Essentials` rather than the full `PySide6`/Addons stack because the application uses only QtCore, QtGui and QtWidgets.

If the bootstrap Python belongs to Conda, the builder creates a private Conda prefix at `.venv_build_windows` with Python 3.12 and pip. If the bootstrap is standard CPython/venv, it creates a normal isolated `venv`. Both paths then install only `requirements.txt` and `requirements-build.txt`.

PyInstaller explicitly excludes unrelated scientific, ML, notebook and alternate Qt stacks. After packaging, unused Qt QML/translations/plugin payloads are pruned conservatively and the frozen `--qt-smoke-test` is run again. A bundle-size report is written to `build_logs/bundle_size_report.txt`; the release ZIP is created under `release/`.


## Windows builds launched from an activated Conda terminal

It is safe to run `build_exe.bat` from a PyCharm terminal that already has a Conda environment activated. The activated environment is used only as the bootstrap interpreter. After the private build environment is created, WebLens removes `CONDA_*`, `VIRTUAL_ENV`, `QT_*`, `PYTHON*`, and `BFSU_WEBLENS_BASE_PREFIX` from child processes and replaces `PATH` with the private build prefix plus Windows system directories. The private Qt runtime therefore cannot accidentally load `Qt6Core.dll` from the outer Conda environment.
