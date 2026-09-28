# -*- coding: utf-8 -*-
"""Small unit-conversion helpers for user-facing timing controls."""
from __future__ import annotations

from typing import Any


def milliseconds_to_ui_seconds(value: Any, default_ms: int = 0) -> int:
    """Convert persisted/internal milliseconds to whole seconds for the GUI."""
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        milliseconds = int(default_ms)
    return max(0, (milliseconds + 500) // 1000)


def ui_seconds_to_milliseconds(value: Any) -> int:
    """Convert a whole-second GUI value back to internal milliseconds."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        seconds = 0
    return max(0, seconds) * 1000
