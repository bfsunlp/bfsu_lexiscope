from __future__ import annotations

import unittest
import sys
from types import SimpleNamespace
from unittest.mock import patch

from clearlens.ai_client import AIClient, AIEditModel, AISettings
from clearlens.llm_chunks import (
    build_document_chunks,
    build_line_spans,
    locate_chunk_fragment,
)


class LLMChunkTests(unittest.TestCase):
    def test_chunk_cores_cover_document_once_and_requests_stay_bounded(self) -> None:
        text = "".join(f"line {number:04d} value\n" for number in range(600))
        chunks = build_document_chunks(text, max_chars=1000, overlap_lines=2)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].core_start_offset, 0)
        self.assertEqual(chunks[-1].core_end_offset, len(text))
        for previous, current in zip(chunks, chunks[1:]):
            self.assertEqual(previous.core_end_offset, current.core_start_offset)
        self.assertTrue(all(chunk.character_count <= 1000 for chunk in chunks))
        reconstructed = "".join(text[chunk.core_start_offset:chunk.core_end_offset] for chunk in chunks)
        self.assertEqual(reconstructed, text)

    def test_one_extreme_html_line_is_segmented_without_loss(self) -> None:
        text = "<html>" + ("A" * 5000) + "</html>"
        chunks = build_document_chunks(text, max_chars=1000, overlap_lines=2)
        self.assertGreater(len(chunks), 5)
        self.assertTrue(all(chunk.core_first_line == 1 for chunk in chunks))
        self.assertTrue(all(chunk.character_count <= 1000 for chunk in chunks))
        for previous, current in zip(chunks, chunks[1:]):
            self.assertEqual(previous.core_end_column, current.core_start_column)
        reconstructed = "".join(text[chunk.core_start_offset:chunk.core_end_offset] for chunk in chunks)
        self.assertEqual(reconstructed, text)

    def test_exact_line_claim_selects_the_intended_duplicate(self) -> None:
        text = "same\nkeep\nsame\n"
        spans = build_line_spans(text)
        chunk = build_document_chunks(text, max_chars=1000)[0]
        self.assertEqual(locate_chunk_fragment(text, spans, chunk, "same", 3, 3, 1), (10, 14))
        self.assertIsNone(locate_chunk_fragment(text, spans, chunk, "same", 2, 2, 1))

    def test_resolved_model_edit_gets_stable_global_location(self) -> None:
        text = "same\nkeep\nsame\n"
        spans = build_line_spans(text)
        chunk = build_document_chunks(text, max_chars=1000)[0]
        edit = AIEditModel(
            edit_id="C00001-E0001",
            chunk_id="C00001",
            source_hash=chunk.source_hash,
            start_line=3,
            end_line=3,
            operation="other",
            original_fragment="same",
            replacement_fragment="Same",
            occurrence=1,
            reason="requested capitalization",
        )
        resolved = AIClient._resolve_chunk_edit(text, spans, chunk, edit, 1)
        self.assertEqual(resolved, (10, 14))
        self.assertEqual(edit.occurrence, 2)
        suggestion = AIClient._to_suggestion(edit)
        self.assertEqual((suggestion.start_line, suggestion.end_line), (3, 3))
        self.assertEqual((suggestion.source_start, suggestion.source_end), (10, 14))

    def test_wrong_provider_metadata_is_rebound_when_fragment_is_unique(self) -> None:
        text = "one\ntwo\n"
        spans = build_line_spans(text)
        chunk = build_document_chunks(text, max_chars=1000)[0]
        edit = AIEditModel(
            edit_id="C00001-E0001",
            chunk_id=chunk.chunk_id,
            source_hash="0" * 16,
            start_line=2,
            end_line=2,
            operation="other",
            original_fragment="two",
            replacement_fragment="Two",
            occurrence=1,
            reason="test",
        )
        resolution = AIClient._resolve_chunk_edit_detailed(text, spans, chunk, edit, 1)
        self.assertEqual(resolution.span, (4, 7))
        self.assertIn("source_hash", resolution.repaired_fields)
        self.assertEqual(edit.source_hash, chunk.source_hash)
        self.assertEqual((edit.start_line, edit.end_line, edit.occurrence), (2, 2, 1))

    def test_recovery_rejects_duplicate_fragment_when_line_hint_is_ambiguous(self) -> None:
        text = "same\nsame\n"
        spans = build_line_spans(text)
        chunk = build_document_chunks(text, max_chars=1000)[0]
        edit = AIEditModel(
            edit_id="C99999-Ebad",
            chunk_id="C99999",
            source_hash="0" * 16,
            start_line=99,
            end_line=99,
            operation="case_conversion",
            original_fragment="same",
            replacement_fragment="Same",
            occurrence=1,
            reason="test",
        )
        resolution = AIClient._resolve_chunk_edit_detailed(text, spans, chunk, edit, 1)
        self.assertIsNone(resolution.span)
        self.assertEqual(resolution.reason, "ambiguous")

    def test_large_document_is_scanned_chunk_by_chunk_and_applied_by_exact_span(self) -> None:
        lines = [f"line {number:04d}\n" for number in range(1, 501)]
        lines[249] = "BAD  VALUE\n"
        text = "".join(lines)
        client = AIClient(AISettings(enabled=True, api_key="test", max_chars_per_request=1000))
        prompts: list[str] = []

        def fake_request(_openai, _instructions: str, prompt: str, chunk=None):
            prompts.append(prompt)
            if "BAD  VALUE" not in prompt:
                return [], []
            return [AIEditModel(
                edit_id="C99999-Ebad",
                chunk_id="C99999",
                source_hash="0" * 16,
                start_line=250,
                end_line=250,
                operation="whitespace",
                original_fragment="BAD  VALUE",
                replacement_fragment="BAD VALUE",
                occurrence=1,
                reason="double space",
                confidence=0.99,
            )], ["ai_provider_items_rejected:1"]

        client._request_openai_edits = fake_request  # type: ignore[method-assign]
        with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=object)}):
            result = client.direct_clean(text)
        self.assertTrue(result.completed)
        self.assertIn("BAD VALUE\n", result.text)
        self.assertNotIn("BAD  VALUE", result.text)
        self.assertTrue(any(warning.startswith("ai_provider_items_rejected:1") for warning in result.warnings))
        self.assertTrue(any(warning.startswith("ai_chunk_locations_repaired:1") for warning in result.warnings))
        self.assertEqual(len(prompts), client.estimate_chunk_count(text))

    def test_client_estimates_multiple_requests_for_large_text(self) -> None:
        client = AIClient(AISettings(max_chars_per_request=1000, chunk_overlap_lines=2))
        text = "\n".join("content" for _ in range(1000))
        self.assertGreater(client.estimate_chunk_count(text), 1)

    def test_extreme_line_prompt_exposes_editable_column_bounds(self) -> None:
        text = "A" * 5000
        chunk = build_document_chunks(text, max_chars=1000)[1]
        client = AIClient(AISettings())
        _instructions, prompt = client._build_prompt(
            chunk.text,
            review=True,
            chunk=chunk,
            chunk_count=len(build_document_chunks(text, max_chars=1000)),
        )
        self.assertIn(f"editable_start=1:{chunk.core_start_column}", prompt)
        self.assertIn(f"editable_end_exclusive=1:{chunk.core_end_column}", prompt)

    def test_one_failed_chunk_discards_all_partial_automatic_edits(self) -> None:
        text = "BAD  VALUE\n" + "".join(f"line {number:04d}\n" for number in range(1000))
        client = AIClient(AISettings(enabled=True, api_key="test", max_chars_per_request=1000))
        calls = 0

        def fake_request(_openai, _instructions: str, prompt: str, chunk=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                return [AIEditModel(
                    edit_id="C99999-Ebad",
                    chunk_id="C99999",
                    source_hash="0" * 16,
                    start_line=1,
                    end_line=1,
                    operation="whitespace",
                    original_fragment="BAD  VALUE",
                    replacement_fragment="BAD VALUE",
                    occurrence=1,
                    reason="double space",
                )], []
            return [], ["ai_response_truncated"]

        client._request_openai_edits = fake_request  # type: ignore[method-assign]
        with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=object)}):
            result = client.direct_clean(text)
        self.assertFalse(result.completed)
        self.assertEqual(result.text, text)
        self.assertIn("ai_response_truncated:chunk=C00002", result.warnings)



if __name__ == "__main__":
    unittest.main()
