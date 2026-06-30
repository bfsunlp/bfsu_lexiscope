# -*- coding: utf-8 -*-
"""PDF rendering utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .utils import smart_join_text_lines


ProgressCallback = Callable[[dict[str, Any]], None]


def render_pdf_to_images(
    pdf_path: str | Path,
    output_dir: str | Path,
    dpi: int = 200,
    progress_callback: ProgressCallback | None = None,
) -> list[str]:
    """Render a PDF into PNG page images using PyMuPDF.

    The optional progress callback is intentionally UI-neutral so this function
    can run safely in a background worker thread. It receives dictionaries such
    as {"stage": "render_page", "page": 3, "total": 10, "path": "..."}.
    """
    try:
        import fitz  # type: ignore
    except Exception as exc:
        raise RuntimeError("PyMuPDF is not installed. Please run: python -m pip install pymupdf") from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(str(pdf_path))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[str] = []
    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        if progress_callback:
            progress_callback({"stage": "open_pdf", "page": 0, "total": total_pages, "path": str(pdf_path)})
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for page_index in range(total_pages):
            if progress_callback:
                progress_callback({"stage": "render_page_start", "page": page_index + 1, "total": total_pages, "path": str(pdf_path)})
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out_path = out_dir / f"{pdf_path.stem}_page_{page_index + 1:04d}.png"
            pix.save(str(out_path))
            image_paths.append(str(out_path))
            if progress_callback:
                progress_callback({"stage": "render_page_done", "page": page_index + 1, "total": total_pages, "image_path": str(out_path), "path": str(pdf_path)})
    except Exception as exc:
        raise RuntimeError(f"PDF rendering failed: {exc}") from exc
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
    return image_paths



def extract_pdf_page_texts(pdf_path: str | Path) -> list[str]:
    """Extract embedded text from a text-based PDF page by page.

    The function uses PyMuPDF text blocks rather than the plain line stream so
    paragraphs are usually preserved better for born-digital journal articles.
    """
    try:
        import fitz  # type: ignore
    except Exception as exc:
        raise RuntimeError("PyMuPDF is not installed. Please run: python -m pip install pymupdf") from exc
    texts: list[str] = []
    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            blocks = []
            try:
                raw_blocks = page.get_text("blocks") or []
                for item in raw_blocks:
                    # PyMuPDF blocks: (x0, y0, x1, y1, text, block_no, block_type)
                    if len(item) >= 5 and str(item[4]).strip():
                        blocks.append((float(item[1]), float(item[0]), str(item[4])))
            except Exception:
                blocks = []
            if blocks:
                paras: list[str] = []
                for _y, _x, block_text in sorted(blocks):
                    raw_lines = [line.strip() for line in block_text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
                    if raw_lines:
                        paras.append(smart_join_text_lines(raw_lines))
                texts.append("\n\n".join(x for x in paras if x.strip()).strip())
            else:
                txt = page.get_text("text") or ""
                raw_lines = [line.strip() for line in txt.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
                texts.append(smart_join_text_lines(raw_lines).strip())
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
    return texts
