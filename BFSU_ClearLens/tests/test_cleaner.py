from __future__ import annotations

import unittest

from clearlens.cleaner import (
    clean_text,
    fullwidth_to_halfwidth,
    halfwidth_to_fullwidth,
    paragraph_reflow,
)
from clearlens.models import CleanOptions, RegexRule


class CleanerTests(unittest.TestCase):
    def test_default_cleaning_is_conservative_and_deterministic(self) -> None:
        source = "\ufeff中 \u200b 文  \r\n\r\n\r\n重复行\r\n重复行\r\n##########\r\n"
        cleaned, result = clean_text(source, CleanOptions())
        self.assertEqual(cleaned, "中文\n\n重复行\n")
        self.assertIn("strip_bom", result.changes)
        self.assertTrue(any(change.startswith("dedupe_adjacent_lines") for change in result.changes))

    def test_width_conversion_round_trip_for_ascii(self) -> None:
        source = "ABC 123!?"
        full = halfwidth_to_fullwidth(source)
        self.assertEqual(full, "ＡＢＣ　１２３！？")
        self.assertEqual(fullwidth_to_halfwidth(full), source)

    def test_paragraph_reflow_preserves_list_layout(self) -> None:
        source = "This is a wrapped\nEnglish paragraph.\n\n- first\n- second"
        self.assertEqual(paragraph_reflow(source), "This is a wrapped English paragraph.\n\n- first\n- second")

    def test_default_cleaning_preserves_leading_indentation(self) -> None:
        source = "\u3000\u3000中文段落   \n    indented code   "
        cleaned, _result = clean_text(source, CleanOptions())
        self.assertEqual(cleaned, "\u3000\u3000中文段落\n    indented code")

    def test_leading_whitespace_can_be_removed_independently(self) -> None:
        source = "  first\n\tsecond\n\u3000third"
        cleaned, result = clean_text(source, CleanOptions(strip_leading_whitespace=True, tabs_to_spaces=False))
        self.assertEqual(cleaned, "first\nsecond\nthird")
        self.assertIn("strip_leading_whitespace", result.changes)

    def test_regex_error_is_logged_without_destroying_text(self) -> None:
        rule = RegexRule(key="bad", name="bad", pattern="[", enabled=True)
        cleaned, result = clean_text("abc", CleanOptions(), [rule])
        self.assertEqual(cleaned, "abc")
        self.assertTrue(result.warnings[0].startswith("regex_error:bad"))

    def test_script_and_punctuation_modes_are_independent(self) -> None:
        options = CleanOptions(
            width_conversion_enabled=True,
            width_conversion="full_to_half",
            punctuation_mode_enabled=True,
            punctuation_mode="cjk",
        )
        cleaned, _result = clean_text("中文，ＡＢＣ。", options)
        self.assertEqual(cleaned, "中文，ABC。")

    def test_paragraph_and_glyph_choices_require_explicit_enable_flags(self) -> None:
        options = CleanOptions(
            unicode_normalization="NFKC",
            width_conversion="full_to_half",
            punctuation_mode="ascii",
            paragraph_indent_mode="strip",
            repair_hyphenated_linebreaks=False,
        )
        source = "　ＡＢＣ，\n  段落"
        cleaned, _result = clean_text(source, options)
        self.assertEqual(cleaned, source)

    def test_remove_emoji_preserves_surrounding_text(self) -> None:
        cleaned, result = clean_text("开始😀文本👍🏽结束", CleanOptions(remove_emoji=True))
        self.assertEqual(cleaned, "开始文本结束")
        self.assertIn("remove_emoji", result.changes)

    def test_remove_web_code_blocks_including_entity_encoded_markup(self) -> None:
        source = "正文\n<script>window.bad = true;</script>\n<style>.bad{display:none}</style>\n结尾"
        cleaned, result = clean_text(source, CleanOptions(remove_web_code_blocks=True))
        self.assertEqual(cleaned, "正文\n\n结尾")
        self.assertIn("remove_web_code_blocks", result.changes)

        encoded = "正文\n&lt;script&gt;alert(1)&lt;/script&gt;\n结尾"
        cleaned, _result = clean_text(
            encoded,
            CleanOptions(remove_web_code_blocks=True, decode_html_entities=True),
        )
        self.assertEqual(cleaned, "正文\n\n结尾")

    def test_remove_empty_lines_understands_html_placeholders(self) -> None:
        source = (
            "第一行\n"
            "&nbsp;\n"
            "<br>\n"
            "<p>&nbsp;</p>\n"
            "<div class=\"placeholder\"><div><br /></div></div>\n"
            "<!-- empty -->\n"
            "第二行"
        )
        cleaned, result = clean_text(source, CleanOptions(remove_empty_lines=True))
        self.assertEqual(cleaned, "第一行\n第二行")
        self.assertTrue(any(change.startswith("remove_empty_lines:") for change in result.changes))


if __name__ == "__main__":
    unittest.main()
