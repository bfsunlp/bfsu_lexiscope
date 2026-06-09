"""Metadata schema creation, editing, import and export helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

from models import MetadataField, MetadataSchema
from utils import parse_bool, slugify


BASE_FIELDS = [
    MetadataField("corpus_id", "语料库编号", "Corpus ID", "corpus_id", "string", True, False, level="corpus", order=1),
    MetadataField("corpus_name", "语料库名称", "Corpus Name", "corpus_name", "string", True, False, level="corpus", order=2),
    MetadataField("corpus_type", "语料库类型", "Corpus Type", "corpus_type", "enum", True, False, controlled_values=["monolingual", "bilingual_parallel", "multilingual_parallel", "multiple_translations", "comparable", "learner", "spoken"], level="corpus", order=3),
    MetadataField("text_id", "文本编号", "Text ID", "text_id", "string", True, False, level="text", order=4),
    MetadataField("title", "标题", "Title", "title", "string", True, False, level="text", order=5),
    MetadataField("author", "作者", "Author", "author", "string", False, True, level="text", order=6),
    MetadataField("translator", "译者", "Translator", "translator", "string", False, True, level="version", order=7),
    MetadataField("source_language", "源语", "Source Language", "source_language", "language_code", False, False, level="text", order=8),
    MetadataField("target_language", "目标语", "Target Language", "target_language", "language_code", False, False, level="version", order=9),
    MetadataField("language", "语种", "Language", "language", "language_code", False, False, level="text", order=10),
    MetadataField("publication_year", "出版年份", "Publication Year", "publication_year", "year", False, False, level="text", order=11),
    MetadataField("original_publication_year", "原文出版年份", "Original Publication Year", "original_publication_year", "year", False, False, level="text", order=12),
    MetadataField("translated_publication_year", "译文出版年份", "Translated Publication Year", "translated_publication_year", "year", False, False, level="version", order=13),
    MetadataField("publisher", "出版社", "Publisher", "publisher", "string", False, False, level="text", order=14),
    MetadataField("genre", "文类", "Genre", "genre", "enum", False, False, controlled_values=["fiction", "news", "academic", "spoken", "legal", "educational", "other"], level="text", order=15),
    MetadataField("text_type", "体裁/文本类型", "Text Type", "text_type", "string", False, False, level="text", order=16),
    MetadataField("word_count", "词数", "Word Count", "word_count", "integer", False, False, level="text", order=17),
    MetadataField("character_count", "字数", "Character Count", "character_count", "integer", False, False, level="text", order=18),
    MetadataField("source_file", "源文件", "Source File", "source_file", "file_path", False, False, level="file", order=19),
    MetadataField("copyright_status", "版权状态", "Copyright Status", "copyright_status", "enum", False, False, controlled_values=["unknown", "public_domain", "licensed", "permission_required", "restricted"], level="text", order=20),
    MetadataField("notes", "备注", "Notes", "notes", "long_text", False, False, level="text", order=21),
]


def default_schema(corpus_type: str = "monolingual") -> MetadataSchema:
    schema = MetadataSchema(schema_name=f"{corpus_type}_default_schema", schema_version="1.0")
    for f in deepcopy(BASE_FIELDS):
        schema.add_field(f)
    extra: list[MetadataField] = []
    if corpus_type == "bilingual_parallel":
        extra = [
            MetadataField("translation_direction", "翻译方向", "Translation Direction", "translation_direction", "string", False, False, level="relation"),
            MetadataField("alignment_level", "对齐层级", "Alignment Level", "alignment_level", "enum", False, False, controlled_values=["text", "paragraph", "sentence", "segment", "word"], level="alignment"),
            MetadataField("source_text_id", "源文本ID", "Source Text ID", "source_text_id", "string", False, False, level="relation"),
            MetadataField("target_text_id", "目标文本ID", "Target Text ID", "target_text_id", "string", False, False, level="relation"),
        ]
    elif corpus_type == "multilingual_parallel":
        extra = [
            MetadataField("language_list", "语种列表", "Language List", "language_list", "language_code", False, True, level="corpus"),
            MetadataField("version_id", "版本ID", "Version ID", "version_id", "string", False, False, level="version"),
            MetadataField("version_relation", "版本关系", "Version Relation", "version_relation", "string", False, False, level="relation"),
            MetadataField("alignment_file", "对齐文件", "Alignment File", "alignment_file", "file_path", False, False, level="alignment"),
        ]
    elif corpus_type == "multiple_translations":
        extra = [
            MetadataField("source_text", "源文本", "Source Text", "source_text", "string", False, False, level="text"),
            MetadataField("translation_version", "译本版本", "Translation Version", "translation_version", "string", False, False, level="version"),
            MetadataField("translation_year", "翻译年份", "Translation Year", "translation_year", "year", False, False, level="version"),
            MetadataField("edition", "版次", "Edition", "edition", "string", False, False, level="version"),
            MetadataField("reprint_information", "重印信息", "Reprint Information", "reprint_information", "long_text", False, False, level="version"),
            MetadataField("translation_strategy_notes", "翻译策略说明", "Translation Strategy Notes", "translation_strategy_notes", "long_text", False, False, level="version"),
            MetadataField("version_relationship", "译本关系", "Version Relationship", "version_relationship", "string", False, False, level="relation"),
        ]
    elif corpus_type == "learner":
        extra = [
            MetadataField("learner_l1", "学习者母语", "Learner L1", "learner_l1", "language_code", False, False, level="speaker"),
            MetadataField("l2_level", "二语水平", "L2 Level", "l2_level", "enum", False, False, controlled_values=["A1", "A2", "B1", "B2", "C1", "C2", "unknown"], level="speaker"),
            MetadataField("age_group", "年龄段", "Age Group", "age_group", "string", False, False, level="speaker", sensitive=True),
            MetadataField("gender", "性别", "Gender", "gender", "enum", False, False, controlled_values=["unknown", "female", "male", "other", "not_disclosed"], level="speaker", sensitive=True),
            MetadataField("education_background", "教育背景", "Education Background", "education_background", "string", False, False, level="speaker", sensitive=True),
            MetadataField("task_type", "任务类型", "Task Type", "task_type", "string", False, False, level="text"),
            MetadataField("exam_level", "考试等级", "Exam Level", "exam_level", "string", False, False, level="text"),
            MetadataField("writing_prompt", "作文题目", "Writing Prompt", "writing_prompt", "long_text", False, False, level="text"),
        ]
    elif corpus_type == "spoken":
        extra = [
            MetadataField("speaker_id", "说话人ID", "Speaker ID", "speaker_id", "string", False, False, level="speaker", sensitive=True),
            MetadataField("recording_file", "录音文件", "Recording File", "recording_file", "file_path", False, False, level="file"),
            MetadataField("transcription_file", "转写文件", "Transcription File", "transcription_file", "file_path", False, False, level="file"),
            MetadataField("setting", "场景", "Setting", "setting", "string", False, False, level="text"),
            MetadataField("interaction_type", "交际类型", "Interaction Type", "interaction_type", "string", False, False, level="text"),
            MetadataField("sampling_rate", "采样率", "Sampling Rate", "sampling_rate", "integer", False, False, level="file"),
            MetadataField("transcription_convention", "转写规范", "Transcription Convention", "transcription_convention", "string", False, False, level="file"),
        ]
    elif corpus_type == "comparable":
        extra = [
            MetadataField("topic", "主题", "Topic", "topic", "string", False, False, level="text"),
            MetadataField("comparability_basis", "可比依据", "Comparability Basis", "comparability_basis", "long_text", False, False, level="corpus"),
        ]
    for f in extra:
        f.order = len(schema.fields) + 1
        schema.add_field(f)
    return schema


def fields_from_headers(headers: list[str]) -> MetadataSchema:
    schema = MetadataSchema(schema_name="schema_from_excel", schema_version="1.0")
    for i, header in enumerate(headers, start=1):
        field_id = slugify(str(header), fallback=f"field_{i}")
        schema.add_field(MetadataField(field_id=field_id, label_zh=str(header), label_en=str(header), xml_tag=field_id, order=i))
    return schema


def schema_to_xml_element(schema: MetadataSchema) -> ET.Element:
    elem = ET.Element("schema", {"schema_id": schema.schema_id, "schema_name": schema.schema_name, "schema_version": schema.schema_version})
    for field in schema.sorted_fields():
        f_elem = ET.SubElement(
            elem,
            "field",
            {
                "field_id": field.field_id,
                "xml_tag": field.xml_tag,
                "data_type": field.data_type,
                "required": str(field.required).lower(),
                "repeatable": str(field.repeatable).lower(),
                "level": field.level,
                "parent": field.parent,
                "order": str(field.order),
                "visible": str(field.visible).lower(),
                "editable": str(field.editable).lower(),
                "sensitive": str(field.sensitive).lower(),
            },
        )
        ET.SubElement(f_elem, "label", {"lang": "zh"}).text = field.label_zh
        ET.SubElement(f_elem, "label", {"lang": "en"}).text = field.label_en
        ET.SubElement(f_elem, "default_value").text = field.default_value
        cv = ET.SubElement(f_elem, "controlled_values")
        for value in field.controlled_values:
            ET.SubElement(cv, "value").text = value
        ET.SubElement(f_elem, "description", {"lang": "zh"}).text = field.description_zh
        ET.SubElement(f_elem, "description", {"lang": "en"}).text = field.description_en
        ET.SubElement(f_elem, "example").text = field.example
        ET.SubElement(f_elem, "validation_rule").text = field.validation_rule
    return elem


def schema_from_xml_element(elem: ET.Element) -> MetadataSchema:
    schema = MetadataSchema(
        schema_id=elem.attrib.get("schema_id", ""),
        schema_name=elem.attrib.get("schema_name", "Imported Schema"),
        schema_version=elem.attrib.get("schema_version", "1.0"),
    )
    for f_elem in elem.findall("field"):
        labels = {x.attrib.get("lang", ""): x.text or "" for x in f_elem.findall("label")}
        descriptions = {x.attrib.get("lang", ""): x.text or "" for x in f_elem.findall("description")}
        values = [v.text or "" for v in f_elem.findall("controlled_values/value")]
        field = MetadataField(
            field_id=f_elem.attrib.get("field_id", ""),
            label_zh=labels.get("zh", ""),
            label_en=labels.get("en", ""),
            xml_tag=f_elem.attrib.get("xml_tag", ""),
            data_type=f_elem.attrib.get("data_type", "string"),
            required=parse_bool(f_elem.attrib.get("required")),
            repeatable=parse_bool(f_elem.attrib.get("repeatable")),
            default_value=f_elem.findtext("default_value", ""),
            controlled_values=values,
            description_zh=descriptions.get("zh", ""),
            description_en=descriptions.get("en", ""),
            example=f_elem.findtext("example", ""),
            level=f_elem.attrib.get("level", "text"),
            parent=f_elem.attrib.get("parent", ""),
            order=int(f_elem.attrib.get("order", "0") or 0),
            visible=parse_bool(f_elem.attrib.get("visible"), True),
            editable=parse_bool(f_elem.attrib.get("editable"), True),
            sensitive=parse_bool(f_elem.attrib.get("sensitive"), False),
            validation_rule=f_elem.findtext("validation_rule", ""),
        )
        if field.field_id:
            schema.add_field(field)
    schema.reindex()
    return schema


def load_schema_xml(path: Path) -> MetadataSchema:
    root = ET.parse(path).getroot()
    if root.tag == "metadata_project":
        schema_elem = root.find("schema")
        if schema_elem is None:
            raise ValueError("No <schema> found in project XML.")
        return schema_from_xml_element(schema_elem)
    if root.tag == "schema":
        return schema_from_xml_element(root)
    raise ValueError(f"Unsupported schema XML root: {root.tag}")


def save_schema_xml(schema: MetadataSchema, path: Path) -> None:
    from utils import ensure_parent, indent_xml

    elem = schema_to_xml_element(schema)
    indent_xml(elem)
    ensure_parent(path)
    ET.ElementTree(elem).write(path, encoding="utf-8", xml_declaration=True)
