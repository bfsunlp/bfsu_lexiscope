# -*- coding: utf-8 -*-
"""Image helper functions."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple


def verify_image(path: str | Path) -> bool:
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def make_preview_image(path: str | Path, max_size: Tuple[int, int] = (900, 900)):
    from PIL import Image  # type: ignore
    img = Image.open(path)
    img.thumbnail(max_size)
    return img


def rotate_image_to_temp(path: str | Path, output_dir: str | Path, degrees: int = 90) -> str:
    from PIL import Image  # type: ignore
    path = Path(path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as img:
        rotated = img.rotate(-degrees, expand=True)
        out_path = out_dir / f"{path.stem}_rot{degrees}{path.suffix or '.png'}"
        rotated.save(out_path)
    return str(out_path)
