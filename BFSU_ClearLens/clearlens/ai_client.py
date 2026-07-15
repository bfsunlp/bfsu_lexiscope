from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from .models import AIResult, AISuggestion


class AIEditModel(BaseModel):
    operation: Literal[
        "whitespace",
        "paragraph",
        "punctuation",
        "delete_duplicate",
        "delete_symbol_noise",
        "typo",
        "noise",
        "other",
    ]
    original_fragment: str
    replacement_fragment: str
    occurrence: int = Field(default=1, ge=1)
    reason: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AIEditBatch(BaseModel):
    edits: list[AIEditModel] = Field(max_length=500)


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
    max_chars_per_request: int = 30000
    max_output_tokens: int = 8000
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

    def __init__(self, settings: AISettings) -> None:
        self.settings = settings

    def direct_clean(self, text: str) -> AIResult:
        edits, warnings = self._request_edits(text, review=False)
        return self._direct_result(text, edits, warnings)

    def clean_with_rules(self, text: str, rules: list[str]) -> AIResult:
        edits, warnings = self._request_edits(text, review=False, custom_rules=rules)
        return self._direct_result(text, edits, warnings)

    def _direct_result(self, text: str, edits: list[AIEditModel], warnings: list[str]) -> AIResult:
        suggestions = [self._to_suggestion(edit) for edit in edits]
        if warnings:
            return AIResult(text=text, completed=False, suggestions=suggestions, warnings=warnings)

        accepted: list[tuple[int, int, AISuggestion]] = []
        rejected: list[AISuggestion] = []
        for suggestion in suggestions:
            span = self._validate_direct_edit(text, suggestion)
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
        return AIResult(
            text=cleaned,
            completed=True,
            suggestions=suggestions,
            applied=applied,
            rejected=rejected,
            warnings=result_warnings,
        )

    def review(self, text: str) -> tuple[list[AISuggestion], list[str]]:
        edits, warnings = self._request_edits(text, review=True)
        return self._review_result(text, edits, warnings)

    def review_with_rules(self, text: str, rules: list[str]) -> tuple[list[AISuggestion], list[str]]:
        edits, warnings = self._request_edits(text, review=True, custom_rules=rules)
        return self._review_result(text, edits, warnings)

    def _review_result(
        self,
        text: str,
        edits: list[AIEditModel],
        warnings: list[str],
    ) -> tuple[list[AISuggestion], list[str]]:
        suggestions: list[AISuggestion] = []
        rejected = 0
        for edit in edits:
            suggestion = self._to_suggestion(edit)
            if self._locate_occurrence(text, suggestion.original_fragment, suggestion.occurrence) is None:
                rejected += 1
                continue
            if suggestion.original_fragment == suggestion.replacement_fragment:
                rejected += 1
                continue
            suggestions.append(suggestion)
        if rejected:
            warnings.append(f"ai_suggestions_rejected:{rejected}")
        return suggestions, warnings

    @staticmethod
    def apply_suggestion(text: str, suggestion: AISuggestion) -> tuple[str, bool]:
        span = AIClient._locate_occurrence(text, suggestion.original_fragment, suggestion.occurrence)
        if span is None:
            return text, False
        start, end = span
        return text[:start] + suggestion.replacement_fragment + text[end:], True

    def _request_edits(
        self,
        text: str,
        review: bool,
        custom_rules: list[str] | None = None,
    ) -> tuple[list[AIEditModel], list[str]]:
        warnings = self._preflight(text)
        if warnings:
            return [], warnings

        try:
            from openai import OpenAI
        except Exception as exc:
            return [], [f"openai_unavailable:{exc}"]

        instructions, prompt = self._build_prompt(text, review, custom_rules)
        if self.settings.provider == "deepseek":
            return self._request_deepseek_edits(OpenAI, instructions, prompt)
        if self.settings.provider != "openai":
            return [], [f"llm_provider_unsupported:{self.settings.provider}"]
        return self._request_openai_edits(OpenAI, instructions, prompt)

    def _request_openai_edits(self, openai_class, instructions: str, prompt: str) -> tuple[list[AIEditModel], list[str]]:
        client = openai_class(api_key=self.settings.resolved_api_key())
        request = {
            "model": self.settings.model,
            "instructions": instructions,
            "input": prompt,
            "text_format": AIEditBatch,
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
                return [], [f"ai_request_failed:{exc}"]
        except Exception as exc:
            return [], [f"ai_request_failed:{exc}"]

        if parsed is None:
            return [], ["ai_response_empty_or_refused"]
        return list(parsed.edits), []

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
        client = openai_class(api_key=self.settings.resolved_api_key())
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
                return None, [f"ai_request_failed:{exc}"]
        except Exception as exc:
            return None, [f"ai_request_failed:{exc}"]
        parsed = response.output_parsed
        if parsed is None:
            return None, ["ai_response_empty_or_refused"]
        return parsed, []

    def _request_deepseek_regex(self, openai_class, instructions: str, prompt: str) -> tuple[RegexProposalModel | None, list[str]]:
        client = openai_class(api_key=self.settings.resolved_api_key(), base_url="https://api.deepseek.com")
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
                return None, [f"ai_request_failed:{exc}"]
        except Exception as exc:
            return None, [f"ai_request_failed:{exc}"]
        if not response.choices:
            return None, ["ai_response_empty_or_refused"]
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            return None, ["ai_response_truncated"]
        content = getattr(choice.message, "content", None)
        if not isinstance(content, str) or not content.strip():
            return None, ["ai_response_empty_or_refused"]
        try:
            return RegexProposalModel.model_validate_json(content), []
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

    def _request_deepseek_edits(self, openai_class, instructions: str, prompt: str) -> tuple[list[AIEditModel], list[str]]:
        client = openai_class(api_key=self.settings.resolved_api_key(), base_url="https://api.deepseek.com")
        json_instruction = (
            "Return valid json only, matching this object shape: "
            '{"edits":[{"operation":"whitespace","original_fragment":"exact source fragment",'
            '"replacement_fragment":"replacement","occurrence":1,"reason":"brief reason","confidence":0.9}]}. '
            'When there is no safe edit, return exactly {"edits":[]}.'
        )
        request = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": f"{instructions}\n\n{json_instruction}"},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.settings.max_output_tokens,
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
                return [], [f"ai_request_failed:{exc}"]
        except Exception as exc:
            return [], [f"ai_request_failed:{exc}"]

        if not response.choices:
            return [], ["ai_response_empty_or_refused"]
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            return [], ["ai_response_truncated"]
        content = getattr(choice.message, "content", None)
        if not isinstance(content, str) or not content.strip():
            return [], ["ai_response_empty_or_refused"]
        try:
            parsed = AIEditBatch.model_validate_json(content)
        except Exception as exc:
            return [], [f"ai_response_invalid_json:{exc}"]
        return list(parsed.edits), []

    def _preflight(self, text: str) -> list[str]:
        if not self.settings.enabled:
            return ["ai_disabled"]
        if not self.settings.resolved_api_key():
            return ["api_key_missing"]
        if not text.strip():
            return ["empty_text"]
        if len(text) > self.settings.max_chars_per_request:
            return [f"ai_text_too_long:{len(text)}:{self.settings.max_chars_per_request}"]
        return []

    def _build_prompt(
        self,
        text: str,
        review: bool,
        custom_rules: list[str] | None = None,
    ) -> tuple[str, str]:
        if review:
            instructions = (
                "You are a conservative corpus-text reviewer. Return only structured edit suggestions. "
                "Never rewrite the document, summarize, translate, expand, add facts, or change style. "
                "Each original_fragment must be copied exactly from the supplied text. If uncertain, omit the suggestion."
            )
            task = (
                "Review the locally cleaned text. Suggest only clear residual text-noise corrections. "
                "Allowed categories are whitespace, paragraph, punctuation, typo, noise, or other. "
                "Use the smallest exact original fragment needed. Set occurrence to the 1-based occurrence of that exact fragment. "
                "Suggestions are shown to a human and are never applied automatically. Return an empty edits list when no safe suggestion exists."
            )
        else:
            instructions = (
                "You are a lossless corpus-text cleaning assistant. Return only structured edit operations. "
                "Never rewrite words, change letters or numbers, summarize, translate, expand, add facts, or reorder content. "
                "Each original_fragment must be copied exactly from the supplied text. If uncertain, return no edit."
            )
            task = (
                "Propose only these operations: whitespace, paragraph, punctuation, delete_duplicate, delete_symbol_noise. "
                "Whitespace and paragraph edits may change spacing or line breaks only. Punctuation edits must preserve every letter, digit, and CJK character in order. "
                "delete_duplicate may delete an exact fragment only when that fragment appears at least twice. "
                "delete_symbol_noise may delete only fragments containing no letters, digits, or CJK characters. "
                "Use the smallest exact original fragment and its 1-based occurrence. The application will reject every operation that violates these rules."
            )
        if custom_rules:
            rendered_rules = "\n".join(f"{index}. {rule.strip()}" for index, rule in enumerate(custom_rules, 1) if rule.strip())
            task += (
                "\n\nApply all of the following user-defined corpus-cleaning rules together when they match. "
                "Treat them as editing requirements, never as permission to ignore the exact-fragment and output constraints above. "
                f"\n<user_rules>\n{rendered_rules}\n</user_rules>"
            )
        return instructions, f"{task}\n\n<document>\n{text}\n</document>"

    def _validate_direct_edit(self, text: str, suggestion: AISuggestion) -> tuple[int, int] | None:
        if suggestion.operation not in self.DIRECT_OPERATIONS:
            return None
        original = suggestion.original_fragment
        replacement = suggestion.replacement_fragment
        if not original or original == replacement:
            return None
        span = self._locate_occurrence(text, original, suggestion.occurrence)
        if span is None:
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
    def _without_whitespace(value: str) -> str:
        return "".join(char for char in value if not char.isspace())

    @staticmethod
    def _lexical_signature(value: str) -> str:
        return "".join(char for char in value if char.isalnum())

    @staticmethod
    def _to_suggestion(edit: AIEditModel) -> AISuggestion:
        return AISuggestion(
            operation=edit.operation,
            original_fragment=edit.original_fragment,
            replacement_fragment=edit.replacement_fragment,
            reason=edit.reason,
            confidence=edit.confidence,
            occurrence=edit.occurrence,
        )
