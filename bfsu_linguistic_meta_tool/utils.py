"""General utility functions."""

from __future__ import annotations

import csv
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


APP_NAME = "Linguistic Metadata Tool"
APP_VERSION = "1.0.0"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def make_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def slugify(text: str, fallback: str = "field") -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_\-]", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def parse_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是", "真"}


def bool_to_str(value: bool) -> str:
    return "true" if value else "false"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def make_backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Pretty-print XML by adding indentation in-place."""
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():  # type: ignore[name-defined]
            child.tail = i  # type: ignore[name-defined]
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def safe_read_text(path: Path, encodings: tuple[str, ...] = ("utf-8", "utf-8-sig", "gb18030")) -> str:
    last_error: Exception | None = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"Unable to read {path}: {last_error}")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
