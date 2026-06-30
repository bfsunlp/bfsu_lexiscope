# -*- coding: utf-8 -*-
"""Process-safe workers for importing files and rendering PDF pages.

The GUI starts these workers in a separate Python process and receives progress
messages through a multiprocessing queue. This is more reliable than doing PDF
rendering in a background thread because PyMuPDF can still make the Tkinter main
thread appear unresponsive on some Windows machines while heavy page rendering
is running.
"""
from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from .file_loader import load_file_to_pages


def import_files_process_worker(payload: dict[str, Any], progress_queue: Any) -> None:
    """Import files in a child process and stream serializable progress events."""
    try:
        selected_paths = [str(p) for p in payload.get("paths", [])]
        temp_root = str(payload.get("temp_root") or "temp")
        dpi = int(payload.get("dpi") or 200)
        preview_max_side = int(payload.get("preview_max_side") or 1800)
        imported_entries: list[dict[str, Any]] = []
        errors: list[str] = []
        total = len(selected_paths)

        for file_index, path in enumerate(selected_paths, start=1):
            file_name = Path(path).name
            progress_queue.put({
                "kind": "progress",
                "payload": {
                    "stage": "file_start",
                    "file": file_name,
                    "file_index": file_index,
                    "file_total": total,
                    "path": path,
                },
            })

            def file_progress(info: dict[str, Any]) -> None:
                data = dict(info)
                data.setdefault("file", file_name)
                data["file_index"] = file_index
                data["file_total"] = total
                progress_queue.put({"kind": "progress", "payload": data})

            try:
                entry = load_file_to_pages(
                    path,
                    temp_root,
                    dpi=dpi,
                    progress_callback=file_progress,
                    preview_max_side=preview_max_side,
                )
                imported_entries.append(entry)
                progress_queue.put({
                    "kind": "progress",
                    "payload": {
                        "stage": "file_done",
                        "file": file_name,
                        "file_index": file_index,
                        "file_total": total,
                        "path": path,
                        "pages": len(entry.get("pages", [])),
                    },
                })
            except Exception as exc:
                err = f"{path}: {exc}"
                errors.append(err)
                progress_queue.put({
                    "kind": "progress",
                    "payload": {
                        "stage": "file_error",
                        "file": file_name,
                        "file_index": file_index,
                        "file_total": total,
                        "path": path,
                        "error": str(exc),
                    },
                })

        progress_queue.put({
            "kind": "result",
            "payload": {"entries": imported_entries, "errors": errors, "count": len(imported_entries)},
        })
    except Exception as exc:
        progress_queue.put({
            "kind": "error",
            "payload": {"exception": str(exc), "traceback": traceback.format_exc()},
        })
