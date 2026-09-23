#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec bash ./build_macos_common.sh arm64 "$@"
