from __future__ import annotations

import difflib
import ctypes
import sys
import tkinter as tk
from typing import Protocol
from dataclasses import dataclass


def locate_fragment_span(text: str, fragment: str, occurrence: int = 1) -> tuple[int, int] | None:
    if not fragment or occurrence < 1:
        return None
    start = -1
    cursor = 0
    for _ in range(occurrence):
        start = text.find(fragment, cursor)
        if start < 0:
            return None
        cursor = start + len(fragment)
    return start, start + len(fragment)


def fragment_line_numbers(text: str, fragment: str, occurrence: int = 1) -> list[int]:
    span = locate_fragment_span(text, fragment, occurrence)
    if span is None:
        return []
    start, end = span
    first = text.count("\n", 0, start) + 1
    last_offset = max(start, end - 1)
    last = text.count("\n", 0, last_offset) + 1
    return list(range(first, last + 1))


def format_line_numbers(lines: list[int]) -> str:
    if not lines:
        return "—"
    if len(lines) <= 4:
        return ", ".join(str(line) for line in lines)
    return f"{lines[0]}–{lines[-1]}"


@dataclass(frozen=True)
class LineDiffRow:
    change: str
    original_line: int | None
    current_line: int | None
    original_text: str
    current_text: str


@dataclass(frozen=True)
class TextExcerpt:
    text: str
    first_line: int
    truncated: bool


def _first_character_difference(before: str, after: str) -> tuple[int, int]:
    limit = min(len(before), len(after))
    block = 4096
    cursor = 0
    while cursor + block <= limit and before[cursor:cursor + block] == after[cursor:cursor + block]:
        cursor += block
    while cursor < limit and before[cursor] == after[cursor]:
        cursor += 1
    return min(cursor, len(before)), min(cursor, len(after))


def first_line_difference(before: str, after: str) -> tuple[int, int, int, int] | None:
    """Return zero-based line/column locations for the first visible difference.

    Newline-style-only changes are intentionally ignored because they cannot be
    distinguished in a Tk text editor. The caller can still report them in the
    task summary.
    """
    if before == after:
        return None
    original = before.splitlines()
    current = after.splitlines()
    if original == current:
        return None
    matcher = difflib.SequenceMatcher(
        a=original,
        b=current,
        autojunk=max(len(original), len(current)) > 4000,
    )
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_line = min(i1, max(0, len(original) - 1))
        new_line = min(j1, max(0, len(current) - 1))
        old_value = original[old_line] if i1 < i2 and original else ""
        new_value = current[new_line] if j1 < j2 and current else ""
        old_column, new_column = _first_character_difference(old_value, new_value)
        return old_line, new_line, old_column, new_column
    return None


def excerpt_around_line(
    text: str,
    focus_line: int,
    max_chars: int,
    focus_column: int = 0,
    context_lines: int = 8,
) -> TextExcerpt:
    """Build a bounded line-aware editor excerpt around a zero-based line."""
    budget = max(1000, int(max_chars))
    lines = text.splitlines(keepends=True)
    if not lines:
        return TextExcerpt(text[:budget], 1, len(text) > budget)
    focus = min(len(lines) - 1, max(0, int(focus_line)))
    center = lines[focus]
    if len(center) > budget:
        start_column = min(max(0, focus_column - budget // 3), max(0, len(center) - budget))
        end_column = min(len(center), start_column + budget)
        excerpt = center[start_column:end_column]
        if start_column:
            excerpt = "…" + excerpt[1:]
        if end_column < len(center) and excerpt:
            excerpt = excerpt[:-1] + "…"
        return TextExcerpt(excerpt, focus + 1, True)

    start = focus
    end = focus + 1
    total = len(center)
    for _ in range(max(0, context_lines)):
        changed = False
        if start > 0 and total + len(lines[start - 1]) <= budget:
            start -= 1
            total += len(lines[start])
            changed = True
        if end < len(lines) and total + len(lines[end]) <= budget:
            total += len(lines[end])
            end += 1
            changed = True
        if not changed:
            break
    return TextExcerpt("".join(lines[start:end]), start + 1, start > 0 or end < len(lines))


def build_line_diff_rows(
    before: str,
    after: str,
    max_rows: int = 5000,
    original_start_line: int = 1,
    current_start_line: int = 1,
) -> list[LineDiffRow]:
    if before == after:
        return []
    original = before.splitlines()
    current = after.splitlines()
    matcher = difflib.SequenceMatcher(
        a=original,
        b=current,
        autojunk=max(len(original), len(current)) > 4000,
    )
    rows: list[LineDiffRow] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        length = max(i2 - i1, j2 - j1)
        for offset in range(length):
            old_index = i1 + offset
            new_index = j1 + offset
            old_exists = old_index < i2
            new_exists = new_index < j2
            rows.append(
                LineDiffRow(
                    change=tag,
                    original_line=(old_index + original_start_line) if old_exists else (i1 + original_start_line - 1 if i1 > 0 else original_start_line),
                    current_line=(new_index + current_start_line) if new_exists else None,
                    original_text=original[old_index] if old_exists else "",
                    current_text=current[new_index] if new_exists else "",
                )
            )
            if len(rows) >= max_rows:
                return rows
    return rows


class TextWidgetProtocol(Protocol):
    def winfo_exists(self) -> int: ...
    def index(self, index: str) -> str: ...
    def dlineinfo(self, index: str) -> tuple[int, int, int, int, int] | None: ...
    def cget(self, key: str) -> object: ...
    def logical_line_number(self, displayed_line: int) -> int: ...
    def viewport_y_offset(self) -> int: ...
    def viewport_height(self) -> int: ...


class TextLineNumbers(tk.Canvas):
    """A lightweight logical-line gutter attached to a Tk Text widget."""

    def __init__(self, master: tk.Misc, text_widget: TextWidgetProtocol, **kwargs: object) -> None:
        self.gutter_width = int(kwargs.pop("width", 48))
        super().__init__(master, width=self.gutter_width, highlightthickness=0, borderwidth=0, background="#edf1f3", **kwargs)
        self.text_widget = text_widget
        self._redraw_after_id: str | None = None
        self._last_scale: float | None = None

    def redraw(self, _event=None) -> None:
        if not self.winfo_exists() or not self.text_widget.winfo_exists():
            return
        scale = self._last_scale
        if scale is None:
            scale = 1.0
            if sys.platform.startswith("win"):
                try:
                    dpi = int(ctypes.windll.user32.GetDpiForWindow(int(self.winfo_toplevel().winfo_id())))
                    if dpi > 0:
                        scale = min(4.0, max(0.75, dpi / 96.0))
                except (AttributeError, OSError, TypeError, ValueError, tk.TclError):
                    pass
            else:
                try:
                    scale = min(4.0, max(0.75, float(self.winfo_fpixels("1i")) / 96.0))
                except (TypeError, ValueError, tk.TclError):
                    pass
            self._last_scale = scale
        scaled_width = max(40, round(self.gutter_width * scale))
        if int(float(self.cget("width"))) != scaled_width:
            self.configure(width=scaled_width)
        self.delete("all")
        viewport_offset = self.text_widget.viewport_y_offset()
        viewport_height = max(1, self.text_widget.viewport_height())
        first_line = int(self.text_widget.index("@0,0").split(".")[0])
        last_line = int(self.text_widget.index(f"@0,{viewport_height}").split(".")[0])
        # Query each logical line's true first display row. If the first visible
        # row is only a wrapped continuation, dlineinfo("N.0") is not visible
        # and no drifting line number is drawn for that continuation.
        for displayed_line in range(first_line, last_line + 1):
            info = self.text_widget.dlineinfo(f"{displayed_line}.0")
            if info is not None:
                y = viewport_offset + info[1]
                self.create_text(
                    scaled_width - max(5, round(6 * scale)),
                    y,
                    anchor=tk.NE,
                    text=str(self.text_widget.logical_line_number(displayed_line)),
                    fill="#68777d",
                    font=(self.text_widget.native_font() if hasattr(self.text_widget, "native_font") else self.text_widget.cget("font")),
                )

    def schedule_redraw(self, _event=None) -> None:
        if self._redraw_after_id is not None:
            return
        def run() -> None:
            self._redraw_after_id = None
            self.redraw()
        try:
            self._redraw_after_id = self.after_idle(run)
        except tk.TclError:
            pass
