from __future__ import annotations

import ctypes
import re
import sys
import tkinter as tk


_GEOMETRY_RE = re.compile(r"^(?P<w>\d+)x(?P<h>\d+)(?P<x>[+-]\d+)?(?P<y>[+-]\d+)?$")


def _virtual_screen_bounds(window: tk.Misc) -> tuple[int, int, int, int]:
    """Return virtual-desktop bounds, including monitors left/above primary."""
    if sys.platform.startswith("win"):
        try:
            user32 = ctypes.windll.user32
            left = int(user32.GetSystemMetrics(76))  # SM_XVIRTUALSCREEN
            top = int(user32.GetSystemMetrics(77))   # SM_YVIRTUALSCREEN
            width = int(user32.GetSystemMetrics(78))
            height = int(user32.GetSystemMetrics(79))
            if width > 0 and height > 0:
                return left, top, left + width, top + height
        except (AttributeError, OSError, TypeError):
            pass
    try:
        left = int(window.winfo_vrootx())
        top = int(window.winfo_vrooty())
        width = int(window.winfo_vrootwidth())
        height = int(window.winfo_vrootheight())
        if width > 0 and height > 0:
            return left, top, left + width, top + height
    except (AttributeError, tk.TclError):
        pass
    return 0, 0, max(640, int(window.winfo_screenwidth())), max(480, int(window.winfo_screenheight()))


def _primary_monitor_work_area(window: tk.Misc) -> tuple[int, int, int, int]:
    """Return the primary monitor work area (taskbar excluded where possible)."""
    if sys.platform.startswith("win"):
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            rect = RECT()
            # SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                if rect.right > rect.left and rect.bottom > rect.top:
                    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
        except (AttributeError, OSError, TypeError):
            pass
    try:
        width = max(640, int(window.winfo_screenwidth()))
        height = max(480, int(window.winfo_screenheight()))
        return 0, 0, width, height
    except (AttributeError, tk.TclError):
        return _virtual_screen_bounds(window)


def _parent_monitor_work_area(parent: tk.Misc) -> tuple[int, int, int, int]:
    """Return the work area of the monitor containing the parent window."""
    if sys.platform.startswith("win"):
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

            user32 = ctypes.windll.user32
            monitor_from_window = user32.MonitorFromWindow
            monitor_from_window.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            monitor_from_window.restype = ctypes.c_void_p
            get_monitor_info = user32.GetMonitorInfoW
            get_monitor_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFO)]
            get_monitor_info.restype = ctypes.c_bool
            monitor = monitor_from_window(ctypes.c_void_p(int(parent.winfo_id())), 2)
            info = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
            if monitor and get_monitor_info(monitor, ctypes.byref(info)):
                work = info.rcWork
                return int(work.left), int(work.top), int(work.right), int(work.bottom)
        except (AttributeError, OSError, TypeError, tk.TclError):
            pass
    return _primary_monitor_work_area(parent)


def enable_windows_dpi_awareness() -> str:
    """Enable the best available Windows per-monitor DPI mode before Tk starts."""
    if not sys.platform.startswith("win"):
        return "not-windows"

    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = (HANDLE)-4
        result = ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        if result:
            return "per-monitor-v2"
    except (AttributeError, OSError, TypeError):
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        result = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        if result in (0, None):
            return "per-monitor"
    except (AttributeError, OSError):
        pass

    try:
        if ctypes.windll.user32.SetProcessDPIAware():
            return "system"
    except (AttributeError, OSError):
        pass
    return "unavailable"


def _fit_requested_size(
    requested_w: int,
    requested_h: int,
    work_area: tuple[int, int, int, int],
    *,
    minimum: tuple[int, int],
    margin: int,
) -> tuple[int, int]:
    left, top, right, bottom = work_area
    work_w = max(640, right - left)
    work_h = max(480, bottom - top)
    max_w = max(520, work_w - margin)
    max_h = max(360, work_h - margin)
    min_w = min(max_w, max(420, minimum[0]))
    min_h = min(max_h, max(320, minimum[1]))
    width = min(max(requested_w, min_w), max_w)
    height = min(max(requested_h, min_h), max_h)
    return width, height


def safe_window_geometry(
    window: tk.Misc,
    geometry: str,
    *,
    fallback: tuple[int, int] = (1440, 900),
    minimum: tuple[int, int] = (960, 640),
    margin: int = 72,
    preserve_saved_position: bool = False,
) -> str:
    """Apply a visible geometry and centre the main window on first display.

    MetadataLens stores the previous *size* for convenience, but by default it
    intentionally ignores the old x/y coordinates. This prevents a saved
    position from reopening the application near an edge or partly off-screen
    after DPI/monitor changes.
    """
    window.update_idletasks()
    work = _primary_monitor_work_area(window)
    left, top, right, bottom = work
    match = _GEOMETRY_RE.match((geometry or "").strip())
    requested_w = int(match.group("w")) if match else fallback[0]
    requested_h = int(match.group("h")) if match else fallback[1]
    width, height = _fit_requested_size(requested_w, requested_h, work, minimum=minimum, margin=margin)

    use_saved = preserve_saved_position and match and match.group("x") and match.group("y")
    if use_saved:
        saved_x = int(match.group("x"))
        saved_y = int(match.group("y"))
        visible = saved_x < right - 80 and saved_y < bottom - 80 and saved_x + width > left + 80 and saved_y + height > top + 80
    else:
        visible = False
    if visible:
        x = min(max(saved_x, left), right - width)
        y = min(max(saved_y, top), bottom - height)
    else:
        x = left + max(0, (right - left - width) // 2)
        y = top + max(0, (bottom - top - height) // 2)

    resolved = f"{width}x{height}+{x}+{y}"
    window.geometry(resolved)
    try:
        window.minsize(min(width, minimum[0]), min(height, minimum[1]))
    except tk.TclError:
        pass
    return resolved


def centre_dialog(
    dialog: tk.Misc,
    parent: tk.Misc,
    width: int,
    height: int,
    *,
    margin: int = 48,
    minimum: tuple[int, int] = (520, 360),
) -> str:
    """Centre a child window in the parent's monitor work area and keep it visible.

    The position is based on the *realized* window dimensions. This is more
    reliable than centring on the requested logical size when Windows display
    scaling is 150–225% and CustomTkinter applies its own widget/window scaling.
    """
    try:
        parent.update_idletasks()
    except tk.TclError:
        pass
    work = _parent_monitor_work_area(parent)
    left, top, right, bottom = work
    fit_w, fit_h = _fit_requested_size(width, height, work, minimum=minimum, margin=margin)

    # Set and constrain the size first. Keeping the footer inside the work area
    # is more important than preserving the nominal dialog dimensions.
    try:
        dialog.maxsize(max(520, right - left - margin), max(360, bottom - top - margin))
    except tk.TclError:
        pass
    dialog.geometry(f"{fit_w}x{fit_h}")
    dialog.update_idletasks()

    actual_w = max(1, int(dialog.winfo_width()))
    actual_h = max(1, int(dialog.winfo_height()))
    max_w = max(520, right - left - margin)
    max_h = max(360, bottom - top - margin)
    if actual_w > max_w or actual_h > max_h:
        fit_w = min(fit_w, max_w)
        fit_h = min(fit_h, max_h)
        dialog.geometry(f"{fit_w}x{fit_h}")
        dialog.update_idletasks()
        actual_w = max(1, int(dialog.winfo_width()))
        actual_h = max(1, int(dialog.winfo_height()))

    x = left + max(0, (right - left - actual_w) // 2)
    y = top + max(0, (bottom - top - actual_h) // 2)
    # Set position only so a realized CTk window does not get re-scaled by a
    # second width/height assignment.
    dialog.geometry(f"+{x}+{y}")
    return f"{actual_w}x{actual_h}+{x}+{y}"
