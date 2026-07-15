from __future__ import annotations

import unittest
from pathlib import Path

from clearlens.history import OperationHistory
from clearlens.models import TextFile


class HistoryTests(unittest.TestCase):
    def test_batch_undo_and_redo_restore_multiple_files(self) -> None:
        files = [
            TextFile(Path("one.txt"), "one"),
            TextFile(Path("two.txt"), "two"),
        ]
        history = OperationHistory(limit=50)
        before = history.capture(files, [0, 1])
        files[0].set_working_text("ONE", "rule_cleaned")
        files[1].set_working_text("TWO", "ai_cleaned")
        after = history.capture(files, [0, 1])
        self.assertTrue(history.record("batch", before, after))

        entry, undo_states = history.undo() or self.fail("missing undo")
        self.assertEqual(entry.label, "batch")
        for item in files:
            undo_states[next(key for key in undo_states if key.endswith(item.path.name))].restore(item)
        self.assertEqual([item.cleaned_text for item in files], ["", ""])

        _entry, redo_states = history.redo() or self.fail("missing redo")
        for item in files:
            redo_states[next(key for key in redo_states if key.endswith(item.path.name))].restore(item)
        self.assertEqual([item.cleaned_text for item in files], ["ONE", "TWO"])
        self.assertEqual([item.active_text for item in files], ["ONE", "TWO"])

    def test_history_retains_only_latest_fifty_operations(self) -> None:
        item = TextFile(Path("one.txt"), "one")
        history = OperationHistory(limit=50)
        for number in range(55):
            before = history.capture([item], [0])
            item.set_working_text(str(number), "manual")
            after = history.capture([item], [0])
            history.record(str(number), before, after)
        labels = []
        while True:
            result = history.undo()
            if result is None:
                break
            labels.append(result[0].label)
        self.assertEqual(len(labels), 50)
        self.assertEqual(labels[-1], "5")

    def test_history_restores_complete_working_and_save_state(self) -> None:
        item = TextFile(Path("one.txt"), "source")
        history = OperationHistory()
        before = history.capture([item], [0])
        item.set_working_text("llm result", "ai_cleaned")
        item.prepare_transcode("utf-16")
        item.mark_saved(Path("out/one_converted.txt"))
        after = history.capture([item], [0])
        self.assertTrue(history.record("pipeline", before, after))

        _entry, undo_states = history.undo() or self.fail("missing undo")
        next(iter(undo_states.values())).restore(item)
        self.assertEqual(item.active_text, "source")
        self.assertIsNone(item.target_encoding)
        self.assertIsNone(item.output_path)
        self.assertFalse(item.dirty)

        _entry, redo_states = history.redo() or self.fail("missing redo")
        next(iter(redo_states.values())).restore(item)
        self.assertEqual(item.active_text, "llm result")
        self.assertEqual(item.target_encoding, "utf-16")
        self.assertEqual(item.output_path, Path("out/one_converted.txt"))
        self.assertFalse(item.dirty)


if __name__ == "__main__":
    unittest.main()
