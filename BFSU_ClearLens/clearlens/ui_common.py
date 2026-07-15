from __future__ import annotations

import tkinter as tk

from .config import resource_path


def apply_window_icon(window: tk.Misc, default: bool = False) -> None:
    """Apply the product icon to both Tk and native Windows title bars."""
    png_path = resource_path("assets/app.png")
    if png_path.exists():
        try:
            photo = tk.PhotoImage(master=window, file=str(png_path))
            window.wm_iconphoto(default, photo)
            setattr(window, "_clearlens_icon_photo", photo)
        except (tk.TclError, OSError):
            pass

    ico_path = resource_path("assets/app.ico")
    if ico_path.exists():
        try:
            window.wm_iconbitmap(str(ico_path))
        except (tk.TclError, OSError):
            pass


class IconToplevel(tk.Toplevel):
    def __init__(self, master: tk.Misc | None = None, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        apply_window_icon(self)
