from __future__ import annotations

import zlib
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from .models import TextFile


def file_identity(path: Path) -> str:
    try:
        return str(path.resolve()).casefold()
    except OSError:
        return str(path.absolute()).casefold()


@dataclass(frozen=True)
class FileEditState:
    cleaned_text: bytes
    has_working_text: bool
    status: str
    output_path: str
    dirty: bool
    target_encoding: str
    output_suffix_key: str

    @property
    def text(self) -> str:
        return zlib.decompress(self.cleaned_text).decode("utf-8")

    @classmethod
    def capture(cls, item: TextFile) -> "FileEditState":
        return cls(
            cleaned_text=zlib.compress(item.cleaned_text.encode("utf-8"), level=1),
            has_working_text=item.has_working_text,
            status=item.status,
            output_path=str(item.output_path) if item.output_path else "",
            dirty=item.dirty,
            target_encoding=item.target_encoding or "",
            output_suffix_key=item.output_suffix_key,
        )

    def restore(self, item: TextFile) -> None:
        item.cleaned_text = self.text
        item.has_working_text = self.has_working_text
        item.status = self.status
        item.output_path = Path(self.output_path) if self.output_path else None
        item.dirty = self.dirty
        item.target_encoding = self.target_encoding or None
        item.output_suffix_key = self.output_suffix_key


@dataclass(frozen=True)
class HistoryEntry:
    entry_id: int
    label: str
    before: dict[str, FileEditState]
    after: dict[str, FileEditState]


class OperationHistory:
    def __init__(self, limit: int = 50) -> None:
        self.limit = max(1, limit)
        self._undo: deque[HistoryEntry] = deque(maxlen=self.limit)
        self._redo: deque[HistoryEntry] = deque(maxlen=self.limit)
        self._next_id = 1

    @staticmethod
    def capture(files: list[TextFile], indices: list[int]) -> dict[str, FileEditState]:
        return {
            file_identity(files[index].path): FileEditState.capture(files[index])
            for index in indices
            if 0 <= index < len(files)
        }

    def record(
        self,
        label: str,
        before: dict[str, FileEditState],
        after: dict[str, FileEditState],
    ) -> HistoryEntry | None:
        shared = before.keys() & after.keys()
        if not shared or all(before[key] == after[key] for key in shared):
            return None
        entry = HistoryEntry(
            entry_id=self._next_id,
            label=label,
            before={key: before[key] for key in shared},
            after={key: after[key] for key in shared},
        )
        self._next_id += 1
        self._undo.append(entry)
        self._redo.clear()
        return entry

    def peek_undo(self) -> HistoryEntry | None:
        return self._undo[-1] if self._undo else None

    def peek_redo(self) -> HistoryEntry | None:
        return self._redo[-1] if self._redo else None

    def undo(self) -> tuple[HistoryEntry, dict[str, FileEditState]] | None:
        if not self._undo:
            return None
        entry = self._undo.pop()
        self._redo.append(entry)
        return entry, entry.before

    def redo(self) -> tuple[HistoryEntry, dict[str, FileEditState]] | None:
        if not self._redo:
            return None
        entry = self._redo.pop()
        self._undo.append(entry)
        return entry, entry.after

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
