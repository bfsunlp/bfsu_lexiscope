from __future__ import annotations

import unittest

from clearlens.ui_text import (
    build_line_diff_rows,
    excerpt_around_line,
    first_line_difference,
    format_line_numbers,
    fragment_line_numbers,
)


class TextNavigationTests(unittest.TestCase):
    def test_multiline_fragment_maps_to_every_affected_line(self) -> None:
        text = "first\nauthor: Liu\nsource: News\nbody"
        lines = fragment_line_numbers(text, "author: Liu\nsource: News", 1)
        self.assertEqual(lines, [2, 3])
        self.assertEqual(format_line_numbers(lines), "2, 3")

    def test_occurrence_selects_the_correct_repeated_fragment(self) -> None:
        text = "header\nsource\nbody\nsource\nend"
        self.assertEqual(fragment_line_numbers(text, "source", 2), [4])

    def test_line_diff_rows_preserve_original_and_current_locations(self) -> None:
        rows = build_line_diff_rows("one\ntwo\nthree", "one\nTWO\nthree\nfour")
        self.assertEqual(rows[0].change, "replace")
        self.assertEqual((rows[0].original_line, rows[0].current_line), (2, 2))
        self.assertEqual((rows[0].original_text, rows[0].current_text), ("two", "TWO"))
        self.assertEqual(rows[1].change, "insert")
        self.assertEqual(rows[1].current_line, 4)

    def test_full_document_preview_can_focus_on_a_change_beyond_the_display_limit(self) -> None:
        before = "".join(f"line {index}\n" for index in range(3000)) + "TARGET\n"
        after = before.replace("TARGET", "DONE")
        location = first_line_difference(before, after)
        self.assertIsNotNone(location)
        old_line, new_line, old_column, new_column = location or (0, 0, 0, 0)
        original = excerpt_around_line(before, old_line, 12000, old_column)
        current = excerpt_around_line(after, new_line, 12000, new_column)
        self.assertGreater(original.first_line, 1)
        self.assertIn("TARGET", original.text)
        self.assertIn("DONE", current.text)

    def test_diff_rows_apply_real_document_line_offsets(self) -> None:
        rows = build_line_diff_rows(
            "same\nold\n",
            "same\nnew\n",
            original_start_line=101,
            current_start_line=201,
        )
        self.assertEqual(rows[0].original_line, 102)
        self.assertEqual(rows[0].current_line, 202)


if __name__ == "__main__":
    unittest.main()
