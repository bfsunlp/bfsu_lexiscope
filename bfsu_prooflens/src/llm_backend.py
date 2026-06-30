# -*- coding: utf-8 -*-
"""OpenAI / ChatGPT LLM backend.

The backend is intentionally defensive: the GUI can start without OpenAI, and
LLM proofreading remains usable even when a model returns JSON embedded in
Markdown or plain-language suggestions instead of a strict JSON object.
"""
from __future__ import annotations

import ast
import base64
import json
import mimetypes
import os
import re
import time
from pathlib import Path
from typing import Any

from .llm_prompts import LLM_OCR_PROMPT, LLM_PROOFREAD_PROMPT, LLM_STRUCTURED_OUTPUT_PROMPT


def _strip_json_fence(text: str) -> str:
    text = (text or "").strip().lstrip("\ufeff")
    text = re.sub(r"^```(?:json|JSON)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _find_json_object(text: str) -> str | None:
    """Return the first balanced JSON object substring in *text*.

    This handles the common cases where models prepend a note, wrap the object in
    Markdown, or append additional commentary after a valid JSON object.
    """
    s = _strip_json_fence(text)
    if not s:
        return None
    starts = [m.start() for m in re.finditer(r"\{", s)]
    for start in starts:
        depth = 0
        in_str = False
        escape = False
        for idx in range(start, len(s)):
            ch = s[idx]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:idx + 1].strip()
    return None


def _load_json_lenient(raw: str) -> dict[str, Any] | None:
    candidates: list[str] = []
    stripped = _strip_json_fence(raw)
    if stripped:
        candidates.append(stripped)
    obj = _find_json_object(raw)
    if obj and obj not in candidates:
        candidates.append(obj)
    # Some OpenAI-compatible models use smart quotes or trailing commas.
    for text in list(candidates):
        candidates.append(re.sub(r",\s*([}\]])", r"\1", text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")))
    for text in candidates:
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"suggestions": parsed} if isinstance(parsed, list) else None
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(text)
            return parsed if isinstance(parsed, dict) else {"suggestions": parsed} if isinstance(parsed, list) else None
        except Exception:
            pass
    return None


def _image_to_data_url(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found for LLM call: {path}")
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _line_no_for_fragment(text: str, fragment: str) -> int | str:
    if not fragment:
        return ""
    pos = text.find(fragment)
    if pos < 0:
        return ""
    return text[:pos].count("\n") + 1


def _normalise_confidence(value: Any, default: float = 0.5) -> float | str:
    if value == "":
        return ""
    try:
        v = float(value)
        if v > 1.0 and v <= 100.0:
            v = v / 100.0
        return max(0.0, min(1.0, v))
    except Exception:
        return default


def _short(text: str, limit: int = 1200) -> str:
    text = str(text or "").strip()
    return text if len(text) <= limit else text[:limit] + "…"


def _plain_text_to_suggestions(raw: str, edited_text: str) -> list[dict[str, Any]]:
    """Turn a non-JSON LLM answer into visible review items.

    The parser is intentionally generous.  Many models return useful feedback in
    prose, Markdown bullets, or sections such as "Corrected text" rather than the
    strict JSON requested by the prompt.  ProofLens should not hide that feedback:
    recover direct replacements when possible, otherwise surface the full prose as
    manual-review notes.
    """
    raw = (raw or "").strip()
    if not raw:
        return []

    suggestions: list[dict[str, Any]] = []

    # 1) Whole-text sections, e.g. "Corrected text:" / "修订文本：".
    corrected_patterns = [
        r"(?:Corrected|Revised|Fixed)\s+(?:text|version)\s*[:：]\s*(?P<text>.+)",
        r"(?:修订文本|修正文本|修改后文本|校对后文本|建议全文)\s*[:：]\s*(?P<text>.+)",
    ]
    for pat in corrected_patterns:
        m = re.search(pat, raw, flags=re.I | re.S)
        if m:
            corrected = m.group("text").strip().strip('`').strip()
            # Stop before a following explanation heading if present.
            corrected = re.split(r"\n\s*(?:Reason|Explanation|Notes?|理由|说明|原因)\s*[:：]", corrected, maxsplit=1, flags=re.I)[0].strip()
            if corrected and corrected != edited_text.strip():
                return [{
                    "line_no": "",
                    "original": edited_text,
                    "suggested": corrected,
                    "reason": "LLM returned a plain-text corrected version. Review before accepting as a whole-text replacement.",
                    "confidence": 0.55,
                    "category": "whole_text_correction",
                    "status": "pending",
                }]

    # 2) Structured Original/Suggested fragments in plain text.
    pattern = re.compile(
        r"(?:Original|原文|原文本|Before|错误文本)\s*[:：]\s*(?P<orig>.+?)\s*"
        r"(?:Suggested|建议|建议文本|Correction|修正|After|修正文本)\s*[:：]\s*(?P<sugg>.+?)"
        r"(?=\n\s*(?:Original|原文|Before|\d+[\.)、]|[-*•])|\Z)",
        flags=re.I | re.S,
    )
    for m in pattern.finditer(raw):
        orig = m.group("orig").strip().strip('"“”')
        sugg = m.group("sugg").strip().strip('"“”')
        sugg = re.split(r"(?:\n|\s{2,}|\s)(?:Reason|理由|原因|Explanation|说明)\s*[:：]", sugg, maxsplit=1, flags=re.I)[0].strip()
        suggestions.append({
            "line_no": _line_no_for_fragment(edited_text, orig),
            "original": orig,
            "suggested": sugg,
            "reason": "LLM returned plain text; this replacement pair was recovered automatically.",
            "confidence": 0.5,
            "category": "llm_plain_text_recovered",
            "status": "pending" if orig and sugg else "info",
        })
    if suggestions:
        return suggestions

    # 3) Arrow/diff style: old -> new, 原文 => 修正.
    arrow = re.compile(r"(?P<orig>[^\n]{1,300}?)\s*(?:->|=>|→|改为|应为)\s*(?P<sugg>[^\n]{1,300})")
    for m in arrow.finditer(raw):
        orig = m.group("orig").strip().strip('-*• 0123456789.、:："“”')
        sugg = m.group("sugg").strip().strip('"“”')
        if orig and sugg and orig != sugg:
            suggestions.append({
                "line_no": _line_no_for_fragment(edited_text, orig),
                "original": orig,
                "suggested": sugg,
                "reason": "LLM returned an arrow-style plain-text correction; ProofLens recovered it automatically.",
                "confidence": 0.5,
                "category": "llm_plain_text_recovered",
                "status": "pending",
            })
    if suggestions:
        return suggestions[:20]

    # 4) Markdown/plain bullets become visible manual-review notes.
    bullet_lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(?:[-*•]|\d+[\.)、])\s*(.+)$", line)
        if m:
            bullet_lines.append(m.group(1).strip())
    if bullet_lines:
        return [{
            "line_no": "",
            "original": "",
            "suggested": "",
            "reason": _short(line, 2500),
            "confidence": "",
            "category": "llm_plain_text_feedback",
            "status": "info",
        } for line in bullet_lines[:30]]

    # 5) Last resort: show the full raw response instead of hiding it in notes.
    return [{
        "line_no": "",
        "original": "",
        "suggested": "",
        "reason": _short(raw, 6000),
        "confidence": "",
        "category": "llm_plain_text_feedback",
        "status": "info",
    }]

def _reflow_hard_wrapped_text(text: str) -> str:
    """Conservative text-only paragraph reflow for OCR/PDF extraction output."""
    if not text:
        return text
    # Remove English hyphenation introduced by line breaks: methodo-\nlogical -> methodological.
    text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", "", text)
    lines = text.splitlines()
    out: list[str] = []
    buf = ""
    end_punct = tuple("。！？；：.!?;:")
    for line in lines:
        raw = line.rstrip()
        s = raw.strip()
        if not s:
            if buf:
                out.append(buf.strip())
                buf = ""
            out.append("")
            continue
        # Keep obvious headings/lists/tables separate.
        is_list = bool(re.match(r"^(?:\d+[\.)、]|[A-Z]\.|[-*•])\s+", s))
        is_heading = len(s) < 90 and not buf and not s.endswith(end_punct) and sum(ch.isalpha() for ch in s) > 0
        if is_list or is_heading:
            if buf:
                out.append(buf.strip())
                buf = ""
            out.append(s)
            continue
        if not buf:
            buf = s
            continue
        if buf.endswith(end_punct) or raw.startswith((" ", "\t")):
            out.append(buf.strip())
            buf = s
        else:
            sep = "" if re.search(r"[\u4e00-\u9fff]$", buf) or re.match(r"^[\u4e00-\u9fff]", s) else " "
            buf += sep + s
    if buf:
        out.append(buf.strip())
    return "\n".join(out)


def _detect_local_text_quality_issues(edited_text: str) -> list[dict[str, Any]]:
    """Rule-based safety net for common OCR/PDF extraction problems."""
    text = edited_text or ""
    suggestions: list[dict[str, Any]] = []
    if not text.strip():
        return suggestions

    noisy_chars = ["�", "□", "▯", "￾", "\ufeff", "\u200b", "\u200c", "\u200d"]
    for ch in noisy_chars:
        if ch in text:
            suggestions.append({
                "line_no": _line_no_for_fragment(text, ch),
                "original": ch,
                "suggested": "" if ch not in {"�", "□", "▯"} else "[?]",
                "reason": "Detected a likely OCR/PDF extraction encoding artifact or invisible control character.",
                "confidence": 0.8 if ch in {"￾", "\ufeff", "\u200b", "\u200c", "\u200d"} else 0.55,
                "category": "encoding_noise",
                "status": "pending",
            })
            break

    hyphen_match = re.search(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", text)
    if hyphen_match:
        frag_start = max(0, hyphen_match.start() - 35)
        frag_end = min(len(text), hyphen_match.end() + 35)
        original = text[frag_start:frag_end]
        suggested = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", "", original)
        suggestions.append({
            "line_no": _line_no_for_fragment(text, original),
            "original": original,
            "suggested": suggested,
            "reason": "Detected line-break hyphenation that is likely an OCR/PDF wrapping artifact.",
            "confidence": 0.75,
            "category": "hyphenation",
            "status": "pending",
        })

    lines = [ln for ln in text.splitlines() if ln.strip()]
    short_unfinished = [ln for ln in lines if 20 <= len(ln.strip()) <= 95 and not ln.strip().endswith(tuple("。！？；：.!?;:)）]}>"))]
    if len(lines) >= 8 and len(short_unfinished) / max(1, len(lines)) >= 0.55:
        reflowed = _reflow_hard_wrapped_text(text)
        if reflowed.strip() != text.strip():
            suggestions.append({
                "line_no": "",
                "original": text,
                "suggested": reflowed,
                "reason": "Many lines look like hard-wrapped PDF/OCR line breaks rather than real paragraph breaks. Review the proposed paragraph reflow before accepting.",
                "confidence": 0.6,
                "category": "paragraph_reflow",
                "status": "pending",
            })

    if re.search(r" {3,}|\t{2,}", text):
        suggestions.append({
            "line_no": "",
            "original": "multiple spaces/tabs",
            "suggested": "single spaces where appropriate",
            "reason": "Detected repeated spaces or tabs that may come from OCR layout extraction.",
            "confidence": 0.55,
            "category": "whitespace",
            "status": "info",
        })

    return suggestions[:8]


def _map_alt_suggestion_keys(item: dict[str, Any], edited_text: str) -> dict[str, Any]:
    original = item.get("original", item.get("source", item.get("old", item.get("before", item.get("error", "")))))
    suggested = item.get("suggested", item.get("replacement", item.get("new", item.get("after", item.get("correction", "")))))
    reason = item.get("reason", item.get("explanation", item.get("comment", item.get("note", ""))))
    category = item.get("category", item.get("type", item.get("error_type", "uncertain")))
    line_no = item.get("line_no", item.get("line", item.get("line_number", "")))
    if not line_no:
        line_no = _line_no_for_fragment(edited_text, str(original or ""))
    return {
        "line_no": line_no,
        "original": "" if original is None else str(original),
        "suggested": "" if suggested is None else str(suggested),
        "reason": "" if reason is None else str(reason),
        "confidence": _normalise_confidence(item.get("confidence", item.get("score", 0.5))),
        "category": "" if category is None else str(category),
        "status": str(item.get("status", "pending")),
    }


def _normalise_proofread_payload(parsed: dict[str, Any], edited_text: str, raw: str) -> dict[str, Any]:
    corrected = parsed.get("corrected_text", parsed.get("corrected", parsed.get("revised_text", parsed.get("fixed_text", ""))))
    if corrected is None or str(corrected).strip() == "":
        corrected = edited_text
    suggestions_raw = parsed.get("suggestions", parsed.get("issues", parsed.get("corrections", parsed.get("changes", []))))
    if isinstance(suggestions_raw, dict):
        suggestions_raw = [suggestions_raw]
    suggestions: list[dict[str, Any]] = []
    if isinstance(suggestions_raw, list):
        for item in suggestions_raw:
            if isinstance(item, dict):
                suggestions.append(_map_alt_suggestion_keys(item, edited_text))
            elif isinstance(item, str) and item.strip():
                suggestions.append({
                    "line_no": "",
                    "original": "",
                    "suggested": "",
                    "reason": item.strip(),
                    "confidence": "",
                    "category": "llm_text_note",
                    "status": "info",
                })

    warnings = parsed.get("warnings", [])
    if isinstance(warnings, str):
        warnings = [warnings]
    elif not isinstance(warnings, list):
        warnings = []

    uncertain = parsed.get("uncertain_spans", [])
    if not isinstance(uncertain, list):
        uncertain = []

    local_suggestions = _detect_local_text_quality_issues(edited_text)
    # Add local findings only when the same category/original has not already
    # been returned by the model.
    seen = {(str(s.get("category", "")), str(s.get("original", ""))[:80]) for s in suggestions}
    for s in local_suggestions:
        key = (str(s.get("category", "")), str(s.get("original", ""))[:80])
        if key not in seen:
            suggestions.append(s)
            seen.add(key)

    for item in suggestions:
        item.setdefault("status", "pending")
        item.setdefault("timestamp", "")
        if not item.get("category"):
            item["category"] = "uncertain"
        if not item.get("reason"):
            item["reason"] = "Potential OCR/PDF extraction issue. Please review manually."

    return {
        "corrected_text": str(corrected),
        "detected_languages": parsed.get("detected_languages", []),
        "suggestions": suggestions,
        "uncertain_spans": uncertain,
        "warnings": [str(x) for x in warnings],
        "layout_notes": str(parsed.get("layout_notes", "") or ""),
        "raw": raw,
    }


def _content_to_text(content: Any) -> str:
    """Extract text from OpenAI-compatible message content variants."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                val = item.get("text") or item.get("content") or item.get("output_text")
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, dict) and isinstance(val.get("text"), str):
                    parts.append(val.get("text", ""))
            else:
                val = getattr(item, "text", None) or getattr(item, "content", None)
                if isinstance(val, str):
                    parts.append(val)
        return "\n".join(x for x in parts if x)
    return str(content)


def _extract_chat_response_text(response: Any) -> str:
    """Best-effort extraction from chat.completions responses.

    Some OpenAI-compatible endpoints return non-string message content, refusal
    fields, or provider-specific annotations.  Returning an empty string makes the
    GUI look like the LLM produced no feedback, so collect every text-like field
    that is safe to surface to the user.
    """
    try:
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        if message is not None:
            text = _content_to_text(getattr(message, "content", ""))
            if text.strip():
                return text
            refusal = getattr(message, "refusal", None)
            if refusal:
                return str(refusal)
            # Pydantic model fallback.
            if hasattr(message, "model_dump"):
                data = message.model_dump()
                for key in ("content", "refusal", "text", "output_text"):
                    val = data.get(key)
                    text = _content_to_text(val)
                    if text.strip():
                        return text
        text = _content_to_text(getattr(choice, "text", ""))
        if text.strip():
            return text
        finish = getattr(choice, "finish_reason", "")
        if finish:
            return f"[Empty LLM message; finish_reason={finish}]"
    except Exception:
        pass
    return ""


def _empty_response_suggestion(raw: str = "") -> dict[str, Any]:
    reason = (
        "The LLM call completed but returned no usable text. Try increasing Max output tokens, "
        "switching to a model that supports chat/completions JSON output, or disabling structured JSON temporarily."
    )
    if raw:
        reason += " Raw provider message: " + _short(raw, 1500)
    return {
        "line_no": "",
        "original": "",
        "suggested": "",
        "reason": reason,
        "confidence": "",
        "category": "llm_empty_response",
        "status": "info",
    }


class LLMBackend:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config or {}
        self.model = self.config.get("model") or "gpt-5-mini"
        self.temperature = float(self.config.get("temperature", 0))
        self.max_tokens = int(self.config.get("max_output_tokens", 4096))
        self.api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = self.config.get("base_url") or os.environ.get("OPENAI_BASE_URL", "")
        self.structured_json = bool(self.config.get("structured_json", True))

    def _client(self):
        if not self.api_key:
            raise RuntimeError("OpenAI API Key 为空。请在设置中填写 API Key，或设置 OPENAI_API_KEY 环境变量。")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise RuntimeError("未安装 openai 包。请先运行：python -m pip install openai") from exc
        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def _chat(self, messages: list[dict[str, Any]], *, prefer_json: bool = False) -> str:
        client = self._client()
        base_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if prefer_json and self.structured_json:
            base_kwargs["response_format"] = {"type": "json_object"}
        attempts = [
            {**base_kwargs, "max_completion_tokens": self.max_tokens},
            {**base_kwargs, "max_tokens": self.max_tokens},
            {**base_kwargs, "temperature": self.temperature, "max_completion_tokens": self.max_tokens},
            {**base_kwargs, "temperature": self.temperature, "max_tokens": self.max_tokens},
            base_kwargs,
        ]
        # If response_format is rejected, retry without it.
        if "response_format" in base_kwargs:
            no_format = {k: v for k, v in base_kwargs.items() if k != "response_format"}
            attempts.extend([
                {**no_format, "max_completion_tokens": self.max_tokens},
                {**no_format, "max_tokens": self.max_tokens},
                {**no_format, "temperature": self.temperature, "max_tokens": self.max_tokens},
                no_format,
            ])
        errors: list[str] = []
        empty_notes: list[str] = []
        for kwargs in attempts:
            try:
                response = client.chat.completions.create(**kwargs)
                text = _extract_chat_response_text(response)
                if text.strip():
                    return text
                empty_notes.append("empty response")
                # Empty provider responses are often parameter/model related;
                # try the remaining compatibility variants before giving up.
                continue
            except Exception as exc:
                msg = str(exc)
                errors.append(msg)
                lower = msg.lower()
                if not any(x in lower for x in ["max_tokens", "max_completion_tokens", "temperature", "response_format", "json", "unsupported", "unrecognized", "invalid parameter"]):
                    break
        if empty_notes and not errors:
            return "[Empty LLM response after compatibility retries]"
        if empty_notes:
            return "[Empty LLM response after compatibility retries. Last API errors: " + " | ".join(errors[-2:]) + "]"
        raise RuntimeError("OpenAI API 调用失败：" + " | ".join(errors[-3:]))

    def _repair_proofread_json(self, raw: str, edited_text: str, language_hint: str) -> tuple[dict[str, Any] | None, str]:
        """Ask the model once to convert/retry proofreading output as strict JSON."""
        if not bool(self.config.get("auto_repair_non_json", True)):
            return None, ""
        raw = raw or ""
        repair_prompt = (
            "You are repairing an OCR proofreading response for BFSU ProofLens.\n"
            "Return ONLY one valid JSON object matching the schema below. Do not use Markdown.\n"
            "If the previous response contains useful feedback, convert it into suggestions.\n"
            "If the previous response is empty or unusable, analyze the current edited text directly for OCR/PDF extraction issues such as hard line breaks, garbled characters, broken hyphenation, duplicate lines, wrong punctuation, and paragraph reflow.\n\n"
            + LLM_STRUCTURED_OUTPUT_PROMPT
            + f"\nLanguage hint: {language_hint}\n\n[Current edited text]\n{edited_text or ''}\n\n[Previous invalid/plain response]\n{raw[:6000]}"
        )
        try:
            repaired_raw = self._chat([{"role": "user", "content": repair_prompt}], prefer_json=True)
        except Exception as exc:
            return None, f"[JSON repair failed: {exc}]"
        parsed = _load_json_lenient(repaired_raw)
        return parsed, repaired_raw

    def ocr_image(self, image_path: str, language_hint: str = "多语混排") -> dict[str, Any]:
        start = time.perf_counter()
        content = [
            {"type": "text", "text": LLM_OCR_PROMPT + f"\n语言提示：{language_hint}"},
            {"type": "image_url", "image_url": {"url": _image_to_data_url(image_path)}},
        ]
        text = self._chat([{"role": "user", "content": content}])
        return {"text": text.strip(), "elapsed_seconds": time.perf_counter() - start, "raw": text}

    def proofread(self, ocr_text: str, edited_text: str, image_path: str | None = None, language_hint: str = "多语混排") -> dict[str, Any]:
        start = time.perf_counter()
        payload_text = (
            LLM_PROOFREAD_PROMPT
            + "\n\n"
            + LLM_STRUCTURED_OUTPUT_PROMPT
            + "\n\nCRITICAL OUTPUT RULES:\n"
            + "- Return exactly one JSON object.\n"
            + "- Do not use Markdown code fences.\n"
            + "- Do not add explanatory prose before or after the JSON.\n"
            + "- If you find no actionable OCR/PDF extraction error, still return suggestions with one no_change item.\n"
            + f"\n语言提示：{language_hint}\n"
            + "\n[OCR 原始文本]\n"
            + (ocr_text or "")
            + "\n\n[用户当前编辑文本]\n"
            + (edited_text or "")
        )
        if image_path:
            content: Any = [
                {"type": "text", "text": payload_text},
                {"type": "image_url", "image_url": {"url": _image_to_data_url(image_path)}},
            ]
        else:
            content = payload_text
        raw = self._chat([{"role": "user", "content": content}], prefer_json=True)
        parsed = _load_json_lenient(raw)
        repair_raw = ""
        if parsed is None:
            parsed, repair_raw = self._repair_proofread_json(raw, edited_text, language_hint)

        if parsed is None:
            source_text = raw or repair_raw
            suggestions = _plain_text_to_suggestions(source_text, edited_text)
            local_suggestions = _detect_local_text_quality_issues(edited_text)
            if local_suggestions:
                # Put deterministic local findings first because they are actionable.
                suggestions = local_suggestions + suggestions
            if not suggestions:
                suggestions = [_empty_response_suggestion(source_text)]
            parsed = {
                "corrected_text": edited_text,
                "detected_languages": [],
                "suggestions": suggestions,
                "uncertain_spans": [],
                "warnings": ["LLM did not return valid JSON; ProofLens recovered the response as plain-text/manual-review feedback."],
                "layout_notes": source_text,
            }
            raw_for_record = source_text
        else:
            raw_for_record = raw
            if repair_raw:
                raw_for_record = (raw or "") + "\n\n[ProofLens JSON repair response]\n" + repair_raw

        normalised = _normalise_proofread_payload(parsed, edited_text, raw_for_record)
        # If normalisation still produces no visible item, show a clear diagnostic
        # rather than an apparently successful but empty proofreading run.
        if not normalised.get("suggestions"):
            normalised["suggestions"] = [_empty_response_suggestion(raw_for_record)]
        normalised["elapsed_seconds"] = time.perf_counter() - start
        return normalised
