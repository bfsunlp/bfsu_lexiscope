from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from itertools import count
from tkinter import font as tkfont
from typing import Callable

import customtkinter as ctk
from tkinter import ttk

from .config import resource_path


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


def apply_window_icon(window: tk.Misc, default: bool = False) -> None:
    """Apply the product icon now and again after the native window is mapped.

    CustomTkinter may recreate or remap a native child window after Python has
    already assigned its icon.  Reapplying on the first idle/map cycle keeps
    every ClearLens dialog on the product icon instead of the generic Tk icon.
    """

    def apply_once() -> None:
        try:
            if not window.winfo_exists():
                return
        except tk.TclError:
            return
        png_path = resource_path("assets/app.png")
        if png_path.exists():
            try:
                photo = getattr(window, "_clearlens_icon_photo", None)
                if photo is None:
                    photo = tk.PhotoImage(master=window, file=str(png_path))
                    setattr(window, "_clearlens_icon_photo", photo)
                window.wm_iconphoto(default, photo)
            except (tk.TclError, OSError):
                pass

        ico_path = resource_path("assets/app.ico")
        if ico_path.exists():
            try:
                window.wm_iconbitmap(str(ico_path))
            except (tk.TclError, OSError):
                pass

    apply_once()
    try:
        window.after_idle(apply_once)
        if not getattr(window, "_clearlens_icon_map_bound", False):
            setattr(window, "_clearlens_icon_map_bound", True)
            window.bind("<Map>", lambda _event: apply_once(), add="+")
    except tk.TclError:
        pass


class IconToplevel(ctk.CTkToplevel):
    """Shared CTk child window with the product icon and Windows-aware scaling."""

    def __init__(self, master: tk.Misc | None = None, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        apply_window_icon(self)


def make_section(parent: tk.Misc, title: str) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(
        parent,
        fg_color=COLOR_SURFACE,
        border_color=COLOR_BORDER,
        border_width=1,
        corner_radius=7,
    )
    ctk.CTkLabel(
        frame,
        text=title,
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=COLOR_ACCENT,
    ).pack(anchor=tk.W, padx=10, pady=(8, 4))
    return frame


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


class CTkSpinbox(ctk.CTkFrame):
    """Compact DPI-aware numeric input composed only of CTk widgets."""

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
        super().__init__(master, width=width, height=30, fg_color="transparent")
        self.from_ = from_
        self.to = to
        self.increment = increment
        self.variable = textvariable
        self.command = command
        self.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(self, textvariable=textvariable, height=30)
        self.entry.grid(row=0, column=0, rowspan=2, sticky=tk.NSEW, padx=(0, 4))
        self.minus = ctk.CTkButton(self, text="−", width=28, height=14, command=lambda: self._step(-1), **button_colors())
        self.plus = ctk.CTkButton(self, text="+", width=28, height=14, command=lambda: self._step(1), **button_colors())
        self.minus.grid(row=0, column=1, sticky=tk.EW, pady=(0, 1))
        self.plus.grid(row=1, column=1, sticky=tk.EW, pady=(1, 0))

    def _step(self, direction: int) -> None:
        try:
            value = float(self.variable.get()) + direction * self.increment
        except (tk.TclError, TypeError, ValueError):
            value = self.from_
        value = min(self.to, max(self.from_, value))
        if isinstance(self.variable, tk.IntVar) or float(value).is_integer() and float(self.increment).is_integer():
            self.variable.set(int(value))
        else:
            self.variable.set(round(value, 8))
        if self.command is not None:
            self.command()


class CTkSplitPane(ctk.CTkFrame):
    """A draggable CTk splitter whose panes always occupy their full allocation.

    CTk deliberately rejects ``width`` and ``height`` in ``place()`` and asks
    callers to set the requested widget size through ``configure()``.  A frame
    with geometry propagation enabled can nevertheless replace that requested
    size with the size requested by its children.  On a scaled Windows display
    that left the separator in the correct place while both pane frames shrank
    into their top-left corners.  The splitter therefore uses Tk's underlying
    place manager with explicit *physical* bounds.  CTk still receives normal
    Configure events and redraws each frame at the assigned size.
    """

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
        # Preserve a ratio, rather than an absolute pixel position, so maximize,
        # restore and monitor-size changes do not distort the workspace layout.
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
            tk.Place.place_configure(
                self.separator,
                x=first_width,
                y=0,
                width=max(1, min(physical_separator, physical_width - first_width)),
                height=physical_height,
            )
            tk.Place.place_configure(
                self.second,
                x=second_x,
                y=0,
                width=max(1, physical_width - second_x),
                height=physical_height,
            )
        else:
            first_height = min(physical_height, physical_position)
            second_y = min(physical_height, first_height + physical_separator)
            tk.Place.place_configure(self.first, x=0, y=0, width=physical_width, height=first_height)
            tk.Place.place_configure(
                self.separator,
                x=0,
                y=first_height,
                width=physical_width,
                height=max(1, min(physical_separator, physical_height - first_height)),
            )
            tk.Place.place_configure(
                self.second,
                x=0,
                y=second_y,
                width=physical_width,
                height=max(1, physical_height - second_y),
            )

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
        width, height = self._logical_size()
        total = width if self.orientation == "horizontal" else height
        self.position = self._clamp_position(total * self.ratio, total)
        self._layout()


class EditorTextbox(ctk.CTkTextbox):
    """CTkTextbox compatibility surface used by the line-numbered editor."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._line_number_start = 1

    def cget(self, attribute_name: str) -> object:
        if attribute_name in {"state", "tabs", "wrap", "undo"}:
            return self._textbox.cget(attribute_name)
        return super().cget(attribute_name)

    def tag_configure(self, tag_name: str, **kwargs: object) -> object:
        return self._textbox.tag_configure(tag_name, **kwargs)

    def event_generate(self, sequence: str, **kwargs: object) -> object:
        return self._textbox.event_generate(sequence, **kwargs)

    def native_font(self) -> object:
        return self._textbox.cget("font")

    def set_wrap_mode(self, mode: str) -> None:
        self._textbox.configure(wrap=mode)

    def set_line_number_start(self, first_line: int) -> None:
        self._line_number_start = max(1, int(first_line))

    def logical_line_number(self, displayed_line: int) -> int:
        return self._line_number_start + max(0, int(displayed_line) - 1)

    def displayed_line_number(self, logical_line: int) -> int | None:
        displayed = int(logical_line) - self._line_number_start + 1
        maximum = max(1, int(self.index("end-1c").split(".")[0]))
        return displayed if 1 <= displayed <= maximum else None

    def viewport_y_offset(self) -> int:
        try:
            return int(self._textbox.winfo_y())
        except tk.TclError:
            return 0

    def viewport_height(self) -> int:
        try:
            return max(1, int(self._textbox.winfo_height()))
        except tk.TclError:
            return max(1, int(self.winfo_height()))

    def reset_undo(self) -> None:
        try:
            self._textbox.edit_reset()
        except tk.TclError:
            pass


class VariableProgressBar(ctk.CTkProgressBar):
    def __init__(self, master: tk.Misc, variable: tk.DoubleVar, maximum: float = 1, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.variable = variable
        self.maximum = max(1.0, float(maximum))
        self._trace_id = variable.trace_add("write", self._sync)
        self._sync()

    def configure(self, **kwargs: object) -> None:
        if "maximum" in kwargs:
            self.maximum = max(1.0, float(kwargs.pop("maximum")))
        super().configure(**kwargs)
        self._sync()

    def _sync(self, *_args: object) -> None:
        try:
            value = float(self.variable.get())
        except (tk.TclError, TypeError, ValueError):
            value = 0.0
        self.set(min(1.0, max(0.0, value / self.maximum)))

    def destroy(self) -> None:
        try:
            self.variable.trace_remove("write", self._trace_id)
        except tk.TclError:
            pass
        super().destroy()


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
    """Native menu whose text follows the DPI of its owning window."""

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
    """Native Treeview with CTk-aligned colors and per-window DPI metrics."""

    def __init__(self, master: tk.Misc, *args: object, base_row_height: int = 28, **kwargs: object) -> None:
        self._style_name = f"ClearLens{next(_TREE_IDS)}.Treeview"
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
        if self._last_scale:
            for column in tuple(self._logical_columns):
                try:
                    current = float(super().column(column, "width"))
                    minimum = float(super().column(column, "minwidth"))
                    self._logical_columns[column] = (current / self._last_scale, minimum / self._last_scale)
                except (tk.TclError, TypeError, ValueError):
                    pass
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
        self._style.map(
            self._style_name,
            background=[("selected", "#b7dfe3")],
            foreground=[("selected", "#10282c")],
        )
        self._style.map(heading_style, background=[("active", "#c5dde0")])
        for column, (width, minwidth) in self._logical_columns.items():
            super().column(column, width=max(1, round(width * scale)), minwidth=max(1, round(minwidth * scale)))
        self._last_scale = scale
