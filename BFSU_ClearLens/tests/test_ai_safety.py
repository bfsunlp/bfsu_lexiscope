from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from clearlens.ai_client import (
    AIClient,
    AIEditModel,
    AIProviderEditBatch,
    AIProviderEditModel,
    AISettings,
    RegexProposalModel,
)
from clearlens.llm_chunks import build_document_chunks
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
            AIEditModel(edit_id="C00001-E0001", chunk_id="C00001", source_hash="0" * 16, start_line=1, end_line=1, operation="whitespace", original_fragment="A  B", replacement_fragment="A B", reason="spacing", occurrence=1),
            AIEditModel(edit_id="C00001-E0002", chunk_id="C00001", source_hash="0" * 16, start_line=1, end_line=1, operation="typo", original_fragment="B", replacement_fragment="C", reason="rewrite", occurrence=1),
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

    def test_deepseek_strict_tool_request_accepts_json_content_compatibility(self) -> None:
        captured: dict[str, object] = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = SimpleNamespace(
                    content=(
                        '{"edits":[{"edit_id":"C00001-E0001","chunk_id":"C00001",'
                        '"source_hash":"0123456789abcdef","start_line":1,"end_line":1,'
                        '"operation":"whitespace","original_fragment":"A  B",'
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
        self.assertEqual(captured["client"], {
            "api_key": "test",
            "base_url": "https://api.deepseek.com",
            "timeout": 180,
            "max_retries": 2,
        })
        self.assertEqual(captured["tool_choice"]["function"]["name"], "submit_atomic_edits")
        self.assertTrue(captured["tools"][0]["function"]["strict"])
        item_schema = captured["tools"][0]["function"]["parameters"]["properties"]["edits"]["items"]
        self.assertNotIn("chunk_id", item_schema["properties"])
        self.assertNotIn("source_hash", item_schema["properties"])
        self.assertNotIn("edit_id", item_schema["properties"])
        self.assertNotIn("response_format", captured)

    def test_deepseek_strict_tool_call_arguments_are_parsed(self) -> None:
        content = (
            '{"edits":[{"edit_id":"C00001-E0001","chunk_id":"C00001",'
            '"source_hash":"0123456789abcdef","start_line":1,"end_line":1,'
            '"operation":"whitespace","original_fragment":"A  B",'
            '"replacement_fragment":"A B","occurrence":1,"reason":"spacing","confidence":0.9}]}'
        )

        class FakeCompletions:
            def create(self, **_kwargs):
                function = SimpleNamespace(name="submit_atomic_edits", arguments=content)
                message = SimpleNamespace(content=None, tool_calls=[SimpleNamespace(function=function)])
                return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls")])

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.chat = SimpleNamespace(completions=FakeCompletions())

        client = AIClient(AISettings(enabled=True, provider="deepseek", api_key="test"))
        edits, warnings = client._request_deepseek_edits(FakeOpenAI, "instructions", "document")
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "whitespace")

    def test_deepseek_actual_request_binds_missing_identity_from_chunk(self) -> None:
        chunk = build_document_chunks("line one\nA  B\n", max_chars=1000)[0]
        content = (
            '{"edits":[{"start_line":1,"end_line":1,"operation":"whitespace",'
            '"original_fragment":"A  B","replacement_fragment":"A B",'
            '"occurrence":1,"reason":"spacing","confidence":0.9}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content, chunk=chunk)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].edit_id, "C00001-E0001")
        self.assertEqual(edits[0].chunk_id, chunk.chunk_id)
        self.assertEqual(edits[0].source_hash, chunk.source_hash)

    def test_deepseek_only_infers_empty_replacement_for_explicit_deletion(self) -> None:
        chunk = build_document_chunks("https://example.com", max_chars=1000)[0]
        content = (
            '{"edits":['
            '{"operation":"delete","original_fragment":"https://example.com","reason":"url"},'
            '{"operation":"replace","original_fragment":"example","reason":"missing target"}'
            ']}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content, chunk=chunk)
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "delete")
        self.assertEqual(edits[0].replacement_fragment, "")
        self.assertIn("ai_provider_items_rejected:1", warnings)

    def test_openai_uses_minimal_edit_schema_and_binds_request_context(self) -> None:
        captured: dict[str, object] = {}
        parsed = AIProviderEditBatch(edits=[AIProviderEditModel(
            start_line=1,
            end_line=1,
            operation="case_conversion",
            original_fragment="NASA",
            replacement_fragment="Nasa",
            occurrence=1,
            reason="case",
            confidence=0.9,
        )])

        class FakeResponses:
            def parse(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(output_parsed=parsed)

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.responses = FakeResponses()

        chunk = build_document_chunks("NASA", max_chars=1000)[0]
        client = AIClient(AISettings(enabled=True, provider="openai", api_key="test"))
        edits, warnings = client._request_openai_edits(
            FakeOpenAI,
            "instructions",
            "prompt",
            chunk=chunk,
        )
        self.assertEqual(warnings, [])
        self.assertIs(captured["text_format"], AIProviderEditBatch)
        self.assertEqual(edits[0].source_hash, chunk.source_hash)
        self.assertEqual(edits[0].edit_id, "C00001-E0001")

    def test_deepseek_unsupported_strict_tool_falls_back_to_json_mode(self) -> None:
        calls: list[dict[str, object]] = []

        class UnsupportedToolError(Exception):
            status_code = 400

        class FakeCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                if "tools" in kwargs:
                    raise UnsupportedToolError("strict tools unavailable")
                message = SimpleNamespace(content='{"edits":[]}', tool_calls=None)
                return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.chat = SimpleNamespace(completions=FakeCompletions())

        client = AIClient(AISettings(enabled=True, provider="deepseek", api_key="test"))
        edits, warnings = client._request_deepseek_edits(FakeOpenAI, "instructions", "document")
        self.assertEqual((edits, warnings), ([], []))
        self.assertEqual(len(calls), 2)
        self.assertIn("tools", calls[0])
        self.assertEqual(calls[1]["response_format"], {"type": "json_object"})
        edits, warnings = client._request_deepseek_edits(FakeOpenAI, "instructions", "second document")
        self.assertEqual((edits, warnings), ([], []))
        self.assertEqual(len(calls), 3)
        self.assertNotIn("tools", calls[2])
        self.assertEqual(calls[2]["response_format"], {"type": "json_object"})

    def test_deepseek_replace_alias_is_canonicalized_without_losing_the_item(self) -> None:
        content = (
            '{"edits":[{"chunk_id":"C00001","source_hash":"0123456789abcdef",'
            '"line":7,"operation":"replace","original_fragment":"Its",'
            '"replacement_fragment":"It\\u0027s","occurrence":1,"reason":"apostrophe"}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].edit_id, "C00001-E0001")
        self.assertEqual((edits[0].start_line, edits[0].end_line), (7, 7))
        self.assertEqual(edits[0].operation, "punctuation")

    def test_deepseek_lexical_replace_gets_a_supported_review_category(self) -> None:
        content = (
            '{"edits":[{"edit_id":"C00001-E0001","chunk_id":"C00001",'
            '"source_hash":"0123456789abcdef","start_line":3,"end_line":3,'
            '"operation":"replace","original_fragment":"teh","replacement_fragment":"the",'
            '"reason":"spelling"}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(edits[0].operation, "replace")
        self.assertIsNone(self.client._validate_direct_edit("teh", self.client._to_suggestion(edits[0])))

    def test_deepseek_accepts_root_aliases_numeric_strings_and_operation_lists(self) -> None:
        content = (
            '{"result":{"changes":[{"chunk_id":"c00001","source_hash":"0123456789ABCDEF",'
            '"line_number":"4","operations":["capitalize","punctuation"],'
            '"original":"NASA.","replacement":"Nasa!","occurrence":"1",'
            '"reason":"coupled requested change","confidence":"92%"}]}}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "composite")
        self.assertEqual((edits[0].start_line, edits[0].end_line), (4, 4))
        self.assertEqual(edits[0].source_hash, "0123456789abcdef")
        self.assertAlmostEqual(edits[0].confidence, 0.92)

    def test_deepseek_expands_nested_operations_for_one_line(self) -> None:
        content = (
            '{"edits":[{"chunk_id":"C00001","source_hash":"0123456789abcdef",'
            '"line":2,"operations":['
            '{"action":"capitalize","original":"NASA","replacement":"Nasa","reason":"case"},'
            '{"action":"replace","original":"A  B","replacement":"A B","reason":"spacing"}'
            ']}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual([edit.operation for edit in edits], ["case_conversion", "whitespace"])
        self.assertEqual([edit.edit_id for edit in edits], ["C00001-E0001", "C00001-E0002"])
        self.assertTrue(all(edit.start_line == 2 and edit.end_line == 2 for edit in edits))

    def test_deepseek_parser_discards_only_bad_items_when_valid_items_remain(self) -> None:
        content = (
            '{"edits":['
            '{"chunk_id":"C00001","source_hash":"0123456789abcdef","line":1,'
            '"action":"replace","original":"A  B","replacement":"A B","reason":"spacing"},'
            '{"operation":"replace","original_fragment":"missing identity",'
            '"replacement_fragment":"x","reason":"bad"}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "whitespace")
        self.assertEqual(warnings, ["ai_provider_items_rejected:1"])
        self.assertFalse(self.client._is_fatal_warning(warnings[0]))

    def test_deepseek_parser_fails_closed_when_no_item_has_source_identity(self) -> None:
        content = '{"edits":[{"operation":"replace","original_fragment":"A","replacement_fragment":"B","reason":"bad"}]}'
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(edits, [])
        self.assertIn("ai_provider_items_rejected:1", warnings)
        self.assertIn("ai_response_no_valid_items:1", warnings)
        self.assertTrue(any(self.client._is_fatal_warning(warning) for warning in warnings))

    def test_deepseek_parser_accepts_json_code_fence(self) -> None:
        content = (
            '```json\n{"edits":[{"chunk_id":"C00001","source_hash":"0123456789abcdef",'
            '"line":1,"operation":"replace","original_fragment":"A","replacement_fragment":"B",'
            '"reason":"review"}]}\n```'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)

    def test_prompt_can_render_a_guarded_numbered_rule_set(self) -> None:
        instructions, prompt = self.client._build_prompt(
            "source text",
            review=False,
            custom_rules=["Remove repeated navigation lines.", "Normalize paragraph spacing."],
        )
        self.assertIn("lossless", instructions)
        self.assertIn("1. Remove repeated navigation lines.", prompt)
        self.assertIn("2. Normalize paragraph spacing.", prompt)
        self.assertEqual(prompt.count("<document>"), 1)

    def test_deepseek_accepts_camel_case_and_before_after_aliases(self) -> None:
        content = (
            '{"changes":[{"editId":"C00001-Ealpha","chunkId":"c00001",'
            '"sourceFingerprint":"0123456789ABCDEF","startLine":"2","endLine":"2",'
            '"op":"transform_case","before":"NASA","after":"Nasa",'
            '"occurrenceIndex":"1","explanation":"case","confidenceScore":"97%"}]}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "case_conversion")
        self.assertEqual(edits[0].chunk_id, "C00001")
        self.assertEqual(edits[0].source_hash, "0123456789abcdef")
        self.assertAlmostEqual(edits[0].confidence, 0.97)

    def test_deepseek_recursively_expands_nested_edit_groups(self) -> None:
        content = (
            '{"result":{"items":[{"chunk_id":"C00001","source_hash":"0123456789abcdef",'
            '"line":4,"changes":[{"changes":[{"op":"spacing","before":"A  B",'
            '"after":"A B","reason":"space","occurrence":1,"confidence":1}]}]}]}}'
        )
        edits, warnings = self.client._parse_deepseek_edit_batch(content)
        self.assertEqual(warnings, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].operation, "whitespace")
        self.assertEqual(edits[0].start_line, 4)
        self.assertEqual(edits[0].end_line, 4)

    def test_multiple_rules_execute_as_independent_stacked_passes(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test"))
        calls: list[tuple[str, list[str]]] = []

        def fake_request(text: str, review: bool, custom_rules=None, **_kwargs):
            calls.append((text, list(custom_rules or [])))
            if "大小写" in custom_rules[0]:
                return [AIEditModel(
                    edit_id="C00001-E0001", chunk_id="C00001", source_hash="0" * 16,
                    start_line=1, end_line=1, operation="case_conversion",
                    original_fragment="NASA", replacement_fragment="Nasa",
                    reason="case", occurrence=1,
                )], []
            return [AIEditModel(
                edit_id="C00001-E0001", chunk_id="C00001", source_hash="0" * 16,
                start_line=1, end_line=1, operation="whitespace",
                original_fragment="has  space", replacement_fragment="has space",
                reason="spacing", occurrence=1,
            )], []

        client._request_edits = fake_request  # type: ignore[method-assign]
        result = client.clean_with_rules(
            "NASA has  space",
            ["调整大小写", "合并重复空格"],
        )
        self.assertTrue(result.completed)
        self.assertEqual(result.text, "Nasa has space")
        self.assertEqual(calls, [
            ("NASA has  space", ["调整大小写"]),
            ("Nasa has  space", ["合并重复空格"]),
        ])
        self.assertEqual(len(result.applied), 2)

    def test_multirule_automatic_edit_is_transactional_when_later_rule_fails(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test"))
        calls = 0

        def fake_request(_text: str, review: bool, custom_rules=None, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return [AIEditModel(
                    edit_id="C00001-E0001", chunk_id="C00001", source_hash="0" * 16,
                    start_line=1, end_line=1, operation="case_conversion",
                    original_fragment="NASA", replacement_fragment="Nasa",
                    reason="case", occurrence=1,
                )], []
            return [], ["ai_response_truncated"]

        client._request_edits = fake_request  # type: ignore[method-assign]
        result = client.clean_with_rules("NASA", ["规则一", "规则二"])
        self.assertFalse(result.completed)
        self.assertEqual(result.text, "NASA")
        self.assertEqual(result.applied, [])
        self.assertIn("ai_response_truncated:rule=2", result.warnings)

    def test_multiple_review_rules_are_all_requested_and_deduplicated(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test"))
        calls: list[list[str]] = []

        def fake_request(_text: str, review: bool, custom_rules=None, **_kwargs):
            calls.append(list(custom_rules or []))
            return [AIEditModel(
                edit_id="C00001-E0001", chunk_id="C00001", source_hash="0" * 16,
                start_line=1, end_line=1, operation="case_conversion",
                original_fragment="NASA", replacement_fragment="Nasa",
                reason="case", occurrence=1,
            )], []

        client._request_edits = fake_request  # type: ignore[method-assign]
        suggestions, warnings = client.review_with_rules("NASA", ["规则一", "规则二"])
        self.assertEqual(calls, [["规则一"], ["规则二"]])
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(warnings, [])

    def test_case_conversion_and_explicit_quoted_replacement_are_safe_custom_edits(self) -> None:
        case = AISuggestion("case_conversion", "NASA", "Nasa", "requested")
        self.assertEqual(
            self.client._validate_direct_edit("NASA", case, custom_rules=["将全大写词改为首字母大写"]),
            (0, 4),
        )
        replacement = AISuggestion("replace", "foo", "bar", "requested")
        self.assertEqual(
            self.client._validate_direct_edit("foo", replacement, custom_rules=['将“foo”替换为“bar”']),
            (0, 3),
        )
        self.assertIsNone(
            self.client._validate_direct_edit("foo", replacement, custom_rules=["修改错误词"]),
        )

    def test_custom_rule_prompt_is_exclusive_instead_of_general_noise_review(self) -> None:
        instructions, prompt = self.client._build_prompt(
            "ADVERTISEMENT\nOKokolkhss\nNASA",
            review=True,
            custom_rules=["请将所有字母都大写的词转换成首字母大写的词。"],
        )
        self.assertIn("complete and exclusive task specification", instructions)
        self.assertIn("Do not perform general proofreading or cleanup", instructions)
        self.assertIn("every replacement_fragment must be non-empty", prompt)
        self.assertIn("all-uppercase-word conversion", prompt)
        self.assertNotIn("Suggest only clear residual text-noise corrections", prompt)

    def test_replacement_only_rule_rejects_deletion_suggestions(self) -> None:
        rules = ["请将所有字母都大写的词转换成首字母大写的词。"]
        edits = [
            AIEditModel(
                edit_id="C00001-E0001",
                chunk_id="C00001",
                source_hash="0" * 16,
                start_line=1,
                end_line=1,
                operation="delete_duplicate",
                original_fragment="ADVERTISEMENT",
                replacement_fragment="",
                reason="ad marker",
            ),
            AIEditModel(
                edit_id="C00001-E0002",
                chunk_id="C00001",
                source_hash="0" * 16,
                start_line=1,
                end_line=1,
                operation="other",
                original_fragment="ADVERTISEMENT",
                replacement_fragment="Advertisement",
                reason="apply capitalization rule",
            ),
        ]
        suggestions, warnings = self.client._review_result("ADVERTISEMENT", edits, [], custom_rules=rules)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].replacement_fragment, "Advertisement")
        self.assertIn("ai_rule_scope_rejected:1", warnings)

    def test_all_caps_rule_rejects_unrelated_replacement(self) -> None:
        rules = ["Convert all-uppercase words to initial-capital words."]
        valid = AISuggestion("other", "NASA TEST", "Nasa Test", "requested")
        invalid = AISuggestion("other", "NASA TEST", "Noise removed", "unrelated")
        self.assertTrue(self.client._validate_custom_rule_suggestion(valid, rules))
        self.assertFalse(self.client._validate_custom_rule_suggestion(invalid, rules))

    def test_llm_preflight_accepts_exact_edits_and_rejects_generative_tasks(self) -> None:
        self.assertEqual(
            AIClient.assess_task(["请将所有字母都大写的词转换成首字母大写的词。"]),
            [],
        )
        self.assertEqual(AIClient.assess_task(["请把全文翻译成英文。"]), ["ai_task_unsuitable:translation"])
        self.assertEqual(AIClient.assess_task(["请总结这篇文档。"]), ["ai_task_unsuitable:summarization"])
        self.assertEqual(AIClient.assess_task(["请润色并扩写全文。"]), ["ai_task_unsuitable:free_rewrite"])
        self.assertEqual(
            AIClient.assess_task(["每个网址单独生成一条建议，只删除网址本身。"]),
            [],
        )
        self.assertEqual(
            AIClient.assess_task(["请生成一篇新的介绍文章。"]),
            ["ai_task_unsuitable:content_generation"],
        )

    def test_llm_preflight_accepts_large_files_for_lossless_chunking(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test", max_chars_per_request=1000))
        self.assertEqual(client.preflight("short"), [])
        self.assertEqual(client.preflight("x" * 5000), [])
        self.assertGreater(client.estimate_chunk_count("x" * 5000), 1)

    def test_llm_preflight_rejects_unsafe_tiny_chunk_budget(self) -> None:
        client = AIClient(AISettings(enabled=True, api_key="test", max_chars_per_request=10))
        self.assertEqual(client.preflight("short"), ["ai_chunk_limit_too_small:10:1000"])

    def test_prompt_requires_atomic_line_indexed_edits_only(self) -> None:
        instructions, prompt = self.client._build_prompt("first\nsecond", review=True)
        self.assertIn("atomic", instructions)
        self.assertIn("start_line", prompt)
        self.assertIn("Return only lines that need a change", prompt)
        self.assertIn("never return the corrected document", prompt)

    def test_atomic_edit_schema_requires_source_identity_and_lines(self) -> None:
        with self.assertRaises(Exception):
            AIEditModel(
                operation="whitespace",
                original_fragment="A  B",
                replacement_fragment="A B",
                reason="spacing",
            )

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

    def test_provider_batch_accepts_edit_dense_responses_above_old_limit(self) -> None:
        item = AIProviderEditModel(
            start_line=1,
            end_line=1,
            operation="whitespace",
            original_fragment="A  B",
            replacement_fragment="A B",
            occurrence=1,
            reason="spacing",
            confidence=0.9,
        )
        batch = AIProviderEditBatch(edits=[item] * 501)
        self.assertEqual(len(batch.edits), 501)

    def test_provider_json_tolerates_wrapper_prose_but_not_missing_json(self) -> None:
        loaded = AIClient._load_provider_json('Result follows:\n{"edits":[]}\nDone.')
        self.assertEqual(loaded, {"edits": []})
        with self.assertRaises(Exception):
            AIClient._load_provider_json("no structured value")

    def test_timeout_errors_are_reported_distinctly(self) -> None:
        warning = AIClient._provider_exception_warning(TimeoutError("read timed out"))
        self.assertTrue(warning.startswith("ai_request_timeout:"))

    def test_incompatible_dense_response_retries_with_smaller_complete_chunks(self) -> None:
        client = AIClient(AISettings(
            enabled=True,
            api_key="test",
            max_chars_per_request=12000,
            adaptive_chunking=True,
        ))
        budgets: list[int] = []
        activity: list[dict[str, object]] = []

        def fake_once(_openai, _text, _review, _rules, budget, _cycle, _progress, _cancel, _activity):
            budgets.append(budget)
            if len(budgets) == 1:
                return [], ["ai_response_invalid_json:too_many_edits:chunk=C00001"]
            return [], []

        client._request_edits_once = fake_once  # type: ignore[method-assign]
        with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=object)}):
            edits, warnings = client._request_edits(
                "A  B",
                review=False,
                activity_callback=activity.append,
            )
        self.assertEqual(edits, [])
        self.assertEqual(budgets, [12000, 6000])
        self.assertIn("ai_adaptive_retry:1:6000", warnings)
        self.assertEqual(activity[-1]["state"], "adaptive_retry")


if __name__ == "__main__":
    unittest.main()
