from __future__ import annotations

from .cleaner import clean_text
from .models import CleanOptions, CleanResult, RegexRule


def clean_text_job(
    index: int,
    text: str,
    options: CleanOptions,
    rules: list[RegexRule],
    abnormal_symbol_ratio: float,
    min_line_length_for_symbol_check: int,
) -> tuple[int, str, CleanResult]:
    cleaned, result = clean_text(
        text,
        options,
        rules,
        abnormal_symbol_ratio,
        min_line_length_for_symbol_check,
    )
    return index, cleaned, result
