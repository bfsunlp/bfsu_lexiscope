"""Importer for existing XML metadata files.

The importer can merge complete project XML files, simple <records> XML, or
arbitrary XML documents. Unknown tags may be preserved as fields or ignored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

from models import MetadataField, MetadataProject, MetadataRecord
from schema_manager import load_schema_xml
from utils import slugify
from xml_repository import XMLRepository


@dataclass
class XMLImportPreview:
    tags: list[str]
    suggested_mapping: dict[str, str]
    unknown_tags: list[str]
    sample_records: list[dict[str, str]] = field(default_factory=list)


class XMLImporter:
    def preview(self, path: Path, project: MetadataProject, max_records: int = 20) -> XMLImportPreview:
        root = ET.parse(path).getroot()
        tags = sorted({el.tag for el in root.iter() if el is not root})
        mapping: dict[str, str] = {}
        unknown: list[str] = []
        lookup: dict[str, str] = {}
        for f in project.schema.fields:
            for key in {f.field_id, f.xml_tag, f.label_zh, f.label_en}:
                if key:
                    lookup[str(key).lower()] = f.field_id
        for tag in tags:
            fid = lookup.get(tag.lower()) or lookup.get(slugify(tag))
            if fid:
                mapping[tag] = fid
            else:
                unknown.append(tag)
        sample: list[dict[str, str]] = []
        for rec in self._extract_records(root)[:max_records]:
            sample.append({child.tag: (child.text or "") for child in list(rec) if child.text})
        return XMLImportPreview(tags, mapping, unknown, sample)

    def import_file(
        self,
        path: Path,
        project: MetadataProject,
        mapping: dict[str, str] | None = None,
        add_unknown_to_schema: bool = False,
        preserve_original_xml: bool = True,
    ) -> tuple[int, list[str]]:
        root = ET.parse(path).getroot()
        logs: list[str] = []
        if root.tag == "metadata_project":
            imported = XMLRepository().element_to_project(root)
            # 合并schema字段。
            for field in imported.schema.fields:
                if project.schema.get_field(field.field_id) is None:
                    project.schema.add_field(field)
            for record in imported.records:
                record.record_id = project.ensure_unique_record_id(record.record_id)
                project.add_record(record)
            for rel in imported.relations:
                project.add_relation(rel)
            return len(imported.records), ["Imported complete metadata_project XML."]
        if root.tag == "schema":
            schema = load_schema_xml(path)
            for field in schema.fields:
                if project.schema.get_field(field.field_id) is None:
                    project.schema.add_field(field)
            project.touch()
            return 0, ["Imported schema XML only."]
        preview = self.preview(path, project)
        mapping = mapping or preview.suggested_mapping
        if add_unknown_to_schema:
            for tag in preview.unknown_tags:
                if tag in {"records", "record", "field", "relations", "relation"}:
                    continue
                fid = slugify(tag)
                if not project.schema.get_field(fid):
                    project.schema.add_field(MetadataField(field_id=fid, label_zh=tag, label_en=tag, xml_tag=tag))
                mapping[tag] = fid
        records = self._extract_records(root)
        count = 0
        if not records:
            records = [root]
        for rec_elem in records:
            record = MetadataRecord(record_type=rec_elem.tag if rec_elem.tag != "record" else "text")
            if rec_elem.attrib.get("record_id"):
                record.record_id = project.ensure_unique_record_id(rec_elem.attrib["record_id"])
            for elem in rec_elem.iter():
                if elem is rec_elem:
                    continue
                if list(elem):
                    continue
                tag = elem.tag
                field_id = mapping.get(tag)
                if not field_id:
                    continue
                text = elem.text or ""
                if text.strip():
                    record.add_value(field_id, text.strip())
            if preserve_original_xml:
                record.original_xml = ET.tostring(rec_elem, encoding="unicode")
            if record.fields:
                project.add_record(record)
                count += 1
        logs.append(f"Imported {count} record(s) from XML.")
        return count, logs

    def _extract_records(self, root: ET.Element) -> list[ET.Element]:
        if root.tag == "records":
            return root.findall("record")
        records = root.findall(".//record")
        if records:
            return records
        # 对通用XML：优先把root下每个含多个子节点的一级元素视为记录。
        candidates = [child for child in list(root) if len(list(child)) > 0]
        return candidates
