from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TextFile:
    path: Path
    original_text: str
    encoding: str = "utf-8"
    confidence: float = 0.0
    source_root: Path | None = None
    cleaned_text: str = ""
    status: str = "pending"
    warnings: list[str] = field(default_factory=list)
    output_path: Path | None = None
    has_working_text: bool = False
    dirty: bool = False
    target_encoding: str | None = None
    output_suffix_key: str = "clean_suffix"

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def relative_path(self) -> Path:
        if self.source_root:
            try:
                return self.path.relative_to(self.source_root)
            except ValueError:
                pass
        return Path(self.path.name)

    @property
    def active_text(self) -> str:
        return self.cleaned_text if self.has_result else self.original_text

    @property
    def has_result(self) -> bool:
        return self.has_working_text or self.status in {
            "rule_cleaned",
            "ai_cleaned",
            "ai_reviewed",
            "manual",
            "transcoded",
        }

    def set_working_text(self, text: str, status: str, suffix_key: str = "clean_suffix") -> None:
        self.cleaned_text = text
        self.has_working_text = True
        self.status = status
        self.dirty = True
        self.output_suffix_key = suffix_key

    def prepare_transcode(self, encoding: str) -> None:
        self.cleaned_text = self.active_text
        self.has_working_text = True
        self.target_encoding = encoding
        self.output_suffix_key = "converted_suffix"
        self.status = "transcoded"
        self.dirty = True

    def reset_working_state(self, dirty: bool = True) -> None:
        self.cleaned_text = ""
        self.has_working_text = False
        self.status = "pending"
        self.output_path = None
        self.target_encoding = None
        self.output_suffix_key = "clean_suffix"
        self.dirty = dirty

    def mark_saved(self, path: Path) -> None:
        self.output_path = path
        self.dirty = False


@dataclass
class CleanOptions:
    normalize_newlines: bool = True
    strip_bom: bool = True
    unicode_normalization_enabled: bool = False
    unicode_normalization: str = "none"
    fix_mojibake: bool = False
    remove_control_chars: bool = True
    remove_zero_width_chars: bool = True
    remove_private_use_chars: bool = False
    remove_emoji: bool = False
    remove_web_code_blocks: bool = False
    decode_html_entities: bool = False
    strip_leading_whitespace: bool = False
    trim_lines: bool = True
    normalize_spaces: bool = True
    tabs_to_spaces: bool = True
    tab_size: int = 4
    fix_cjk_spacing: bool = True
    width_conversion_enabled: bool = False
    width_conversion: str = "none"
    chinese_conversion_enabled: bool = False
    chinese_conversion: str = "none"
    punctuation_mode_enabled: bool = False
    punctuation_mode: str = "none"
    remove_empty_lines: bool = False
    collapse_blank_lines: bool = True
    dedupe_adjacent_lines: bool = True
    dedupe_all_lines: bool = False
    dedupe_paragraphs: bool = False
    remove_abnormal_symbol_lines: bool = True
    remove_repeated_short_lines: bool = False
    remove_ocr_placeholders: bool = False
    normalize_repeated_punctuation: bool = False
    paragraph_reflow: bool = False
    paragraph_indent_enabled: bool = False
    paragraph_indent_mode: str = "keep"
    repair_hyphenated_linebreaks: bool = False
    ensure_final_newline: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CleanOptions":
        defaults = cls()
        values = {
            field_name: data.get(field_name, getattr(defaults, field_name))
            for field_name in cls.__annotations__
        }
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__annotations__}


@dataclass
class RegexRule:
    key: str
    name: str
    pattern: str
    replacement: str = ""
    flags: str = ""
    enabled: bool = False
    description: str = ""
    category: str = "general"
    names: dict[str, str] = field(default_factory=dict)
    descriptions: dict[str, str] = field(default_factory=dict)
    custom: bool = False

    def display_name(self, language: str) -> str:
        return self.names.get(language) or self.names.get("en") or self.name

    def display_description(self, language: str) -> str:
        return self.descriptions.get(language) or self.descriptions.get("en") or self.description


@dataclass
class LLMRule:
    key: str
    name: str
    instruction: str
    enabled: bool = True



@dataclass
class CleanResult:
    original_chars: int
    cleaned_chars: int
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    applied_regex_rules: list[str] = field(default_factory=list)
    ai_used: bool = False
    ai_summary: str = ""


@dataclass
class AISuggestion:
    operation: str
    original_fragment: str
    replacement_fragment: str
    reason: str
    confidence: float = 0.0
    occurrence: int = 1
    status: str = "pending"
    edit_id: str = ""
    chunk_id: str = ""
    source_hash: str = ""
    start_line: int = 1
    end_line: int = 1
    source_start: int | None = None
    source_end: int | None = None


@dataclass
class AIResult:
    text: str
    completed: bool = False
    suggestions: list[AISuggestion] = field(default_factory=list)
    applied: list[AISuggestion] = field(default_factory=list)
    rejected: list[AISuggestion] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
