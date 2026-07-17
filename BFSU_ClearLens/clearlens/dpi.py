from __future__ import annotations

import os


def enable_windows_high_dpi() -> None:
    """Set one stable DPI-awareness mode before Tk creates any native window."""
    if os.name != "nt":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        try:
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
                return
        except (AttributeError, OSError):
            pass
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except (AttributeError, OSError):
            pass
        try:
            user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    except Exception:
        pass
