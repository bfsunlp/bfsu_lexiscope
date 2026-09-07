from __future__ import annotations

import customtkinter as ctk

from .theme import COLORS, ctk_font


def primary_button(master, **kwargs) -> ctk.CTkButton:
    kwargs.setdefault("height", 40)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("fg_color", COLORS["blue"])
    kwargs.setdefault("hover_color", COLORS["blue2"])
    kwargs.setdefault("text_color", "#FFFFFF")
    kwargs.setdefault("font", ctk_font("button", semibold=True))
    return ctk.CTkButton(master, **kwargs)


def secondary_button(master, **kwargs) -> ctk.CTkButton:
    kwargs.setdefault("height", 40)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("fg_color", COLORS["panel"])
    kwargs.setdefault("hover_color", COLORS["toolbar"])
    kwargs.setdefault("text_color", COLORS["navy"])
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", COLORS["border"])
    kwargs.setdefault("font", ctk_font("button"))
    return ctk.CTkButton(master, **kwargs)


def quiet_button(master, **kwargs) -> ctk.CTkButton:
    kwargs.setdefault("height", 38)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("fg_color", "transparent")
    kwargs.setdefault("hover_color", COLORS["border"])
    kwargs.setdefault("text_color", COLORS["navy"])
    kwargs.setdefault("border_width", 0)
    kwargs.setdefault("font", ctk_font("button"))
    return ctk.CTkButton(master, **kwargs)


def heading_label(master, **kwargs) -> ctk.CTkLabel:
    kwargs.setdefault("text_color", COLORS["navy"])
    kwargs.setdefault("font", ctk_font("heading", semibold=True))
    kwargs.setdefault("anchor", "w")
    return ctk.CTkLabel(master, **kwargs)


def body_label(master, *, muted: bool = False, semibold: bool = False, **kwargs) -> ctk.CTkLabel:
    kwargs.setdefault("text_color", COLORS["muted"] if muted else COLORS["text"])
    kwargs.setdefault("font", ctk_font("body", semibold=semibold))
    kwargs.setdefault("anchor", "w")
    kwargs.setdefault("justify", "left")
    return ctk.CTkLabel(master, **kwargs)


def card(master, **kwargs) -> ctk.CTkFrame:
    kwargs.setdefault("fg_color", COLORS["panel"])
    kwargs.setdefault("corner_radius", 7)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", COLORS["border"])
    return ctk.CTkFrame(master, **kwargs)


def surface_card(master, **kwargs) -> ctk.CTkFrame:
    kwargs.setdefault("fg_color", COLORS["surface"])
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", COLORS["border"])
    return ctk.CTkFrame(master, **kwargs)


def style_tabview(tabview: ctk.CTkTabview) -> ctk.CTkTabview:
    segmented = getattr(tabview, "_segmented_button", None)
    if segmented is not None:
        # Explicit dark text is important for unselected tabs on the light
        # BFSU CiteLens-style toolbar; relying on CustomTkinter defaults can
        # make inactive provider tabs appear washed out on Windows.
        segmented.configure(
            font=ctk_font("button", semibold=True),
            height=42,
            text_color=COLORS["text"],
        )
    return tabview
