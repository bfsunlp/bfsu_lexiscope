from __future__ import annotations

from dataclasses import dataclass, field, asdict, fields, MISSING
from pathlib import Path
from typing import Any, Dict, List
import time
import uuid


def _field_default(cls, name: str):
    for f in fields(cls):
        if f.name == name:
            if f.default is not MISSING:
                return f.default
            if f.default_factory is not MISSING:  # type: ignore[attr-defined]
                return f.default_factory()  # type: ignore[misc]
    return None


@dataclass
class FileRecord:
    file_id: str
    path: str
    filename: str
    lang: str = ""
    file_type: str = ""
    size: int = 0
    created_time: str = ""
    modified_time: str = ""
    char_count: int = 0
    paragraph_count: int = 0
    sentence_count: int = 0
    group_id: str = "set_001"
    sort_order: int = 1
    status: str = "unread"
    note: str = ""
    text: str = ""
    # V1.2.0: file-level alignment columns.  They make one-source-multiple-translations
    # and multilingual projects stable even when two translation columns use the same language.
    alignment_role: str = "target"       # source | target
    role_label: str = "Target 1"
    column_key: str = ""                 # source_zh_sim | target_01_en | target_02_en
    target_index: int = 1
    segmentation_engine: str = ""
    segmentation_model: str = ""
    segmentation_level: str = ""

    @classmethod
    def from_path(
        cls,
        path: str,
        lang: str = "",
        group_id: str = "set_001",
        sort_order: int = 1,
        alignment_role: str = "target",
        role_label: str = "Target 1",
        column_key: str = "",
        target_index: int = 1,
    ) -> "FileRecord":
        p = Path(path)
        stat = p.stat()
        return cls(
            file_id=f"file_{int(time.time()*1000)}_{abs(hash(str(p))) % 1000000}",
            path=str(p),
            filename=p.name,
            lang=lang,
            file_type=p.suffix.lower().lstrip('.'),
            size=stat.st_size,
            created_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime)),
            modified_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
            group_id=group_id,
            sort_order=sort_order,
            alignment_role=alignment_role,
            role_label=role_label,
            column_key=column_key,
            target_index=target_index,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileRecord":
        kwargs = {}
        for f in fields(cls):
            if f.name in data and data.get(f.name) is not None:
                kwargs[f.name] = data.get(f.name)
            else:
                kwargs[f.name] = _field_default(cls, f.name)
        # Legacy projects did not have column_key.  Recreate a stable key.
        if not kwargs.get('column_key'):
            role = kwargs.get('alignment_role') or 'target'
            idx = int(kwargs.get('target_index') or 1)
            lang = kwargs.get('lang') or 'unknown'
            kwargs['column_key'] = f"source_{lang}" if role == 'source' else f"target_{idx:02d}_{lang}"
        return cls(**kwargs)


@dataclass
class Segment:
    seg_id: str
    file_id: str
    lang: str
    text: str
    paragraph_id: int = 0
    sentence_id: int = 0
    char_start: int = 0
    char_end: int = 0
    status: str = "segmented"
    segmenter_engine: str = ""
    segmenter_model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Segment":
        kwargs = {f.name: (data.get(f.name) if data.get(f.name) is not None else _field_default(cls, f.name)) for f in fields(cls)}
        return cls(**kwargs)


@dataclass
class AlignmentUnit:
    row_id: int
    group_id: str
    segments: Dict[str, str] = field(default_factory=dict)  # column_key -> aligned text
    source_ids: List[int] = field(default_factory=list)
    target_ids: Dict[str, List[int]] = field(default_factory=dict)
    similarity: float = 0.0
    similarities: Dict[str, float] = field(default_factory=dict)
    status: str = "needs_review"
    issue_type: str = ""
    note: str = ""
    llm_suggestion: str = ""
    confirmed: bool = False
    source_lang: str = ""
    alignment_level: str = "sentence"  # sentence | paragraph
    positions: Dict[str, List[str]] = field(default_factory=dict)  # column_key -> P/S position tokens
    unit_id: str = field(default_factory=lambda: f"au_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlignmentUnit":
        kwargs = {f.name: (data.get(f.name) if data.get(f.name) is not None else _field_default(cls, f.name)) for f in fields(cls)}
        return cls(**kwargs)


@dataclass
class LLMSuggestion:
    row_id: int
    issue_type: str
    severity: str
    problem: str
    suggested_operation: str
    affected_rows: List[int] = field(default_factory=list)
    confidence: float = 0.0
    status: str = "pending"
    group_id: str = ""
    column_key: str = ""
    reason: str = ""
    anchor_uid: str = ""
    anchor_signature: str = ""
    current_row_id: int = 0
    batch_no: int = 0
    relative_row_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
