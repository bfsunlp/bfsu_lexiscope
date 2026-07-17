from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk
from itertools import count
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk
from typing import Callable

import customtkinter as ctk


FONT_FAMILY = "Microsoft YaHei UI"
COLOR_BG = "#f3f7f8"
COLOR_PANEL = "#e7f0f2"
COLOR_SURFACE = "#ffffff"
COLOR_BORDER = "#b7cdd1"
COLOR_TEXT = "#17272b"
COLOR_MUTED = "#5d747a"
COLOR_ACCENT = "#0b6f75"
COLOR_ACCENT_HOVER = "#095b60"
COLOR_LLM = "#155a8a"
COLOR_LLM_HOVER = "#10486e"
COLOR_DANGER = "#8b1e2d"
COLOR_DANGER_HOVER = "#6f1723"
COLOR_TOOLBAR = "#dfeaec"


def button_colors(kind: str = "normal") -> dict[str, object]:
    if kind == "accent":
        return {"fg_color": COLOR_ACCENT, "hover_color": COLOR_ACCENT_HOVER, "text_color": "#ffffff"}
    if kind == "llm":
        return {"fg_color": COLOR_LLM, "hover_color": COLOR_LLM_HOVER, "text_color": "#ffffff"}
    if kind == "danger":
        return {"fg_color": COLOR_DANGER, "hover_color": COLOR_DANGER_HOVER, "text_color": "#ffffff"}
    return {
        "fg_color": "#e2ecee",
        "hover_color": "#cadde0",
        "text_color": COLOR_TEXT,
        "border_color": "#aac0c4",
        "border_width": 1,
    }


def apply_window_icon(window: tk.Misc, png_path: str | os.PathLike[str], ico_path: str | os.PathLike[str], *, default: bool = False) -> None:
    """Apply a multi-size product icon to Tk/CTk and the Windows shell."""
    png = Path(png_path)
    ico = Path(ico_path)
    if png.exists():
        try:
            # Several source sizes improve taskbar/title-bar rendering on scaled displays.
            photos: list[tk.PhotoImage] = []
            for size in (16, 24, 32, 48, 64, 128, 256):
                candidate = png.with_name(f"app_{size}.png")
                if candidate.exists():
                    photos.append(tk.PhotoImage(master=window, file=str(candidate)))
            if not photos:
                photos.append(tk.PhotoImage(master=window, file=str(png)))
            window.wm_iconphoto(default, *photos)
            setattr(window, "_weblens_icon_photos", photos)
        except (tk.TclError, OSError):
            pass
    if ico.exists():
        try:
            window.wm_iconbitmap(str(ico))
        except (tk.TclError, OSError):
            pass


def _window_scaling(window: tk.Misc) -> float:
    """Return CustomTkinter's window scaling, or 1.0 for native Tk windows."""
    try:
        scale = float(getattr(window, "_get_window_scaling")())
        if scale > 0:
            return scale
    except Exception:
        pass
    return 1.0


def _windows_work_area(window: tk.Misc) -> tuple[int, int, int, int] | None:
    """Return the usable pixel rectangle of the nearest Windows monitor.

    The work area excludes the taskbar and app bars.  Coordinates are physical
    desktop coordinates and may be negative on monitors placed left/above the
    primary display.
    """
    if not sys.platform.startswith("win"):
        return None
    try:
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        hwnd = wintypes.HWND(int(window.winfo_id()))
        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        if not monitor:
            return None
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return None
        rect = info.rcWork
        if rect.right <= rect.left or rect.bottom <= rect.top:
            return None
        return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    except Exception:
        return None


def fit_window_to_screen(
    window: tk.Misc,
    *,
    requested_width: int,
    requested_height: int,
    parent: tk.Misc | None = None,
    margin: int = 52,
    min_width: int = 520,
    min_height: int = 360,
) -> tuple[int, int]:
    """Fit and center a window once inside the usable monitor work area.

    CustomTkinter geometry sizes are logical units but screen/work-area values
    are physical pixels.  Converting between those coordinate systems prevents
    high-DPI Windows displays from scaling an already-clamped size a second time,
    which previously pushed the right and bottom edges behind the desktop/taskbar.
    """
    window.update_idletasks()
    scale = _window_scaling(window)

    work_area = _windows_work_area(window)
    if work_area is None:
        screen_w = max(640, int(window.winfo_screenwidth()))
        screen_h = max(480, int(window.winfo_screenheight()))
        work_left, work_top, work_right, work_bottom = 0, 0, screen_w, screen_h
    else:
        work_left, work_top, work_right, work_bottom = work_area

    work_w_px = max(320, work_right - work_left)
    work_h_px = max(260, work_bottom - work_top)
    margin_px = max(0, round(margin * scale))

    max_w = max(320, int((work_w_px - margin_px * 2) / scale))
    max_h = max(260, int((work_h_px - margin_px * 2) / scale))

    req_w_px = max(1, int(window.winfo_reqwidth()))
    req_h_px = max(1, int(window.winfo_reqheight()))
    req_w = max(1, round(req_w_px / scale))
    req_h = max(1, round(req_h_px / scale))

    width = min(max_w, max(min_width, requested_width, req_w))
    height = min(max_h, max(min_height, requested_height, req_h))
    try:
        window.minsize(min(min_width, width), min(min_height, height))
    except tk.TclError:
        pass

    physical_w = max(1, round(width * scale))
    physical_h = max(1, round(height * scale))

    if parent is not None:
        try:
            parent.update_idletasks()
            center_x = int(parent.winfo_rootx() + parent.winfo_width() / 2)
            center_y = int(parent.winfo_rooty() + parent.winfo_height() / 2)
        except tk.TclError:
            center_x = work_left + work_w_px // 2
            center_y = work_top + work_h_px // 2
    else:
        center_x = work_left + work_w_px // 2
        center_y = work_top + work_h_px // 2

    x = center_x - physical_w // 2
    y = center_y - physical_h // 2
    edge_margin_px = max(0, margin_px // 2)
    min_x = work_left + edge_margin_px
    min_y = work_top + edge_margin_px
    max_x = max(min_x, work_right - physical_w - edge_margin_px)
    max_y = max(min_y, work_bottom - physical_h - edge_margin_px)
    x = max(min_x, min(x, max_x))
    y = max(min_y, min(y, max_y))

    window.geometry(f"{width}x{height}{x:+d}{y:+d}")
    return width, height


class CTkSection(ctk.CTkFrame):
    """ClearLens-style bordered section with a translatable heading."""

    def __init__(self, master: tk.Misc, text: str = "", **kwargs: object) -> None:
        kwargs.setdefault("fg_color", COLOR_SURFACE)
        kwargs.setdefault("border_color", COLOR_BORDER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 7)
        super().__init__(master, **kwargs)
        self._section_title = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLOR_ACCENT,
            anchor="w",
        )
        self._section_title.grid(row=0, column=0, columnspan=20, sticky="ew", padx=12, pady=(9, 5))

    def configure(self, require_redraw: bool = False, **kwargs: object) -> None:
        text = kwargs.pop("text", None)
        if text is not None:
            self._section_title.configure(text=str(text))
        super().configure(require_redraw=require_redraw, **kwargs)

    config = configure


class HoverScrollableFrame(ctk.CTkScrollableFrame):
    """CTk settings pane whose wheel scrolls whenever the pointer is inside it."""

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        kwargs.setdefault("fg_color", COLOR_PANEL)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("scrollbar_button_color", "#88a7ac")
        kwargs.setdefault("scrollbar_button_hover_color", "#65878d")
        super().__init__(master, **kwargs)
        self.inner = self

    def _scroll(self, units: int) -> str:
        try:
            self._parent_canvas.yview_scroll(units, "units")
        except (AttributeError, tk.TclError):
            pass
        return "break"

    def _normalized_units(self, event: tk.Event) -> int:
        delta = int(getattr(event, "delta", 0))
        if delta > 0:
            return -3
        if delta < 0:
            return 3
        return 0

    def _mouse_wheel_all(self, event: tk.Event) -> str | None:
        """Override CTk's very large delta/6 step with a stable three-unit step."""
        try:
            if not self.check_if_master_is_canvas(event.widget):
                return None
            units = self._normalized_units(event)
            if units:
                return self._scroll(units)
        except (AttributeError, tk.TclError):
            return None
        return None

    def _wheel(self, event: tk.Event) -> str:
        units = self._normalized_units(event)
        return self._scroll(units or 3)

    def _bind_one(self, widget: tk.Misc) -> None:
        # Text/Listbox class bindings would otherwise consume the wheel first.
        if not isinstance(widget, (tk.Text, tk.Listbox)):
            return
        if getattr(widget, "_weblens_panel_scroll_bound", False):
            return
        try:
            widget.bind("<MouseWheel>", self._wheel, add="+")
            widget.bind("<Button-4>", lambda _e: self._scroll(-3), add="+")
            widget.bind("<Button-5>", lambda _e: self._scroll(3), add="+")
            setattr(widget, "_weblens_panel_scroll_bound", True)
        except (tk.TclError, ValueError):
            pass

    def bind_mousewheel_to_descendants(self) -> None:
        def walk(widget: tk.Misc) -> None:
            self._bind_one(widget)
            for child in widget.winfo_children():
                walk(child)
        walk(self)
        self.after_idle(lambda: walk(self))


class CTkSpinbox(ctk.CTkFrame):
    """Compact DPI-aware numeric input made only from CTk widgets."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        from_: float,
        to: float,
        textvariable: tk.Variable,
        increment: float = 1,
        width: int = 150,
        command: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, width=width, height=32, fg_color="transparent")
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.from_ = from_
        self.to = to
        self.increment = increment
        self.variable = textvariable
        self.command = command
        self.grid_columnconfigure(1, weight=1)
        self.minus = ctk.CTkButton(self, text="−", width=28, height=32, command=lambda: self._step(-1), **button_colors())
        self.entry = ctk.CTkEntry(self, textvariable=textvariable, height=32)
        self.plus = ctk.CTkButton(self, text="+", width=28, height=32, command=lambda: self._step(1), **button_colors())
        self.minus.grid(row=0, column=0, sticky="nsw", padx=(0, 4))
        self.entry.grid(row=0, column=1, sticky="nsew")
        self.plus.grid(row=0, column=2, sticky="nse", padx=(4, 0))

    def _step(self, direction: int) -> None:
        try:
            value = float(self.variable.get()) + direction * self.increment
        except (tk.TclError, TypeError, ValueError):
            value = self.from_
        value = min(self.to, max(self.from_, value))
        if isinstance(self.variable, tk.IntVar) or (float(value).is_integer() and float(self.increment).is_integer()):
            self.variable.set(int(value))
        else:
            self.variable.set(round(value, 8))
        if self.command is not None:
            self.command()

    def get(self) -> object:
        return self.variable.get()

    def set(self, value: object) -> None:
        self.variable.set(value)


class CompatProgressBar(ctk.CTkProgressBar):
    """CTk progress bar accepting ttk-style maximum/value configuration."""

    def __init__(self, master: tk.Misc, *, maximum: float = 100, value: float = 0, **kwargs: object) -> None:
        kwargs.pop("mode", None)
        super().__init__(master, **kwargs)
        self.maximum = max(1.0, float(maximum))
        self.value = float(value)
        self._sync()

    def _sync(self) -> None:
        self.set(min(1.0, max(0.0, self.value / self.maximum)))

    def configure(self, require_redraw: bool = False, **kwargs: object) -> None:
        kwargs.pop("mode", None)
        if "maximum" in kwargs:
            self.maximum = max(1.0, float(kwargs.pop("maximum")))
        if "value" in kwargs:
            self.value = float(kwargs.pop("value"))
        super().configure(require_redraw=require_redraw, **kwargs)
        self._sync()

    config = configure


class CTkSplitPane(ctk.CTkFrame):
    """Draggable CTk splitter with DPI-correct physical bounds."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        orientation: str = "horizontal",
        initial_ratio: float = 0.25,
        min_first: int = 180,
        min_second: int = 240,
        separator_width: int = 7,
        first_color: str | tuple[str, str] = "transparent",
        second_color: str | tuple[str, str] = "transparent",
    ) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=0)
        if orientation not in {"horizontal", "vertical"}:
            raise ValueError("orientation must be horizontal or vertical")
        self.orientation = orientation
        self.initial_ratio = min(0.9, max(0.1, initial_ratio))
        self.min_first = min_first
        self.min_second = min_second
        self.separator_width = separator_width
        self.ratio = self.initial_ratio
        self.position: float | None = None
        self.first = ctk.CTkFrame(self, fg_color=first_color, corner_radius=0)
        self.second = ctk.CTkFrame(self, fg_color=second_color, corner_radius=0)
        self.first.pack_propagate(False)
        self.first.grid_propagate(False)
        self.second.pack_propagate(False)
        self.second.grid_propagate(False)
        cursor = "sb_h_double_arrow" if orientation == "horizontal" else "sb_v_double_arrow"
        self.separator = ctk.CTkFrame(self, fg_color="#9fb9bd", corner_radius=3, cursor=cursor)
        self.separator.bind("<ButtonPress-1>", self._start_drag)
        self.separator.bind("<B1-Motion>", self._drag)
        self.bind("<Configure>", self._layout, add="+")
        self._drag_offset = 0.0

    def _logical_size(self) -> tuple[float, float]:
        width = max(1.0, float(self._reverse_widget_scaling(self.winfo_width())))
        height = max(1.0, float(self._reverse_widget_scaling(self.winfo_height())))
        return width, height

    def _clamp_position(self, value: float, total: float) -> float:
        maximum = max(float(self.min_first), total - self.separator_width - self.min_second)
        return min(maximum, max(float(self.min_first), value))

    def _layout(self, _event: object = None) -> None:
        width, height = self._logical_size()
        total = width if self.orientation == "horizontal" else height
        if total >= self.min_first + self.separator_width + self.min_second:
            self.position = self._clamp_position(total * self.ratio, total)
            position = self.position
        else:
            position = max(1.0, total * self.ratio)
        physical_width = max(1, int(self.winfo_width()))
        physical_height = max(1, int(self.winfo_height()))
        physical_position = max(1, round(float(self._apply_widget_scaling(position))))
        physical_separator = max(1, round(float(self._apply_widget_scaling(self.separator_width))))
        if self.orientation == "horizontal":
            first_width = min(physical_width, physical_position)
            second_x = min(physical_width, first_width + physical_separator)
            tk.Place.place_configure(self.first, x=0, y=0, width=first_width, height=physical_height)
            tk.Place.place_configure(self.separator, x=first_width, y=0, width=max(1, min(physical_separator, physical_width - first_width)), height=physical_height)
            tk.Place.place_configure(self.second, x=second_x, y=0, width=max(1, physical_width - second_x), height=physical_height)
        else:
            first_height = min(physical_height, physical_position)
            second_y = min(physical_height, first_height + physical_separator)
            tk.Place.place_configure(self.first, x=0, y=0, width=physical_width, height=first_height)
            tk.Place.place_configure(self.separator, x=0, y=first_height, width=physical_width, height=max(1, min(physical_separator, physical_height - first_height)))
            tk.Place.place_configure(self.second, x=0, y=second_y, width=physical_width, height=max(1, physical_height - second_y))

    def _start_drag(self, event: tk.Event) -> None:
        pointer = event.x_root if self.orientation == "horizontal" else event.y_root
        origin = self.winfo_rootx() if self.orientation == "horizontal" else self.winfo_rooty()
        current = float(self._apply_widget_scaling(self.position or 0))
        self._drag_offset = pointer - origin - current

    def _drag(self, event: tk.Event) -> None:
        pointer = event.x_root if self.orientation == "horizontal" else event.y_root
        origin = self.winfo_rootx() if self.orientation == "horizontal" else self.winfo_rooty()
        physical = pointer - origin - self._drag_offset
        logical = float(self._reverse_widget_scaling(physical))
        width, height = self._logical_size()
        total = width if self.orientation == "horizontal" else height
        self.position = self._clamp_position(logical, total)
        if total > 0:
            self.ratio = min(0.95, max(0.05, self.position / total))
        self._layout()

    def set_ratio(self, ratio: float) -> None:
        self.ratio = min(0.95, max(0.05, ratio))
        self._layout()


_TREE_IDS = count(1)


def _window_scale(widget: tk.Misc) -> float:
    if sys.platform.startswith("win"):
        try:
            hwnd = int(widget.winfo_toplevel().winfo_id())
            dpi = int(ctypes.windll.user32.GetDpiForWindow(hwnd))
            if dpi > 0:
                return min(4.0, max(0.75, dpi / 96.0))
        except (AttributeError, OSError, TypeError, ValueError, tk.TclError):
            pass
    try:
        return min(4.0, max(0.75, float(widget.winfo_fpixels("1i")) / 96.0))
    except (TypeError, ValueError, tk.TclError):
        return 1.0


class DpiAwareMenu(tk.Menu):
    """Traditional menu bar with per-window DPI-correct typography."""

    def __init__(self, master: tk.Misc, *args: object, base_font_size: int = 13, **kwargs: object) -> None:
        self._base_font_size = max(8, int(base_font_size))
        self._last_scale: float | None = None
        inherited_dpi_window = getattr(master, "_dpi_window", None)
        if inherited_dpi_window is not None:
            self._dpi_window = inherited_dpi_window
        else:
            try:
                self._dpi_window = master.winfo_toplevel()
            except tk.TclError:
                self._dpi_window = master
        self._menu_font = tkfont.Font(root=master, family=FONT_FAMILY, size=-self._base_font_size)
        kwargs.setdefault("font", self._menu_font)
        super().__init__(master, *args, **kwargs)
        self.bind("<Map>", self._sync_dpi, add="+")
        self._sync_dpi()
        self.after_idle(self._sync_dpi)

    def _sync_dpi(self, _event: object = None) -> None:
        try:
            if not self.winfo_exists():
                return
            scale = _window_scale(self._dpi_window)
            if self._last_scale is None or abs(scale - self._last_scale) > 0.01:
                self._menu_font.configure(size=-max(12, round(self._base_font_size * scale)))
                self._last_scale = scale
        except tk.TclError:
            return


class DpiAwareTreeview(ttk.Treeview):
    """Native Treeview with ClearLens colors and per-window DPI metrics."""

    def __init__(self, master: tk.Misc, *args: object, base_row_height: int = 28, **kwargs: object) -> None:
        self._style_name = f"WebLens{next(_TREE_IDS)}.Treeview"
        kwargs["style"] = self._style_name
        super().__init__(master, *args, **kwargs)
        self._base_row_height = base_row_height
        self._last_scale: float | None = None
        self._logical_columns: dict[str, tuple[float, float]] = {}
        self._style = ttk.Style(self)
        try:
            self._style.theme_use("clam")
        except tk.TclError:
            pass
        self.after(20, self._poll_dpi)

    def logical_column(self, column: str, *, width: int, minwidth: int = 20, **kwargs: object) -> None:
        self._logical_columns[column] = (float(width), float(minwidth))
        scale = self._last_scale or _window_scale(self)
        super().column(column, width=max(1, round(width * scale)), minwidth=max(1, round(minwidth * scale)), **kwargs)

    def _poll_dpi(self) -> None:
        try:
            if not self.winfo_exists():
                return
            scale = _window_scale(self)
            if self._last_scale is None or abs(scale - self._last_scale) > 0.01:
                self._apply_dpi(scale)
            self.after(600, self._poll_dpi)
        except tk.TclError:
            return

    def _apply_dpi(self, scale: float) -> None:
        body_px = max(12, round(14 * scale))
        heading_px = max(12, round(14 * scale))
        row_height = max(22, round(self._base_row_height * scale))
        self._style.configure(
            self._style_name,
            font=(FONT_FAMILY, -body_px),
            rowheight=row_height,
            background=COLOR_SURFACE,
            fieldbackground=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
        )
        heading_style = f"{self._style_name}.Heading"
        self._style.configure(
            heading_style,
            font=(FONT_FAMILY, -heading_px, "bold"),
            padding=(round(6 * scale), round(4 * scale)),
            background="#d9e8eb",
            foreground=COLOR_TEXT,
            relief="flat",
        )
        self._style.map(self._style_name, background=[("selected", "#b7dfe3")], foreground=[("selected", "#10282c")])
        self._style.map(heading_style, background=[("active", "#c5dde0")])
        for column, (width, minwidth) in self._logical_columns.items():
            super().column(column, width=max(1, round(width * scale)), minwidth=max(1, round(minwidth * scale)))
        self._last_scale = scale
