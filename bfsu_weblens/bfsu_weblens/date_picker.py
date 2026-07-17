# -*- coding: utf-8 -*-
"""CustomTkinter date selector with Windows DPI-safe sizing."""
from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from .ui_common import (
    FONT_FAMILY,
    COLOR_BG,
    COLOR_PANEL,
    COLOR_SURFACE,
    COLOR_BORDER,
    COLOR_TEXT,
    COLOR_MUTED,
    COLOR_ACCENT,
    CTkSection,
    CTkSpinbox,
    apply_window_icon,
    button_colors,
    fit_window_to_screen,
)


class DateEntry(ctk.CTkFrame):
    def __init__(self, master, text_getter, icon_path: str | None = None, initial: date | None = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.text_getter = text_getter
        self.icon_path = icon_path
        self.var = tk.StringVar(value=(initial or date.today()).isoformat())
        self.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.var,
            width=150,
            height=32,
            state="readonly",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.entry.grid(row=0, column=0, sticky="ew")
        self.button = ctk.CTkButton(
            self,
            text="▣",
            width=38,
            height=32,
            command=self.open_picker,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15),
            **button_colors(),
        )
        self.button.grid(row=0, column=1, padx=(6, 0))

    def get_date(self) -> date:
        return date.fromisoformat(self.var.get())

    def set_date(self, d: date) -> None:
        self.var.set(d.isoformat())

    def open_picker(self) -> None:
        DatePicker(self, self.get_date(), self.set_date, self.text_getter, self.icon_path)


class DatePicker(ctk.CTkToplevel):
    def __init__(self, master, initial: date, callback, text_getter, icon_path: str | None = None):
        super().__init__(master)
        self.callback = callback
        self.text_getter = text_getter
        self.selected = initial
        self.year_var = tk.IntVar(value=initial.year)
        self.month_var = tk.StringVar(value=str(initial.month))
        self.title(self._t("date_picker_title"))
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        if icon_path:
            ico = Path(icon_path)
            apply_window_icon(self, ico.with_suffix(".png"), ico)
        self._build()
        self._render_days()
        fit_window_to_screen(
            self,
            requested_width=540,
            requested_height=500,
            parent=master.winfo_toplevel(),
            min_width=460,
            min_height=420,
        )
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self._apply())
        self.lift()
        self.focus_force()

    def _t(self, key):
        return self.text_getter(key)

    def _build(self):
        root = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=14, pady=14)
        section = CTkSection(root, text=self._t("date_picker_title"))
        section.pack(fill="both", expand=True)
        section.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(section, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 10))
        ctk.CTkLabel(nav, text=self._t("year"), text_color=COLOR_MUTED).pack(side="left")
        self.year_spin = CTkSpinbox(
            nav,
            from_=1900,
            to=2100,
            textvariable=self.year_var,
            width=130,
            command=self._render_days,
        )
        self.year_spin.pack(side="left", padx=(6, 14))
        ctk.CTkLabel(nav, text=self._t("month"), text_color=COLOR_MUTED).pack(side="left")
        self.month_box = ctk.CTkComboBox(
            nav,
            variable=self.month_var,
            values=[str(value) for value in range(1, 13)],
            width=82,
            height=32,
            state="readonly",
            command=lambda _value: self._render_days(),
        )
        self.month_box.pack(side="left", padx=(6, 10))
        ctk.CTkButton(nav, text="‹", width=38, height=32, command=self._prev_month, **button_colors()).pack(side="left")
        ctk.CTkButton(nav, text="›", width=38, height=32, command=self._next_month, **button_colors()).pack(side="left", padx=(5, 0))

        self.days_frame = ctk.CTkFrame(section, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=6)
        self.days_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
        for column in range(7):
            self.days_frame.grid_columnconfigure(column, weight=1, uniform="day")

        bottom = ctk.CTkFrame(section, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkButton(bottom, text=self._t("today"), command=self._today, width=96, height=32, **button_colors()).pack(side="left")
        ctk.CTkButton(bottom, text=self._t("cancel"), command=self.destroy, width=96, height=32, **button_colors()).pack(side="right")
        ctk.CTkButton(bottom, text=self._t("apply"), command=self._apply, width=96, height=32, **button_colors("accent")).pack(side="right", padx=(0, 8))

    def _month(self) -> int:
        try:
            return int(self.month_var.get())
        except (TypeError, ValueError, tk.TclError):
            return 1

    def _prev_month(self):
        y, m = self.year_var.get(), self._month()
        if m == 1:
            y -= 1
            m = 12
        else:
            m -= 1
        self.year_var.set(y)
        self.month_var.set(str(m))
        self._render_days()

    def _next_month(self):
        y, m = self.year_var.get(), self._month()
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
        self.year_var.set(y)
        self.month_var.set(str(m))
        self._render_days()

    def _today(self):
        current = date.today()
        self.year_var.set(current.year)
        self.month_var.set(str(current.month))
        self.selected = current
        self._render_days()

    def _apply(self):
        self.callback(self.selected)
        self.destroy()

    def _select_day(self, day: int):
        self.selected = date(self.year_var.get(), self._month(), day)
        self._render_days()

    def _render_days(self):
        if not hasattr(self, "days_frame"):
            return
        for child in self.days_frame.winfo_children():
            child.destroy()
        weekday_names = self._t("weekday_names").split()
        if len(weekday_names) != 7:
            weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_font = ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")
        day_font = ctk.CTkFont(family=FONT_FAMILY, size=11)
        for col, name in enumerate(weekday_names):
            ctk.CTkLabel(
                self.days_frame,
                text=name,
                height=28,
                font=header_font,
                text_color=COLOR_ACCENT,
            ).grid(row=0, column=col, sticky="ew", padx=2, pady=(6, 2))
        y, m = int(self.year_var.get()), self._month()
        cal = calendar.Calendar(firstweekday=0)
        for row, week in enumerate(cal.monthdayscalendar(y, m), start=1):
            for col, day_number in enumerate(week):
                if day_number == 0:
                    ctk.CTkLabel(self.days_frame, text="", height=34).grid(row=row, column=col, sticky="ew", padx=2, pady=2)
                    continue
                selected = self.selected == date(y, m, day_number)
                colors = button_colors("accent") if selected else button_colors()
                ctk.CTkButton(
                    self.days_frame,
                    text=str(day_number),
                    height=32,
                    width=44,
                    font=day_font,
                    command=lambda value=day_number: self._select_day(value),
                    **colors,
                ).grid(row=row, column=col, sticky="ew", padx=2, pady=2)
