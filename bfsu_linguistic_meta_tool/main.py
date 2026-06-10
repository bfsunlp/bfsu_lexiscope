"""Program entry point."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

# Make local imports work when launched by double-clicking main.py.
SOURCE_DIR = Path(__file__).resolve().parent

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return SOURCE_DIR


BASE_DIR = app_base_dir()

from controllers import MetadataController  # noqa: E402
from i18n import I18N  # noqa: E402
from views.main_window import MainWindow  # noqa: E402


def center_window(root: tk.Tk, width: int = 1280, height: int = 760) -> None:
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = max((screen_w - width) // 2, 0)
    y = max((screen_h - height) // 2, 0)
    root.geometry(f"{width}x{height}+{x}+{y}")


def main() -> None:
    root = tk.Tk()

    # 设置窗口图标
    icon_ico = BASE_DIR / "assets" / "app.ico"
    icon_png = BASE_DIR / "assets" / "app.png"

    try:
        if icon_ico.exists():
            root.iconbitmap(str(icon_ico))
        elif icon_png.exists():
            icon = tk.PhotoImage(file=str(icon_png))
            root.iconphoto(True, icon)
            root._icon_ref = icon  # 防止图标被垃圾回收
    except tk.TclError:
        pass

    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass

    i18n = I18N("en_US")
    window = MainWindow(root, i18n)
    MetadataController(root, window, i18n)
    center_window(root)
    root.mainloop()


if __name__ == "__main__":
    main()
