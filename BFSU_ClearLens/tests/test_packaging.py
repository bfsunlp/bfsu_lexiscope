from __future__ import annotations

import unittest
import runpy
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_windows_build_uses_isolated_onedir_layout(self) -> None:
        script = (ROOT / "build_clearlens.bat").read_text(encoding="utf-8")
        for required in (
            "virtual_env",
            "--onedir",
            '--contents-directory "_internal"',
            "BFSU_ClearLens.exe",
            "assets config samples",
            "README.md technical_readme.md RELEASE_NOTES.md requirements.txt",
        ):
            self.assertIn(required, script)
        self.assertNotIn("--add-data", script)

    def test_all_toplevels_use_the_shared_icon_base(self) -> None:
        for path in (ROOT / "clearlens").glob("ui_*.py"):
            if path.name == "ui_common.py":
                continue
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("(tk.Toplevel)", source, path.name)
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        self.assertIn("apply_window_icon(self, default=True)", app_source)

    def test_frozen_resources_prefer_the_executable_directory(self) -> None:
        original_executable = sys.executable
        had_frozen = hasattr(sys, "frozen")
        original_frozen = getattr(sys, "frozen", None)
        had_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                internal = root / "_internal"
                external_icon = root / "assets" / "app.png"
                internal_icon = internal / "assets" / "app.png"
                external_icon.parent.mkdir(parents=True)
                internal_icon.parent.mkdir(parents=True)
                external_icon.write_bytes(b"external")
                internal_icon.write_bytes(b"internal")
                sys.executable = str(root / "BFSU_ClearLens.exe")
                sys.frozen = True  # type: ignore[attr-defined]
                sys._MEIPASS = str(internal)  # type: ignore[attr-defined]

                namespace = runpy.run_path(str(ROOT / "clearlens" / "config.py"))

                self.assertEqual(namespace["resource_path"]("assets/app.png"), external_icon)
        finally:
            sys.executable = original_executable
            if had_frozen:
                sys.frozen = original_frozen  # type: ignore[attr-defined]
            elif hasattr(sys, "frozen"):
                del sys.frozen  # type: ignore[attr-defined]
            if had_meipass:
                sys._MEIPASS = original_meipass  # type: ignore[attr-defined]
            elif hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
