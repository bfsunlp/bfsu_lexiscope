from __future__ import annotations

import unittest
from types import SimpleNamespace

from clearlens.ai_client import AIClient, AIEditModel, AISettings, RegexProposalModel
from clearlens.models import AISuggestion


class AISafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = AIClient(AISettings())

    def test_whitespace_edit_must_preserve_non_whitespace_sequence(self) -> None:
        text = "A  B"
        valid = AISuggestion("whitespace", "A  B", "A B", "spacing")
        invalid = AISuggestion("whitespace", "A  B", "A C", "rewrite")
        self.assertIsNotNone(self.client._validate_direct_edit(text, valid))
        self.assertIsNone(self.client._validate_direct_edit(text, invalid))

    def test_punctuation_edit_cannot_change_letters_or_numbers(self) -> None:
        text = "版本1.2"
        valid = AISuggestion("punctuation", "版本1.2", "版本1。2", "punctuation")
        invalid = AISuggestion("punctuation", "版本1.2", "版本1。3", "number changed")
        self.assertIsNotNone(self.client._validate_direct_edit(text, valid))
        self.assertIsNone(self.client._validate_direct_edit(text, invalid))

    def test_duplicate_deletion_requires_an_exact_duplicate(self) -> None:
        valid = AISuggestion("delete_duplicate", "same\n", "", "duplicate", occurrence=2)
        invalid = AISuggestion("delete_duplicate", "unique", "", "delete", occurrence=1)
        self.assertIsNotNone(self.client._validate_direct_edit("same\nsame\n", valid))
        self.assertIsNone(self.client._validate_direct_edit("unique", invalid))

    def test_symbol_noise_deletion_rejects_lexical_content(self) -> None:
        valid = AISuggestion("delete_symbol_noise", "####", "", "noise")
        invalid = AISuggestion("delete_symbol_noise", "A###", "", "noise")
        self.assertIsNotNone(self.client._validate_direct_edit("text####", valid))
        self.assertIsNone(self.client._validate_direct_edit("textA###", invalid))

    def test_apply_suggestion_uses_exact_occurrence(self) -> None:
        suggestion = AISuggestion("typo", "word", "term", "review", occurrence=2)
        result, applied = AIClient.apply_suggestion("word and word", suggestion)
        self.assertTrue(applied)
        self.assertEqual(result, "word and term")

    def test_direct_clean_applies_only_guarded_edits(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test"))
        edits = [
            AIEditModel(operation="whitespace", original_fragment="A  B", replacement_fragment="A B", reason="spacing", occurrence=1),
            AIEditModel(operation="typo", original_fragment="B", replacement_fragment="C", reason="rewrite", occurrence=1),
        ]
        client._request_edits = lambda _text, review: (edits, [])  # type: ignore[method-assign]
        result = client.direct_clean("A  B")
        self.assertTrue(result.completed)
        self.assertEqual(result.text, "A B")
        self.assertEqual(len(result.applied), 1)
        self.assertEqual(len(result.rejected), 1)

    def test_disabled_ai_does_not_report_success(self) -> None:
        result = AIClient(AISettings(enabled=False)).direct_clean("text")
        self.assertFalse(result.completed)
        self.assertEqual(result.text, "text")

    def test_deepseek_json_response_is_parsed_as_exact_edits(self) -> None:
        captured: dict[str, object] = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = SimpleNamespace(
                    content=(
                        '{"edits":[{"operation":"whitespace","original_fragment":"A  B",'
                        '"replacement_fragment":"A B","occurrence":1,"reason":"spacing","confidence":0.99}]}'
                    )
                )
                return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])

        class FakeOpenAI:
            def __init__(self, **kwargs):
                captured["client"] = kwargs
                self.chat = SimpleNamespace(completions=FakeCompletions())

        client = AIClient(AISettings(enabled=True, provider="deepseek", api_key="test", model="deepseek-v4-flash"))
        edits, warnings = client._request_deepseek_edits(FakeOpenAI, "instructions", "document")
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].original_fragment, "A  B")
        self.assertEqual(captured["client"], {"api_key": "test", "base_url": "https://api.deepseek.com"})
        self.assertEqual(captured["response_format"], {"type": "json_object"})

    def test_multiple_natural_language_rules_share_one_guarded_request(self) -> None:
        instructions, prompt = self.client._build_prompt(
            "source text",
            review=False,
            custom_rules=["Remove repeated navigation lines.", "Normalize paragraph spacing."],
        )
        self.assertIn("lossless", instructions)
        self.assertIn("1. Remove repeated navigation lines.", prompt)
        self.assertIn("2. Normalize paragraph spacing.", prompt)
        self.assertEqual(prompt.count("<document>"), 1)

    def test_regex_proposal_is_compiled_before_human_review(self) -> None:
        valid = RegexProposalModel(name="Pages", pattern=r"(?m)^Page \d+$", replacement="", flags="m")
        invalid = RegexProposalModel(name="Bad", pattern="[", replacement="", flags="m")
        self.assertIsNone(AIClient._validate_regex_proposal(valid, "Page 12\nText"))
        self.assertIsNotNone(AIClient._validate_regex_proposal(invalid, "text"))

    def test_regex_proposal_rejects_invalid_replacement_without_a_match(self) -> None:
        proposal = RegexProposalModel(
            name="Invalid group",
            pattern=r"heading",
            replacement=r"\2",
            flags="m",
        )

        self.assertIsNotNone(AIClient._validate_regex_proposal(proposal, "unrelated sample"))


if __name__ == "__main__":
    unittest.main()
