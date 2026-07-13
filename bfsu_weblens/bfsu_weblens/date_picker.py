# -*- coding: utf-8 -*-
"""Pure-tkinter date selector with quick year/month navigation."""
from __future__ import annotations

import calendar
from datetime import date
import tkinter as tk
from tkinter import ttk

class DateEntry(ttk.Frame):
    def __init__(self, master, text_getter, icon_path: str | None = None, initial: date | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self.text_getter = text_getter
        self.icon_path = icon_path
        self.var = tk.StringVar(value=(initial or date.today()).isoformat())
        self.entry = ttk.Entry(self, textvariable=self.var, width=13, state="readonly")
        self.entry.pack(side="left", fill="x", expand=True)
        self.button = ttk.Button(self, text="📅", width=3, command=self.open_picker)
        self.button.pack(side="left", padx=(4, 0))
    def get_date(self) -> date:
        return date.fromisoformat(self.var.get())
    def set_date(self, d: date) -> None:
        self.var.set(d.isoformat())
    def open_picker(self) -> None:
        DatePicker(self, self.get_date(), self.set_date, self.text_getter, self.icon_path)

class DatePicker(tk.Toplevel):
    def __init__(self, master, initial: date, callback, text_getter, icon_path: str | None = None):
        super().__init__(master)
        self.callback = callback
        self.text_getter = text_getter
        self.selected = initial
        self.year_var = tk.IntVar(value=initial.year)
        self.month_var = tk.IntVar(value=initial.month)
        self.title(self._t("date_picker_title"))
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.configure(bg="#EEF3F5")
        if icon_path:
            try: self.iconbitmap(icon_path)
            except Exception: pass
        self._build()
        self._render_days()
        self.update_idletasks()
        x = master.winfo_rootx()
        y = master.winfo_rooty() + master.winfo_height() + 4
        self.geometry(f"+{x}+{y}")
    def _t(self, key): return self.text_getter(key)
    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="both", expand=True)
        nav = ttk.Frame(top)
        nav.pack(fill="x", pady=(0, 8))
        ttk.Label(nav, text=self._t("year")).pack(side="left")
        self.year_spin = ttk.Spinbox(nav, from_=1900, to=2100, textvariable=self.year_var, width=7, command=self._render_days)
        self.year_spin.pack(side="left", padx=(4, 12))
        ttk.Label(nav, text=self._t("month")).pack(side="left")
        self.month_box = ttk.Combobox(nav, textvariable=self.month_var, values=list(range(1, 13)), width=5, state="readonly")
        self.month_box.pack(side="left", padx=(4, 8))
        self.month_box.bind("<<ComboboxSelected>>", lambda e: self._render_days())
        ttk.Button(nav, text="‹", width=3, command=self._prev_month).pack(side="left")
        ttk.Button(nav, text="›", width=3, command=self._next_month).pack(side="left", padx=(3, 0))
        self.days_frame = ttk.Frame(top)
        self.days_frame.pack()
        bottom = ttk.Frame(top)
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Button(bottom, text=self._t("today"), command=self._today).pack(side="left")
        ttk.Button(bottom, text=self._t("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(bottom, text=self._t("apply"), command=self._apply).pack(side="right", padx=(0, 6))
    def _prev_month(self):
        y, m = self.year_var.get(), self.month_var.get()
        if m == 1: y -= 1; m = 12
        else: m -= 1
        self.year_var.set(y); self.month_var.set(m); self._render_days()
    def _next_month(self):
        y, m = self.year_var.get(), self.month_var.get()
        if m == 12: y += 1; m = 1
        else: m += 1
        self.year_var.set(y); self.month_var.set(m); self._render_days()
    def _today(self):
        d = date.today(); self.year_var.set(d.year); self.month_var.set(d.month); self.selected = d; self._render_days()
    def _apply(self):
        self.callback(self.selected); self.destroy()
    def _select_day(self, day: int):
        self.selected = date(self.year_var.get(), self.month_var.get(), day); self._render_days()
    def _render_days(self):
        for child in self.days_frame.winfo_children(): child.destroy()
        weekday_names = self._t("weekday_names").split()
        if len(weekday_names) != 7: weekday_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        for col, name in enumerate(weekday_names):
            ttk.Label(self.days_frame, text=name, width=5, anchor="center").grid(row=0, column=col, padx=1, pady=1)
        y, m = int(self.year_var.get()), int(self.month_var.get())
        cal = calendar.Calendar(firstweekday=0)
        for r, week in enumerate(cal.monthdayscalendar(y, m), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text="", width=5).grid(row=r, column=c, padx=1, pady=1)
                else:
                    text = f"[{day}]" if self.selected == date(y, m, day) else str(day)
                    ttk.Button(self.days_frame, text=text, width=5, command=lambda d=day: self._select_day(d)).grid(row=r, column=c, padx=1, pady=1)
