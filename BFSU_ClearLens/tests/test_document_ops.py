from __future__ import annotations

import unittest

from clearlens.document_ops import merge_texts


class DocumentOperationTests(unittest.TestCase):
    def test_merge_preserves_order_without_metadata(self) -> None:
        self.assertEqual(merge_texts(["first\n", "second"]), "first\n\n\nsecond")

if __name__ == "__main__":
    unittest.main()
