# LLM Metadata Extraction Prompt / 大模型元信息识别提示词说明

This document records the internal prompt contract used by `llm_metadata.py`.
The runtime prompt is generated dynamically from the current project's active Schema and the current record.

## 1. Internal System Prompt / 内部系统提示词

The extractor acts as a schema-bound metadata extraction assistant. It must:

1. Use only `field_id` values that exist in the current Schema.
2. Respect each field's `data_type`, `repeatable`, `required`, `controlled_values`, `xml_tag`, bilingual labels, descriptions, examples and validation rules.
3. Prefer explicit source evidence; infer only when strongly supported.
4. Return JSON only, without Markdown, comments or XML.
5. Leave uncertain values empty and report warnings rather than inventing metadata.

## 2. Runtime JSON Input / 运行时 JSON 输入

```json
{
  "task": "extract_metadata_for_current_record",
  "schema_binding_rule": "Only output field IDs that appear in fields[].field_id. Values must match the current schema definition.",
  "project": {
    "project_name": "Untitled Metadata Project",
    "corpus_type": "monolingual",
    "schema_name": "monolingual_default_schema",
    "schema_version": "1.0"
  },
  "current_record": {
    "record_id": "rec_xxxxxxxxxx",
    "record_type": "text",
    "existing_values": {
      "title": [],
      "author": []
    }
  },
  "fields": [
    {
      "field_id": "title",
      "xml_tag": "title",
      "label_zh": "标题",
      "label_en": "Title",
      "data_type": "string",
      "required": true,
      "repeatable": false,
      "controlled_values": [],
      "description_zh": "",
      "description_en": "",
      "example": "",
      "level": "text",
      "validation_rule": "",
      "sensitive": false
    }
  ],
  "source": {
    "source_kind": "text_file | pdf_text | pdf_file | image_file | html_file | webpage | pasted_text",
    "file_name": "example.pdf",
    "url": "",
    "mime_type": "application/pdf",
    "text": "Extracted or pasted text when available"
  },
  "output_contract": {
    "record_id": "string, optional",
    "record_type": "string, optional",
    "fields": {
      "field_id_from_schema": {
        "value": "schema-compatible scalar or array; empty string if unavailable",
        "confidence": "number from 0 to 1",
        "evidence": "brief source evidence",
        "reasoning_note": "brief reason",
        "source": "explicit | inferred | existing | empty"
      }
    },
    "warnings": ["short warning text"],
    "overall_confidence": "number from 0 to 1"
  }
}
```

## 3. Required JSON Output / 必须返回的 JSON 输出

```json
{
  "record_id": "",
  "record_type": "text",
  "fields": {
    "title": {
      "value": "A Corpus-based Study of ...",
      "confidence": 0.94,
      "evidence": "Title line on page 1",
      "reasoning_note": "The document title is explicitly printed at the top of the first page.",
      "source": "explicit"
    },
    "publication_year": {
      "value": "2024",
      "confidence": 0.82,
      "evidence": "© 2024",
      "reasoning_note": "The copyright year is treated as publication year.",
      "source": "inferred"
    }
  },
  "unmapped_candidates": [
    {
      "label": "DOI",
      "value": "10.xxxx/xxxxx",
      "evidence": "DOI line on page 1"
    }
  ],
  "warnings": [
    "DOI was found but no DOI field exists in the current Schema."
  ],
  "overall_confidence": 0.88
}
```

## 4. Application Rule / 回填规则

The application never creates new fields from model output. Returned fields are validated against the current Schema again before being written into the current record. Invalid enum values, invalid language codes, invalid years and non-Schema fields are discarded with warnings.

---

## 4. 大模型辅助 Schema 生成 / 扩展 Prompt

本版本新增 **Schema 级大模型交互**。该功能与“记录元信息识别”分离，不直接填写记录，而是根据用户对语料库类型、研究目标、元信息层级、样本文档等的说明，生成或扩展当前项目的 Schema。

### 4.1 交互入口

- **规范 → 大模型生成新Schema**：生成一个完整的新 Schema。应用前会预览；应用后用所选字段替换当前 Schema 字段定义。
- **规范 → 大模型扩展当前Schema**：在现有 Schema 基础上提出新增字段或可选替换建议。默认不会覆盖已有字段。

### 4.2 输入 JSON

```json
{
  "task": "generate_or_extend_metadata_schema",
  "mode": "generate_new_schema | extend_current_schema",
  "project": {
    "project_name": "...",
    "corpus_type": "monolingual | bilingual_parallel | multilingual_parallel | multiple_translations | comparable | learner | spoken | custom",
    "current_schema_name": "...",
    "current_schema_version": "..."
  },
  "existing_schema_fields": [
    {
      "field_id": "title",
      "xml_tag": "title",
      "label_zh": "标题",
      "label_en": "Title",
      "data_type": "string",
      "required": true,
      "repeatable": false,
      "default_value": "",
      "controlled_values": [],
      "description_zh": "",
      "description_en": "",
      "example": "",
      "level": "text",
      "parent": "",
      "order": 1,
      "visible": true,
      "editable": true,
      "sensitive": false,
      "validation_rule": ""
    }
  ],
  "user_requirements": "用户对语料库、研究任务、字段需求和规范偏好的自然语言说明。",
  "source": {
    "source_kind": "pasted_text | text_file | html_file | webpage | pdf_text | pdf_file | image_file",
    "file_name": "...",
    "url": "...",
    "mime_type": "...",
    "text": "可选样本文本或从文档抽取的文本"
  }
}
```

### 4.3 输出 JSON

```json
{
  "schema_name": "ai_generated_schema",
  "schema_version": "1.0",
  "corpus_type": "custom",
  "mode": "generate_new_schema",
  "fields": [
    {
      "field_id": "text_id",
      "label_zh": "文本编号",
      "label_en": "Text ID",
      "xml_tag": "text_id",
      "data_type": "string",
      "required": true,
      "repeatable": false,
      "default_value": "",
      "controlled_values": [],
      "description_zh": "文本记录的唯一编号。",
      "description_en": "Unique identifier for the text record.",
      "example": "TXT_0001",
      "level": "text",
      "parent": "",
      "order": 1,
      "visible": true,
      "editable": true,
      "sensitive": false,
      "validation_rule": "",
      "action": "add",
      "rationale": "用于稳定标识语料库中的文本记录。",
      "confidence": 0.95
    }
  ],
  "warnings": []
}
```

### 4.4 本地安全约束

程序会在应用前再次做本地规范化与约束：

1. 非法 `data_type` 自动降级为 `string`。
2. 非法 `level` 自动降级为 `text`。
3. `field_id` 和 `xml_tag` 会规范化为 ASCII snake_case。
4. `extend_current_schema` 模式默认跳过与已有字段冲突的建议；只有勾选“允许替换已有字段定义”后才会处理替换。
5. `generate_new_schema` 模式应用前会再次确认，防止误替换当前 Schema。

## 5. OpenAI API Invocation / OpenAI API 调用方式

The software uses the official OpenAI Python SDK and the Responses API by default. The default model field is:

```text
gpt-5.4-mini-2026-03-17
```

For image inputs, the runtime request uses `input_text` plus `input_image`, with local images converted to data URLs. For PDF inputs without extractable local text, the runtime request uses `input_file` with `file_data`. Text, pasted text, HTML and webpage sources use `input_text` only.

本软件默认使用 OpenAI 官方 Python SDK 与 Responses API。图片输入采用 `input_text` + `input_image`，本地图片会转换为 data URL；无法本地抽取文本的 PDF 会采用 `input_file` + `file_data`；文本、粘贴文本、HTML 与网页来源则采用 `input_text`。
