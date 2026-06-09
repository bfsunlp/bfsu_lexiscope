"""Validation rules for schemas and records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

from models import DATA_TYPES, FIELD_LEVELS, MetadataField, MetadataProject, MetadataRecord, MetadataSchema


@dataclass
class ValidationMessage:
    level: str  # info, warning, error
    item: str
    message: str

    def as_row(self) -> dict[str, str]:
        return {"level": self.level, "item": self.item, "message": self.message}


def validate_schema(schema: MetadataSchema) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    seen_ids: set[str] = set()
    seen_tags: set[str] = set()
    for field in schema.fields:
        if not field.field_id:
            messages.append(ValidationMessage("error", "schema", "Field ID is empty."))
        if field.field_id in seen_ids:
            messages.append(ValidationMessage("error", field.field_id, "Duplicate field_id."))
        seen_ids.add(field.field_id)
        if not field.xml_tag:
            messages.append(ValidationMessage("error", field.field_id, "XML tag is empty."))
        if field.xml_tag in seen_tags:
            messages.append(ValidationMessage("warning", field.field_id, "Duplicate XML tag."))
        seen_tags.add(field.xml_tag)
        if field.data_type not in DATA_TYPES:
            messages.append(ValidationMessage("error", field.field_id, f"Unsupported data type: {field.data_type}"))
        if field.level not in FIELD_LEVELS:
            messages.append(ValidationMessage("warning", field.field_id, f"Unknown level: {field.level}"))
        if field.data_type == "enum" and not field.controlled_values:
            messages.append(ValidationMessage("warning", field.field_id, "Enum field has no controlled values."))
    return messages


def validate_project(project: MetadataProject) -> list[ValidationMessage]:
    messages = validate_schema(project.schema)
    seen: set[str] = set()
    for r in project.records:
        if r.record_id in seen:
            messages.append(ValidationMessage("error", r.record_id, "Duplicate record_id."))
        seen.add(r.record_id)
        messages.extend(validate_record(r, project.schema))
    record_ids = project.record_ids()
    for rel in project.relations:
        if rel.source_record and rel.source_record not in record_ids:
            messages.append(ValidationMessage("warning", rel.relation_id, f"Unknown source record: {rel.source_record}"))
        if rel.target_record and rel.target_record not in record_ids:
            messages.append(ValidationMessage("warning", rel.relation_id, f"Unknown target record: {rel.target_record}"))
    return messages


def validate_record(record: MetadataRecord, schema: MetadataSchema) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    for field in schema.fields:
        values = record.get_values(field.field_id)
        non_empty = [v for v in values if str(v).strip()]
        if field.required and not non_empty:
            messages.append(ValidationMessage("error", record.record_id, f"Required field is empty: {field.field_id}"))
            continue
        if not field.repeatable and len(non_empty) > 1:
            messages.append(ValidationMessage("error", record.record_id, f"Field is not repeatable: {field.field_id}"))
        for value in non_empty:
            msg = validate_field_value(field, value)
            if msg:
                messages.append(ValidationMessage("error", record.record_id, f"{field.field_id}: {msg}"))
    for unknown in sorted(set(record.fields.keys()) - set(schema.field_ids())):
        messages.append(ValidationMessage("warning", record.record_id, f"Unknown field not defined in schema: {unknown}"))
    return messages


def validate_field_value(field: MetadataField, value: str) -> str | None:
    value = str(value).strip()
    if value == "":
        return None
    try:
        if field.data_type == "integer":
            int(value)
        elif field.data_type == "float":
            float(value)
        elif field.data_type == "year":
            if not re.fullmatch(r"\d{4}", value):
                return "Year must be in YYYY format."
        elif field.data_type == "date":
            _parse_date(value)
        elif field.data_type == "boolean":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no", "是", "否"}:
                return "Boolean must be true/false, yes/no, 1/0, 是/否."
        elif field.data_type == "enum":
            if field.controlled_values and value not in field.controlled_values:
                return f"Value not in controlled vocabulary: {value}"
        elif field.data_type == "language_code":
            if not re.fullmatch(r"[a-zA-Z]{2,3}(-[a-zA-Z]{2,4})?", value):
                return "Language code should look like zh, en, zh-CN, etc."
        elif field.data_type == "file_path":
            # 只做基本路径合法性检查，不要求文件必须存在。
            Path(value)
    except Exception as exc:  # noqa: BLE001
        return str(exc)
    if field.validation_rule:
        try:
            if not re.fullmatch(field.validation_rule, value):
                return f"Regex validation failed: {field.validation_rule}"
        except re.error as exc:
            return f"Invalid validation regex: {exc}"
    return None


def _parse_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m", "%Y/%m"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError("Date must be YYYY-MM-DD or a close variant.")
