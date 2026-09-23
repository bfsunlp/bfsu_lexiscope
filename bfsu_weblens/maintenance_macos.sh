#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ACTION="${1:-}"
if [[ -z "$ACTION" ]]; then
  echo "Usage: $0 reset-settings|clear-web|purge-user-state|self-check" >&2
  exit 2
fi

APP="${BFSU_WEBLENS_APP:-$(pwd)/BFSU_WebLens.app}"
if [[ -x "$APP/Contents/MacOS/BFSU_WebLens" ]]; then
  "$APP/Contents/MacOS/BFSU_WebLens" --maintenance "$ACTION"
  exit $?
fi

PY="${BFSU_WEBLENS_PYTHON:-}"
if [[ -z "$PY" && -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then PY="$VIRTUAL_ENV/bin/python"; fi
if [[ -z "$PY" && -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then PY="$CONDA_PREFIX/bin/python"; fi
if [[ -z "$PY" ]]; then PY="$(command -v python3 || command -v python || true)"; fi
if [[ -z "$PY" ]]; then
  echo "ERROR: Python was not found. Activate the WebLens environment or set BFSU_WEBLENS_PYTHON." >&2
  exit 3
fi
"$PY" maintenance_cli.py "$ACTION"
