from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


# Shared BFSU LexiScope / CiteLens palette.  MetadataLens intentionally uses
# the same colour system so the tools look and behave as one desktop suite.
COLORS = {
    "navy": "#17384A",
    "blue": "#1F4E5F",
    "blue2": "#2F6F7E",
    "cyan": "#4C91A1",
    "gold": "#D5A84A",
    "background": "#E8EEF1",
    "toolbar": "#D8E3E8",
    "panel": "#F7FAFB",
    "surface": "#FFFFFF",
    "text": "#1F2A30",
    "muted": "#61717A",
    "border": "#CAD6DB",
    "error": "#B43A34",
    "warning": "#A56300",
    "success": "#26734D",
    "disabled": "#98A8B0",
}

FONT_FAMILY = "Segoe UI"
FONT_SEMIBOLD = "Segoe UI Semibold"

# Slightly larger minimum roles than CiteLens. Metadata entry is form-heavy and
# needs comfortable reading at 125–225% Windows scaling.
FONT_SIZES = {
    "small": 12,
    "body": 15,
    "button": 15,
    "table": 14,
    "table_heading": 14,
    "subtitle": 17,
    "heading": 22,
    "metric": 29,
    "brand": 31,
}


def calculate_ctk_font_sizes(system_points: int) -> dict[str, int]:
    points = max(9, abs(int(system_points)))
    base_pixels = max(15, round(points * 96 / 72) + 1)
    return {
        "small": max(12, base_pixels - 2),
        "body": base_pixels,
        "button": max(15, base_pixels),
        "table": max(14, base_pixels - 1),
        "table_heading": max(14, base_pixels - 1),
        "subtitle": base_pixels + 2,
        "heading": base_pixels + 7,
        "metric": base_pixels + 14,
        "brand": base_pixels + 16,
    }


def ctk_font(role: str = "body", *, semibold: bool = False) -> tuple[str, int]:
    family = FONT_SEMIBOLD if semibold else FONT_FAMILY
    return family, FONT_SIZES.get(role, FONT_SIZES["body"])


def configure_customtkinter() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def apply_theme(root: tk.Misc) -> None:
    style = ttk.Style(root)
    available = style.theme_names()
    style.theme_use("clam" if "clam" in available else available[0])

    try:
        system_points = max(9, abs(int(tkfont.nametofont("TkDefaultFont", root=root).actual("size"))))
    except (tk.TclError, TypeError, ValueError):
        system_points = 10
    FONT_SIZES.update(calculate_ctk_font_sizes(system_points))

    font_sizes = {
        "TkDefaultFont": max(10, system_points + 1),
        "TkTextFont": max(10, system_points + 1),
        "TkFixedFont": max(10, system_points + 1),
        "TkMenuFont": max(10, system_points + 1),
        "TkHeadingFont": max(10, system_points + 1),
        "TkCaptionFont": max(10, system_points + 1),
        "TkSmallCaptionFont": max(9, system_points),
        "TkIconFont": max(10, system_points + 1),
        "TkTooltipFont": max(9, system_points),
    }
    for font_name, size in font_sizes.items():
        try:
            tkfont.nametofont(font_name, root=root).configure(family=FONT_FAMILY, size=size)
        except tk.TclError:
            continue

    root.option_add("*tearOff", 0)
    root.option_add("*Menu.background", COLORS["panel"])
    root.option_add("*Menu.foreground", COLORS["text"])
    root.option_add("*Menu.activeBackground", COLORS["blue2"])
    root.option_add("*Menu.activeForeground", "#FFFFFF")

    style.configure(".", background=COLORS["background"], foreground=COLORS["text"], font=(FONT_FAMILY, max(10, system_points + 1)))
    style.configure("TPanedwindow", background=COLORS["border"])

    row_height = max(34, round(FONT_SIZES["table"] * 2.35))
    style.configure(
        "MetadataLens.Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        rowheight=row_height,
        font=(FONT_FAMILY, max(10, system_points + 1)),
    )
    style.configure(
        "MetadataLens.Treeview.Heading",
        background=COLORS["toolbar"],
        foreground=COLORS["navy"],
        bordercolor=COLORS["border"],
        relief="flat",
        padding=(9, 9),
        font=(FONT_SEMIBOLD, max(10, system_points + 1)),
    )
    style.map(
        "MetadataLens.Treeview",
        background=[("selected", COLORS["blue2"])],
        foreground=[("selected", "#FFFFFF")],
    )
    style.map(
        "MetadataLens.Treeview.Heading",
        background=[("active", COLORS["border"])],
        foreground=[("active", COLORS["navy"])],
    )

    # Native Listbox remains useful for template selection; make it match the
    # surrounding CTk cards and readable at high DPI.
    root.option_add("*Listbox.background", COLORS["surface"])
    root.option_add("*Listbox.foreground", COLORS["text"])
    root.option_add("*Listbox.selectBackground", COLORS["blue2"])
    root.option_add("*Listbox.selectForeground", "#FFFFFF")
