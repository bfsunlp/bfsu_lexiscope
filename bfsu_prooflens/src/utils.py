# -*- coding: utf-8 -*-
"""Utility helpers for BFSU ProofLens."""
from __future__ import annotations

import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Iterable

APP_NAME = "BFSU ProofLens"
APP_VERSION = "V1.0.14"
PROJECT_EXT = ".bfsu_prooflens"
SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
SUPPORTED_FILES = SUPPORTED_IMAGES | {".pdf"}


def app_root() -> Path:
    """Return the project/application root in source and PyInstaller modes."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def runtime_root() -> Path:
    """Return a writable runtime root beside the executable or source project."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(relative_path: str) -> str:
    """Resolve resource paths for source and PyInstaller builds."""
    return str(app_root() / relative_path)


def writable_path(relative_path: str) -> Path:
    """Resolve writable paths for config, logs, temp and output."""
    return runtime_root() / relative_path


def ensure_runtime_dirs() -> None:
    for item in ["config", "logs", "temp", "output", "models/rapidocr", "models/easyocr", "assets"]:
        writable_path(item).mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_filename(name: str, replacement: str = "_") -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", replacement, name).strip()
    return name or "untitled"


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def copy_if_missing(src: str | Path, dst: str | Path) -> None:
    src, dst = Path(src), Path(dst)
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def open_folder(path: str | Path) -> None:
    path = Path(path)
    folder = path if path.is_dir() else path.parent
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception:
        pass



# ---------- Tkinter mouse-wheel support ----------
def _wheel_units(event: Any) -> int:
    """Normalize Windows/macOS/Linux wheel events to Tk scroll units."""
    num = getattr(event, "num", None)
    if num == 4:  # Linux wheel up
        return -1
    if num == 5:  # Linux wheel down
        return 1
    delta = int(getattr(event, "delta", 0) or 0)
    if delta == 0:
        return 0
    # Windows commonly reports +/-120 multiples; macOS may report small values.
    if abs(delta) >= 120:
        return int(-delta / 120)
    return -1 if delta > 0 else 1


def enable_mousewheel(widget: Any, yview_widget: Any | None = None, xview_widget: Any | None = None) -> None:
    """Mark a widget area as scrollable by the global mouse-wheel router.

    Tkinter's default mouse-wheel behavior is inconsistent across Windows,
    macOS and Linux, especially when the mouse pointer is over child widgets
    inside a scrollable frame.  This helper stores the actual y/x scrolling
    targets on the container widget.  ``install_global_mousewheel_support``
    then walks up from the event widget to find the nearest scroll target.
    """
    try:
        setattr(widget, "_prooflens_scroll_y", yview_widget or widget)
        setattr(widget, "_prooflens_scroll_x", xview_widget)
    except Exception:
        pass


def install_global_mousewheel_support(root: Any) -> None:
    """Install application-wide wheel routing for registered scrollable areas."""
    if getattr(root, "_prooflens_mousewheel_installed", False):
        return

    def _find_target(widget: Any) -> tuple[Any | None, Any | None]:
        current = widget
        while current is not None:
            y_target = getattr(current, "_prooflens_scroll_y", None)
            x_target = getattr(current, "_prooflens_scroll_x", None)
            if y_target is not None or x_target is not None:
                return y_target, x_target
            try:
                parent_name = current.winfo_parent()
                if not parent_name:
                    break
                current = current._nametowidget(parent_name)
            except Exception:
                break
        return None, None

    def _on_wheel(event: Any):
        y_target, x_target = _find_target(getattr(event, "widget", None))
        if y_target is None and x_target is None:
            return None
        units = _wheel_units(event)
        if units == 0:
            return None
        use_x = bool(x_target) and bool(int(getattr(event, "state", 0) or 0) & 0x0001)
        target = x_target if use_x and x_target is not None else y_target
        if target is None:
            return None
        try:
            if use_x and hasattr(target, "xview_scroll"):
                target.xview_scroll(units, "units")
            elif hasattr(target, "yview_scroll"):
                target.yview_scroll(units, "units")
            else:
                return None
            return "break"
        except Exception:
            return None

    try:
        root.bind_all("<MouseWheel>", _on_wheel, add="+")
        root.bind_all("<Button-4>", _on_wheel, add="+")
        root.bind_all("<Button-5>", _on_wheel, add="+")
        setattr(root, "_prooflens_mousewheel_installed", True)
    except Exception:
        pass

def guess_file_type(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in SUPPORTED_IMAGES:
        return "image"
    return "unknown"




_CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]")


def _is_cjk_char(ch: str) -> bool:
    return bool(ch and _CJK_RE.match(ch[-1]))


def _smart_join_piece(left: str, right: str) -> str:
    """Join two OCR text fragments without blindly forcing line breaks.

    English and other alphabetic scripts normally need a space between wrapped
    lines; CJK scripts normally do not. Hyphenated line endings are repaired.
    """
    left = str(left or "").rstrip()
    right = str(right or "").lstrip()
    if not left:
        return right
    if not right:
        return left
    if left.endswith("-") and right and right[0].isalpha():
        return left[:-1] + right
    if _is_cjk_char(left[-1]) or _is_cjk_char(right[0]):
        return left + right
    if left[-1] in "([{《〈“‘\"'" or right[0] in ",.;:!?)]}，。；：！？、》〉”’\"'":
        return left + right
    return left + " " + right


def smart_join_text_lines(lines: Iterable[str], paragraph_breaks: Iterable[bool] | None = None) -> str:
    """Reconstruct paragraph-like text from OCR lines.

    ``paragraph_breaks`` is an optional iterable parallel to ``lines``.  A true
    value before a line starts a new paragraph.  Without it, the function simply
    joins all non-empty lines into one paragraph using script-aware spacing.
    """
    clean = [str(x).strip() for x in lines if str(x).strip()]
    if not clean:
        return ""
    breaks = list(paragraph_breaks or [False] * len(clean))
    paras: list[str] = []
    cur = ""
    for idx, line in enumerate(clean):
        start_new = bool(breaks[idx]) if idx < len(breaks) else False
        if start_new and cur:
            paras.append(cur.strip())
            cur = line
        else:
            cur = _smart_join_piece(cur, line)
    if cur.strip():
        paras.append(cur.strip())
    return "\n\n".join(paras)


def _block_bbox_stats(block: Any) -> tuple[float, float, float, float, float, float] | None:
    bbox = getattr(block, "bbox", None)
    if bbox is None and isinstance(block, dict):
        bbox = block.get("bbox")
    if not bbox:
        return None
    try:
        # Handle either four-point polygons or [x1, y1, x2, y2].
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4 and all(not isinstance(v, (list, tuple)) for v in bbox):
            x1, y1, x2, y2 = [float(v) for v in bbox]
            xs = [x1, x2]
            ys = [y1, y2]
        else:
            xs = [float(p[0]) for p in bbox if len(p) >= 2]
            ys = [float(p[1]) for p in bbox if len(p) >= 2]
        if not xs or not ys:
            return None
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        height = max(1.0, y_max - y_min)
        cy = (y_min + y_max) / 2.0
        return x_min, y_min, x_max, y_max, cy, height
    except Exception:
        return None


def reconstruct_text_from_blocks(blocks: Iterable[Any], mode: str = "paragraph") -> str:
    """Build readable text from OCR blocks.

    Modes:
    - ``line``: preserve OCR line/block breaks.
    - ``paragraph``: group blocks into lines and merge wrapped lines into paragraphs.

    This is intentionally conservative: it improves text-PDF and article scans by
    avoiding one OCR line per editor line, while still preserving paragraph breaks
    when vertical gaps indicate a new paragraph.
    """
    items = list(blocks or [])
    if not items:
        return ""
    lines_fallback = [getattr(b, "text", "") if not isinstance(b, dict) else b.get("text", "") for b in items]
    if str(mode or "paragraph").lower() == "line":
        return flatten_text(lines_fallback)

    enriched: list[tuple[Any, tuple[float, float, float, float, float, float]]] = []
    for b in items:
        txt = getattr(b, "text", "") if not isinstance(b, dict) else b.get("text", "")
        if not str(txt).strip():
            continue
        stats = _block_bbox_stats(b)
        if stats is None:
            return smart_join_text_lines(lines_fallback)
        enriched.append((b, stats))
    if not enriched:
        return ""

    heights = sorted(s[5] for _, s in enriched)
    median_h = heights[len(heights)//2] if heights else 12.0
    line_tol = max(6.0, median_h * 0.65)
    enriched.sort(key=lambda item: (item[1][4], item[1][0]))

    line_groups: list[list[tuple[Any, tuple[float, float, float, float, float, float]]]] = []
    for b, stats in enriched:
        cy = stats[4]
        if not line_groups:
            line_groups.append([(b, stats)])
            continue
        last = line_groups[-1]
        avg_cy = sum(x[1][4] for x in last) / len(last)
        if abs(cy - avg_cy) <= line_tol:
            last.append((b, stats))
        else:
            line_groups.append([(b, stats)])

    line_records: list[dict[str, Any]] = []
    for group in line_groups:
        group.sort(key=lambda item: item[1][0])
        text_line = ""
        for b, _stats in group:
            txt = getattr(b, "text", "") if not isinstance(b, dict) else b.get("text", "")
            text_line = _smart_join_piece(text_line, str(txt).strip())
        xs = [g[1][0] for g in group]
        ymins = [g[1][1] for g in group]
        ymaxs = [g[1][3] for g in group]
        line_records.append({
            "text": text_line.strip(),
            "x_min": min(xs or [0.0]),
            "y_min": min(ymins or [0.0]),
            "y_max": max(ymaxs or [0.0]),
            "height": max(ymaxs or [0.0]) - min(ymins or [0.0]),
        })
    line_records = [x for x in line_records if x["text"]]
    if not line_records:
        return ""

    text_lines = [x["text"] for x in line_records]
    breaks = [False] * len(line_records)
    if len(line_records) > 1:
        heights2 = sorted(max(1.0, x["height"]) for x in line_records)
        med_line_h = heights2[len(heights2)//2]
        lefts = sorted(x["x_min"] for x in line_records)
        typical_left = lefts[min(len(lefts)-1, max(0, len(lefts)//5))]
        for i in range(1, len(line_records)):
            prev = line_records[i-1]
            cur = line_records[i]
            gap = cur["y_min"] - prev["y_max"]
            indent_jump = cur["x_min"] - typical_left
            prev_text = prev["text"].rstrip()
            # A clear vertical gap or a strong first-line indentation after a
            # sentence boundary starts a new paragraph.  Otherwise wrapped lines
            # are merged into the same paragraph.
            if gap > med_line_h * 0.85:
                breaks[i] = True
            elif indent_jump > med_line_h * 2.5 and (not prev_text.endswith("-") and (prev_text.endswith(tuple(".?!。！？:：")) or len(prev_text) < 60)):
                breaks[i] = True
    return smart_join_text_lines(text_lines, breaks)


def flatten_text(lines: Iterable[str]) -> str:
    return "\n".join(str(x).rstrip() for x in lines if str(x).strip())


def is_dependency_available(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False
