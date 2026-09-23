#!/usr/bin/env bash
cd "$(dirname "$0")"
printf 'Remove WebLens-managed portable browsers and WebDrivers? System Chrome/Edge will not be touched. [y/N] '
read -r ans
[[ "$ans" =~ ^[Yy]$ ]] || exit 0
./maintenance_macos.sh clear-web
printf '\nWeb components cleared. Press Return to close.'
read -r _
