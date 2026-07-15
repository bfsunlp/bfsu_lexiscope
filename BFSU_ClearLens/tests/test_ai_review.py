from __future__ import annotations

import unittest

from clearlens.models import AISuggestion
from clearlens.ui_ai_review import SuggestionReviewSession


class SuggestionReviewSessionTests(unittest.TestCase):
    def test_individual_accept_and_reject(self) -> None:
        suggestions = [
            AISuggestion("whitespace", "A  B", "A B", "spacing"),
            AISuggestion("typo", "wrong", "right", "correction"),
        ]
        session = SuggestionReviewSession("A  B and wrong", suggestions)

        self.assertTrue(session.accept(0))
        self.assertTrue(session.reject(1))
        self.assertEqual(session.text, "A B and wrong")
        self.assertEqual(session.counts(), {"pending": 0, "applied": 1, "rejected": 1, "stale": 0})

    def test_accept_all_skips_stale_fragments(self) -> None:
        suggestions = [
            AISuggestion("typo", "alpha", "ALPHA", "case"),
            AISuggestion("typo", "missing", "present", "not in source"),
            AISuggestion("punctuation", "beta!", "beta！", "punctuation"),
        ]
        session = SuggestionReviewSession("alpha beta!", suggestions)

        self.assertEqual(session.accept_all(), 2)
        self.assertEqual(session.text, "ALPHA beta！")
        self.assertEqual(session.applied_count, 2)
        self.assertEqual(session.counts(), {"pending": 0, "applied": 2, "rejected": 0, "stale": 1})

    def test_reject_all_never_changes_text(self) -> None:
        suggestions = [
            AISuggestion("typo", "one", "ONE", "case"),
            AISuggestion("typo", "two", "TWO", "case"),
        ]
        session = SuggestionReviewSession("one two", suggestions)

        self.assertEqual(session.reject_all(), 2)
        self.assertEqual(session.text, "one two")
        self.assertEqual(session.applied_count, 0)


if __name__ == "__main__":
    unittest.main()
