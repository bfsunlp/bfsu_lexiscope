#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
APP="$(pwd)/BFSU_WebLens.app"
if [[ ! -d "$APP" ]]; then
  echo "Source-code mode detected. The source folder will NOT be deleted."
  printf 'Reset WebLens user state and managed web components? [y/N] '
  read -r ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 0
  ./maintenance_macos.sh purge-user-state
  exit 0
fi
printf 'Uninstall BFSU WebLens.app? User output/content folders in Application Support will be preserved. [y/N] '
read -r ans
[[ "$ans" =~ ^[Yy]$ ]] || exit 0
BFSU_WEBLENS_APP="$APP" ./maintenance_macos.sh purge-user-state
rm -rf "$APP"
echo "BFSU WebLens.app was removed. User output/content folders were preserved."
