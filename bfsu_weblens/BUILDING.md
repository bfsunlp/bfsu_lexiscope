# BFSU WebLens 3.1.6 release builds

BFSU WebLens release builds must be created on the target operating system. Windows packages are built on Windows; macOS packages are built on macOS.

## Selenium packaging validation

The release build explicitly collects the complete `selenium` package. This is intentional: Selenium exposes concrete Chrome/Edge WebDriver implementations and Selenium Manager resources that may otherwise be missed by static PyInstaller analysis. `build_probe.py runtime-check` and the frozen `--qt-smoke-test` both import the concrete modules used by WebLens (`selenium.webdriver.chrome.webdriver`, Edge equivalents, driver finder, Selenium Manager, and remote WebDriver). A release is rejected if any of them is missing.

## Windows x64

Run `build_exe.bat` from the project directory. The BAT file is deliberately small and BOM-free; it starts `build_launcher.py`, which chooses a safe build Python before the real build begins.

The launcher prefers, in order: an explicit `BFSU_WEBLENS_PYTHON`, the active `VIRTUAL_ENV`, the active `CONDA_PREFIX`, a nearby BFSU LexiScope environment, and finally the Python that launched the build. The selected interpreter is only a **bootstrap**. It is checked for Windows x64 and a supported Python version; its installed scientific/Qt packages are not exposed to PyInstaller.

### Why v3.1.6 uses a private minimal runtime

Earlier builds showed two opposite failure modes: reusing a large Conda environment made the release grow to several gigabytes, while creating a normal venv from an activated Conda environment could let the outer Conda Qt DLLs leak into the private PySide6 runtime. The current builder therefore creates a clean runtime that owns its native dependencies and then runs every probe/PyInstaller subprocess with the outer Conda/Qt/Python environment removed.

If the bootstrap interpreter belongs to Conda, the builder uses Conda only to create a fresh private prefix at `.venv_build_windows` with Python 3.12 and pip. If the bootstrap interpreter is standard CPython/venv, the builder creates a normal isolated `venv`. **Neither mode uses `--system-site-packages`.** Both then install only `requirements.txt` and `requirements-build.txt`. `requirements.txt` uses `PySide6-Essentials`, while PyInstaller explicitly excludes unrelated scientific, ML, notebook and alternate-Qt stacks.

This keeps the release small while still collecting the complete Selenium runtime with `--collect-all selenium`; build-time and frozen smoke tests import the concrete Chrome/Edge WebDriver modules before a release ZIP is accepted.

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

Both macOS scripts choose Python in this order: `BFSU_WEBLENS_PYTHON`, active `VIRTUAL_ENV`, active `CONDA_PREFIX`, `python3`, then `python`. They create architecture-specific isolated build venvs, install only the WebLens runtime/build requirements, generate a native `.icns`, and build a windowed `.app` with `PySide6-Essentials` plus complete Selenium collection. After PyInstaller finishes, unused Qt QML/translations/plugin payloads are conservatively pruned, the Cocoa platform plugin is verified, the app is ad-hoc signed, and frozen Qt/Selenium/maintenance smoke tests run with outer Conda/venv/Python/Qt/DYLD variables removed. A per-architecture bundle-size report is written to `build_logs/bundle_size_report_macos_<arch>.txt`, and `ditto` is used to preserve macOS metadata when creating the ZIP.

`clean_build.sh` deletes build intermediates but keeps `release/`.

## Writable data on macOS

A signed `.app` bundle is not used as writable application storage. Frozen macOS builds store settings, managed browser/driver files, output data, downloaded content, and debug HTML under:

`~/Library/Application Support/BFSU WebLens`

Cache files use:

`~/Library/Caches/BFSU WebLens`

This keeps runtime data outside the application bundle and avoids invalidating the bundle after packaging.

## macOS distribution note

The supplied scripts use ad-hoc signing so the local `.app` bundle has a coherent signature after PyInstaller packaging. Ad-hoc signing is not Apple notarization. For broad public distribution without Gatekeeper warnings, sign the final app with an Apple Developer ID Application certificate and submit it for Apple notarization before creating the release ZIP.

## Windows slim build (v3.1.6)

The Windows release builder now uses a private minimal build environment and never exposes the whole development Conda environment through `--system-site-packages`. WebLens installs `PySide6-Essentials` rather than the full `PySide6`/Addons stack because the application uses only QtCore, QtGui and QtWidgets.

If the bootstrap Python belongs to Conda, the builder creates a private Conda prefix at `.venv_build_windows` with Python 3.12 and pip. If the bootstrap is standard CPython/venv, it creates a normal isolated `venv`. Both paths then install only `requirements.txt` and `requirements-build.txt`.

PyInstaller explicitly excludes unrelated scientific, ML, notebook and alternate Qt stacks. After packaging, unused Qt QML/translations/plugin payloads are pruned conservatively and the frozen `--qt-smoke-test` is run again. A bundle-size report is written to `build_logs/bundle_size_report.txt`; the release ZIP is created under `release/`.


## Windows builds launched from an activated Conda terminal

It is safe to run `build_exe.bat` from a PyCharm terminal that already has a Conda environment activated. The activated environment is used only as the bootstrap interpreter and, when applicable, to locate the Conda executable that creates the new private prefix. After the private build environment is created, WebLens removes `CONDA_*`, `VIRTUAL_ENV`, `QT_*`, `PYTHON*`, and `BFSU_WEBLENS_BASE_PREFIX` from child processes and replaces `PATH` with the private build prefix plus Windows system directories. The private Qt runtime therefore cannot accidentally load `Qt6Core.dll` from the outer Conda environment.

## Release maintenance files

Windows `onedir` builds copy `README.md`, `MAINTENANCE.md`, `maintenance.bat`, `reset_user_settings.bat`, `clear_web_components.bat`, and `uninstall_weblens.bat` beside `BFSU_WebLens.exe`. The frozen smoke test also runs `BFSU_WebLens.exe --maintenance self-check`, so a package missing the maintenance module cannot pass release validation.

macOS builds create a release staging folder containing `BFSU_WebLens.app` plus `reset_user_settings.command`, `clear_web_components.command`, `uninstall_weblens.command`, `maintenance_macos.sh`, `README.md`, and `MAINTENANCE.md`. Both Intel and Apple Silicon builds continue to use the same minimal runtime requirements and `--collect-all selenium` so Selenium remains complete without reintroducing unrelated scientific/ML packages.

Windows `onedir` 发布目录会把维护脚本直接放在 `BFSU_WebLens.exe` 同级，并在 frozen smoke test 中额外执行维护模块自检。macOS Intel 与 Apple Silicon 发布 ZIP 则包含 `.app` 和对应 `.command` 维护脚本。三套构建都继续使用最小运行依赖与完整 Selenium 收集策略。

