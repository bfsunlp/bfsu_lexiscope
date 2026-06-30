# -*- coding: utf-8 -*-
"""OCR backend abstractions."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class OCRBlock:
    text: str
    confidence: float = 0.0
    bbox: list[list[float]] | None = None
    reading_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OCRResult:
    text: str
    blocks: list[OCRBlock]
    engine: str = "unknown"
    language: str = ""
    elapsed_seconds: float = 0.0
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "blocks": [b.to_dict() for b in self.blocks],
            "engine": self.engine,
            "language": self.language,
            "elapsed_seconds": self.elapsed_seconds,
            "raw": self.raw,
        }


class OCRBackend:
    name = "base"

    def recognize(self, image_path: str, options: dict | None = None) -> OCRResult:
        raise NotImplementedError
