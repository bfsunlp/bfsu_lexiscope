from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from clearlens.app import ClearLensApp
from clearlens.models import TextFile


class ProcessingStateTests(unittest.TestCase):
    def test_processing_stacks_on_latest_working_text(self) -> None:
        item = TextFile(Path("sample.txt"), "imported source")
        item.set_working_text("LLM result", "ai_cleaned")
        rule_input = item.active_text
        item.set_working_text(rule_input + " + rule result", "rule_cleaned")

        self.assertEqual(item.active_text, "LLM result + rule result")
        self.assertTrue(item.dirty)

        item.status = "failed_status"
        self.assertEqual(item.active_text, "LLM result + rule result")

    def test_transcode_is_pending_state_until_explicit_save(self) -> None:
        item = TextFile(Path("sample.txt"), "source")
        item.set_working_text("processed", "ai_cleaned")
        item.prepare_transcode("utf-16")

        self.assertEqual(item.active_text, "processed")
        self.assertEqual(item.target_encoding, "utf-16")
        self.assertEqual(item.output_suffix_key, "converted_suffix")
        self.assertTrue(item.dirty)
        self.assertIsNone(item.output_path)

        item.mark_saved(Path("results/sample_converted.txt"))
        self.assertFalse(item.dirty)
        self.assertEqual(item.output_path, Path("results/sample_converted.txt"))

    def test_reset_is_the_only_direct_return_to_imported_text(self) -> None:
        item = TextFile(Path("sample.txt"), "source")
        item.set_working_text("processed", "rule_cleaned")
        item.prepare_transcode("gb18030")
        item.reset_working_state()

        self.assertEqual(item.active_text, "source")
        self.assertIsNone(item.target_encoding)
        self.assertTrue(item.dirty)

    def test_processing_entry_points_use_current_text_and_do_not_write(self) -> None:
        input_methods = (
            ClearLensApp._run_rule_indices,
            ClearLensApp._run_ai_indices,
            ClearLensApp._run_llm_rule_indices,
            ClearLensApp.run_llm_rules_review_current,
            ClearLensApp.run_ai_review_current,
            ClearLensApp._transcode_indices,
        )
        processing_methods = input_methods + (ClearLensApp._open_review_dialog,)
        forbidden = ("write_output_file", "write_text_path", "_save_item_threadsafe")
        for method in input_methods:
            self.assertIn("active_text", inspect.getsource(method), method.__name__)
        for method in processing_methods:
            source = inspect.getsource(method)
            for call in forbidden:
                self.assertNotIn(call, source, f"{method.__name__} writes through {call}")


if __name__ == "__main__":
    unittest.main()
