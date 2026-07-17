from __future__ import annotations

import unittest

from clearlens.config import load_default_settings, normalize_settings


class DisplaySettingsTests(unittest.TestCase):
    def test_default_settings_have_no_interface_scale(self) -> None:
        self.assertNotIn("display", load_default_settings())

    def test_legacy_interface_scale_is_removed_during_migration(self) -> None:
        settings = normalize_settings({"display": {"ui_scale_percent": 150, "sidebar_ratio": 0.4}})
        self.assertNotIn("display", settings)

    def test_output_encoding_defaults_to_utf8(self) -> None:
        self.assertEqual(normalize_settings({"output": {}})["output"]["encoding"], "utf-8")
        self.assertEqual(normalize_settings({"output": {"encoding": ""}})["output"]["encoding"], "utf-8")


if __name__ == "__main__":
    unittest.main()
