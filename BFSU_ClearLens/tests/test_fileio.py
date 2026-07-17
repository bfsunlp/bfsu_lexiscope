from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clearlens.fileio import DETECTION_SAMPLE_BYTES, read_text_file, write_output_file, write_text_path


class FileIOTests(unittest.TestCase):
    def test_encoding_detection_and_utf8_sig_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            nested = source_root / "chapter"
            nested.mkdir(parents=True)
            source = nested / "sample.txt"
            source.write_bytes("中文文本\n第二行".encode("gb18030"))
            item = read_text_file(source, source_root=source_root)
            self.assertEqual(item.original_text, "中文文本\n第二行")

            target = write_output_file(
                item.original_text,
                item,
                root / "output",
                encoding="utf-8-sig",
                newline_style="crlf",
                preserve_folders=True,
                overwrite=True,
            )
            self.assertEqual(target.relative_to(root / "output"), Path("chapter/sample_cleaned.txt"))
            raw = target.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            self.assertIn(b"\r\n", raw)

    def test_utf32_conversion_and_source_protection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("中文", encoding="utf-8")
            item = read_text_file(source)
            target = write_output_file(item.original_text, item, root / "output", encoding="utf-32", overwrite=True)
            self.assertEqual(target.read_text(encoding="utf-32"), "中文")
            with self.assertRaises(ValueError):
                write_text_path("changed", source, protected_paths=[source])
            with self.assertRaises(ValueError):
                write_output_file(
                    "changed",
                    item,
                    root,
                    suffix="",
                    preserve_folders=False,
                    overwrite=True,
                )
            self.assertEqual(source.read_text(encoding="utf-8"), "中文")

    def test_large_non_utf8_file_is_detected_from_a_bounded_sample(self) -> None:
        text = "中文文本第二行。\n" * 70000
        raw = text.encode("gb18030")
        self.assertGreater(len(raw), DETECTION_SAMPLE_BYTES)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "large.html"
            source.write_bytes(raw)
            item = read_text_file(source)
        self.assertEqual(item.original_text, text)
        self.assertIn(item.encoding, {"gb18030", "gbk"})


if __name__ == "__main__":
    unittest.main()
