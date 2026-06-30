# -*- coding: utf-8 -*-
"""File importing and page rendering."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from .pdf_utils import render_pdf_to_images, extract_pdf_page_texts
from .utils import SUPPORTED_IMAGES, guess_file_type, safe_filename, now_iso

ProgressCallback = Callable[[dict[str, Any]], None]


def _make_preview_image(image_path: str | Path, output_dir: str | Path, max_side: int = 1800) -> str:
    """Create a smaller preview image for the Tkinter canvas.

    OCR continues to use the original rendered/copy image. This prevents the GUI
    from decoding very large PDF page PNGs in the Tk main thread after import.
    """
    source = Path(image_path)
    if max_side <= 0:
        return str(source)
    preview_dir = Path(output_dir) / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{source.stem}_preview.jpg"
    try:
        from PIL import Image  # type: ignore
        with Image.open(source) as img:
            img = img.convert("RGB")
            if max(img.size) > max_side:
                img.thumbnail((max_side, max_side))
            img.save(preview_path, format="JPEG", quality=88, optimize=True)
        return str(preview_path)
    except Exception:
        # Preview generation is a performance optimization, not a hard import
        # requirement. Fall back to the source image if Pillow fails.
        return str(source)


def load_file_to_pages(
    file_path: str | Path,
    temp_root: str | Path,
    dpi: int = 200,
    progress_callback: ProgressCallback | None = None,
    preview_max_side: int = 1800,
) -> dict[str, Any]:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    file_type = guess_file_type(file_path)
    if file_type == "unknown":
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    file_id = f"file_{abs(hash(str(file_path.resolve()))) % 10_000_000}_{int(__import__('time').time())}"
    work_dir = Path(temp_root) / safe_filename(file_path.stem) / file_id
    work_dir.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback({"stage": "start_file", "path": str(file_path), "file_name": file_path.name, "file_type": file_type})

    image_paths: list[str] = []
    embedded_texts: list[str] = []
    if file_type == "pdf":
        try:
            embedded_texts = extract_pdf_page_texts(file_path)
        except Exception:
            embedded_texts = []
        image_paths = render_pdf_to_images(file_path, work_dir, dpi=dpi, progress_callback=progress_callback)
    else:
        # Copy image to temp to keep a stable editable/rendering target.
        dst = work_dir / file_path.name
        shutil.copy2(file_path, dst)
        image_paths = [str(dst)]
        if progress_callback:
            progress_callback({"stage": "copy_image_done", "page": 1, "total": 1, "image_path": str(dst), "path": str(file_path)})

    pages = []
    total_images = len(image_paths)
    for idx, image_path in enumerate(image_paths, start=1):
        if progress_callback:
            progress_callback({"stage": "preview_page_start", "page": idx, "total": total_images, "image_path": str(image_path), "path": str(file_path)})
        preview_path = _make_preview_image(image_path, work_dir, max_side=int(preview_max_side or 1800))
        if progress_callback:
            progress_callback({"stage": "preview_page_done", "page": idx, "total": total_images, "image_path": str(image_path), "preview_path": preview_path, "path": str(file_path)})
        embedded_text = embedded_texts[idx - 1].strip() if idx - 1 < len(embedded_texts) and embedded_texts[idx - 1] else ""
        pages.append({
            "page_no": idx,
            "image_path": image_path,
            "preview_path": preview_path,
            "embedded_text": embedded_text,
            "ocr_text": embedded_text if embedded_text else "",
            "corrected_text": "",
            "final_text": embedded_text if embedded_text else "",
            "ocr_blocks": [],
            "suggestions": [],
            "uncertain_spans": [],
            "warnings": [],
            "layout_notes": "",
            "ocr_backend": "",
            "llm_model": "",
            "ocr_status": "text_layer" if embedded_text else "pending",
            "proofread_status": "pending",
            "ocr_time": 0.0,
            "llm_time": 0.0,
            "timestamp": now_iso(),
        })
    if progress_callback:
        progress_callback({"stage": "file_done", "path": str(file_path), "file_name": file_path.name, "pages": len(pages)})
    return {
        "id": file_id,
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_type": file_type,
        "pages": pages,
        "import_time": now_iso(),
    }
