from __future__ import annotations

import unittest

from clearlens.statistics import calculate_statistics


class StatisticsTests(unittest.TestCase):
    def test_counts_files_characters_lines_and_paragraphs(self) -> None:
        stats = calculate_statistics(["中文 A1.\n\nSecond", "hello"])
        self.assertEqual(stats.files, 2)
        self.assertEqual(stats.total_chars, len("中文 A1.\n\nSecond") + len("hello"))
        self.assertEqual(stats.cjk_chars, 2)
        self.assertEqual(stats.digits, 1)
        self.assertEqual(stats.latin_words, 3)
        self.assertEqual(stats.lines, 4)
        self.assertEqual(stats.paragraphs, 3)


if __name__ == "__main__":
    unittest.main()
