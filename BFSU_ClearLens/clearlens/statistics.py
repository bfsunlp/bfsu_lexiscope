from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


CJK_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0x20000, 0x2FA1F),
)
LATIN_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")


@dataclass(frozen=True)
class TextStatistics:
    files: int = 0
    total_chars: int = 0
    non_whitespace_chars: int = 0
    cjk_chars: int = 0
    letters: int = 0
    digits: int = 0
    whitespace: int = 0
    punctuation: int = 0
    symbols: int = 0
    latin_words: int = 0
    lines: int = 0
    paragraphs: int = 0
    utf8_bytes: int = 0


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return any(start <= code <= end for start, end in CJK_RANGES)


def calculate_statistics(texts: list[str]) -> TextStatistics:
    joined = "".join(texts)
    whitespace = sum(char.isspace() for char in joined)
    cjk = sum(_is_cjk(char) for char in joined)
    letters = sum(char.isalpha() and not _is_cjk(char) for char in joined)
    digits = sum(char.isdigit() for char in joined)
    punctuation = sum(unicodedata.category(char).startswith("P") for char in joined)
    symbols = sum(unicodedata.category(char).startswith("S") for char in joined)
    lines = sum(text.count("\n") + 1 if text else 0 for text in texts)
    paragraphs = sum(
        len([block for block in re.split(r"\n\s*\n", text.strip()) if block.strip()])
        for text in texts
    )
    return TextStatistics(
        files=len(texts),
        total_chars=len(joined),
        non_whitespace_chars=len(joined) - whitespace,
        cjk_chars=cjk,
        letters=letters,
        digits=digits,
        whitespace=whitespace,
        punctuation=punctuation,
        symbols=symbols,
        latin_words=sum(len(LATIN_WORD_RE.findall(text)) for text in texts),
        lines=lines,
        paragraphs=paragraphs,
        utf8_bytes=len(joined.encode("utf-8")),
    )
