#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
TARGET_ARCH="${1:-}"
if [[ "$TARGET_ARCH" != "arm64" && "$TARGET_ARCH" != "x86_64" ]]; then
  echo "Usage: $0 arm64|x86_64 [--fresh]" >&2
  exit 2
fi
shift || true

APP_NAME="BFSU_WebLens"
ENTRY="main.py"
VENV_DIR=".venv_build_macos_${TARGET_ARCH}"
VENV_PY="${VENV_DIR}/bin/python"
RELEASE_DIR="release"
FRESH=0
if [[ "${1:-}" == "--fresh" ]]; then FRESH=1; fi

SOURCE_PYTHON="${BFSU_WEBLENS_PYTHON:-}"
if [[ -z "$SOURCE_PYTHON" && -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then SOURCE_PYTHON="${VIRTUAL_ENV}/bin/python"; fi
if [[ -z "$SOURCE_PYTHON" && -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/python" ]]; then SOURCE_PYTHON="${CONDA_PREFIX}/bin/python"; fi
if [[ -z "$SOURCE_PYTHON" ]]; then SOURCE_PYTHON="$(command -v python3 || true)"; fi
if [[ -z "$SOURCE_PYTHON" ]]; then SOURCE_PYTHON="$(command -v python || true)"; fi
if [[ -z "$SOURCE_PYTHON" || ! -x "$SOURCE_PYTHON" ]]; then
  echo "ERROR: No Python interpreter was found. Set BFSU_WEBLENS_PYTHON, activate Conda/venv, or install a compatible Python." >&2
  exit 3
fi

echo "============================================================"
echo "BFSU WebLens - macOS ${TARGET_ARCH} SLIM/COMPLETE build"
echo "============================================================"

echo "[1/15] Checking source Python architecture..."
"$SOURCE_PYTHON" build_probe.py check-base --platform macos --arch "$TARGET_ARCH"
APP_VERSION="$("$SOURCE_PYTHON" build_probe.py version)"
RELEASE_ZIP="${RELEASE_DIR}/${APP_NAME}_v${APP_VERSION}_macos_${TARGET_ARCH}.zip"
STAGE_DIR="dist/${APP_NAME}_v${APP_VERSION}_macos_${TARGET_ARCH}"

echo "[2/15] Creating clean private virtualenv..."
rm -rf "$VENV_DIR"
"$SOURCE_PYTHON" -m venv --clear --copies "$VENV_DIR"

echo "[3/15] Installing only WebLens runtime/build dependencies..."
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install --no-cache-dir -r requirements.txt -r requirements-build.txt

echo "[4/15] Verifying private runtime including Selenium WebDriver modules..."
export PYTHONNOUSERSITE=1
export QT_API=PySide6
"$VENV_PY" build_probe.py runtime-check
"$VENV_PY" build_probe.py check-base --platform macos --arch "$TARGET_ARCH"

echo "[5/15] Cleaning previous build output..."
rm -rf build dist "${APP_NAME}.spec"
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

echo "[6/15] Compiling sources..."
"$VENV_PY" -m compileall -q bfsu_weblens main.py build_probe.py maintenance_cli.py

echo "[7/15] Preparing native macOS icon..."
ICON_PATH="assets/app_1024.png"
ICONSET=".build_${APP_NAME}.iconset"
ICNS=".build_${APP_NAME}.icns"
rm -rf "$ICONSET" "$ICNS"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$ICON_PATH" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$ICON_PATH" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$ICNS"

echo "[8/15] Building minimal ONEDIR + .app bundle with complete Selenium..."
PYI_ARGS=(
  --noconfirm --clean --onedir --windowed --contents-directory "_internal"
  --name "$APP_NAME" --icon "$ICNS"
  --osx-bundle-identifier "cn.edu.bfsu.weblens"
  --target-architecture "$TARGET_ARCH"
  --add-data "assets:assets" --add-data "config:config"
  --collect-data newspaper --collect-data tldextract --collect-all selenium
  --hidden-import lxml_html_clean --hidden-import charset_normalizer --hidden-import openpyxl --hidden-import docx
  --paths "."
  --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2 --exclude-module tkinter
  --exclude-module numpy --exclude-module pandas --exclude-module scipy --exclude-module sklearn --exclude-module matplotlib --exclude-module seaborn
  --exclude-module torch --exclude-module torchvision --exclude-module torchaudio --exclude-module tensorflow --exclude-module keras --exclude-module transformers --exclude-module spacy
  --exclude-module IPython --exclude-module jupyter --exclude-module notebook --exclude-module pytest
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtWebChannel
  --exclude-module PySide6.QtPdf --exclude-module PySide6.QtPdfWidgets --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtMultimediaWidgets
  --exclude-module PySide6.QtQuick --exclude-module PySide6.QtQml --exclude-module PySide6.QtCharts --exclude-module PySide6.QtDataVisualization
)
"$VENV_PY" -m PyInstaller "${PYI_ARGS[@]}" "$ENTRY"

APP_BUNDLE="dist/${APP_NAME}.app"
APP_EXE="${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
if [[ ! -d "$APP_BUNDLE" || ! -x "$APP_EXE" ]]; then
  echo "ERROR: macOS app bundle was not created." >&2
  exit 8
fi

echo "[9/15] Pruning unused Qt payloads while keeping QtWidgets essentials..."
QT_DIR="$(find "$APP_BUNDLE" -type d -path '*/PySide6/Qt' -print -quit || true)"
if [[ -n "$QT_DIR" ]]; then
  for rel in \
    qml translations resources \
    plugins/designer plugins/qmltooling plugins/multimedia plugins/sqldrivers \
    plugins/geoservices plugins/position plugins/sensors plugins/canbus \
    plugins/gamepads plugins/webview; do
    target="$QT_DIR/$rel"
    if [[ -e "$target" ]]; then
      rm -rf "$target"
      echo "  removed: ${target#$APP_BUNDLE/}"
    fi
  done
else
  echo "  No PySide6/Qt payload directory was found; PyInstaller may already have produced a minimal bundle."
fi

echo "[10/15] Verifying Qt bundle, version metadata and ad-hoc signing..."
if ! find "$APP_BUNDLE" -type f -name 'libqcocoa.dylib' -print -quit | grep -q .; then
  echo "ERROR: libqcocoa.dylib is missing from the macOS application bundle." >&2
  exit 9
fi
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
codesign --force --deep --sign - "$APP_BUNDLE"

echo "[11/15] Running frozen Qt/Selenium/maintenance smoke tests in a clean environment..."
env -u QT_PLUGIN_PATH -u QT_QPA_PLATFORM_PLUGIN_PATH -u QT_QPA_PLATFORM -u PYTHONHOME -u PYTHONPATH -u CONDA_PREFIX -u CONDA_DEFAULT_ENV -u VIRTUAL_ENV -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH "$APP_EXE" --qt-smoke-test
env -u QT_PLUGIN_PATH -u QT_QPA_PLATFORM_PLUGIN_PATH -u QT_QPA_PLATFORM -u PYTHONHOME -u PYTHONPATH -u CONDA_PREFIX -u CONDA_DEFAULT_ENV -u VIRTUAL_ENV -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH "$APP_EXE" --maintenance self-check

echo "[12/15] Writing macOS bundle-size report..."
mkdir -p build_logs
SIZE_REPORT="build_logs/bundle_size_report_macos_${TARGET_ARCH}.txt"
{
  echo "BFSU WebLens v${APP_VERSION} macOS ${TARGET_ARCH} bundle size report"
  echo
  echo "Total app bundle (KB):"
  du -sk "$APP_BUNDLE"
  echo
  echo "Top-level Contents entries (KB, descending):"
  du -sk "$APP_BUNDLE"/Contents/* 2>/dev/null | sort -nr | head -30 || true
  echo
  echo "Largest _internal/PySide6 entries when present (KB, descending):"
  find "$APP_BUNDLE" -type d -path '*/_internal/PySide6' -print -quit | while IFS= read -r pyside_dir; do
    [[ -n "$pyside_dir" ]] && du -sk "$pyside_dir"/* 2>/dev/null | sort -nr | head -30 || true
  done
} > "$SIZE_REPORT"
echo "  Size report: $SIZE_REPORT"

echo "[13/15] Creating release staging folder with maintenance tools..."
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
ditto "$APP_BUNDLE" "$STAGE_DIR/${APP_NAME}.app"
cp README.md MAINTENANCE.md maintenance_macos.sh reset_user_settings.command clear_web_components.command uninstall_weblens.command "$STAGE_DIR/"
chmod +x "$STAGE_DIR"/*.command "$STAGE_DIR/maintenance_macos.sh"

echo "[14/15] Creating release ZIP with macOS metadata preserved..."
mkdir -p "$RELEASE_DIR"
rm -f "$RELEASE_ZIP"
ditto -c -k --sequesterRsrc --keepParent "$STAGE_DIR" "$RELEASE_ZIP"

echo "[15/15] Release validation..."
[[ -s "$RELEASE_ZIP" ]]
[[ -d "$STAGE_DIR/${APP_NAME}.app" ]]
[[ -x "$STAGE_DIR/reset_user_settings.command" ]]
[[ -x "$STAGE_DIR/clear_web_components.command" ]]
[[ -x "$STAGE_DIR/uninstall_weblens.command" ]]
rm -rf "$ICONSET" "$ICNS"

echo "============================================================"
echo "BUILD COMPLETE"
echo "App: ${APP_BUNDLE}"
echo "Staging: ${STAGE_DIR}"
echo "Release ZIP: ${RELEASE_ZIP}"
echo "============================================================"
