# -*- coding: utf-8 -*-
"""Import collected or user-supplied URL lists into BFSU WebLens."""
from __future__ import annotations

import csv
from datetime import datetime
import html
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urlparse

from .collector import SearchRecord, primary_domain, result_source_domain
from .crawl_state import CRAWL_STATE_MARKER, CRAWL_STATE_SHEET, state_from_json

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.I)
HEADER_ALIASES = {
    "link", "url", "网址", "链接", "連結", "final_url",
    "title", "标题", "標題", "source", "来源", "來源",
    "published_time", "published", "date", "发布时间", "發布時間",
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def int_safe(value, default=0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _value(row: dict, *names: str):
    for name in names:
        if name in row and row.get(name) not in (None, ""):
            return row.get(name)
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ""):
            return value
    return ""


def make_record(row: dict, rank: int = 0, *, plain_url: bool = False) -> SearchRecord | None:
    link = str(_value(row, "link", "url", "URL", "网址", "链接", "連結", "final_url") or "").strip()
    if not link or not link.lower().startswith(("http://", "https://")):
        return None
    title = str(_value(row, "title", "Title", "标题", "標題") or "").strip()
    if plain_url and title == link:
        title = ""
    input_source = str(_value(row, "source", "Source", "来源", "來源") or "").strip()
    input_actual_domain = str(_value(row, "actual_domain") or "").strip().lower().lstrip("www.")
    try:
        link_host = (urlparse(link).hostname or "").lower().lstrip("www.")
    except Exception:
        link_host = ""
    link_main_domain = primary_domain(link)
    # Search-engine redirect links do not reveal their destination host.  When a
    # structured import already carries an actual_domain or an old display-URL
    # Source, use that only to recover the main domain; the original source label
    # itself is never preserved at import time.
    actual_domain = link_host if link_main_domain else input_actual_domain
    source_domain = result_source_domain(link, input_actual_domain or input_source)
    rec = SearchRecord(
        collected_at=str(_value(row, "collected_at", "Collected") or now_iso()),
        query=str(_value(row, "query", "Query") or "imported"),
        search_vertical=str(_value(row, "search_vertical", "vertical") or "imported"),
        shard_start=str(_value(row, "shard_start") or ""),
        shard_end=str(_value(row, "shard_end") or ""),
        page=int_safe(_value(row, "page"), 0),
        rank=int_safe(_value(row, "rank"), rank),
        title=title,
        link=link,
        # Import is intentionally URL-first: Source is normalized to the main
        # domain regardless of any source label carried by the input file.
        # Full-text download may later replace it with a reliably detected
        # publication/source name.
        source=source_domain,
        published_time=str(_value(row, "published_time", "Published", "date", "发布时间", "發布時間") or ""),
        snippet=str(_value(row, "snippet", "Snippet") or ""),
        search_url=str(_value(row, "search_url") or ""),
        language_lr=str(_value(row, "language_lr") or ""),
        country_cr=str(_value(row, "country_cr") or ""),
        search_engine=str(_value(row, "search_engine", "engine") or "import"),
        source_filter=str(_value(row, "source_filter", "baidu_source_filter") or ""),
        sort_mode=str(_value(row, "sort_mode", "baidu_sort") or ""),
        site_limit=str(_value(row, "site_limit") or ""),
        actual_domain=actual_domain,
        query_raw=str(_value(row, "query_raw") or ""),
        date_filter_type=str(_value(row, "date_filter_type") or ""),
        date_start=str(_value(row, "date_start") or ""),
        date_end=str(_value(row, "date_end") or ""),
        start_ts=str(_value(row, "start_ts") or ""),
        end_ts=str(_value(row, "end_ts") or ""),
        baidu_gpc=str(_value(row, "baidu_gpc") or ""),
    )
    for field in [
        "content_status", "content_word_count", "content_quality_score", "content_error",
        "content_extraction_method", "content_cleaning_scheme",
        "raw_html_path", "raw_text_path", "clean_text_path", "metadata_path", "metadata_excel_path",
    ]:
        value = _value(row, field)
        if value not in (None, ""):
            setattr(rec, field, value)
    return rec


def dedup_records(records: Iterable[SearchRecord]) -> list[SearchRecord]:
    seen = set()
    out = []
    for r in records:
        key = (r.link or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _looks_like_header(values) -> bool:
    tokens = {str(v or "").strip().lower() for v in values}
    return bool(tokens & {x.lower() for x in HEADER_ALIASES})


def _plain_url_records(values: Iterable, start_rank: int = 1) -> list[SearchRecord]:
    records = []
    rank = start_rank
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        urls = URL_RE.findall(text)
        for url in urls:
            rec = make_record({"link": url.strip(), "title": "", "rank": rank}, rank, plain_url=True)
            if rec:
                records.append(rec)
                rank += 1
    return records


def import_records(path: str | Path) -> list[SearchRecord]:
    """Import records only, preserving the legacy public API."""
    records, _state = import_records_with_state(path)
    return records


def import_records_with_state(path: str | Path) -> tuple[list[SearchRecord], dict | None]:
    """Import result records plus an optional WebLens crawl checkpoint.

    Files created by other tools (or older WebLens versions) simply return
    ``None`` for the state and are imported exactly as ordinary URL/result
    files.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return import_csv(p), _read_csv_crawl_state(p)
    if suffix == ".xlsx":
        return import_xlsx(p), _read_xlsx_crawl_state(p)
    if suffix == ".xml":
        return import_xml(p), _read_xml_crawl_state(p)
    if suffix == ".docx":
        return import_docx(p), _read_docx_crawl_state(p)
    return import_txt(p), _read_txt_crawl_state(p)


def _read_csv_crawl_state(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if row and str(row[0] or "").strip() == CRAWL_STATE_MARKER:
                    return state_from_json(row[1] if len(row) > 1 else "")
    except Exception:
        return None
    return None


def _read_xlsx_crawl_state(path: Path) -> dict | None:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        if CRAWL_STATE_SHEET not in wb.sheetnames:
            return None
        ws = wb[CRAWL_STATE_SHEET]
        if str(ws["A1"].value or "").strip() != CRAWL_STATE_MARKER:
            return None
        return state_from_json(ws["A2"].value)
    except Exception:
        return None


def _read_xml_crawl_state(path: Path) -> dict | None:
    try:
        root = ET.parse(path).getroot()
        node = root.find("./crawl_state")
        if node is None:
            return None
        if str(node.get("marker") or CRAWL_STATE_MARKER).strip() != CRAWL_STATE_MARKER:
            return None
        return state_from_json(node.text or "")
    except Exception:
        return None


def _read_docx_crawl_state(path: Path) -> dict | None:
    try:
        from docx import Document
        doc = Document(path)
        for p in doc.paragraphs:
            text = str(p.text or "").strip()
            if text.startswith(CRAWL_STATE_MARKER):
                return state_from_json(text[len(CRAWL_STATE_MARKER):].strip())
    except Exception:
        return None
    return None


def _read_txt_crawl_state(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return None
    marker = CRAWL_STATE_MARKER
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped.startswith("#"):
            stripped = stripped[1:].strip()
        if stripped.startswith(marker):
            return state_from_json(stripped[len(marker):].strip())
    return None


def import_csv(path: Path) -> list[SearchRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    records = []
    if _looks_like_header(rows[0]):
        headers = [str(x or "").strip() for x in rows[0]]
        for i, values in enumerate(rows[1:], 1):
            if values and str(values[0] or "").strip() == CRAWL_STATE_MARKER:
                continue
            row = {headers[j]: values[j] if j < len(values) else "" for j in range(len(headers))}
            rec = make_record(row, i)
            if rec:
                records.append(rec)
    else:
        records = _plain_url_records((row[0] if row else "" for row in rows))
    return dedup_records(records)


def import_xlsx(path: Path) -> list[SearchRecord]:
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    records = []
    if _looks_like_header(rows[0]):
        headers = [str(x or "").strip() for x in rows[0]]
        for i, values in enumerate(rows[1:], 1):
            row = {headers[j]: values[j] if j < len(values) else "" for j in range(len(headers))}
            rec = make_record(row, i)
            if rec:
                records.append(rec)
    else:
        # User-friendly fallback: a headerless workbook may contain one URL per
        # row in the first column.  The first row is data, not discarded.
        records = _plain_url_records((values[0] if values else "" for values in rows))
    return dedup_records(records)


def import_xml(path: Path) -> list[SearchRecord]:
    records = []
    root = ET.parse(path).getroot()
    for i, elem in enumerate(root.findall(".//record"), 1):
        row = {child.tag: child.text or "" for child in list(elem)}
        rec = make_record(row, i)
        if rec:
            records.append(rec)
    if records:
        return dedup_records(records)
    # A WebLens XML file may legitimately contain only crawl-state metadata and
    # no result records. Never interpret URLs inside that state JSON as result
    # links. Third-party XML without the WebLens marker still keeps the generic
    # URL-extraction fallback.
    state_node = root.find("./crawl_state")
    if state_node is not None and str(state_node.get("marker") or CRAWL_STATE_MARKER).strip() == CRAWL_STATE_MARKER:
        return []
    return import_urls_from_text(path.read_text(encoding="utf-8", errors="ignore"))


def import_docx(path: Path) -> list[SearchRecord]:
    from docx import Document
    doc = Document(path)
    parts = []
    for paragraph in doc.paragraphs:
        text = str(paragraph.text or "")
        if text.strip().startswith(CRAWL_STATE_MARKER):
            continue
        parts.append(text)
    return import_urls_from_text("\n".join(parts))


def import_txt(path: Path) -> list[SearchRecord]:
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    records = []
    current_title = ""
    current_source = ""
    current_time = ""
    rank = 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        marker_text = s[1:].strip() if s.startswith("#") else s
        if marker_text.startswith(CRAWL_STATE_MARKER):
            continue
        # Simplest supported format: exactly one URL per line.
        if re.fullmatch(r"https?://\S+", s, flags=re.I):
            rank += 1
            rec = make_record({"link": s, "title": "", "rank": rank}, rank, plain_url=True)
            if rec:
                records.append(rec)
            continue
        m_title = re.match(r"^\[(\d+)\]\s*(.*)$", s)
        if m_title:
            current_title = m_title.group(2).strip()
            try:
                rank = int(m_title.group(1))
            except Exception:
                rank += 1
            continue
        if s.lower().startswith("time:"):
            parts = [p.strip() for p in s.split("|")]
            if parts:
                current_time = parts[0].split(":", 1)[-1].strip()
            for part in parts:
                if part.lower().startswith("source:"):
                    current_source = part.split(":", 1)[-1].strip()
            continue
        if s.lower().startswith("url:"):
            url = s.split(":", 1)[-1].strip()
            rec = make_record({"link": url, "title": current_title, "source": current_source, "published_time": current_time, "rank": rank or len(records) + 1}, len(records) + 1)
            if rec:
                records.append(rec)
            continue
    if records:
        return dedup_records(records)
    # Remove WebLens checkpoint metadata before the generic URL fallback so
    # page URLs contained inside the JSON cannot become fake imported records.
    fallback_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        marker_text = stripped[1:].strip() if stripped.startswith("#") else stripped
        if marker_text.startswith(CRAWL_STATE_MARKER):
            continue
        fallback_lines.append(line)
    return import_urls_from_text("\n".join(fallback_lines))


def _clean_extracted_url(value: str) -> str:
    """Normalize a URL captured from prose, HTML or Markdown text.

    The parser deliberately keeps query strings/fragments intact, but removes
    punctuation that commonly follows a URL in normal prose. Closing brackets
    are removed only when they are unmatched, so legitimate parentheses inside
    a URL are preserved.
    """
    value = html.unescape(str(value or "")).strip().strip("<>\"'`")
    while value and value[-1] in ".,;:!?，。；：！？、…":
        value = value[:-1]
    pairs = (("(", ")"), ("[", "]"), ("{", "}"))
    changed = True
    while value and changed:
        changed = False
        for left, right in pairs:
            if value.endswith(right) and value.count(right) > value.count(left):
                value = value[:-1]
                changed = True
    # Common Chinese quotation/book-title closers after pasted URLs.
    value = value.rstrip("）】〉》」』")
    return value.strip()


def extract_urls_from_text(text: str) -> list[str]:
    """Extract unique HTTP(S) links from arbitrary pasted text, preserving order."""
    decoded = html.unescape(text or "")
    out: list[str] = []
    seen: set[str] = set()
    for match in URL_RE.finditer(decoded):
        url = _clean_extracted_url(match.group(0))
        if not url.lower().startswith(("http://", "https://")):
            continue
        key = url.strip()
        if key and key not in seen:
            seen.add(key)
            out.append(url)
    return out


def import_urls_from_text(text: str) -> list[SearchRecord]:
    return dedup_records(_plain_url_records(extract_urls_from_text(text or "")))
