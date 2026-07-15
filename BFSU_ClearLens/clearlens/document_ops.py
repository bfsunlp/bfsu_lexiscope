from __future__ import annotations

def merge_texts(texts: list[str], separator: str = "\n\n") -> str:
    return separator.join(texts)
