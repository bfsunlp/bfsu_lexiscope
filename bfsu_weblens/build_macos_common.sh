#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
TARGET_ARCH="${1:-}"
if [[ "$TARGET_ARCH" != "arm64" && "$TARGET_ARCH" != "x86_64" ]]; then
  echo "Usage: $0 arm64|x86_64" >&2
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
  echo "ERROR: No Python interpreter was found. Set BFSU_WEBLENS_PYTHON, activate Conda, or install Python 3.10-3.13." >&2
  exit 3
fi

echo "============================================================"
echo "BFSU WebLens - macOS ${TARGET_ARCH} build"
echo "============================================================"

echo "[1/12] Checking source Python architecture..."
"$SOURCE_PYTHON" build_probe.py check-base --platform macos --arch "$TARGET_ARCH"
APP_VERSION="$("$SOURCE_PYTHON" build_probe.py version)"
RELEASE_ZIP="${RELEASE_DIR}/${APP_NAME}_v${APP_VERSION}_macos_${TARGET_ARCH}.zip"

echo "[2/12] Creating clean virtualenv..."
rm -rf "$VENV_DIR"
"$SOURCE_PYTHON" -m venv --clear --copies "$VENV_DIR"

echo "[3/12] Installing only runtime/build dependencies..."
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install --no-cache-dir -r requirements.txt -r requirements-build.txt

echo "[4/12] Verifying isolated runtime..."
export PYTHONNOUSERSITE=1
export QT_API=PySide6
"$VENV_PY" build_probe.py runtime-check
"$VENV_PY" build_probe.py check-base --platform macos --arch "$TARGET_ARCH"

echo "[5/12] Cleaning previous build output..."
rm -rf build dist "${APP_NAME}.spec"
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

echo "[6/12] Compiling sources..."
"$VENV_PY" -m compileall -q bfsu_weblens main.py build_probe.py

echo "[7/12] Preparing native macOS icon..."
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

echo "[8/12] Building ONEDIR + .app bundle..."
"$VENV_PY" -m PyInstaller --noconfirm --clean --onedir --windowed --contents-directory "_internal" --name "$APP_NAME" --icon "$ICNS" --osx-bundle-identifier "cn.edu.bfsu.weblens" --target-architecture "$TARGET_ARCH" --add-data "assets:assets" --add-data "config:config" --add-data "README.md:." --collect-data newspaper --collect-data tldextract --hidden-import lxml_html_clean --hidden-import charset_normalizer --hidden-import openpyxl --hidden-import docx --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2 --exclude-module tkinter --exclude-module IPython --exclude-module jupyter --exclude-module pytest --paths "." "$ENTRY"

APP_BUNDLE="dist/${APP_NAME}.app"
APP_EXE="${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
if [[ ! -d "$APP_BUNDLE" || ! -x "$APP_EXE" ]]; then
  echo "ERROR: macOS app bundle was not created." >&2
  exit 8
fi

echo "[9/12] Verifying Qt bundle, writing version metadata and ad-hoc signing..."
if ! find "$APP_BUNDLE" -type f -name 'libqcocoa.dylib' -print -quit | grep -q .; then
  echo "ERROR: libqcocoa.dylib is missing from the macOS application bundle." >&2
  exit 9
fi
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
codesign --force --deep --sign - "$APP_BUNDLE"

echo "[10/12] Running frozen Qt/runtime smoke test in a clean environment..."
env -u QT_PLUGIN_PATH -u QT_QPA_PLATFORM_PLUGIN_PATH -u QT_QPA_PLATFORM -u PYTHONHOME -u PYTHONPATH "$APP_EXE" --qt-smoke-test

echo "[11/12] Creating release ZIP with macOS metadata preserved..."
mkdir -p "$RELEASE_DIR"
rm -f "$RELEASE_ZIP"
ditto -c -k --sequesterRsrc --keepParent "$APP_BUNDLE" "$RELEASE_ZIP"

echo "[12/12] Release validation..."
[[ -s "$RELEASE_ZIP" ]]
rm -rf "$ICONSET" "$ICNS"

echo "============================================================"
echo "BUILD COMPLETE"
echo "App: ${APP_BUNDLE}"
echo "Release ZIP: ${RELEASE_ZIP}"
echo "============================================================"
