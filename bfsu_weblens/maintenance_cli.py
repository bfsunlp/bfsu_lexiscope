# -*- coding: utf-8 -*-
"""Source-checkout maintenance CLI for BFSU WebLens."""
from __future__ import annotations

import argparse

from bfsu_weblens.maintenance import report_text, run_maintenance


def main() -> int:
    parser = argparse.ArgumentParser(description="BFSU WebLens maintenance utility")
    parser.add_argument("action", choices=["reset-settings", "clear-web", "purge-user-state", "self-check"])
    args = parser.parse_args()
    report = run_maintenance(args.action)
    print(report_text(report))
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
