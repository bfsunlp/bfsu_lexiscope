# -*- coding: utf-8 -*-
"""Export utilities for BFSU WebLens."""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from .crawl_state import CRAWL_STATE_MARKER, CRAWL_STATE_SHEET, state_to_json

FIELDS = [
    "collected_at", "search_engine", "query", "query_raw", "search_vertical",
    "source_filter", "sort_mode", "site_limit", "date_filter_type", "date_start",
    "date_end", "start_ts", "end_ts", "baidu_gpc", "shard_start", "shard_end",
    "page", "rank", "title", "source", "actual_domain", "published_time",
    "link", "snippet", "search_url", "language_lr", "country_cr",
    "content_status", "content_word_count", "content_quality_score", "content_error",
    "content_extraction_method", "content_cleaning_scheme", "raw_html_path",
    "raw_text_path", "clean_text_path", "metadata_path", "metadata_excel_path"
]


def record_dicts(records: Iterable) -> list[dict]:
    rows = []
    extra_fields = [
        "content_status", "content_word_count", "content_quality_score", "content_error",
        "content_extraction_method", "content_cleaning_scheme", "raw_html_path",
        "raw_text_path", "clean_text_path", "metadata_path", "metadata_excel_path",
    ]
    for rec in records:
        if hasattr(rec, "to_dict"):
            row = rec.to_dict()
            for field in extra_fields:
                if hasattr(rec, field):
                    row[field] = getattr(rec, field)
            rows.append(row)
        elif isinstance(rec, dict):
            rows.append(rec)
    return rows


def export_records(records: Iterable, output_path: str, fmt: str, crawl_state: dict | None = None) -> None:
    """Export records and, when available, the resumable collection checkpoint.

    The checkpoint is intentionally embedded in the same result file so moving
    the result file also moves its resume information.  Ordinary third-party
    files remain fully importable because the importer treats the state as
    optional metadata.
    """
    rows = record_dicts(records)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = fmt.lower().strip().lstrip(".")
    state_json = state_to_json(crawl_state)
    if fmt == "xlsx":
        export_xlsx(rows, path, state_json)
    elif fmt == "csv":
        export_csv(rows, path, state_json)
    elif fmt == "txt":
        export_txt(rows, path, state_json)
    elif fmt == "docx":
        export_docx(rows, path, state_json)
    elif fmt == "xml":
        export_xml(rows, path, state_json)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def export_xlsx(rows: list[dict], path: Path, state_json: str = "") -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "WebLens Results"
    ws.append(FIELDS)
    for row in rows:
        ws.append([row.get(f, "") for f in FIELDS])
    fill = PatternFill("solid", fgColor="17384A")
    font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")
    for idx, field in enumerate(FIELDS, start=1):
        col = get_column_letter(idx)
        if field in {"title", "link", "snippet", "search_url"}:
            width = 60
        elif field.endswith("path") or field in {"baidu_gpc", "query_raw"}:
            width = 45
        elif field in {"collected_at", "published_time", "actual_domain"}:
            width = 22
        else:
            width = 16
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"

    if state_json:
        state_ws = wb.create_sheet(CRAWL_STATE_SHEET)
        state_ws["A1"] = CRAWL_STATE_MARKER
        state_ws["A2"] = state_json
        state_ws.sheet_state = "hidden"
    wb.save(path)


def export_csv(rows: list[dict], path: Path, state_json: str = "") -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for row in rows:
            writer.writerow([row.get(k, "") for k in FIELDS])
        if state_json:
            # A dedicated final metadata row keeps the normal header and result
            # records intact.  WebLens ignores this row as a data record.
            writer.writerow([CRAWL_STATE_MARKER, state_json])


def export_txt(rows: list[dict], path: Path, state_json: str = "") -> None:
    with path.open("w", encoding="utf-8") as f:
        for i, row in enumerate(rows, 1):
            f.write(f"[{i}] {row.get('title','')}\n")
            f.write(f"Time: {row.get('published_time','')} | Source: {row.get('source','')}\n")
            f.write(f"URL: {row.get('link','')}\n")
            f.write(f"Collected: {row.get('collected_at','')} | Shard: {row.get('shard_start','')}~{row.get('shard_end','')} | Page: {row.get('page','')} | Rank: {row.get('rank','')}\n")
            if row.get('snippet'):
                f.write(f"Snippet: {row.get('snippet','')}\n")
            f.write("\n")
        if state_json:
            f.write(f"# {CRAWL_STATE_MARKER} {state_json}\n")


def export_docx(rows: list[dict], path: Path, state_json: str = "") -> None:
    from docx import Document

    doc = Document()
    doc.add_heading("BFSU WebLens Results", level=1)
    for i, row in enumerate(rows, 1):
        doc.add_heading(f"{i}. {row.get('title','')}", level=2)
        p = doc.add_paragraph()
        p.add_run("Time: ").bold = True; p.add_run(str(row.get('published_time','')))
        p = doc.add_paragraph()
        p.add_run("Source: ").bold = True; p.add_run(str(row.get('source','')))
        p = doc.add_paragraph()
        p.add_run("URL: ").bold = True; p.add_run(str(row.get('link','')))
        p = doc.add_paragraph()
        p.add_run("Collected: ").bold = True; p.add_run(str(row.get('collected_at','')))
        if row.get('snippet'):
            doc.add_paragraph(str(row.get('snippet','')))
    if state_json:
        p = doc.add_paragraph()
        run = p.add_run(f"{CRAWL_STATE_MARKER} {state_json}")
        # Keep resume metadata available to WebLens without cluttering a normal
        # human-readable Word export.
        run.font.hidden = True
    doc.save(path)


def export_xml(rows: list[dict], path: Path, state_json: str = "") -> None:
    root = ET.Element("weblens_results")
    if state_json:
        state_node = ET.SubElement(root, "crawl_state")
        state_node.set("marker", CRAWL_STATE_MARKER)
        state_node.text = state_json
    for row in rows:
        item = ET.SubElement(root, "record")
        for field in FIELDS:
            child = ET.SubElement(item, field)
            child.text = str(row.get(field, ""))
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def export_import_template(output_path: str | Path) -> None:
    """Create a simple user-facing URL import template.

    Only the ``link`` column is required.  Optional metadata can be filled when
    available; missing title/source/date values can be supplemented during
    content download.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Import URLs"
    headers = ["link", "title", "source", "published_time"]
    ws.append(headers)
    ws.append(["https://example.com/article", "", "", ""])
    fill = PatternFill("solid", fgColor="C96F32")
    font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")
    widths = [62, 42, 24, 22]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A2"
    wb.save(path)
