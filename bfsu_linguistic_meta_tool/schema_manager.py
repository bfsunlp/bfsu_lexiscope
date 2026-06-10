"""Metadata schema creation, editing, import and export helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

from models import MetadataField, MetadataSchema
from utils import parse_bool, slugify


CORPUS_TYPE_VALUES = [
    "monolingual",
    "bilingual_parallel",
    "multilingual_parallel",
    "multiple_translations",
    "comparable",
    "learner",
    "spoken",
]

GENRE_VALUES = ["fiction", "news", "academic", "spoken", "legal", "educational", "other"]
COPYRIGHT_VALUES = ["unknown", "public_domain", "licensed", "permission_required", "restricted"]
ALIGNMENT_VALUES = ["text", "paragraph", "sentence", "segment", "word"]
CEFR_VALUES = ["A1", "A2", "B1", "B2", "C1", "C2", "unknown"]
GENDER_VALUES = ["unknown", "female", "male", "other", "not_disclosed"]


def _field(
    field_id: str,
    zh: str,
    en: str,
    data_type: str = "string",
    required: bool = False,
    repeatable: bool = False,
    *,
    controlled_values: list[str] | None = None,
    level: str = "text",
    sensitive: bool = False,
    description_zh: str = "",
    description_en: str = "",
    example: str = "",
    validation_rule: str = "",
) -> MetadataField:
    return MetadataField(
        field_id=field_id,
        label_zh=zh,
        label_en=en,
        xml_tag=field_id,
        data_type=data_type,
        required=required,
        repeatable=repeatable,
        controlled_values=controlled_values or [],
        level=level,
        sensitive=sensitive,
        description_zh=description_zh,
        description_en=description_en,
        example=example,
        validation_rule=validation_rule,
    )


def _corpus_fields(corpus_type: str) -> list[MetadataField]:
    return [
        _field("corpus_id", "语料库编号", "Corpus ID", required=True, level="corpus"),
        _field("corpus_name", "语料库名称", "Corpus Name", required=True, level="corpus"),
        _field("corpus_type", "语料库类型", "Corpus Type", "enum", True, False, controlled_values=CORPUS_TYPE_VALUES, level="corpus", example=corpus_type),
    ]


def _common_text_fields(*, include_language: bool = True) -> list[MetadataField]:
    fields = [
        _field("text_id", "文本编号", "Text ID", required=True, level="text"),
        _field("title", "标题", "Title", required=True, level="text"),
        _field("author", "作者", "Author", repeatable=True, level="text"),
    ]
    if include_language:
        fields.append(_field("language", "语种", "Language", "language_code", level="text", example="zh"))
    fields.extend(
        [
            _field("publication_year", "出版年份", "Publication Year", "year", level="text", validation_rule=r"\d{4}"),
            _field("publisher", "出版社", "Publisher", level="text"),
            _field("genre", "文类", "Genre", "enum", controlled_values=GENRE_VALUES, level="text"),
            _field("text_type", "体裁/文本类型", "Text Type", level="text"),
            _field("word_count", "词数", "Word Count", "integer", level="text"),
            _field("character_count", "字数", "Character Count", "integer", level="text"),
            _field("source_file", "源文件", "Source File", "file_path", level="file"),
            _field("copyright_status", "版权状态", "Copyright Status", "enum", controlled_values=COPYRIGHT_VALUES, level="text"),
            _field("notes", "备注", "Notes", "long_text", level="text"),
        ]
    )
    return fields


def _translation_core_fields() -> list[MetadataField]:
    return [
        _field("source_language", "源语", "Source Language", "language_code", level="text", example="en"),
        _field("target_language", "目标语", "Target Language", "language_code", level="version", example="zh"),
        _field("translator", "译者", "Translator", repeatable=True, level="version"),
        _field("original_title", "原文标题", "Original Title", level="text"),
        _field("original_author", "原作者", "Original Author", repeatable=True, level="text"),
        _field("original_publication_year", "原文出版年份", "Original Publication Year", "year", level="text", validation_rule=r"\d{4}"),
        _field("translated_title", "译文标题", "Translated Title", level="version"),
        _field("translated_publication_year", "译文出版年份", "Translated Publication Year", "year", level="version", validation_rule=r"\d{4}"),
    ]


def default_schema(corpus_type: str = "monolingual") -> MetadataSchema:
    """Return a corpus-type-specific default schema.

    Translation-specific fields are intentionally excluded from monolingual,
    learner, spoken and comparable schemas. They are added only to parallel and
    multiple-translation schemas.
    """
    corpus_type = corpus_type or "monolingual"
    schema = MetadataSchema(schema_name=f"{corpus_type}_default_schema", schema_version="1.0")

    fields: list[MetadataField]
    if corpus_type == "monolingual":
        fields = _corpus_fields(corpus_type) + _common_text_fields(include_language=True)
    elif corpus_type == "bilingual_parallel":
        fields = (
            _corpus_fields(corpus_type)
            + _common_text_fields(include_language=False)
            + _translation_core_fields()
            + [
                _field("translation_direction", "翻译方向", "Translation Direction", level="relation", example="en-zh"),
                _field("source_text_id", "源文本ID", "Source Text ID", level="relation"),
                _field("target_text_id", "目标文本ID", "Target Text ID", level="relation"),
                _field("alignment_level", "对齐层级", "Alignment Level", "enum", controlled_values=ALIGNMENT_VALUES, level="alignment"),
                _field("alignment_file", "对齐文件", "Alignment File", "file_path", level="alignment"),
            ]
        )
    elif corpus_type == "multilingual_parallel":
        fields = (
            _corpus_fields(corpus_type)
            + _common_text_fields(include_language=False)
            + _translation_core_fields()
            + [
                _field("language_list", "语种列表", "Language List", "language_code", repeatable=True, level="corpus", example="en; zh; ja"),
                _field("version_id", "版本ID", "Version ID", level="version"),
                _field("version_language", "版本语种", "Version Language", "language_code", level="version"),
                _field("version_relation", "版本关系", "Version Relation", level="relation"),
                _field("pivot_text_id", "枢轴文本ID", "Pivot Text ID", level="relation"),
                _field("alignment_level", "对齐层级", "Alignment Level", "enum", controlled_values=ALIGNMENT_VALUES, level="alignment"),
                _field("alignment_file", "对齐文件", "Alignment File", "file_path", level="alignment"),
            ]
        )
    elif corpus_type == "multiple_translations":
        fields = (
            _corpus_fields(corpus_type)
            + _common_text_fields(include_language=False)
            + _translation_core_fields()
            + [
                _field("source_text_id", "源文本ID", "Source Text ID", level="relation"),
                _field("translation_version", "译本版本", "Translation Version", level="version"),
                _field("translation_year", "翻译年份", "Translation Year", "year", level="version", validation_rule=r"\d{4}"),
                _field("edition", "版次", "Edition", level="version"),
                _field("reprint_information", "重印信息", "Reprint Information", "long_text", level="version"),
                _field("translation_strategy_notes", "翻译策略说明", "Translation Strategy Notes", "long_text", level="version"),
                _field("version_relationship", "译本关系", "Version Relationship", level="relation"),
            ]
        )
    elif corpus_type == "learner":
        fields = _corpus_fields(corpus_type) + _common_text_fields(include_language=True) + [
            _field("learner_id", "学习者ID", "Learner ID", level="speaker", sensitive=True),
            _field("learner_l1", "学习者母语", "Learner L1", "language_code", level="speaker"),
            _field("target_language", "目标语/学习语", "Target/Learned Language", "language_code", level="speaker"),
            _field("l2_level", "二语水平", "L2 Level", "enum", controlled_values=CEFR_VALUES, level="speaker"),
            _field("age_group", "年龄段", "Age Group", level="speaker", sensitive=True),
            _field("gender", "性别", "Gender", "enum", controlled_values=GENDER_VALUES, level="speaker", sensitive=True),
            _field("education_background", "教育背景", "Education Background", level="speaker", sensitive=True),
            _field("task_type", "任务类型", "Task Type", level="text"),
            _field("exam_level", "考试等级", "Exam Level", level="text"),
            _field("writing_prompt", "作文题目", "Writing Prompt", "long_text", level="text"),
        ]
    elif corpus_type == "spoken":
        fields = _corpus_fields(corpus_type) + _common_text_fields(include_language=True) + [
            _field("speaker_id", "说话人ID", "Speaker ID", level="speaker", sensitive=True),
            _field("speaker_role", "说话人角色", "Speaker Role", level="speaker"),
            _field("recording_file", "录音文件", "Recording File", "file_path", level="file"),
            _field("transcription_file", "转写文件", "Transcription File", "file_path", level="file"),
            _field("recording_date", "录音日期", "Recording Date", "date", level="file"),
            _field("recording_location", "录音地点", "Recording Location", level="file", sensitive=True),
            _field("setting", "场景", "Setting", level="text"),
            _field("interaction_type", "交际类型", "Interaction Type", level="text"),
            _field("duration", "时长", "Duration", level="file", example="00:12:35"),
            _field("sampling_rate", "采样率", "Sampling Rate", "integer", level="file"),
            _field("transcription_convention", "转写规范", "Transcription Convention", level="file"),
        ]
    elif corpus_type == "comparable":
        fields = _corpus_fields(corpus_type) + _common_text_fields(include_language=True) + [
            _field("subcorpus_id", "子库ID", "Subcorpus ID", level="subcorpus"),
            _field("subcorpus_name", "子库名称", "Subcorpus Name", level="subcorpus"),
            _field("topic", "主题", "Topic", level="text"),
            _field("domain", "领域", "Domain", level="text"),
            _field("comparability_basis", "可比依据", "Comparability Basis", "long_text", level="corpus"),
            _field("sampling_criteria", "抽样标准", "Sampling Criteria", "long_text", level="corpus"),
        ]
    else:
        fields = _corpus_fields("custom") + _common_text_fields(include_language=True)

    for i, field in enumerate(deepcopy(fields), start=1):
        field.order = i
        schema.add_field(field)
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
