from __future__ import annotations

import json
import os
import re
import threading
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field, PrivateAttr

from .llm_chunks import (
    DocumentChunk,
    LineSpan,
    build_document_chunks,
    build_line_spans,
    line_number_at_offset,
    locate_chunk_fragment,
    locate_chunk_fragment_candidates,
    occurrence_for_span,
)
from .models import AIResult, AISuggestion


class AIEditModel(BaseModel):
    edit_id: str = Field(pattern=r"^C\d{5}-E[A-Za-z0-9_.-]{1,50}$")
    chunk_id: str = Field(pattern=r"^C\d{5}$")
    source_hash: str = Field(pattern=r"^[0-9a-f]{16}$")
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    operation: Literal[
        "whitespace",
        "paragraph",
        "punctuation",
        "delete_duplicate",
        "delete_symbol_noise",
        "case_conversion",
        "replace",
        "insert",
        "delete",
        "reorder",
        "composite",
        "typo",
        "noise",
        "other",
    ]
    original_fragment: str
    replacement_fragment: str
    occurrence: int = Field(default=1, ge=1)
    reason: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    _resolved_start: int | None = PrivateAttr(default=None)
    _resolved_end: int | None = PrivateAttr(default=None)


class AIEditBatch(BaseModel):
    edits: list[AIEditModel] = Field(max_length=5000)


class AIProviderEditModel(BaseModel):
    """Minimal provider contract; source identity is bound by the application.

    A provider should identify an exact source fragment and the requested
    replacement.  Chunk ids, fingerprints, stable edit ids, and authoritative
    line numbers are application-owned data and are deliberately absent from
    this schema.
    """

    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    operation: Literal[
        "whitespace",
        "paragraph",
        "punctuation",
        "delete_duplicate",
        "delete_symbol_noise",
        "case_conversion",
        "replace",
        "insert",
        "delete",
        "reorder",
        "composite",
        "typo",
        "noise",
        "other",
    ]
    original_fragment: str
    replacement_fragment: str
    occurrence: int = Field(default=1, ge=1)
    reason: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AIProviderEditBatch(BaseModel):
    edits: list[AIProviderEditModel] = Field(max_length=5000)


@dataclass(frozen=True)
class EditResolution:
    span: tuple[int, int] | None
    reason: str = ""
    repaired_fields: tuple[str, ...] = ()


class RegexProposalModel(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    pattern: str = Field(min_length=1, max_length=4000)
    replacement: str = Field(default="", max_length=4000)
    flags: str = Field(default="m", pattern=r"^[ims]*$")
    description: str = Field(default="", max_length=500)


@dataclass
class AISettings:
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-5.4-mini"
    api_key: str = ""
    reasoning_effort: str = "low"
    max_chars_per_request: int = 24000
    max_output_tokens: int = 16000
    chunk_overlap_lines: int = 2
    request_timeout_seconds: int = 180
    retry_attempts: int = 2
    adaptive_chunking: bool = True
    confirm_before_send: bool = True
    remember_api_key: bool = False

    def resolved_api_key(self) -> str:
        environment_name = "DEEPSEEK_API_KEY" if self.provider == "deepseek" else "OPENAI_API_KEY"
        return self.api_key or os.getenv(environment_name, "")


class AIClient:
    """LLM-assisted editing with deterministic guards around every auto-applied edit."""

    DIRECT_OPERATIONS = {
        "whitespace",
        "paragraph",
        "punctuation",
        "delete_duplicate",
        "delete_symbol_noise",
    }
    UNSUITABLE_TASK_PATTERNS = (
        ("translation", re.compile(r"(?:翻译成|翻譯成|译成|譯成|译为|譯為|\btranslate\b)", re.IGNORECASE)),
        ("summarization", re.compile(r"(?:总结|總結|概括|摘要(?:这|這|本文|文档|文檔)|\bsummari[sz]e\b)", re.IGNORECASE)),
        ("free_rewrite", re.compile(r"(?:改写|改寫|重写|重寫|润色|潤色|扩写|擴寫|续写|續寫|\b(?:rewrite|paraphrase|polish|expand)\b)", re.IGNORECASE)),
        ("content_generation", re.compile(
            r"(?:生成.{0,8}(?:文章|内容|內容|正文|文本|段落|故事|报告|報告|标题|標題|文案)|"
            r"创作|創作|撰写|撰寫|编写.{0,5}(?:文章|内容|內容)|"
            r"\b(?:generate\s+(?:(?:an?|the)\s+)?(?:article|content|text|paragraph|story|report|summary|title)|compose)\b)",
            re.IGNORECASE,
        )),
        ("external_knowledge", re.compile(r"(?:查询网络|查詢網路|搜索网络|搜尋網路|联网|聯網|事实核查|事實核查|核实事实|核實事實|补充事实|補充事實|\bweb\s+search\b|\bbrowse\b|\bfact.?check)", re.IGNORECASE)),
        ("unsupported_input", re.compile(r"(?:执行\s*ocr|執行\s*ocr|图片文字识别|圖片文字識別|识别图片|識別圖片|提取元(?:信息|数据|資訊|資料)|抓取网页|抓取網頁|爬取|\bextract\s+metadata\b)", re.IGNORECASE)),
    )

    def __init__(self, settings: AISettings) -> None:
        self.settings = settings
        self._deepseek_strict_tools_supported: bool | None = None

    def direct_clean(
        self,
        text: str,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
        activity_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> AIResult:
        request_options: dict[str, object] = {}
        if progress_callback is not None:
            request_options["progress_callback"] = progress_callback
        if cancel_event is not None:
            request_options["cancel_event"] = cancel_event
        if activity_callback is not None:
            request_options["activity_callback"] = activity_callback
        edits, warnings = self._request_edits(text, review=False, **request_options)
        return self._direct_result(text, edits, warnings)

    def clean_with_rules(
        self,
        text: str,
        rules: list[str],
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
        activity_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> AIResult:
        rendered_rules = [rule.strip() for rule in rules if rule.strip()]
        preflight_warnings = self.preflight(text, custom_rules=rendered_rules)
        if preflight_warnings:
            return AIResult(text=text, completed=False, warnings=preflight_warnings)

        # One user action may contain many rules, but each rule gets its own
        # pass. This prevents a provider from stopping after the first list
        # item and, crucially, keeps each rule's local scope guard independent.
        original = text
        working = text
        all_suggestions: list[AISuggestion] = []
        all_applied: list[AISuggestion] = []
        all_rejected: list[AISuggestion] = []
        all_warnings: list[str] = []
        planned_total = max(1, sum(
            self.estimate_chunk_count(working, custom_rules=[rule])
            for rule in rendered_rules
        ))
        completed_chunks = 0

        for rule_number, rule in enumerate(rendered_rules, 1):
            if cancel_event is not None and cancel_event.is_set():
                return AIResult(text=original, completed=False, warnings=["ai_cancelled"])

            pass_chunks = self.estimate_chunk_count(working, custom_rules=[rule])

            def rule_progress(current: int, _total: int, base: int = completed_chunks) -> None:
                if progress_callback is not None:
                    progress_callback(min(planned_total, base + current), planned_total)

            edits, warnings = self._request_edits(
                working,
                review=False,
                custom_rules=[rule],
                progress_callback=rule_progress,
                cancel_event=cancel_event,
                activity_callback=activity_callback,
            )
            result = self._direct_result(working, edits, warnings, custom_rules=[rule])
            all_suggestions.extend(result.suggestions)
            all_applied.extend(result.applied)
            all_rejected.extend(result.rejected)
            all_warnings.extend(self._tag_rule_warning(warning, rule_number) for warning in result.warnings)
            if not result.completed:
                # Automatic mode is transactional at file level. A failed
                # later rule must not leave a silently partial document.
                return AIResult(
                    text=original,
                    completed=False,
                    suggestions=all_suggestions,
                    applied=[],
                    rejected=all_rejected,
                    warnings=all_warnings,
                )
            working = result.text
            completed_chunks += pass_chunks

        if progress_callback is not None:
            progress_callback(planned_total, planned_total)
        return AIResult(
            text=working,
            completed=True,
            suggestions=all_suggestions,
            applied=all_applied,
            rejected=all_rejected,
            warnings=all_warnings,
        )

    def _direct_result(
        self,
        text: str,
        edits: list[AIEditModel],
        warnings: list[str],
        custom_rules: list[str] | None = None,
    ) -> AIResult:
        suggestions = [self._to_suggestion(edit) for edit in edits]
        if any(self._is_fatal_warning(warning) for warning in warnings):
            return AIResult(text=text, completed=False, suggestions=suggestions, warnings=warnings)

        accepted: list[tuple[int, int, AISuggestion]] = []
        rejected: list[AISuggestion] = []
        scope_rejected = 0
        for suggestion in suggestions:
            if custom_rules and not self._validate_custom_rule_suggestion(suggestion, custom_rules):
                suggestion.status = "rejected_scope"
                rejected.append(suggestion)
                scope_rejected += 1
                continue
            span = self._validate_direct_edit(text, suggestion, custom_rules=custom_rules)
            if span is None:
                suggestion.status = "rejected"
                rejected.append(suggestion)
                continue
            start, end = span
            if any(not (end <= old_start or start >= old_end) for old_start, old_end, _ in accepted):
                suggestion.status = "rejected_overlap"
                rejected.append(suggestion)
                continue
            accepted.append((start, end, suggestion))

        cleaned = text
        applied: list[AISuggestion] = []
        for start, end, suggestion in sorted(accepted, key=lambda item: item[0], reverse=True):
            cleaned = cleaned[:start] + suggestion.replacement_fragment + cleaned[end:]
            suggestion.status = "applied"
            applied.append(suggestion)
        applied.reverse()

        result_warnings = list(warnings)
        if rejected:
            result_warnings.append(f"ai_edits_rejected:{len(rejected)}")
        if scope_rejected:
            result_warnings.append(f"ai_rule_scope_rejected:{scope_rejected}")
        return AIResult(
            text=cleaned,
            completed=True,
            suggestions=suggestions,
            applied=applied,
            rejected=rejected,
            warnings=result_warnings,
        )

    def review(
        self,
        text: str,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
        activity_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> tuple[list[AISuggestion], list[str]]:
        edits, warnings = self._request_edits(
            text,
            review=True,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
            activity_callback=activity_callback,
        )
        return self._review_result(text, edits, warnings)

    def review_with_rules(
        self,
        text: str,
        rules: list[str],
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
        activity_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> tuple[list[AISuggestion], list[str]]:
        rendered_rules = [rule.strip() for rule in rules if rule.strip()]
        preflight_warnings = self.preflight(text, custom_rules=rendered_rules)
        if preflight_warnings:
            return [], preflight_warnings

        suggestions: list[AISuggestion] = []
        warnings: list[str] = []
        seen: set[tuple[int | None, int | None, str, str]] = set()
        rule_chunk_counts = [
            self.estimate_chunk_count(text, review=True, custom_rules=[rule])
            for rule in rendered_rules
        ]
        planned_total = max(1, sum(rule_chunk_counts))
        completed_chunks = 0
        for rule_number, rule in enumerate(rendered_rules, 1):
            if cancel_event is not None and cancel_event.is_set():
                return suggestions, warnings + ["ai_cancelled"]
            chunks_for_rule = rule_chunk_counts[rule_number - 1]

            def rule_progress(current: int, _total: int, base: int = completed_chunks) -> None:
                if progress_callback is not None:
                    progress_callback(min(planned_total, base + current), planned_total)

            edits, rule_warnings = self._request_edits(
                text,
                review=True,
                custom_rules=[rule],
                progress_callback=rule_progress,
                cancel_event=cancel_event,
                activity_callback=activity_callback,
            )
            rule_suggestions, rule_warnings = self._review_result(
                text,
                edits,
                rule_warnings,
                custom_rules=[rule],
            )
            for suggestion in rule_suggestions:
                key = (
                    suggestion.source_start,
                    suggestion.source_end,
                    suggestion.original_fragment,
                    suggestion.replacement_fragment,
                )
                if key not in seen:
                    seen.add(key)
                    suggestions.append(suggestion)
            warnings.extend(self._tag_rule_warning(warning, rule_number) for warning in rule_warnings)
            completed_chunks += chunks_for_rule

        if progress_callback is not None:
            progress_callback(planned_total, planned_total)
        suggestions.sort(key=lambda item: (item.source_start if item.source_start is not None else 10**18, item.edit_id))
        return suggestions, warnings

    @staticmethod
    def _tag_rule_warning(warning: str, rule_number: int) -> str:
        return f"{warning}:rule={rule_number}"

    def _review_result(
        self,
        text: str,
        edits: list[AIEditModel],
        warnings: list[str],
        custom_rules: list[str] | None = None,
    ) -> tuple[list[AISuggestion], list[str]]:
        suggestions: list[AISuggestion] = []
        rejected = 0
        scope_rejected = 0
        for edit in edits:
            suggestion = self._to_suggestion(edit)
            if custom_rules and not self._validate_custom_rule_suggestion(suggestion, custom_rules):
                rejected += 1
                scope_rejected += 1
                continue
            if self._locate_suggestion(text, suggestion) is None:
                rejected += 1
                continue
            if suggestion.original_fragment == suggestion.replacement_fragment:
                rejected += 1
                continue
            suggestions.append(suggestion)
        if rejected:
            warnings.append(f"ai_suggestions_rejected:{rejected}")
        if scope_rejected:
            warnings.append(f"ai_rule_scope_rejected:{scope_rejected}")
        return suggestions, warnings

    @staticmethod
    def apply_suggestion(text: str, suggestion: AISuggestion) -> tuple[str, bool]:
        span = AIClient._locate_suggestion(text, suggestion)
        if span is None:
            return text, False
        start, end = span
        return text[:start] + suggestion.replacement_fragment + text[end:], True

    def _request_edits(
        self,
        text: str,
        review: bool,
        custom_rules: list[str] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
        activity_callback: Callable[[dict[str, object]], None] | None = None,
    ) -> tuple[list[AIEditModel], list[str]]:
        warnings = self.preflight(text, custom_rules=custom_rules)
        if warnings:
            return [], warnings

        try:
            from openai import OpenAI
        except Exception as exc:
            return [], [f"openai_unavailable:{exc}"]

        initial_budget = self._effective_chunk_budget(review=review, custom_rules=custom_rules)
        budgets = [initial_budget]
        if self.settings.adaptive_chunking:
            while len(budgets) < 3 and budgets[-1] > 3000:
                smaller = max(3000, budgets[-1] // 2)
                if smaller == budgets[-1]:
                    break
                budgets.append(smaller)

        retry_warnings: list[str] = []
        for level, budget in enumerate(budgets):
            if cancel_event is not None and cancel_event.is_set():
                return [], ["ai_cancelled"]
            edits, attempt_warnings = self._request_edits_once(
                OpenAI,
                text,
                review,
                custom_rules,
                budget,
                level + 1,
                progress_callback,
                cancel_event,
                activity_callback,
            )
            fatal = [warning for warning in attempt_warnings if self._is_fatal_warning(warning)]
            can_retry = (
                bool(fatal)
                and level + 1 < len(budgets)
                and self._should_retry_with_smaller_chunks(fatal)
                and not (cancel_event is not None and cancel_event.is_set())
            )
            if not can_retry:
                return edits, retry_warnings + attempt_warnings
            next_budget = budgets[level + 1]
            retry_warnings.append(f"ai_adaptive_retry:{level + 1}:{next_budget}")
            self._emit_activity(activity_callback, {
                "state": "adaptive_retry",
                "level": level + 1,
                "budget": next_budget,
            })
        return [], retry_warnings + ["ai_response_invalid_json:adaptive_retry_exhausted"]

    def _request_edits_once(
        self,
        openai_class,
        text: str,
        review: bool,
        custom_rules: list[str] | None,
        chunk_budget: int,
        request_cycle: int,
        progress_callback: Callable[[int, int], None] | None,
        cancel_event: threading.Event | None,
        activity_callback: Callable[[dict[str, object]], None] | None,
    ) -> tuple[list[AIEditModel], list[str]]:
        chunks = build_document_chunks(
            text,
            chunk_budget,
            overlap_lines=self.settings.chunk_overlap_lines,
        )
        spans = build_line_spans(text)
        edits: list[AIEditModel] = []
        warnings: list[str] = []
        rejected: Counter[str] = Counter()
        repaired = 0
        seen: set[tuple[int, int, str, str]] = set()
        total_chunks = len(chunks)
        for position, chunk in enumerate(chunks, 1):
            if cancel_event is not None and cancel_event.is_set():
                return [], ["ai_cancelled"]
            instructions, prompt = self._build_prompt(
                chunk.text,
                review,
                custom_rules,
                chunk=chunk,
                chunk_count=total_chunks,
            )
            self._emit_activity(activity_callback, {
                "state": "waiting",
                "current": position,
                "total": total_chunks,
                "attempt": request_cycle,
                "timeout": max(10, int(self.settings.request_timeout_seconds)),
                "retries": max(0, int(self.settings.retry_attempts)),
            })
            if self.settings.provider == "deepseek":
                chunk_edits, chunk_warnings = self._request_deepseek_edits(
                    openai_class,
                    instructions,
                    prompt,
                    chunk=chunk,
                )
            elif self.settings.provider == "openai":
                chunk_edits, chunk_warnings = self._request_openai_edits(
                    openai_class,
                    instructions,
                    prompt,
                    chunk=chunk,
                )
            else:
                return [], [f"llm_provider_unsupported:{self.settings.provider}"]
            self._emit_activity(activity_callback, {
                "state": "received",
                "current": position,
                "total": total_chunks,
            })
            if chunk_warnings:
                warnings.extend(f"{warning}:chunk={chunk.chunk_id}" for warning in chunk_warnings)
                if any(self._is_fatal_warning(warning) for warning in chunk_warnings):
                    return [], warnings
            for edit_position, edit in enumerate(chunk_edits, 1):
                edit.operation = self._canonical_operation(
                    edit.operation,
                    edit.original_fragment,
                    edit.replacement_fragment,
                )
                resolution = self._resolve_chunk_edit_detailed(text, spans, chunk, edit, edit_position)
                if resolution.span is None:
                    rejected[resolution.reason or "invalid"] += 1
                    continue
                if resolution.repaired_fields:
                    repaired += 1
                resolved = resolution.span
                key = (resolved[0], resolved[1], edit.replacement_fragment, edit.operation)
                if key in seen:
                    rejected["duplicate"] += 1
                    continue
                seen.add(key)
                edits.append(edit)
            if progress_callback is not None:
                progress_callback(position, total_chunks)
        if repaired:
            warnings.append(f"ai_chunk_locations_repaired:{repaired}")
        warning_names = {
            "fragment_not_found": "ai_chunk_fragments_not_found",
            "ambiguous": "ai_chunk_fragments_ambiguous",
            "overlap": "ai_chunk_overlap_edits_rejected",
            "duplicate": "ai_chunk_duplicate_edits_rejected",
            "invalid": "ai_chunk_edits_rejected",
        }
        for reason, count in sorted(rejected.items()):
            warnings.append(f"{warning_names.get(reason, 'ai_chunk_edits_rejected')}:{count}")
        return edits, warnings

    def _effective_chunk_budget(self, review: bool, custom_rules: list[str] | None = None) -> int:
        configured = max(1000, int(self.settings.max_chars_per_request))
        if not self.settings.adaptive_chunking:
            return configured
        # Edit-heavy natural-language rules can legitimately produce hundreds
        # of atomic items.  Smaller initial chunks make complete structured
        # responses much more reliable without omitting any source text.
        if custom_rules:
            return min(configured, 12000)
        if review:
            return min(configured, 18000)
        return min(configured, 24000)

    @staticmethod
    def _should_retry_with_smaller_chunks(warnings: list[str]) -> bool:
        retryable_prefixes = (
            "ai_response_truncated",
            "ai_response_empty_or_refused",
            "ai_response_invalid_json:invalid_json",
            "ai_response_invalid_json:missing_edits_array",
            "ai_response_invalid_json:too_many_edits",
            "ai_response_invalid_json:schema_validation",
            "ai_response_invalid_json:adaptive_retry_exhausted",
            "ai_response_no_valid_items:",
        )
        return any(warning.split(":chunk=", 1)[0].startswith(retryable_prefixes) for warning in warnings)

    @staticmethod
    def _emit_activity(
        callback: Callable[[dict[str, object]], None] | None,
        payload: dict[str, object],
    ) -> None:
        if callback is None:
            return
        try:
            callback(payload)
        except Exception:
            pass

    def estimate_chunk_count(
        self,
        text: str,
        review: bool = False,
        custom_rules: list[str] | None = None,
    ) -> int:
        return len(
            build_document_chunks(
                text,
                self._effective_chunk_budget(review=review, custom_rules=custom_rules),
                overlap_lines=self.settings.chunk_overlap_lines,
            )
        )

    @staticmethod
    def _is_fatal_warning(warning: str) -> bool:
        return not warning.startswith((
            "ai_chunk_edits_rejected:",
            "ai_chunk_locations_repaired:",
            "ai_chunk_fragments_not_found:",
            "ai_chunk_fragments_ambiguous:",
            "ai_chunk_overlap_edits_rejected:",
            "ai_chunk_duplicate_edits_rejected:",
            "ai_edits_rejected:",
            "ai_rule_scope_rejected:",
            "ai_suggestions_rejected:",
            "ai_provider_items_rejected:",
            "ai_adaptive_retry:",
        ))

    @staticmethod
    def _resolve_chunk_edit(
        text: str,
        spans: list[LineSpan],
        chunk: DocumentChunk,
        edit: AIEditModel,
        edit_position: int,
    ) -> tuple[int, int] | None:
        return AIClient._resolve_chunk_edit_detailed(
            text,
            spans,
            chunk,
            edit,
            edit_position,
        ).span

    @staticmethod
    def _resolve_chunk_edit_detailed(
        text: str,
        spans: list[LineSpan],
        chunk: DocumentChunk,
        edit: AIEditModel,
        edit_position: int,
    ) -> EditResolution:
        """Bind one provider edit to exact application-owned source metadata.

        Provider ids, hashes, line numbers, and occurrence values are hints,
        not trust anchors.  The response is already associated with exactly
        one request chunk.  ClearLens therefore recomputes those fields from
        an exact source-fragment match.  A unique exact match can be repaired;
        zero matches or unresolved duplicate matches remain fail-closed.
        """

        fragment = edit.original_fragment
        if not fragment:
            return EditResolution(None, "fragment_not_found")

        span = locate_chunk_fragment(
            text,
            spans,
            chunk,
            fragment,
            edit.start_line,
            edit.end_line,
            edit.occurrence,
        )
        if span is None:
            candidates = locate_chunk_fragment_candidates(text, chunk, fragment)
            if not candidates:
                visible_match = text.find(fragment, chunk.start_offset, chunk.end_offset)
                reason = "overlap" if visible_match >= 0 else "fragment_not_found"
                return EditResolution(None, reason)
            if len(candidates) == 1:
                span = candidates[0]
            else:
                # First try the provider's global line hints, ignoring a bad
                # occurrence value. Then try line numbers local to the visible
                # <document> block, a common compatible-provider convention.
                line_pairs = [(edit.start_line, edit.end_line)]
                local_pair = (
                    chunk.first_line + edit.start_line - 1,
                    chunk.first_line + edit.end_line - 1,
                )
                if local_pair != line_pairs[0]:
                    line_pairs.append(local_pair)
                for claimed_start, claimed_end in line_pairs:
                    matching = [
                        candidate
                        for candidate in candidates
                        if line_number_at_offset(spans, candidate[0]) == claimed_start
                        and line_number_at_offset(spans, max(candidate[0], candidate[1] - 1)) == claimed_end
                    ]
                    if len(matching) == 1:
                        span = matching[0]
                        break
                if span is None:
                    return EditResolution(None, "ambiguous")

        global_occurrence = occurrence_for_span(text, edit.original_fragment, span[0])
        if global_occurrence is None:
            return EditResolution(None, "invalid")

        actual_start_line = line_number_at_offset(spans, span[0])
        actual_end_line = line_number_at_offset(spans, max(span[0], span[1] - 1))
        expected_edit_id = f"{chunk.chunk_id}-E{edit_position:04d}"
        repaired_fields = tuple(
            name
            for name, old, new in (
                ("edit_id", edit.edit_id, expected_edit_id),
                ("chunk_id", edit.chunk_id, chunk.chunk_id),
                ("source_hash", edit.source_hash, chunk.source_hash),
                ("start_line", edit.start_line, actual_start_line),
                ("end_line", edit.end_line, actual_end_line),
                ("occurrence", edit.occurrence, global_occurrence),
            )
            if old != new
        )
        edit.edit_id = expected_edit_id
        edit.chunk_id = chunk.chunk_id
        edit.source_hash = chunk.source_hash
        edit.start_line = actual_start_line
        edit.end_line = actual_end_line
        edit.occurrence = global_occurrence
        edit._resolved_start, edit._resolved_end = span
        return EditResolution(span, repaired_fields=repaired_fields)

    def _request_openai_edits(
        self,
        openai_class,
        instructions: str,
        prompt: str,
        chunk: DocumentChunk | None = None,
    ) -> tuple[list[AIEditModel], list[str]]:
        client = openai_class(
            api_key=self.settings.resolved_api_key(),
            timeout=max(10, int(self.settings.request_timeout_seconds)),
            max_retries=max(0, int(self.settings.retry_attempts)),
        )
        request = {
            "model": self.settings.model,
            "instructions": instructions,
            "input": prompt,
            "text_format": AIProviderEditBatch,
            "max_output_tokens": self.settings.max_output_tokens,
            "store": False,
        }
        if self.settings.model.startswith(("gpt-5", "o")) and self.settings.reasoning_effort in {"none", "low", "medium", "high"}:
            request["reasoning"] = {"effort": self.settings.reasoning_effort}
        try:
            response = client.responses.parse(**request)
            parsed = response.output_parsed
        except TypeError:
            request.pop("reasoning", None)
            try:
                response = client.responses.parse(**request)
                parsed = response.output_parsed
            except Exception as exc:
                return [], [self._provider_exception_warning(exc)]
        except Exception as exc:
            return [], [self._provider_exception_warning(exc)]

        status = str(getattr(response, "status", "") or "").lower()
        incomplete = getattr(response, "incomplete_details", None)
        incomplete_reason = str(getattr(incomplete, "reason", "") or "").lower()
        if status == "incomplete" or incomplete_reason in {"max_output_tokens", "length"}:
            return [], ["ai_response_truncated"]
        if parsed is None:
            return [], ["ai_response_empty_or_refused"]
        if chunk is None:
            return [], ["ai_response_invalid_json:missing_request_context"]
        return [
            self._provider_edit_to_internal(edit, chunk, position)
            for position, edit in enumerate(parsed.edits, 1)
        ], []

    @staticmethod
    def _provider_exception_warning(exc: Exception) -> str:
        rendered = str(exc)
        lowered = rendered.lower()
        if any(term in lowered for term in ("timed out", "timeout", "read timeout", "connect timeout")):
            return f"ai_request_timeout:{rendered}"
        if "too many" in lowered or "max_length" in lowered or "too_long" in lowered:
            return "ai_response_invalid_json:too_many_edits"
        if any(term in lowered for term in ("max_output_tokens", "finish_reason=length", "truncated", "incomplete")):
            return "ai_response_truncated"
        if any(term in lowered for term in ("validation error", "structured output", "output_parsed", "schema")):
            return f"ai_response_invalid_json:schema_validation:{rendered}"
        return f"ai_request_failed:{rendered}"

    @staticmethod
    def _provider_edit_to_internal(
        edit: AIProviderEditModel,
        chunk: DocumentChunk,
        position: int,
    ) -> AIEditModel:
        return AIEditModel(
            edit_id=f"{chunk.chunk_id}-E{position:04d}",
            chunk_id=chunk.chunk_id,
            source_hash=chunk.source_hash,
            start_line=edit.start_line,
            end_line=edit.end_line,
            operation=edit.operation,
            original_fragment=edit.original_fragment,
            replacement_fragment=edit.replacement_fragment,
            occurrence=edit.occurrence,
            reason=edit.reason,
            confidence=edit.confidence,
        )

    def generate_regex_rule(
        self,
        requirement: str,
        sample_text: str = "",
    ) -> tuple[RegexProposalModel | None, list[str]]:
        if not self.settings.enabled:
            return None, ["ai_disabled"]
        if not self.settings.resolved_api_key():
            return None, ["api_key_missing"]
        requirement = requirement.strip()
        if not requirement:
            return None, ["regex_requirement_empty"]
        request_chars = len(requirement) + len(sample_text)
        if request_chars > self.settings.max_chars_per_request:
            return None, [f"ai_text_too_long:{request_chars}:{self.settings.max_chars_per_request}"]
        try:
            from openai import OpenAI
        except Exception as exc:
            return None, [f"openai_unavailable:{exc}"]

        instructions = (
            "You design conservative Python regular-expression rules for corpus text organization. "
            "Return exactly one structured rule. Use Python re syntax, no surrounding slash delimiters and no Markdown. "
            "The replacement must use Python re.sub replacement syntax. Use only i, m, and s flags. "
            "Prefer narrow patterns that avoid consuming meaningful text. Do not invent sample content."
        )
        prompt = (
            f"Natural-language requirement:\n{requirement}\n\n"
            "Create a concise name, regex pattern, replacement, flags, and description. "
            "The user will inspect and edit the proposal before saving it."
        )
        if sample_text:
            prompt += f"\n\n<sample_document>\n{sample_text}\n</sample_document>"

        if self.settings.provider == "deepseek":
            proposal, warnings = self._request_deepseek_regex(OpenAI, instructions, prompt)
        elif self.settings.provider == "openai":
            proposal, warnings = self._request_openai_regex(OpenAI, instructions, prompt)
        else:
            return None, [f"llm_provider_unsupported:{self.settings.provider}"]
        if proposal is None or warnings:
            return proposal, warnings
        validation_error = self._validate_regex_proposal(proposal, sample_text)
        if validation_error:
            return None, [f"regex_proposal_invalid:{validation_error}"]
        return proposal, []

    def _request_openai_regex(self, openai_class, instructions: str, prompt: str) -> tuple[RegexProposalModel | None, list[str]]:
        client = openai_class(
            api_key=self.settings.resolved_api_key(),
            timeout=max(10, int(self.settings.request_timeout_seconds)),
            max_retries=max(0, int(self.settings.retry_attempts)),
        )
        request = {
            "model": self.settings.model,
            "instructions": instructions,
            "input": prompt,
            "text_format": RegexProposalModel,
            "max_output_tokens": min(self.settings.max_output_tokens, 4000),
            "store": False,
        }
        if self.settings.model.startswith(("gpt-5", "o")) and self.settings.reasoning_effort in {"none", "low", "medium", "high"}:
            request["reasoning"] = {"effort": self.settings.reasoning_effort}
        try:
            response = client.responses.parse(**request)
        except TypeError:
            request.pop("reasoning", None)
            try:
                response = client.responses.parse(**request)
            except Exception as exc:
                return None, [self._provider_exception_warning(exc)]
        except Exception as exc:
            return None, [self._provider_exception_warning(exc)]
        status = str(getattr(response, "status", "") or "").lower()
        incomplete = getattr(response, "incomplete_details", None)
        incomplete_reason = str(getattr(incomplete, "reason", "") or "").lower()
        if status == "incomplete" or incomplete_reason in {"max_output_tokens", "length"}:
            return None, ["ai_response_truncated"]
        parsed = response.output_parsed
        if parsed is None:
            return None, ["ai_response_empty_or_refused"]
        return parsed, []

    def _request_deepseek_regex(self, openai_class, instructions: str, prompt: str) -> tuple[RegexProposalModel | None, list[str]]:
        client = openai_class(
            api_key=self.settings.resolved_api_key(),
            base_url="https://api.deepseek.com",
            timeout=max(10, int(self.settings.request_timeout_seconds)),
            max_retries=max(0, int(self.settings.retry_attempts)),
        )
        json_instruction = (
            "Return valid json only with this exact object shape: "
            '{"name":"rule name","pattern":"python regex","replacement":"python replacement",'
            '"flags":"ims subset","description":"what it changes"}.'
        )
        request = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": f"{instructions}\n\n{json_instruction}"},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": min(self.settings.max_output_tokens, 4000),
            "temperature": 0,
            "extra_body": {"thinking": {"type": "disabled"}},
        }
        try:
            response = client.chat.completions.create(**request)
        except TypeError:
            request.pop("extra_body", None)
            try:
                response = client.chat.completions.create(**request)
            except Exception as exc:
                return None, [self._provider_exception_warning(exc)]
        except Exception as exc:
            return None, [self._provider_exception_warning(exc)]
        if not response.choices:
            return None, ["ai_response_empty_or_refused"]
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            return None, ["ai_response_truncated"]
        content = getattr(choice.message, "content", None)
        if not isinstance(content, str) or not content.strip():
            return None, ["ai_response_empty_or_refused"]
        try:
            return RegexProposalModel.model_validate(self._load_provider_json(content)), []
        except Exception as exc:
            return None, [f"ai_response_invalid_json:{exc}"]

    @staticmethod
    def _validate_regex_proposal(proposal: RegexProposalModel, sample_text: str) -> str | None:
        flags = 0
        for char in proposal.flags:
            flags |= {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}[char]
        try:
            compiled = re.compile(proposal.pattern, flags)
            compiled.sub(proposal.replacement, sample_text, count=1)
        except (re.error, IndexError) as exc:
            return str(exc)
        return None

    def _request_deepseek_edits(
        self,
        openai_class,
        instructions: str,
        prompt: str,
        chunk: DocumentChunk | None = None,
    ) -> tuple[list[AIEditModel], list[str]]:
        client = openai_class(
            api_key=self.settings.resolved_api_key(),
            base_url="https://api.deepseek.com",
            timeout=max(10, int(self.settings.request_timeout_seconds)),
            max_retries=max(0, int(self.settings.retry_attempts)),
        )
        json_instruction = (
            "Return valid json only, matching this object shape: "
            '{"edits":[{"start_line":1,"end_line":1,"operation":"whitespace",'
            '"original_fragment":"exact source fragment","replacement_fragment":"replacement",'
            '"occurrence":1,"reason":"brief reason","confidence":0.9}]}. '
            "The application binds chunk identity and recomputes authoritative locations; do not add chunk ids, hashes, or edit ids. "
            'When there is no safe edit, return exactly {"edits":[]}.'
        )
        messages = [
            {"role": "system", "content": f"{instructions}\n\n{json_instruction}"},
            {"role": "user", "content": prompt},
        ]
        request = {
            "model": self.settings.model,
            "messages": messages,
            "tools": [{
                "type": "function",
                "function": {
                    "name": "submit_atomic_edits",
                    "description": "Submit only exact, source-indexed atomic text edits.",
                    "strict": True,
                    "parameters": self._deepseek_edit_tool_schema(),
                },
            }],
            "tool_choice": {
                "type": "function",
                "function": {"name": "submit_atomic_edits"},
            },
            "max_tokens": self.settings.max_output_tokens,
            "temperature": 0,
            "extra_body": {"thinking": {"type": "disabled"}},
        }
        response = None
        error: Exception | None = None
        if self._deepseek_strict_tools_supported is not False:
            response, error = self._call_deepseek_completion(client.chat.completions, request)
            if error is None:
                self._deepseek_strict_tools_supported = True
            elif self._deepseek_can_fallback_to_json(error):
                self._deepseek_strict_tools_supported = False
            else:
                return [], [self._provider_exception_warning(error)]
        if self._deepseek_strict_tools_supported is False:
            fallback_request = {
                "model": self.settings.model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "max_tokens": self.settings.max_output_tokens,
                "temperature": 0,
                "extra_body": {"thinking": {"type": "disabled"}},
            }
            response, error = self._call_deepseek_completion(client.chat.completions, fallback_request)
            if error is not None:
                return [], [self._provider_exception_warning(error)]

        if response is None or not response.choices:
            return [], ["ai_response_empty_or_refused"]
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            return [], ["ai_response_truncated"]
        tool_calls = getattr(choice.message, "tool_calls", None)
        if tool_calls:
            for tool_call in tool_calls:
                function = getattr(tool_call, "function", None)
                if getattr(function, "name", None) != "submit_atomic_edits":
                    continue
                arguments = getattr(function, "arguments", None)
                if isinstance(arguments, str) and arguments.strip():
                    return self._parse_deepseek_edit_batch(arguments, chunk=chunk)
        content = getattr(choice.message, "content", None)
        if not isinstance(content, str) or not content.strip():
            return [], ["ai_response_empty_or_refused"]
        return self._parse_deepseek_edit_batch(content, chunk=chunk)

    @staticmethod
    def _call_deepseek_completion(completions, request: dict[str, Any]) -> tuple[Any | None, Exception | None]:
        try:
            return completions.create(**request), None
        except TypeError:
            compatible = dict(request)
            compatible.pop("extra_body", None)
            try:
                return completions.create(**compatible), None
            except Exception as exc:
                return None, exc
        except Exception as exc:
            return None, exc

    @staticmethod
    def _deepseek_can_fallback_to_json(error: Exception) -> bool:
        return isinstance(error, TypeError) or getattr(error, "status_code", None) in {400, 404, 422}

    @staticmethod
    def _deepseek_edit_tool_schema() -> dict[str, Any]:
        operations = [
            "whitespace", "paragraph", "punctuation", "delete_duplicate",
            "delete_symbol_noise", "case_conversion", "replace", "insert",
            "delete", "reorder", "composite", "typo", "noise", "other",
        ]
        item_properties: dict[str, Any] = {
            "start_line": {"type": "integer", "minimum": 1},
            "end_line": {"type": "integer", "minimum": 1},
            "operation": {"type": "string", "enum": operations},
            "original_fragment": {"type": "string"},
            "replacement_fragment": {"type": "string"},
            "occurrence": {"type": "integer", "minimum": 1},
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        }
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "edits": {
                    "type": "array",
                    "maxItems": 5000,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": item_properties,
                        "required": list(item_properties),
                    },
                },
            },
            "required": ["edits"],
        }

    @staticmethod
    def _load_provider_json(content: str) -> Any:
        rendered = content.strip().lstrip("\ufeff")
        if rendered.startswith("```"):
            lines = rendered.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                rendered = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(rendered)
        except (json.JSONDecodeError, TypeError):
            # Some compatible endpoints prepend a sentence or append a note
            # despite JSON mode.  Accept one complete JSON value embedded in
            # that wrapper, but never repair a genuinely truncated value.
            decoder = json.JSONDecoder()
            starts = [index for index, char in enumerate(rendered) if char in "{["]
            for start in starts:
                try:
                    payload, _end = decoder.raw_decode(rendered[start:])
                    return payload
                except (json.JSONDecodeError, TypeError):
                    continue
            raise ValueError("invalid_json")

    @classmethod
    def _parse_deepseek_edit_batch(
        cls,
        content: str,
        chunk: DocumentChunk | None = None,
    ) -> tuple[list[AIEditModel], list[str]]:
        """Parse DeepSeek JSON without letting one provider enum alias drop a batch.

        DeepSeek-compatible models sometimes emit editing verbs such as
        ``replace`` even when the requested schema enumerates semantic edit
        categories. The adapter canonicalizes presentation-level aliases,
        then validates every item independently. Source identity, hashes,
        line ranges, exact fragments, and later local guards remain strict.
        """

        try:
            payload = cls._load_provider_json(content)
        except (ValueError, json.JSONDecodeError, TypeError):
            return [], ["ai_response_invalid_json:invalid_json"]
        if isinstance(payload, list):
            raw_edits = payload
        elif isinstance(payload, dict):
            raw_edits = None
            for key in ("edits", "suggestions", "changes", "operations", "items"):
                if isinstance(payload.get(key), list):
                    raw_edits = payload[key]
                    break
            if raw_edits is None and isinstance(payload.get("result"), dict):
                result = payload["result"]
                for key in ("edits", "suggestions", "changes", "operations", "items"):
                    if isinstance(result.get(key), list):
                        raw_edits = result[key]
                        break
            if raw_edits is None:
                return [], ["ai_response_invalid_json:missing_edits_array"]
        else:
            return [], ["ai_response_invalid_json:missing_edits_array"]
        raw_edits = cls._flatten_provider_edits(raw_edits)
        if len(raw_edits) > 5000:
            return [], ["ai_response_invalid_json:too_many_edits"]
        if not raw_edits:
            return [], []

        valid: list[AIEditModel] = []
        rejected = 0
        for position, raw in enumerate(raw_edits, 1):
            if not isinstance(raw, dict):
                rejected += 1
                continue
            normalized = cls._normalize_deepseek_edit_payload(raw, position, chunk=chunk)
            try:
                valid.append(AIEditModel.model_validate(normalized))
            except Exception:
                rejected += 1

        warnings: list[str] = []
        if rejected:
            warnings.append(f"ai_provider_items_rejected:{rejected}")
        if not valid:
            warnings.append(f"ai_response_no_valid_items:{len(raw_edits)}")
        return valid, warnings

    @classmethod
    def _flatten_provider_edits(cls, raw_edits: list[Any], depth: int = 0) -> list[Any]:
        """Expand a provider's line/item container into atomic child edits.

        Some compatible models return one line-level object with a nested
        ``changes``/``operations`` array. Parent source identity and line
        fields are inherited, but every child is still validated separately.
        String operation lists remain a single composite edit.
        """

        flattened: list[Any] = []
        if depth > 8:
            return list(raw_edits)
        for raw in raw_edits:
            if not isinstance(raw, dict):
                flattened.append(raw)
                continue
            nested = None
            for key in ("edits", "changes", "operations", "suggestions"):
                candidate = raw.get(key)
                if isinstance(candidate, list) and candidate and all(isinstance(item, dict) for item in candidate):
                    nested = candidate
                    break
            if nested is None:
                flattened.append(raw)
                continue
            inherited = {
                key: value
                for key, value in raw.items()
                if key not in {"edits", "changes", "operations", "suggestions", "edit_id", "operation", "action"}
            }
            for child in nested:
                merged = dict(inherited)
                merged.update(child)
                # Providers occasionally group a line, then a phrase, then
                # the individual changes. Recursively flatten those bounded
                # containers while preserving the outer source identity.
                flattened.extend(cls._flatten_provider_edits([merged], depth + 1))
        return flattened

    @classmethod
    def _normalize_deepseek_edit_payload(
        cls,
        raw: dict[str, Any],
        position: int,
        chunk: DocumentChunk | None = None,
    ) -> dict[str, Any]:
        item = dict(raw)
        aliases = {
            "edit_id": ("id", "editId", "edit_identifier"),
            "chunk_id": ("chunk", "chunkId", "chunk_identifier"),
            "source_hash": ("hash", "sourceHash", "source_fingerprint", "sourceFingerprint"),
            "start_line": ("line_start", "startLine", "from_line", "fromLine"),
            "end_line": ("line_end", "endLine", "to_line", "toLine"),
            "original_fragment": (
                "original", "source_fragment", "source_text", "old_text", "target_text",
                "before", "before_text", "old", "matched_text",
            ),
            "replacement_fragment": (
                "replacement", "suggested_fragment", "corrected_fragment", "new_text", "result_text",
                "after", "after_text", "new", "corrected_text", "replacement_text",
            ),
            "operation": ("action", "type", "edit_type", "operations", "actions", "op", "command"),
            "occurrence": ("occurrence_index", "occurrenceIndex", "match_index", "matchIndex"),
            "reason": ("rationale", "explanation", "description"),
            "confidence": ("score", "confidence_score", "confidenceScore"),
        }
        for target, candidates in aliases.items():
            if target in item:
                continue
            for candidate in candidates:
                if candidate in item:
                    item[target] = item[candidate]
                    break
        line_range = item.get("line_range")
        if isinstance(line_range, (list, tuple)) and len(line_range) == 2:
            item.setdefault("start_line", line_range[0])
            item.setdefault("end_line", line_range[1])
        if "start_line" not in item:
            item["start_line"] = item.get("line", item.get("line_number"))
        for key in ("start_line", "end_line", "occurrence"):
            value = item.get(key)
            if isinstance(value, str) and value.strip().isdigit():
                item[key] = int(value.strip())
        if "end_line" not in item and isinstance(item.get("start_line"), int):
            item["end_line"] = item["start_line"]
        chunk_id = item.get("chunk_id")
        if isinstance(chunk_id, str):
            item["chunk_id"] = chunk_id.strip().upper()
            chunk_id = item["chunk_id"]
        source_hash = item.get("source_hash")
        if isinstance(source_hash, str):
            item["source_hash"] = source_hash.strip().lower()
        edit_id = item.get("edit_id")
        if (
            not isinstance(edit_id, str)
            or not re.fullmatch(r"C\d{5}-E[A-Za-z0-9_.-]{1,50}", edit_id)
        ) and isinstance(chunk_id, str) and re.fullmatch(r"C\d{5}", chunk_id):
            item["edit_id"] = f"{chunk_id}-E{position:04d}"
        confidence = item.get("confidence")
        if isinstance(confidence, str):
            try:
                confidence = float(confidence.rstrip("%"))
            except ValueError:
                confidence = None
        if isinstance(confidence, (int, float)) and confidence > 1 and confidence <= 100:
            confidence = confidence / 100
        if isinstance(confidence, (int, float)):
            item["confidence"] = confidence
        operation = item.get("operation")
        replacement_missing = "replacement_fragment" not in item
        deletion_labels = {
            "delete", "delete_text", "deletion", "remove", "删除", "刪除", "移除",
            "delete_duplicate", "delete_symbol_noise",
        }
        explicit_deletion = False
        if isinstance(operation, str):
            explicit_deletion = re.sub(r"[\s-]+", "_", operation.strip().lower()) in deletion_labels
        elif isinstance(operation, list):
            explicit_deletion = any(
                re.sub(r"[\s-]+", "_", str(value).strip().lower()) in deletion_labels
                for value in operation
            )
        if replacement_missing and explicit_deletion:
            item["replacement_fragment"] = ""
        original = str(item.get("original_fragment", ""))
        replacement = str(item.get("replacement_fragment", ""))
        if isinstance(operation, str):
            item["operation"] = cls._canonical_operation(operation, original, replacement)
        elif isinstance(operation, list):
            canonical = {
                cls._canonical_operation(str(value), original, replacement)
                for value in operation
                if isinstance(value, (str, int, float))
            }
            canonical.discard("other")
            if len(canonical) == 1:
                item["operation"] = canonical.pop()
            elif len(canonical) > 1:
                item["operation"] = "composite"
            else:
                item["operation"] = cls._infer_operation_from_fragments(original, replacement)
        else:
            item["operation"] = cls._infer_operation_from_fragments(original, replacement)
        if chunk is not None:
            # The response arrived from this exact request. Bind all transport
            # identity locally instead of trusting a model to copy it.
            item["edit_id"] = f"{chunk.chunk_id}-E{position:04d}"
            item["chunk_id"] = chunk.chunk_id
            item["source_hash"] = chunk.source_hash
            start_line = item.get("start_line")
            end_line = item.get("end_line")
            occurrence = item.get("occurrence")
            if not isinstance(start_line, int) or start_line < 1:
                item["start_line"] = chunk.core_first_line
            if not isinstance(end_line, int) or end_line < 1:
                item["end_line"] = item["start_line"]
            if not isinstance(occurrence, int) or occurrence < 1:
                item["occurrence"] = 1
            if "reason" not in item or not isinstance(item.get("reason"), str):
                item["reason"] = "Provider edit"
            if "confidence" not in item or not isinstance(item.get("confidence"), (int, float)):
                item["confidence"] = 0.5
        return item

    @classmethod
    def _canonical_operation(cls, value: str, original: str, replacement: str) -> str:
        normalized = re.sub(r"[\s-]+", "_", value.strip().lower())
        canonical = {
            "whitespace", "paragraph", "punctuation", "delete_duplicate",
            "delete_symbol_noise", "case_conversion", "replace", "insert",
            "delete", "reorder", "composite", "typo", "noise", "other",
        }
        if normalized in {"other", "replace"}:
            return cls._infer_operation_from_fragments(original, replacement)
        if normalized in canonical:
            return normalized
        explicit_aliases = {
            "space": "whitespace", "spacing": "whitespace", "空白": "whitespace",
            "line_break": "paragraph", "linebreak": "paragraph", "reflow": "paragraph",
            "merge_lines": "paragraph", "split_lines": "paragraph", "join_lines": "paragraph", "段落": "paragraph",
            "punct": "punctuation", "标点": "punctuation", "標點": "punctuation",
            "duplicate": "delete_duplicate", "deduplicate": "delete_duplicate", "去重": "delete_duplicate",
            "symbol_noise": "delete_symbol_noise", "符号噪声": "delete_symbol_noise", "符號雜訊": "delete_symbol_noise",
            "spelling": "typo", "spelling_error": "typo", "correction": "typo", "错字": "typo", "錯字": "typo",
            "gibberish": "noise", "residual_noise": "noise", "噪声": "noise", "雜訊": "noise",
            "case": "case_conversion", "case_change": "case_conversion", "transform_case": "case_conversion",
            "capitalization": "case_conversion",
            "capitalisation": "case_conversion", "capitalize": "case_conversion", "uppercase": "case_conversion",
            "lowercase": "case_conversion", "title_case": "case_conversion", "sentence_case": "case_conversion",
            "大小写": "case_conversion", "大小寫": "case_conversion",
            "insert_text": "insert", "insertion": "insert", "add": "insert", "append": "insert",
            "prepend": "insert", "插入": "insert", "添加": "insert", "新增": "insert",
            "delete_text": "delete", "deletion": "delete", "remove": "delete", "删除": "delete",
            "刪除": "delete", "移除": "delete",
            "move": "reorder", "swap": "reorder", "reordering": "reorder", "order": "reorder", "移动": "reorder",
            "移動": "reorder", "重排": "reorder",
            "multiple": "composite", "multi_step": "composite", "compound": "composite", "组合": "composite",
            "組合": "composite",
        }
        if normalized in explicit_aliases:
            return explicit_aliases[normalized]
        replace_aliases = {
            "replace", "replacement", "substitute", "substitution", "edit", "modify",
            "change", "convert", "transform", "normalize", "normalise", "format",
            "修改", "替换", "替換", "更正", "纠正", "糾正", "转换", "轉換", "规范化", "規範化",
        }
        if normalized in replace_aliases:
            return cls._infer_operation_from_fragments(original, replacement)
        # Unknown edit verbs are safe as a review label. Automatic cleaning
        # rejects ``other`` through DIRECT_OPERATIONS unless a stricter local
        # deterministic category was inferred above.
        return "other"

    @classmethod
    def _infer_operation_from_fragments(cls, original: str, replacement: str) -> str:
        if original and not replacement:
            return "delete"
        if not original and replacement:
            return "insert"
        if original and original != replacement:
            if cls._without_whitespace(original) == cls._without_whitespace(replacement):
                return "paragraph" if ("\n" in original or "\n" in replacement) else "whitespace"
            if cls._lexical_signature(original) == cls._lexical_signature(replacement):
                return "punctuation"
            if cls._casefold_signature(original) == cls._casefold_signature(replacement):
                return "case_conversion"
            return "replace"
        return "other"

    @classmethod
    def assess_task(cls, custom_rules: list[str] | None = None) -> list[str]:
        """Reject tasks that cannot be represented as bounded exact-fragment edits."""
        if custom_rules is None:
            return []
        rendered_rules = [rule.strip() for rule in custom_rules if rule.strip()]
        if not rendered_rules:
            return ["ai_task_unsuitable:empty_rules"]
        if len(rendered_rules) > 50 or sum(len(rule) for rule in rendered_rules) > 12000:
            return ["ai_task_unsuitable:rules_too_large"]
        rendered = "\n".join(rendered_rules)
        for reason, pattern in cls.UNSUITABLE_TASK_PATTERNS:
            if pattern.search(rendered):
                return [f"ai_task_unsuitable:{reason}"]
        return []

    def preflight(self, text: str, custom_rules: list[str] | None = None) -> list[str]:
        if not self.settings.enabled:
            return ["ai_disabled"]
        if not self.settings.resolved_api_key():
            return ["api_key_missing"]
        task_warnings = self.assess_task(custom_rules)
        if task_warnings:
            return task_warnings
        if not text.strip():
            return ["empty_text"]
        if self.settings.max_chars_per_request < 1000:
            return [f"ai_chunk_limit_too_small:{self.settings.max_chars_per_request}:1000"]
        return []

    def _build_prompt(
        self,
        text: str,
        review: bool,
        custom_rules: list[str] | None = None,
        chunk: DocumentChunk | None = None,
        chunk_count: int = 1,
    ) -> tuple[str, str]:
        rendered_rules = ""
        if custom_rules:
            rendered_rules = "\n".join(
                f"{index}. {rule.strip()}"
                for index, rule in enumerate(custom_rules, 1)
                if rule.strip()
            )
            instructions = (
                "You are an exact, lossless executor of user-defined corpus editing rules. Return only structured atomic exact-fragment edits. "
                "Execute every numbered user rule in the current request completely. Those rules are the complete and exclusive task specification. Do not perform general proofreading or cleanup. "
                "Do not identify or remove advertisements, duplicate text, authors, sources, boilerplate, gibberish, or noise unless an enabled user rule explicitly requests that operation. "
                "Never infer an additional goal, rewrite unrelated text, summarize, translate, expand, add facts, or change style. "
                "Each original_fragment must be copied exactly from the supplied document and each replacement must implement only a selected rule. "
                "Split independent problems into separate edit items; never combine distant lines or unrelated changes in one item. "
                "Use case_conversion for letter-case-only changes, replace for bounded lexical substitutions, delete for rule-authorized deletion, insert for anchored insertion, reorder for bounded reordering, and composite only when one indivisible fragment requires more than one of these operations. "
                "If no text directly matches a rule, return an empty edits list. If uncertain whether an edit is in scope, omit it."
            )
            task = (
                "Apply only the numbered user rules below. Use the smallest exact fragment and its 1-based occurrence within the claimed line range. "
                + (
                    "Return suggestions for human approval; do not add any general corpus-review suggestion."
                    if review
                    else
                    "Return lossless structured edits; the application will reject operations that do not pass its local automatic safety guards."
                )
            )
            if not self._rules_allow_deletion(custom_rules):
                task += (
                    " These rules do not explicitly authorize deletion: every replacement_fragment must be non-empty, "
                    "and delete_duplicate, delete_symbol_noise, and deletion-like noise operations are forbidden."
                )
            if self._all_caps_to_initial_requested(custom_rules):
                task += (
                    " For the requested all-uppercase-word conversion, change each matching Latin word deterministically: "
                    "keep its first letter uppercase and lowercase its remaining letters. Preserve all surrounding text and never delete the word."
                )
            task += (
                " Insertions must use a non-empty exact source anchor as original_fragment and include that anchor unchanged in replacement_fragment; "
                "never return an unanchored empty original_fragment. A deletion must use a non-empty exact original_fragment and an empty replacement_fragment."
            )
            task += f"\n<user_rules>\n{rendered_rules}\n</user_rules>"
        elif review:
            instructions = (
                "You are a conservative corpus-text reviewer. Return only structured atomic edit suggestions. "
                "Never rewrite the document, summarize, translate, expand, add facts, or change style. "
                "Each original_fragment must be copied exactly from the supplied text. Split every independent issue into a separate item, preferably one line and one correction per item. "
                "Use multiple lines only when one indivisible paragraph or line-break problem requires them. If uncertain, omit the suggestion."
            )
            task = (
                "Review the locally cleaned text. Suggest only clear residual text-noise corrections. "
                "Allowed categories are whitespace, paragraph, punctuation, typo, noise, or other. "
                "Use the smallest exact original fragment needed. Set occurrence to the 1-based occurrence inside the claimed line range. "
                "Suggestions are shown to a human and are never applied automatically. Return an empty edits list when no safe suggestion exists."
            )
        else:
            instructions = (
                "You are a lossless corpus-text cleaning assistant. Return only structured atomic edit operations. "
                "Never rewrite words, change letters or numbers, summarize, translate, expand, add facts, or reorder content. "
                "Each original_fragment must be copied exactly from the supplied text. Split independent issues into separate items, preferably one line and one correction per item. If uncertain, return no edit."
            )
            task = (
                "Propose only these operations: whitespace, paragraph, punctuation, delete_duplicate, delete_symbol_noise. "
                "Whitespace and paragraph edits may change spacing or line breaks only. Punctuation edits must preserve every letter, digit, and CJK character in order. "
                "delete_duplicate may delete an exact fragment only when that fragment appears at least twice. "
                "delete_symbol_noise may delete only fragments containing no letters, digits, or CJK characters. "
                "Use the smallest exact original fragment and its 1-based occurrence inside the claimed line range. The application will reject every operation that violates these rules."
            )
        if chunk is None:
            metadata = (
                "request_chunk=C00001; chunk=1/1; visible_lines=1-"
                f"{max(1, text.count(chr(10)) + 1)}; editable_lines=1-{max(1, text.count(chr(10)) + 1)}; "
                "start_column=0."
            )
        else:
            metadata = (
                f"request_chunk={chunk.chunk_id}; chunk={int(chunk.chunk_id[1:])}/{chunk_count}; "
                f"visible_lines={chunk.first_line}-{chunk.last_line}; "
                f"editable_lines={chunk.core_first_line}-{chunk.core_last_line}; "
                f"visible_columns={chunk.start_column}-{chunk.end_column}; "
                f"editable_start={chunk.core_first_line}:{chunk.core_start_column}; "
                f"editable_end_exclusive={chunk.core_last_line}:{chunk.core_end_column}."
            )
        protocol = (
            "Return only lines that need a change; never return the corrected document or unchanged lines. "
            "For every item, report the best 1-based start_line and end_line hints and keep original_fragment/replacement_fragment to one independent correction. "
            "The application owns request identity, fingerprints, stable edit ids, and authoritative line numbers; do not invent or return those transport fields. "
            "If an indivisible target needs multiple coupled changes, return one bounded composite item, not overlapping edits. "
            "Read-only overlap may appear around the editable range: return an edit only when its original_fragment starts inside the editable line-and-column bounds. "
            "The application will search the exact original_fragment in this request, recompute its true line and occurrence, reject ambiguous or absent fragments, verify overlap ownership, and check edit safety locally."
        )
        return instructions, (
            f"{task}\n\n<edit_protocol>\n{protocol}\n{metadata}\n</edit_protocol>"
            f"\n\n<document>\n{text}\n</document>"
        )

    @staticmethod
    def _rules_allow_deletion(rules: list[str]) -> bool:
        rendered = "\n".join(rules).lower()
        deletion_terms = (
            "删除", "删去", "去除", "移除", "清除", "剔除", "delete", "remove",
            "strip", "drop", "omit", "erase",
        )
        return any(term in rendered for term in deletion_terms)

    @staticmethod
    def _all_caps_to_initial_requested(rules: list[str]) -> bool:
        rendered = "\n".join(rules).lower()
        source_requested = any(term in rendered for term in ("字母都大写", "全部大写", "全大写", "all uppercase", "all-uppercase", "all caps"))
        target_requested = any(term in rendered for term in ("首字母大写", "首字大写", "capitalize", "capitalized", "initial-capital", "initial capital", "title case"))
        return source_requested and target_requested

    @classmethod
    def _validate_custom_rule_suggestion(cls, suggestion: AISuggestion, rules: list[str]) -> bool:
        if not cls._rules_allow_deletion(rules):
            if not suggestion.replacement_fragment:
                return False
            if suggestion.operation in {"delete_duplicate", "delete_symbol_noise", "noise"}:
                return False
        if cls._all_caps_to_initial_requested(rules):
            expected, count = re.subn(
                r"(?<![A-Za-z])([A-Z]{2,})(?![A-Za-z])",
                lambda match: match.group(1)[0] + match.group(1)[1:].lower(),
                suggestion.original_fragment,
            )
            return count > 0 and expected == suggestion.replacement_fragment
        literal_specs = cls._literal_rule_specs(rules)
        if literal_specs:
            return (suggestion.original_fragment, suggestion.replacement_fragment) in literal_specs
        return True

    @classmethod
    def _literal_rule_specs(cls, rules: list[str]) -> set[tuple[str, str]]:
        """Extract only explicit quoted source/target transformations.

        These pairs make otherwise lexical replace/delete/insert operations
        deterministic enough for automatic mode. Unquoted or ambiguous rules
        remain available in human-review mode but are not auto-applied.
        """

        specs: set[tuple[str, str]] = set()
        quote = r'["“”‘’\']'
        value = rf'{quote}(.+?){quote}'
        for rule in rules:
            for pattern in (
                rf'(?:将|把)\s*{value}\s*(?:替换为|替換為|改为|改為|更改为|更改為)\s*{value}',
                rf'\breplace\s+{value}\s+(?:with|by)\s+{value}',
            ):
                for match in re.finditer(pattern, rule, re.IGNORECASE):
                    specs.add((match.group(1), match.group(2)))
            for pattern in (
                rf'(?:删除|刪除|去除|移除)\s*{value}',
                rf'\b(?:delete|remove)\s+{value}',
            ):
                for match in re.finditer(pattern, rule, re.IGNORECASE):
                    specs.add((match.group(1), ""))
            for pattern, before in (
                (rf'(?:在)\s*{value}\s*(?:后|後)(?:插入|添加|加入)\s*{value}', False),
                (rf'(?:在)\s*{value}\s*(?:前)(?:插入|添加|加入)\s*{value}', True),
                (rf'\binsert\s+{value}\s+(?:after)\s+{value}', False),
                (rf'\binsert\s+{value}\s+(?:before)\s+{value}', True),
            ):
                for match in re.finditer(pattern, rule, re.IGNORECASE):
                    if pattern.startswith(r'\binsert'):
                        inserted, anchor = match.group(1), match.group(2)
                    else:
                        anchor, inserted = match.group(1), match.group(2)
                    specs.add((anchor, inserted + anchor if before else anchor + inserted))
        return specs

    def _validate_direct_edit(
        self,
        text: str,
        suggestion: AISuggestion,
        custom_rules: list[str] | None = None,
    ) -> tuple[int, int] | None:
        original = suggestion.original_fragment
        replacement = suggestion.replacement_fragment
        if not original or original == replacement:
            return None
        span = self._locate_suggestion(text, suggestion)
        if span is None:
            return None

        if suggestion.operation not in self.DIRECT_OPERATIONS:
            if not custom_rules:
                return None
            if suggestion.operation == "case_conversion":
                if self._casefold_signature(original) != self._casefold_signature(replacement):
                    return None
                if self._nonletter_signature(original) != self._nonletter_signature(replacement):
                    return None
                return span
            if suggestion.operation in {"replace", "insert", "delete", "reorder", "composite", "typo", "other"}:
                return span if (original, replacement) in self._literal_rule_specs(custom_rules) else None
            return None

        if suggestion.operation in {"whitespace", "paragraph"}:
            if self._without_whitespace(original) != self._without_whitespace(replacement):
                return None
        elif suggestion.operation == "punctuation":
            if self._lexical_signature(original) != self._lexical_signature(replacement):
                return None
        elif suggestion.operation == "delete_duplicate":
            if replacement or text.count(original) < 2:
                return None
        elif suggestion.operation == "delete_symbol_noise":
            if replacement or any(char.isalnum() for char in original):
                return None
        return span

    @staticmethod
    def _locate_occurrence(text: str, fragment: str, occurrence: int) -> tuple[int, int] | None:
        if not fragment or occurrence < 1:
            return None
        start = -1
        search_from = 0
        for _ in range(occurrence):
            start = text.find(fragment, search_from)
            if start < 0:
                return None
            search_from = start + len(fragment)
        return start, start + len(fragment)

    @staticmethod
    def _locate_suggestion(text: str, suggestion: AISuggestion) -> tuple[int, int] | None:
        if not suggestion.original_fragment:
            return None
        if suggestion.source_start is not None:
            start = suggestion.source_start
            end = start + len(suggestion.original_fragment)
            if start >= 0 and text[start:end] == suggestion.original_fragment:
                return start, end
        return AIClient._locate_occurrence(text, suggestion.original_fragment, suggestion.occurrence)

    @staticmethod
    def _without_whitespace(value: str) -> str:
        return "".join(char for char in value if not char.isspace())

    @staticmethod
    def _lexical_signature(value: str) -> str:
        return "".join(char for char in value if char.isalnum())

    @staticmethod
    def _casefold_signature(value: str) -> str:
        return "".join(char.casefold() for char in value if char.isalnum())

    @staticmethod
    def _nonletter_signature(value: str) -> str:
        return "".join(char for char in value if not char.isalpha())

    @staticmethod
    def _to_suggestion(edit: AIEditModel) -> AISuggestion:
        return AISuggestion(
            operation=edit.operation,
            original_fragment=edit.original_fragment,
            replacement_fragment=edit.replacement_fragment,
            reason=edit.reason,
            confidence=edit.confidence,
            occurrence=edit.occurrence,
            edit_id=edit.edit_id,
            chunk_id=edit.chunk_id,
            source_hash=edit.source_hash,
            start_line=edit.start_line or 1,
            end_line=edit.end_line or edit.start_line or 1,
            source_start=edit._resolved_start,
            source_end=edit._resolved_end,
        )
