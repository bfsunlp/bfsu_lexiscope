#!/usr/bin/env bash
cd "$(dirname "$0")"
./maintenance_macos.sh reset-settings
printf '\nSettings reset complete. Press Return to close.'
read -r _
