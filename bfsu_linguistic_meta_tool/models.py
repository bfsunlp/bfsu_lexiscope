"""Core data models for the Linguistic Metadata Tool.

The model layer is intentionally GUI-independent.  It describes metadata
schemas, records and relations in a way that can be serialized to XML, CSV,
Excel, or other formats by repository/import/export modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils import make_id, now_iso


DATA_TYPES = [
    "string",
    "integer",
    "float",
    "date",
    "year",
    "boolean",
    "enum",
    "long_text",
    "language_code",
    "file_path",
]

FIELD_LEVELS = [
    "corpus",
    "subcorpus",
    "text",
    "version",
    "file",
    "speaker",
    "segment",
    "alignment",
    "relation",
    "project",
]

CORPUS_TYPES = {
    "monolingual": {"zh": "单语语料库", "en": "Monolingual Corpus"},
    "bilingual_parallel": {"zh": "双语平行语料库", "en": "Bilingual Parallel Corpus"},
    "multilingual_parallel": {"zh": "多语平行语料库", "en": "Multilingual Parallel Corpus"},
    "multiple_translations": {"zh": "一本多译平行语料库", "en": "Multiple Translations Corpus"},
    "comparable": {"zh": "可比语料库", "en": "Comparable Corpus"},
    "learner": {"zh": "学习者语料库", "en": "Learner Corpus"},
    "spoken": {"zh": "口语语料库", "en": "Spoken Corpus"},
}


@dataclass
class MetadataField:
    """Definition of a metadata field in a project schema."""

    field_id: str
    label_zh: str = ""
    label_en: str = ""
    xml_tag: str = ""
    data_type: str = "string"
    required: bool = False
    repeatable: bool = False
    default_value: str = ""
    controlled_values: list[str] = field(default_factory=list)
    description_zh: str = ""
    description_en: str = ""
    example: str = ""
    level: str = "text"
    parent: str = ""
    order: int = 0
    visible: bool = True
    editable: bool = True
    sensitive: bool = False
    validation_rule: str = ""

    def __post_init__(self) -> None:
        if not self.xml_tag:
            self.xml_tag = self.field_id
        if not self.label_zh:
            self.label_zh = self.field_id
        if not self.label_en:
            self.label_en = self.field_id
        if self.data_type not in DATA_TYPES:
            self.data_type = "string"
        if self.level not in FIELD_LEVELS:
            self.level = "text"

    def display_label(self, lang: str = "zh_CN") -> str:
        return self.label_zh if lang.startswith("zh") else self.label_en


@dataclass
class MetadataSchema:
    """Collection of metadata field definitions."""

    schema_id: str = field(default_factory=lambda: make_id("schema"))
    schema_name: str = "Default Metadata Schema"
    schema_version: str = "1.0"
    fields: list[MetadataField] = field(default_factory=list)

    def sorted_fields(self, visible_only: bool = False) -> list[MetadataField]:
        fields = [f for f in self.fields if (f.visible or not visible_only)]
        return sorted(fields, key=lambda f: (f.order, f.field_id))

    def field_ids(self) -> list[str]:
        return [f.field_id for f in self.sorted_fields()]

    def get_field(self, field_id: str) -> MetadataField | None:
        for f in self.fields:
            if f.field_id == field_id:
                return f
        return None

    def get_field_by_xml_tag(self, xml_tag: str) -> MetadataField | None:
        for f in self.fields:
            if f.xml_tag == xml_tag:
                return f
        return None

    def add_field(self, metadata_field: MetadataField, replace: bool = False) -> None:
        existing = self.get_field(metadata_field.field_id)
        if existing:
            if not replace:
                raise ValueError(f"Field already exists: {metadata_field.field_id}")
            self.fields = [metadata_field if f.field_id == metadata_field.field_id else f for f in self.fields]
        else:
            if metadata_field.order <= 0:
                metadata_field.order = len(self.fields) + 1
            self.fields.append(metadata_field)

    def remove_field(self, field_id: str) -> None:
        self.fields = [f for f in self.fields if f.field_id != field_id]
        self.reindex()

    def reindex(self) -> None:
        for i, f in enumerate(self.sorted_fields(), start=1):
            f.order = i

    def move_field(self, field_id: str, direction: int) -> None:
        ordered = self.sorted_fields()
        idx = next((i for i, f in enumerate(ordered) if f.field_id == field_id), -1)
        if idx < 0:
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(ordered):
            return
        ordered[idx], ordered[new_idx] = ordered[new_idx], ordered[idx]
        for i, f in enumerate(ordered, start=1):
            f.order = i
        self.fields = ordered


@dataclass
class MetadataRecord:
    """One metadata record. Values are stored as list[str] to support repeatable fields."""

    record_id: str = field(default_factory=lambda: make_id("rec"))
    record_type: str = "text"
    fields: dict[str, list[str]] = field(default_factory=dict)
    original_xml: str = ""

    def set_value(self, field_id: str, value: str | list[str] | None) -> None:
        if value is None:
            self.fields[field_id] = []
        elif isinstance(value, list):
            self.fields[field_id] = ["" if v is None else str(v) for v in value]
        else:
            self.fields[field_id] = [str(value)]

    def add_value(self, field_id: str, value: str) -> None:
        self.fields.setdefault(field_id, []).append(value)

    def get_values(self, field_id: str) -> list[str]:
        return self.fields.get(field_id, [])

    def get_value(self, field_id: str, sep: str = "; ") -> str:
        return sep.join(v for v in self.get_values(field_id) if v is not None)

    def to_flat_dict(self, schema: MetadataSchema | None = None) -> dict[str, str]:
        keys = schema.field_ids() if schema else sorted(self.fields.keys())
        data = {"record_id": self.record_id, "record_type": self.record_type}
        for k in keys:
            data[k] = self.get_value(k)
        return data


@dataclass
class MetadataRelation:
    """A typed relation among records, used for source/translation/alignment links."""

    relation_id: str = field(default_factory=lambda: make_id("rel"))
    relation_type: str = "translation"
    source_record: str = ""
    target_record: str = ""
    description: str = ""
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectInfo:
    project_id: str = field(default_factory=lambda: make_id("project"))
    project_name: str = "Untitled Metadata Project"
    corpus_type: str = "monolingual"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    interface_language: str = "zh_CN"


@dataclass
class MetadataProject:
    """Complete project data: project information, schema, records and relations."""

    project_info: ProjectInfo = field(default_factory=ProjectInfo)
    schema: MetadataSchema = field(default_factory=MetadataSchema)
    records: list[MetadataRecord] = field(default_factory=list)
    relations: list[MetadataRelation] = field(default_factory=list)
    file_path: Path | None = None
    dirty: bool = False

    def touch(self) -> None:
        self.project_info.updated_at = now_iso()
        self.dirty = True

    def add_record(self, record: MetadataRecord | None = None) -> MetadataRecord:
        record = record or MetadataRecord()
        record.record_id = self.ensure_unique_record_id(record.record_id)
        self.records.append(record)
        self.touch()
        return record

    def remove_record(self, record_id: str) -> None:
        self.records = [r for r in self.records if r.record_id != record_id]
        self.relations = [rel for rel in self.relations if rel.source_record != record_id and rel.target_record != record_id]
        self.touch()

    def get_record(self, record_id: str) -> MetadataRecord | None:
        for r in self.records:
            if r.record_id == record_id:
                return r
        return None

    def record_ids(self) -> set[str]:
        return {r.record_id for r in self.records}

    def ensure_unique_record_id(self, candidate: str | None = None) -> str:
        base = candidate or make_id("rec")
        if base not in self.record_ids():
            return base
        i = 2
        while f"{base}_{i}" in self.record_ids():
            i += 1
        return f"{base}_{i}"

    def add_relation(self, relation: MetadataRelation) -> None:
        self.relations.append(relation)
        self.touch()

    def get_corpus_type_label(self, lang: str = "zh_CN") -> str:
        key = "zh" if lang.startswith("zh") else "en"
        return CORPUS_TYPES.get(self.project_info.corpus_type, CORPUS_TYPES["monolingual"])[key]
