from __future__ import annotations

import sys


def dependency_check() -> int:
    required = ["customtkinter", "openpyxl", "pypdf", "openai", "PIL"]
    missing = []
    for name in required:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    if missing:
        print("Missing required packages:", ", ".join(missing))
        return 1
    from metadatalens import APP_NAME, APP_VERSION
    from metadatalens.templates import TemplateLibrary

    lib = TemplateLibrary()
    assert lib.system, "No system templates found"
    print(f"{APP_NAME} {APP_VERSION}: dependency and template checks passed.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(dependency_check())
    try:
        from metadatalens.ui.dpi import enable_windows_dpi_awareness

        enable_windows_dpi_awareness()
        from metadatalens.app import run
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            print(
                "CustomTkinter is not installed in this Python environment.\n"
                "Run: python -m pip install -r requirements.txt"
            )
            raise SystemExit(1) from exc
        raise
    run()
