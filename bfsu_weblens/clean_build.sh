#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf build dist .venv_build_macos_arm64 .venv_build_macos_x86_64 BFSU_WebLens.spec .build_BFSU_WebLens.iconset .build_BFSU_WebLens.icns
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
echo "Build intermediates cleaned. The release folder was kept."
