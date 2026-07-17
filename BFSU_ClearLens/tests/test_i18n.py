from __future__ import annotations

import unittest

from clearlens.i18n import EN, ZH_SIM, ZH_TRA, I18n
from clearlens.models import CleanOptions


class I18nTests(unittest.TestCase):
    def test_chinese_product_name_and_option_labels(self) -> None:
        i18n = I18n("zh_sim")
        self.assertEqual(i18n.t("app_title"), "BFSU 文本整理器")
        for key, value in CleanOptions().to_dict().items():
            if isinstance(value, bool):
                label = i18n.t(f"option_{key}")
                self.assertNotEqual(label, f"option_{key}")

    def test_all_supported_languages_have_main_menu_labels(self) -> None:
        for language in ("en", "zh_sim", "zh_tra"):
            i18n = I18n(language)
            for key in ("file", "edit", "document", "cleaning", "ai", "tools", "settings", "help"):
                self.assertNotEqual(i18n.t(key), key)

    def test_all_languages_cover_the_same_interface_keys(self) -> None:
        self.assertEqual(set(EN), set(ZH_SIM))
        self.assertEqual(set(EN), set(ZH_TRA))

    def test_review_and_about_text_are_complete(self) -> None:
        for language in ("en", "zh_sim", "zh_tra"):
            i18n = I18n(language)
            for key in ("review_accept", "review_reject", "review_accept_all", "review_reject_all"):
                self.assertNotEqual(i18n.t(key), key)
            about = i18n.t("about_text", version="1.5.11")
            self.assertIn("djliu@bfsu.edu.cn", about)
            self.assertIn("Liu Dingjia", about)
            self.assertIn("OpenAI", about)
            self.assertIn("DeepSeek", about)
            self.assertIn("Save" if language == "en" else "保存" if language == "zh_sim" else "儲存", about)

    def test_toolbar_and_transcode_labels_are_compact(self) -> None:
        for language in ("en", "zh_sim", "zh_tra"):
            i18n = I18n(language)
            for key in (
                "toolbar_import", "toolbar_reset_current", "toolbar_reset_all",
                "toolbar_rule_current", "toolbar_rule_all", "transcode_current",
                "transcode_selected", "transcode_all", "progress_overall", "toolbar_open_output",
                "new_session", "find_next", "find_all", "find_count_message", "replace_count_message",
                "ai_preflight_title", "ai_preflight_failed", "compact_markup_preview_chars",
            ):
                self.assertNotEqual(i18n.t(key), key)
            self.assertNotIn("Prepare", i18n.t("transcode_current"))
            self.assertNotIn("准备", i18n.t("transcode_current"))
            self.assertNotIn("準備", i18n.t("transcode_current"))


if __name__ == "__main__":
    unittest.main()
