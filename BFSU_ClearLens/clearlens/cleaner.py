from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter

from .models import CleanOptions, CleanResult, RegexRule


CJK_RE = re.compile(r"[\u3400-\u9fff]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ZERO_WIDTH_RE = re.compile(r"[\u00ad\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]")
PRIVATE_USE_RE = re.compile(r"[\ue000-\uf8ff\U000f0000-\U000ffffd\U00100000-\U0010fffd]")
OCR_PLACEHOLDER_RE = re.compile(r"[\ufffd\u25a1\u25a0]")
ALNUM_CJK_RE = re.compile(r"[A-Za-z0-9\u3400-\u9fff]")
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U0001FC00-\U0001FFFD"
    "\u2300-\u23FF"
    "\u2600-\u27BF"
    "]"
)
EMOJI_COMPONENT_RE = re.compile(r"[\U0001F3FB-\U0001F3FF\u200d\ufe0e\ufe0f\u20e3]")
WEB_CODE_BLOCK_RE = re.compile(
    r"<\s*(script|style|noscript|template)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_BREAK_RE = re.compile(r"<\s*br\b[^>]*?/?>", re.IGNORECASE)
EMPTY_HTML_TAG_RE = re.compile(r"<([A-Za-z][\w:.-]*)\b[^>]*>\s*</\1\s*>", re.IGNORECASE)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_bom(text: str) -> str:
    return text.lstrip("\ufeff")


def remove_control_chars(text: str) -> str:
    return CONTROL_RE.sub("", text)


def remove_zero_width_chars(text: str) -> str:
    return ZERO_WIDTH_RE.sub("", text)


def remove_emoji(text: str) -> str:
    text = re.sub(r"[#*0-9]\ufe0f?\u20e3", "", text)
    text = EMOJI_RE.sub("", text)
    return EMOJI_COMPONENT_RE.sub("", text)


def remove_web_code_blocks(text: str) -> str:
    lowered = text.lower()
    if not any(marker in lowered for marker in ("<script", "<style", "<noscript", "<template")):
        return text
    return WEB_CODE_BLOCK_RE.sub("", text)


def is_effectively_blank_line(line: str) -> bool:
    stripped = line.strip()
    if stripped and not any(marker in line for marker in ("&", "<", "\u00ad", "\u200b", "\u200c", "\u200d", "\ufeff")):
        return False
    candidate = html.unescape(line)
    candidate = ZERO_WIDTH_RE.sub("", candidate)
    candidate = HTML_COMMENT_RE.sub("", candidate)
    candidate = HTML_BREAK_RE.sub("", candidate)
    for _ in range(12):
        updated = EMPTY_HTML_TAG_RE.sub("", candidate)
        if updated == candidate:
            break
        candidate = updated
    return not candidate.strip()


def normalize_spaces(text: str) -> str:
    if "\u00a0" not in text and "\u202f" not in text and "\t" not in text and "  " not in text:
        return text
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    normalized: list[str] = []
    for line in text.split("\n"):
        match = re.match(r"^[ \t\u3000]*", line)
        prefix = match.group(0) if match else ""
        body = line[len(prefix):]
        normalized.append(prefix + re.sub(r"[ \t]{2,}", " ", body))
    return "\n".join(normalized)


def fix_cjk_spacing(text: str) -> str:
    if " " not in text and "\t" not in text:
        return text
    text = re.sub(r"(?<=[\u3400-\u9fff])[ \t]+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])[ \t]+([，。！？；：、）】》〉])", r"\1", text)
    text = re.sub(r"([（【《〈])[ \t]+(?=[\u3400-\u9fff])", r"\1", text)
    return text


def fullwidth_to_halfwidth(text: str) -> str:
    converted: list[str] = []
    for char in text:
        code = ord(char)
        if code == 0x3000:
            converted.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            converted.append(chr(code - 0xFEE0))
        else:
            converted.append(char)
    return "".join(converted)


def halfwidth_to_fullwidth(text: str) -> str:
    converted: list[str] = []
    for char in text:
        code = ord(char)
        if char == " ":
            converted.append("\u3000")
        elif 0x21 <= code <= 0x7E:
            converted.append(chr(code + 0xFEE0))
        else:
            converted.append(char)
    return "".join(converted)


def convert_chinese(text: str, mode: str) -> tuple[str, str | None]:
    if mode not in {"t2s", "s2t"}:
        return text, None
    try:
        from opencc import OpenCC
    except Exception:
        return text, "opencc_unavailable"
    config = "t2s" if mode == "t2s" else "s2t"
    return OpenCC(config).convert(text), None


def normalize_punctuation(text: str, mode: str) -> str:
    if mode == "ascii":
        table = str.maketrans({
            "，": ",", "。": ".", "；": ";", "：": ":", "！": "!", "？": "?",
            "（": "(", "）": ")", "【": "[", "】": "]", "“": '"', "”": '"',
            "‘": "'", "’": "'", "—": "-", "–": "-", "…": "...",
        })
        return text.translate(table)
    if mode == "cjk":
        replacements = {",": "，", ".": "。", ";": "；", ":": "：", "!": "！", "?": "？"}
        for source, target in replacements.items():
            text = re.sub(
                rf"(?:(?<=[\u3400-\u9fff]){re.escape(source)}|{re.escape(source)}(?=[\u3400-\u9fff]))",
                target,
                text,
            )
        return text
    return text


def normalize_repeated_punctuation(text: str) -> str:
    return re.sub(r"([!?！？。,.，、；;：:])\1{2,}", r"\1\1", text)


def repair_hyphenated_linebreaks(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        left, right = match.group(1), match.group(2)
        if len(right) <= 3:
            return f"{left}- {right}"
        return f"{left}{right}"

    return re.sub(r"([A-Za-z]{3,})-\n([a-z]{2,})", repl, text)


def is_abnormal_symbol_line(line: str, threshold: float = 0.65, min_length: int = 8) -> bool:
    stripped = line.strip()
    if len(stripped) < min_length:
        return False
    content_chars = len(ALNUM_CJK_RE.findall(stripped))
    return 1 - (content_chars / max(len(stripped), 1)) >= threshold


def _dedupe_paragraphs(text: str) -> tuple[str, int]:
    paragraphs = re.split(r"\n\s*\n", text)
    seen: set[str] = set()
    result: list[str] = []
    removed = 0
    for paragraph in paragraphs:
        key = re.sub(r"\s+", " ", paragraph).strip()
        if key and key in seen:
            removed += 1
            continue
        result.append(paragraph.strip("\n"))
        if key:
            seen.add(key)
    return "\n\n".join(result), removed


def process_lines(
    text: str,
    options: CleanOptions,
    abnormal_symbol_ratio: float,
    min_line_length: int,
) -> tuple[str, list[str]]:
    changes: list[str] = []
    lines = text.split("\n")

    if options.trim_lines:
        if not options.paragraph_indent_enabled or options.paragraph_indent_mode == "keep":
            updated = [line.rstrip() for line in lines]
        else:
            updated = [line.strip() for line in lines]
        if updated != lines:
            changes.append("trim_lines")
        lines = updated

    if options.remove_abnormal_symbol_lines:
        before = len(lines)
        lines = [line for line in lines if not is_abnormal_symbol_line(line, abnormal_symbol_ratio, min_line_length)]
        removed = before - len(lines)
        if removed:
            changes.append(f"remove_abnormal_symbol_lines:{removed}")

    if options.remove_repeated_short_lines:
        normalized = [" ".join(line.split()) for line in lines]
        counts = Counter(line for line in normalized if 0 < len(line) <= 40)
        seen: set[str] = set()
        filtered: list[str] = []
        removed = 0
        for line, key in zip(lines, normalized):
            if key and counts[key] >= 3 and key in seen:
                removed += 1
                continue
            filtered.append(line)
            if key and counts[key] >= 3:
                seen.add(key)
        if removed:
            changes.append(f"remove_repeated_short_lines:{removed}")
        lines = filtered

    if options.remove_empty_lines:
        before = len(lines)
        lines = [line for line in lines if not is_effectively_blank_line(line)]
        removed = before - len(lines)
        if removed:
            changes.append(f"remove_empty_lines:{removed}")
    elif options.collapse_blank_lines:
        collapsed: list[str] = []
        blank_seen = False
        for line in lines:
            if not is_effectively_blank_line(line):
                collapsed.append(line)
                blank_seen = False
            elif not blank_seen:
                collapsed.append("")
                blank_seen = True
        if collapsed != lines:
            changes.append("collapse_blank_lines")
        lines = collapsed

    if options.dedupe_adjacent_lines:
        deduped: list[str] = []
        last: str | None = None
        removed = 0
        for line in lines:
            key = " ".join(line.split())
            if key and key == last:
                removed += 1
                continue
            deduped.append(line)
            last = key
        if removed:
            changes.append(f"dedupe_adjacent_lines:{removed}")
        lines = deduped

    if options.dedupe_all_lines:
        seen: set[str] = set()
        deduped = []
        removed = 0
        for line in lines:
            key = " ".join(line.split())
            if key and key in seen:
                removed += 1
                continue
            deduped.append(line)
            if key:
                seen.add(key)
        if removed:
            changes.append(f"dedupe_all_lines:{removed}")
        lines = deduped

    return "\n".join(lines), changes


def paragraph_reflow(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    reflowed: list[str] = []
    structured_line = re.compile(r"^\s*(?:[-*+#>]|\d+[.)]|\|)|\t| {4}")
    for paragraph in paragraphs:
        raw_lines = [line.strip() for line in paragraph.split("\n") if line.strip()]
        if not raw_lines:
            continue
        if any(structured_line.match(line) for line in paragraph.split("\n") if line.strip()):
            reflowed.append("\n".join(raw_lines))
            continue
        merged = raw_lines[0]
        for line in raw_lines[1:]:
            if CJK_RE.search(merged[-1:]) or CJK_RE.search(line[:1]):
                merged += line
            else:
                merged += " " + line
        reflowed.append(merged)
    return "\n\n".join(reflowed)


def normalize_paragraph_indents(text: str, mode: str) -> str:
    if mode == "strip":
        return re.sub(r"(?m)^[ \t\u3000]+", "", text)
    if mode == "cjk_2":
        paragraphs = re.split(r"(\n\s*\n)", text)
        for index in range(0, len(paragraphs), 2):
            if paragraphs[index].strip():
                paragraphs[index] = "\u3000\u3000" + re.sub(r"^[ \t\u3000]+", "", paragraphs[index])
        return "".join(paragraphs)
    return text


def regex_flags(flag_text: str) -> int:
    flags = 0
    lowered = flag_text.lower()
    if "i" in lowered:
        flags |= re.IGNORECASE
    if "m" in lowered:
        flags |= re.MULTILINE
    if "s" in lowered:
        flags |= re.DOTALL
    return flags


def apply_regex_rules(text: str, rules: list[RegexRule]) -> tuple[str, list[str], list[str]]:
    applied: list[str] = []
    warnings: list[str] = []
    for rule in rules:
        if not rule.enabled or not rule.pattern:
            continue
        try:
            updated, count = re.subn(rule.pattern, rule.replacement, text, flags=regex_flags(rule.flags))
            if count:
                applied.append(f"{rule.key}:{count}")
            text = updated
        except re.error as exc:
            warnings.append(f"regex_error:{rule.key}:{exc}")
    return text, applied, warnings


def _apply_transform(text: str, transform, change_key: str, changes: list[str]) -> str:
    updated = transform(text)
    if updated != text:
        changes.append(change_key)
    return updated


def clean_text(
    text: str,
    options: CleanOptions,
    regex_rules: list[RegexRule] | None = None,
    abnormal_symbol_ratio: float = 0.65,
    min_line_length_for_symbol_check: int = 8,
) -> tuple[str, CleanResult]:
    original = text
    changes: list[str] = []
    warnings: list[str] = []
    regex_rules = regex_rules or []

    if options.normalize_newlines:
        text = _apply_transform(text, normalize_newlines, "normalize_newlines", changes)
    if options.strip_bom:
        text = _apply_transform(text, strip_bom, "strip_bom", changes)
    if options.unicode_normalization_enabled and options.unicode_normalization in {"NFC", "NFKC", "NFD", "NFKD"}:
        text = _apply_transform(
            text,
            lambda value: unicodedata.normalize(options.unicode_normalization, value),
            "unicode_normalization",
            changes,
        )
    if options.fix_mojibake:
        try:
            from ftfy import fix_text

            text = _apply_transform(text, fix_text, "fix_mojibake", changes)
        except Exception:
            warnings.append("ftfy_unavailable")
    if options.remove_control_chars:
        text = _apply_transform(text, remove_control_chars, "remove_control_chars", changes)
    if options.remove_zero_width_chars:
        text = _apply_transform(text, remove_zero_width_chars, "remove_zero_width_chars", changes)
    if options.remove_private_use_chars:
        text = _apply_transform(text, lambda value: PRIVATE_USE_RE.sub("", value), "remove_private_use_chars", changes)
    if options.remove_emoji:
        text = _apply_transform(text, remove_emoji, "remove_emoji", changes)
    if options.decode_html_entities:
        text = _apply_transform(text, html.unescape, "decode_html_entities", changes)
    if options.remove_web_code_blocks:
        text = _apply_transform(text, remove_web_code_blocks, "remove_web_code_blocks", changes)
    if options.remove_ocr_placeholders:
        text = _apply_transform(text, lambda value: OCR_PLACEHOLDER_RE.sub("", value), "remove_ocr_placeholders", changes)
    if options.tabs_to_spaces:
        text = _apply_transform(text, lambda value: value.expandtabs(max(1, options.tab_size)), "tabs_to_spaces", changes)
    if options.strip_leading_whitespace:
        text = _apply_transform(
            text,
            lambda value: re.sub(r"(?m)^[ \t\u3000]+", "", value),
            "strip_leading_whitespace",
            changes,
        )
    if options.repair_hyphenated_linebreaks:
        text = _apply_transform(text, repair_hyphenated_linebreaks, "repair_hyphenated_linebreaks", changes)
    if options.normalize_spaces:
        text = _apply_transform(text, normalize_spaces, "normalize_spaces", changes)
    if options.fix_cjk_spacing:
        text = _apply_transform(text, fix_cjk_spacing, "fix_cjk_spacing", changes)
    if options.width_conversion_enabled and options.width_conversion == "full_to_half":
        text = _apply_transform(text, fullwidth_to_halfwidth, "full_to_half", changes)
    elif options.width_conversion_enabled and options.width_conversion == "half_to_full":
        text = _apply_transform(text, halfwidth_to_fullwidth, "half_to_full", changes)
    if options.chinese_conversion_enabled and options.chinese_conversion in {"t2s", "s2t"}:
        converted, warning = convert_chinese(text, options.chinese_conversion)
        if warning:
            warnings.append(warning)
        elif converted != text:
            changes.append(options.chinese_conversion)
            text = converted
    if options.punctuation_mode_enabled and options.punctuation_mode in {"ascii", "cjk"}:
        text = _apply_transform(
            text,
            lambda value: normalize_punctuation(value, options.punctuation_mode),
            f"punctuation_{options.punctuation_mode}",
            changes,
        )
    if options.normalize_repeated_punctuation:
        text = _apply_transform(text, normalize_repeated_punctuation, "normalize_repeated_punctuation", changes)

    text, line_changes = process_lines(text, options, abnormal_symbol_ratio, min_line_length_for_symbol_check)
    changes.extend(line_changes)

    if options.dedupe_paragraphs:
        updated, removed = _dedupe_paragraphs(text)
        if removed:
            changes.append(f"dedupe_paragraphs:{removed}")
        text = updated

    text, applied_rules, regex_warnings = apply_regex_rules(text, regex_rules)
    warnings.extend(regex_warnings)

    if options.paragraph_reflow:
        text = _apply_transform(text, paragraph_reflow, "paragraph_reflow", changes)
    if options.paragraph_indent_enabled and options.paragraph_indent_mode in {"strip", "cjk_2"}:
        text = _apply_transform(
            text,
            lambda value: normalize_paragraph_indents(value, options.paragraph_indent_mode),
            f"paragraph_indent_{options.paragraph_indent_mode}",
            changes,
        )
    if options.collapse_blank_lines and not options.remove_empty_lines:
        text = re.sub(r"\n{3,}", "\n\n", text)
    if options.ensure_final_newline and text and not text.endswith("\n"):
        text += "\n"
        changes.append("ensure_final_newline")

    result = CleanResult(
        original_chars=len(original),
        cleaned_chars=len(text),
        changes=changes,
        warnings=warnings,
        applied_regex_rules=applied_rules,
    )
    return text, result
