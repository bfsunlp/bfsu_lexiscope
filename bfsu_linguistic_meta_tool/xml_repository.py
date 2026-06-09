"""Project XML repository.

This module is the single source of truth for saving and loading the unified
intermediate XML project format.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from models import MetadataProject, MetadataRecord, MetadataRelation, ProjectInfo
from schema_manager import schema_from_xml_element, schema_to_xml_element
from utils import ensure_parent, indent_xml, make_backup, now_iso


class XMLRepository:
    def new_project(self, project_name: str, corpus_type: str, schema=None, interface_language: str = "zh_CN") -> MetadataProject:
        from schema_manager import default_schema

        project = MetadataProject()
        project.project_info.project_name = project_name or "Untitled Metadata Project"
        project.project_info.corpus_type = corpus_type
        project.project_info.interface_language = interface_language
        project.schema = schema or default_schema(corpus_type)
        project.dirty = True
        return project

    def save_project(self, project: MetadataProject, path: Path, backup: bool = True) -> None:
        path = Path(path)
        ensure_parent(path)
        if backup and path.exists():
            make_backup(path)
        project.project_info.updated_at = now_iso()
        root = self.project_to_element(project)
        indent_xml(root)
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        project.file_path = path
        project.dirty = False

    def load_project(self, path: Path) -> MetadataProject:
        path = Path(path)
        root = ET.parse(path).getroot()
        if root.tag != "metadata_project":
            raise ValueError(f"Unsupported project XML root: {root.tag}")
        project = self.element_to_project(root)
        project.file_path = path
        project.dirty = False
        return project

    def export_schema(self, project: MetadataProject, path: Path) -> None:
        from schema_manager import save_schema_xml

        save_schema_xml(project.schema, Path(path))

    def export_records_xml(self, project: MetadataProject, path: Path) -> None:
        root = ET.Element("records")
        for record in project.records:
            root.append(self.record_to_element(record, project))
        indent_xml(root)
        ensure_parent(Path(path))
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def project_to_element(self, project: MetadataProject) -> ET.Element:
        root = ET.Element("metadata_project")
        p = ET.SubElement(root, "project_info")
        for name in ("project_id", "project_name", "corpus_type", "created_at", "updated_at", "interface_language"):
            ET.SubElement(p, name).text = getattr(project.project_info, name)
        root.append(schema_to_xml_element(project.schema))
        records_elem = ET.SubElement(root, "records")
        for record in project.records:
            records_elem.append(self.record_to_element(record, project))
        relations_elem = ET.SubElement(root, "relations")
        for relation in project.relations:
            relations_elem.append(self.relation_to_element(relation))
        return root

    def element_to_project(self, root: ET.Element) -> MetadataProject:
        project = MetadataProject()
        info = root.find("project_info")
        if info is not None:
            project.project_info = ProjectInfo(
                project_id=info.findtext("project_id", project.project_info.project_id),
                project_name=info.findtext("project_name", project.project_info.project_name),
                corpus_type=info.findtext("corpus_type", project.project_info.corpus_type),
                created_at=info.findtext("created_at", project.project_info.created_at),
                updated_at=info.findtext("updated_at", project.project_info.updated_at),
                interface_language=info.findtext("interface_language", project.project_info.interface_language),
            )
        schema_elem = root.find("schema")
        if schema_elem is not None:
            project.schema = schema_from_xml_element(schema_elem)
        records_elem = root.find("records")
        if records_elem is not None:
            for r_elem in records_elem.findall("record"):
                project.records.append(self.record_from_element(r_elem))
        relations_elem = root.find("relations")
        if relations_elem is not None:
            for rel_elem in relations_elem.findall("relation"):
                project.relations.append(self.relation_from_element(rel_elem))
        return project

    def record_to_element(self, record: MetadataRecord, project: MetadataProject | None = None) -> ET.Element:
        elem = ET.Element("record", {"record_id": record.record_id, "record_type": record.record_type})
        # 先按schema顺序输出已定义字段，再输出未知字段，最大程度保留导入信息。
        ordered = project.schema.field_ids() if project else []
        keys = ordered + sorted(k for k in record.fields.keys() if k not in ordered)
        for field_id in keys:
            values = record.get_values(field_id)
            if not values:
                continue
            field_def = project.schema.get_field(field_id) if project else None
            xml_tag = field_def.xml_tag if field_def else field_id
            for value in values:
                f_elem = ET.SubElement(elem, "field", {"name": field_id, "xml_tag": xml_tag})
                f_elem.text = str(value)
        if record.original_xml:
            original = ET.SubElement(elem, "original_xml")
            original.text = record.original_xml
        return elem

    def record_from_element(self, elem: ET.Element) -> MetadataRecord:
        record = MetadataRecord(
            record_id=elem.attrib.get("record_id", ""),
            record_type=elem.attrib.get("record_type", "text"),
        )
        for f_elem in elem.findall("field"):
            name = f_elem.attrib.get("name") or f_elem.attrib.get("xml_tag") or "field"
            record.add_value(name, f_elem.text or "")
        record.original_xml = elem.findtext("original_xml", "")
        return record

    def relation_to_element(self, relation: MetadataRelation) -> ET.Element:
        elem = ET.Element("relation", {"relation_id": relation.relation_id, "relation_type": relation.relation_type})
        ET.SubElement(elem, "source_record").text = relation.source_record
        ET.SubElement(elem, "target_record").text = relation.target_record
        ET.SubElement(elem, "description").text = relation.description
        attrs = ET.SubElement(elem, "attributes")
        for k, v in relation.attributes.items():
            ET.SubElement(attrs, "attribute", {"name": k}).text = v
        return elem

    def relation_from_element(self, elem: ET.Element) -> MetadataRelation:
        relation = MetadataRelation(
            relation_id=elem.attrib.get("relation_id", ""),
            relation_type=elem.attrib.get("relation_type", "translation"),
            source_record=elem.findtext("source_record", ""),
            target_record=elem.findtext("target_record", ""),
            description=elem.findtext("description", ""),
        )
        for attr in elem.findall("attributes/attribute"):
            relation.attributes[attr.attrib.get("name", "attribute")] = attr.text or ""
        return relation
