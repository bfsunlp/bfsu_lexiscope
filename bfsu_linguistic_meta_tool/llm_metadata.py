"""Large-language-model assisted metadata extraction.

This module is intentionally GUI-independent.  It prepares schema-bound JSON
prompts, reads supported source files, calls the ChatGPT/OpenAI API, normalizes
JSON output, and applies validated values to the current metadata record.
"""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import os
import re
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]

from models import MetadataField, MetadataProject, MetadataRecord
from utils import safe_read_text


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
MAX_SOURCE_CHARS = 60000
SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm"}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


INTERNAL_SYSTEM_PROMPT = """
You are a schema-bound metadata extraction assistant for a linguistic corpus
metadata editor. Your task is to infer metadata values from the supplied source
content and fill the CURRENT record only.

Critical rules:
1. Use ONLY the field_id values provided in input_json.fields. Never create,
   rename, translate, or output any field that is not in the current schema.
2. Treat the current project schema as the authority. Respect each field's
   data_type, repeatable flag, required flag, controlled_values, xml_tag,
   labels, descriptions, examples, and validation_rule.
3. Extract explicit metadata when available. Infer cautiously only when the
   evidence is strong. If a value is uncertain, leave it empty and explain why
   in warnings rather than inventing metadata.
4. For enum fields, return only one of controlled_values. If the document uses a
   synonym, map it to the nearest controlled value only when unambiguous;
   otherwise leave the field empty.
5. For language_code fields, prefer ISO-style codes such as zh, en, zh-CN,
   en-US, ja, de, fr, es, ru. Do not return language names unless the schema's
   controlled vocabulary explicitly requires names.
6. For year fields, return YYYY only. For date fields, prefer YYYY-MM-DD.
7. For repeatable fields, return a JSON array. For non-repeatable fields, return
   one scalar string/number/boolean as appropriate.
8. Preserve existing metadata unless the source clearly provides a better value.
   Use existing_values as context, not as evidence from the source.
9. Return JSON only. Do not include markdown, comments, explanations outside the
   JSON object, or XML.

Expected output JSON object:
{
  "record_id": "optional suggested record_id or empty string",
  "record_type": "optional suggested record_type or empty string",
  "fields": {
    "field_id_from_schema": {
      "value": "string | number | boolean | array | empty string",
      "confidence": 0.0,
      "evidence": "short quote or location from the source",
      "reasoning_note": "brief reason for this extraction",
      "source": "explicit | inferred | existing | empty"
    }
  },
  "unmapped_candidates": [
    {"label": "metadata found but not in schema", "value": "...", "evidence": "..."}
  ],
  "warnings": ["short warning text"],
  "overall_confidence": 0.0
}
""".strip()


@dataclass
class LLMSettings:
    api_key: str = ""
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    max_source_chars: int = MAX_SOURCE_CHARS

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.strip())


class AppSettingsStore:
    """Store API settings outside the project XML.

    The API key is stored locally in a user-level JSON settings file.  This is
    intentionally separated from metadata project files so project XML exports
    do not accidentally include the key.
    """

    def __init__(self) -> None:
        self.path = self._settings_path()

    def _settings_path(self) -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home())) / "BFSU_Linguistic_Meta_Tool"
        else:
            base = Path.home() / ".bfsu_linguistic_meta_tool"
        return base / "settings.json"

    def load(self) -> LLMSettings:
        if not self.path.exists():
            return LLMSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return LLMSettings()
        return LLMSettings(
            api_key=str(data.get("openai_api_key", "")),
            model=str(data.get("openai_model", DEFAULT_MODEL) or DEFAULT_MODEL),
            base_url=str(data.get("openai_base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL).rstrip("/"),
            max_source_chars=int(data.get("max_source_chars", MAX_SOURCE_CHARS) or MAX_SOURCE_CHARS),
        )

    def save(self, settings: LLMSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "openai_api_key": settings.api_key.strip(),
            "openai_model": settings.model.strip() or DEFAULT_MODEL,
            "openai_base_url": settings.base_url.strip().rstrip("/") or DEFAULT_BASE_URL,
            "max_source_chars": int(settings.max_source_chars or MAX_SOURCE_CHARS),
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class SourcePayload:
    source_kind: str
    text: str = ""
    file_path: Path | None = None
    file_name: str = ""
    url: str = ""
    mime_type: str = ""
    binary_base64: str = ""
    is_image: bool = False
    is_pdf_file_input: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractedField:
    field_id: str
    value: Any = ""
    confidence: float = 0.0
    evidence: str = ""
    reasoning_note: str = ""
    source: str = ""
    warning: str = ""


@dataclass
class ExtractionResult:
    fields: dict[str, ExtractedField] = field(default_factory=dict)
    record_id: str = ""
    record_type: str = ""
    warnings: list[str] = field(default_factory=list)
    unmapped_candidates: list[dict[str, Any]] = field(default_factory=list)
    overall_confidence: float = 0.0
    raw_json: dict[str, Any] = field(default_factory=dict)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "section", "article", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag.lower() in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text + " ")

    def text(self) -> str:
        text = "".join(self.parts)
        text = html.unescape(text)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()


def html_to_text(raw_html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(raw_html)
    return parser.text()


def truncate_text(text: str, max_chars: int = MAX_SOURCE_CHARS) -> tuple[str, list[str]]:
    warnings: list[str] = []
    text = text or ""
    if len(text) <= max_chars:
        return text, warnings
    head = max_chars // 2
    tail = max_chars - head
    warnings.append(f"Source text was truncated from {len(text)} to {max_chars} characters before API submission.")
    return text[:head] + "\n\n[...TRUNCATED...]\n\n" + text[-tail:], warnings


def read_webpage(url: str, max_chars: int = MAX_SOURCE_CHARS) -> SourcePayload:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are supported.")
    req = urllib.request.Request(url, headers={"User-Agent": "BFSU-Linguistic-Meta-Tool/1.1"})
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as resp:  # noqa: S310
        raw = resp.read()
        content_type = resp.headers.get("Content-Type", "")
    charset = "utf-8"
    m = re.search(r"charset=([^;]+)", content_type, re.I)
    if m:
        charset = m.group(1).strip()
    try:
        decoded = raw.decode(charset, errors="replace")
    except LookupError:
        decoded = raw.decode("utf-8", errors="replace")
    text = html_to_text(decoded) if "html" in content_type.lower() or "<html" in decoded[:1000].lower() else decoded
    text, warnings = truncate_text(text, max_chars)
    return SourcePayload(source_kind="webpage", text=text, url=url, mime_type=content_type, warnings=warnings)


def read_source_file(path: Path, max_chars: int = MAX_SOURCE_CHARS) -> SourcePayload:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    suffix = path.suffix.lower()
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        binary = path.read_bytes()
        return SourcePayload(
            source_kind="image_file",
            file_path=path,
            file_name=path.name,
            mime_type=mime_type,
            binary_base64=base64.b64encode(binary).decode("ascii"),
            is_image=True,
        )

    if suffix in SUPPORTED_PDF_EXTENSIONS:
        warnings: list[str] = []
        text = ""
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages[:20], start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(f"\n[PDF page {i}]\n{page_text}")
            text = "\n".join(pages).strip()
            if len(reader.pages) > 20:
                warnings.append("Only the first 20 PDF pages were locally extracted before API submission.")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Local PDF text extraction failed: {exc}")
        if text:
            text, more = truncate_text(text, max_chars)
            return SourcePayload(source_kind="pdf_text", text=text, file_path=path, file_name=path.name, mime_type=mime_type, warnings=warnings + more)
        binary = path.read_bytes()
        warnings.append("No extractable PDF text was found. The PDF will be sent to the Responses API as a file input if the selected model supports file input.")
        return SourcePayload(
            source_kind="pdf_file",
            file_path=path,
            file_name=path.name,
            mime_type=mime_type,
            binary_base64=base64.b64encode(binary).decode("ascii"),
            is_pdf_file_input=True,
            warnings=warnings,
        )

    if suffix in {".html", ".htm"}:
        raw = safe_read_text(path)
        text = html_to_text(raw)
        text, warnings = truncate_text(text, max_chars)
        return SourcePayload(source_kind="html_file", text=text, file_path=path, file_name=path.name, mime_type="text/html", warnings=warnings)

    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        text = safe_read_text(path)
        text, warnings = truncate_text(text, max_chars)
        return SourcePayload(source_kind="text_file", text=text, file_path=path, file_name=path.name, mime_type=mime_type, warnings=warnings)

    raise ValueError(f"Unsupported file type: {suffix}. Supported: txt/md/csv/tsv/json/xml/html/htm/pdf/jpg/jpeg/png/webp/bmp/gif/tif/tiff.")


def read_pasted_text(text: str, max_chars: int = MAX_SOURCE_CHARS) -> SourcePayload:
    text, warnings = truncate_text(text, max_chars)
    return SourcePayload(source_kind="pasted_text", text=text, warnings=warnings)


def schema_to_prompt_fields(project: MetadataProject) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for f in project.schema.sorted_fields(visible_only=True):
        fields.append(
            {
                "field_id": f.field_id,
                "xml_tag": f.xml_tag,
                "label_zh": f.label_zh,
                "label_en": f.label_en,
                "data_type": f.data_type,
                "required": f.required,
                "repeatable": f.repeatable,
                "controlled_values": f.controlled_values,
                "description_zh": f.description_zh,
                "description_en": f.description_en,
                "example": f.example,
                "level": f.level,
                "validation_rule": f.validation_rule,
                "sensitive": f.sensitive,
            }
        )
    return fields


def build_prompt_input(project: MetadataProject, record: MetadataRecord, source: SourcePayload) -> dict[str, Any]:
    existing_values = {f.field_id: record.get_values(f.field_id) for f in project.schema.sorted_fields(visible_only=True)}
    return {
        "task": "extract_metadata_for_current_record",
        "schema_binding_rule": "Only output field IDs that appear in fields[].field_id. Values must match the current schema definition.",
        "project": {
            "project_name": project.project_info.project_name,
            "corpus_type": project.project_info.corpus_type,
            "schema_name": project.schema.schema_name,
            "schema_version": project.schema.schema_version,
        },
        "current_record": {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "existing_values": existing_values,
        },
        "fields": schema_to_prompt_fields(project),
        "source": {
            "source_kind": source.source_kind,
            "file_name": source.file_name,
            "url": source.url,
            "mime_type": source.mime_type,
            "text": source.text,
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
                    "source": "explicit | inferred | existing | empty",
                }
            },
            "warnings": ["short warning text"],
            "overall_confidence": "number from 0 to 1",
        },
    }


class OpenAIHTTPClient:
    """OpenAI SDK wrapper using the official Responses API.

    This wrapper uses the official Python SDK and a single Responses API path
    for text, image, and PDF/file inputs.
    """

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        if OpenAI is None:
            raise RuntimeError("The openai Python package is not installed. Please run: pip install openai")
        kwargs: dict[str, Any] = {"api_key": self.settings.api_key.strip()}
        base_url = (self.settings.base_url or DEFAULT_BASE_URL).strip().rstrip("/")
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)  # type: ignore[operator]

    def extract(self, project: MetadataProject, record: MetadataRecord, source: SourcePayload) -> dict[str, Any]:
        prompt_input = build_prompt_input(project, record, source)
        if source.is_pdf_file_input:
            return self._extract_with_responses_file(prompt_input, source)
        if source.is_image:
            return self._extract_with_responses_image(prompt_input, source)
        return self._extract_with_responses_text(prompt_input)

    def _responses_json(self, instructions: str, content: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            response = self.client.responses.create(
                model=self.settings.model.strip() or DEFAULT_MODEL,
                instructions=instructions,
                input=[{"role": "user", "content": content}],
                text={"format": {"type": "json_object"}},
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"OpenAI Responses API call failed: {exc}") from exc
        output_text = getattr(response, "output_text", "") or ""
        if output_text:
            return parse_json_object(output_text)
        try:
            return _parse_responses_json(response.model_dump())
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Unexpected OpenAI Responses API response: {response}") from exc

    def _extract_with_responses_text(self, prompt_input: dict[str, Any]) -> dict[str, Any]:
        user_text = "Return JSON only. INPUT_JSON:\n" + json.dumps(prompt_input, ensure_ascii=False, indent=2)
        return self._responses_json(INTERNAL_SYSTEM_PROMPT, [{"type": "input_text", "text": user_text}])

    def _extract_with_responses_image(self, prompt_input: dict[str, Any], source: SourcePayload) -> dict[str, Any]:
        input_without_text = dict(prompt_input)
        input_without_text["source"] = dict(prompt_input["source"])
        input_without_text["source"].pop("text", None)
        user_text = "Return JSON only. Use the attached image as source evidence. INPUT_JSON:\n" + json.dumps(input_without_text, ensure_ascii=False, indent=2)
        data_uri = f"data:{source.mime_type or 'image/png'};base64,{source.binary_base64}"
        return self._responses_json(
            INTERNAL_SYSTEM_PROMPT,
            [
                {"type": "input_text", "text": user_text},
                {"type": "input_image", "image_url": data_uri},
            ],
        )

    def _extract_with_responses_file(self, prompt_input: dict[str, Any], source: SourcePayload) -> dict[str, Any]:
        input_without_text = dict(prompt_input)
        input_without_text["source"] = dict(prompt_input["source"])
        input_without_text["source"].pop("text", None)
        user_text = "Return JSON only. Use the attached PDF file as source evidence. INPUT_JSON:\n" + json.dumps(input_without_text, ensure_ascii=False, indent=2)
        data_uri = f"data:{source.mime_type or 'application/pdf'};base64,{source.binary_base64}"
        return self._responses_json(
            INTERNAL_SYSTEM_PROMPT,
            [
                {"type": "input_text", "text": user_text},
                {"type": "input_file", "filename": source.file_name or "document.pdf", "file_data": data_uri},
            ],
        )



def _parse_responses_json(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("output_text"), str):
        return parse_json_object(data["output_text"])
    pieces: list[str] = []
    for item in data.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text") or content.get("output_text")
            if text:
                pieces.append(str(text))
    if pieces:
        return parse_json_object("\n".join(pieces))
    raise RuntimeError(f"Unexpected Responses API response: {data}")


def parse_json_object(text: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(text, dict):
        return text
    text = (text or "").strip()
    if not text:
        raise ValueError("The model returned an empty response.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("The model response does not contain a JSON object.")
    return json.loads(m.group(0))


LANGUAGE_ALIASES = {
    "中文": "zh",
    "汉语": "zh",
    "英语": "en",
    "英文": "en",
    "日语": "ja",
    "日文": "ja",
    "德语": "de",
    "法语": "fr",
    "西班牙语": "es",
    "俄语": "ru",
    "chinese": "zh",
    "english": "en",
    "japanese": "ja",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "russian": "ru",
}


def normalize_extraction(project: MetadataProject, raw: dict[str, Any]) -> ExtractionResult:
    result = ExtractionResult(raw_json=raw)
    result.record_id = str(raw.get("record_id") or "").strip()
    result.record_type = str(raw.get("record_type") or "").strip()
    result.warnings = [str(x) for x in raw.get("warnings", []) if str(x).strip()]
    try:
        result.overall_confidence = float(raw.get("overall_confidence") or 0.0)
    except Exception:  # noqa: BLE001
        result.overall_confidence = 0.0
    if isinstance(raw.get("unmapped_candidates"), list):
        result.unmapped_candidates = [x for x in raw["unmapped_candidates"] if isinstance(x, dict)]

    schema_fields = {f.field_id: f for f in project.schema.fields}
    fields_obj = raw.get("fields", {})
    if not isinstance(fields_obj, dict):
        result.warnings.append("Model output did not contain a valid fields object.")
        return result

    for field_id, payload in fields_obj.items():
        if field_id not in schema_fields:
            result.warnings.append(f"Ignored non-schema field returned by model: {field_id}")
            continue
        field_def = schema_fields[field_id]
        if isinstance(payload, dict):
            value = payload.get("value", "")
            confidence = payload.get("confidence", 0.0)
            evidence = str(payload.get("evidence", "") or "")
            reasoning_note = str(payload.get("reasoning_note", "") or "")
            source = str(payload.get("source", "") or "")
        else:
            value = payload
            confidence = 0.0
            evidence = ""
            reasoning_note = ""
            source = ""
        cleaned, warning = coerce_value(field_def, value)
        if _is_empty_value(cleaned):
            continue
        try:
            conf = float(confidence)
        except Exception:  # noqa: BLE001
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        result.fields[field_id] = ExtractedField(
            field_id=field_id,
            value=cleaned,
            confidence=conf,
            evidence=evidence,
            reasoning_note=reasoning_note,
            source=source,
            warning=warning,
        )
        if warning:
            result.warnings.append(f"{field_id}: {warning}")
    return result


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return not any(not _is_empty_value(v) for v in value)
    return str(value).strip() == ""


def coerce_value(field: MetadataField, value: Any) -> tuple[Any, str]:
    warning = ""
    if value is None:
        return "", warning

    if field.repeatable:
        values = value if isinstance(value, list) else [x.strip() for x in str(value).split(";")]
        cleaned_values: list[str] = []
        warnings: list[str] = []
        for item in values:
            cleaned, item_warning = _coerce_scalar(field, item)
            if not _is_empty_value(cleaned):
                cleaned_values.append(str(cleaned))
            if item_warning:
                warnings.append(item_warning)
        return cleaned_values, "; ".join(dict.fromkeys(warnings))

    if isinstance(value, list):
        value = next((v for v in value if not _is_empty_value(v)), "")
        warning = "Multiple values returned for a non-repeatable field; kept the first non-empty value."
    cleaned, scalar_warning = _coerce_scalar(field, value)
    if scalar_warning:
        warning = (warning + " " + scalar_warning).strip()
    return cleaned, warning


def _coerce_scalar(field: MetadataField, value: Any) -> tuple[str, str]:
    text = "" if value is None else str(value).strip()
    if text == "":
        return "", ""
    if field.data_type == "boolean":
        low = text.lower()
        if low in {"true", "1", "yes", "y", "是", "对", "有"}:
            return "true", ""
        if low in {"false", "0", "no", "n", "否", "不", "无"}:
            return "false", ""
        return "", f"Discarded invalid boolean value: {text}"
    if field.data_type == "integer":
        m = re.search(r"-?\d+", text.replace(",", ""))
        return (m.group(0), "") if m else ("", f"Discarded invalid integer value: {text}")
    if field.data_type == "float":
        m = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        return (m.group(0), "") if m else ("", f"Discarded invalid float value: {text}")
    if field.data_type == "year":
        m = re.search(r"(?:18|19|20|21)\d{2}", text)
        return (m.group(0), "") if m else ("", f"Discarded invalid year value: {text}")
    if field.data_type == "date":
        m = re.search(r"((?:18|19|20|21)\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
        if m:
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", ""
        m = re.search(r"(?:18|19|20|21)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}", text)
        return (text.replace("/", "-"), "") if m else ("", f"Discarded invalid date value: {text}")
    if field.data_type == "enum" and field.controlled_values:
        if text in field.controlled_values:
            return text, ""
        lower_map = {v.lower(): v for v in field.controlled_values}
        if text.lower() in lower_map:
            return lower_map[text.lower()], ""
        return "", f"Discarded value outside controlled vocabulary: {text}"
    if field.data_type == "language_code":
        mapped = LANGUAGE_ALIASES.get(text) or LANGUAGE_ALIASES.get(text.lower())
        if mapped:
            text = mapped
        if re.fullmatch(r"[a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?", text):
            return text, ""
        return "", f"Discarded invalid language code: {text}"
    text = re.sub(r"\s+", " ", text).strip()
    return text, ""


def apply_extraction_to_record(project: MetadataProject, record: MetadataRecord, extraction: ExtractionResult, overwrite: bool = False, selected_field_ids: set[str] | None = None) -> int:
    selected = selected_field_ids or set(extraction.fields.keys())
    count = 0
    if extraction.record_type and (overwrite or not record.record_type):
        record.record_type = extraction.record_type
    for field_id, extracted in extraction.fields.items():
        if field_id not in selected:
            continue
        field = project.schema.get_field(field_id)
        if not field or not field.editable:
            continue
        if not overwrite and record.get_value(field_id).strip():
            continue
        record.set_value(field_id, extracted.value)
        count += 1
    if count:
        project.touch()
    return count


class ExtractionWorker:
    """Small helper for Tkinter dialogs: run extraction in a background thread."""

    def __init__(self, settings: LLMSettings, project: MetadataProject, record: MetadataRecord, source: SourcePayload, callback) -> None:  # noqa: ANN001
        self.settings = settings
        self.project = project
        self.record = record
        self.source = source
        self.callback = callback

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            raw = OpenAIHTTPClient(self.settings).extract(self.project, self.record, self.source)
            result = normalize_extraction(self.project, raw)
            result.warnings = self.source.warnings + result.warnings
            self.callback(result, None)
        except Exception as exc:  # noqa: BLE001
            self.callback(None, exc)


# ---------------------------------------------------------------------------
# LLM-assisted schema generation / extension
# ---------------------------------------------------------------------------

INTERNAL_SCHEMA_SYSTEM_PROMPT = """
You are a schema-design assistant for a linguistic corpus metadata editor.
Your task is to design or extend a metadata Schema for corpus linguistics,
corpus construction, and corpus-based translation studies.

Critical rules:
1. Return JSON only. Do not include markdown, XML, comments, or explanatory
   text outside the JSON object.
2. Use only these data_type values: string, integer, float, date, year, boolean,
   enum, long_text, language_code, file_path.
3. Use only these level values: corpus, subcorpus, text, version, file, speaker,
   segment, alignment, relation, project.
4. Every field must contain field_id, label_zh, label_en, xml_tag, data_type,
   required, repeatable, default_value, controlled_values, description_zh,
   description_en, example, level, parent, visible, editable, sensitive,
   validation_rule, action, rationale, and confidence.
5. field_id and xml_tag must be stable ASCII identifiers in snake_case. They
   must not contain spaces, punctuation other than underscore, or Chinese
   characters.
6. For enum fields, controlled_values must be a JSON array of stable values.
7. For language_code fields, prefer ISO-style language codes such as zh, en,
   ja, de, fr, es, ru, zh-CN, en-US.
8. Mark sensitive=true for fields involving personal data such as speaker ID,
   learner background, age group, gender, education background, contact details,
   or other human-subject information.
9. In generate_new_schema mode, return a complete, coherent schema suitable for
   replacing the current schema after user review.
10. In extend_current_schema mode, preserve the current schema as the authority.
    Propose only genuinely useful additions or clearly justified replacements.
    Do not duplicate existing field_id or xml_tag values.
11. Always include a concise rationale and confidence for each proposed field.

Expected output JSON object:
{
  "schema_name": "snake_case_schema_name",
  "schema_version": "1.0",
  "corpus_type": "monolingual | bilingual_parallel | multilingual_parallel | multiple_translations | comparable | learner | spoken | custom",
  "mode": "generate_new_schema | extend_current_schema",
  "fields": [
    {
      "field_id": "title",
      "label_zh": "标题",
      "label_en": "Title",
      "xml_tag": "title",
      "data_type": "string",
      "required": true,
      "repeatable": false,
      "default_value": "",
      "controlled_values": [],
      "description_zh": "字段说明。",
      "description_en": "Field description.",
      "example": "",
      "level": "text",
      "parent": "",
      "order": 1,
      "visible": true,
      "editable": true,
      "sensitive": false,
      "validation_rule": "",
      "action": "add | replace | skip",
      "rationale": "why this field is needed",
      "confidence": 0.0
    }
  ],
  "warnings": ["short warning text"]
}
""".strip()


@dataclass
class SchemaCandidate:
    field: MetadataField
    action: str = "add"  # add, replace, skip
    rationale: str = ""
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class SchemaGenerationResult:
    schema_name: str = "ai_generated_schema"
    schema_version: str = "1.0"
    corpus_type: str = "custom"
    mode: str = "extend_current_schema"
    candidates: list[SchemaCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_json: dict[str, Any] = field(default_factory=dict)


def _schema_field_to_dict(f: MetadataField) -> dict[str, Any]:
    return {
        "field_id": f.field_id,
        "xml_tag": f.xml_tag,
        "label_zh": f.label_zh,
        "label_en": f.label_en,
        "data_type": f.data_type,
        "required": f.required,
        "repeatable": f.repeatable,
        "default_value": f.default_value,
        "controlled_values": f.controlled_values,
        "description_zh": f.description_zh,
        "description_en": f.description_en,
        "example": f.example,
        "level": f.level,
        "parent": f.parent,
        "order": f.order,
        "visible": f.visible,
        "editable": f.editable,
        "sensitive": f.sensitive,
        "validation_rule": f.validation_rule,
    }


def build_schema_prompt_input(project: MetadataProject, mode: str, user_requirements: str, source: SourcePayload) -> dict[str, Any]:
    return {
        "task": "generate_or_extend_metadata_schema",
        "mode": mode,
        "mode_explanation": {
            "generate_new_schema": "Create a complete schema that may replace the current schema after user review.",
            "extend_current_schema": "Propose additions or justified replacements while preserving the current schema.",
        },
        "project": {
            "project_name": project.project_info.project_name,
            "corpus_type": project.project_info.corpus_type,
            "current_schema_name": project.schema.schema_name,
            "current_schema_version": project.schema.schema_version,
        },
        "existing_schema_fields": [_schema_field_to_dict(f) for f in project.schema.sorted_fields()],
        "user_requirements": user_requirements,
        "source": {
            "source_kind": source.source_kind,
            "file_name": source.file_name,
            "url": source.url,
            "mime_type": source.mime_type,
            "text": source.text,
        },
        "output_contract": {
            "schema_name": "snake_case_schema_name",
            "schema_version": "string",
            "corpus_type": "known corpus type or custom",
            "mode": mode,
            "fields": [
                {
                    "field_id": "snake_case ASCII identifier",
                    "label_zh": "Chinese label",
                    "label_en": "English label",
                    "xml_tag": "snake_case XML tag",
                    "data_type": "one allowed data type",
                    "required": "boolean",
                    "repeatable": "boolean",
                    "default_value": "string",
                    "controlled_values": "array; required for enum when applicable",
                    "description_zh": "Chinese field description",
                    "description_en": "English field description",
                    "example": "example value",
                    "level": "one allowed field level",
                    "parent": "parent field_id or empty string",
                    "order": "integer",
                    "visible": "boolean",
                    "editable": "boolean",
                    "sensitive": "boolean",
                    "validation_rule": "regex or empty string",
                    "action": "add | replace | skip",
                    "rationale": "brief design reason",
                    "confidence": "0 to 1",
                }
            ],
            "warnings": ["short warning text"],
        },
    }


class OpenAISchemaClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.http = OpenAIHTTPClient(settings)
        self.settings = settings

    def generate(self, project: MetadataProject, mode: str, user_requirements: str, source: SourcePayload) -> dict[str, Any]:
        prompt_input = build_schema_prompt_input(project, mode, user_requirements, source)
        if source.is_pdf_file_input:
            return self._generate_with_responses_file(prompt_input, source)
        if source.is_image:
            return self._generate_with_responses_image(prompt_input, source)
        return self._generate_with_responses_text(prompt_input)

    def _generate_with_responses_text(self, prompt_input: dict[str, Any]) -> dict[str, Any]:
        user_text = "Return JSON only. INPUT_JSON:\n" + json.dumps(prompt_input, ensure_ascii=False, indent=2)
        return self.http._responses_json(INTERNAL_SCHEMA_SYSTEM_PROMPT, [{"type": "input_text", "text": user_text}])

    def _generate_with_responses_image(self, prompt_input: dict[str, Any], source: SourcePayload) -> dict[str, Any]:
        input_without_text = dict(prompt_input)
        input_without_text["source"] = dict(prompt_input["source"])
        input_without_text["source"].pop("text", None)
        user_text = "Return JSON only. Use the attached image as schema-design evidence. INPUT_JSON:\n" + json.dumps(input_without_text, ensure_ascii=False, indent=2)
        data_uri = f"data:{source.mime_type or 'image/png'};base64,{source.binary_base64}"
        return self.http._responses_json(
            INTERNAL_SCHEMA_SYSTEM_PROMPT,
            [
                {"type": "input_text", "text": user_text},
                {"type": "input_image", "image_url": data_uri},
            ],
        )

    def _generate_with_responses_file(self, prompt_input: dict[str, Any], source: SourcePayload) -> dict[str, Any]:
        input_without_text = dict(prompt_input)
        input_without_text["source"] = dict(prompt_input["source"])
        input_without_text["source"].pop("text", None)
        user_text = "Return JSON only. Use the attached PDF as schema-design evidence. INPUT_JSON:\n" + json.dumps(input_without_text, ensure_ascii=False, indent=2)
        data_uri = f"data:{source.mime_type or 'application/pdf'};base64,{source.binary_base64}"
        return self.http._responses_json(
            INTERNAL_SCHEMA_SYSTEM_PROMPT,
            [
                {"type": "input_text", "text": user_text},
                {"type": "input_file", "filename": source.file_name or "document.pdf", "file_data": data_uri},
            ],
        )


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是", "真"}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value).replace("\n", ";").split(";") if x.strip()]


def normalize_schema_generation(project: MetadataProject, raw: dict[str, Any], requested_mode: str) -> SchemaGenerationResult:
    from models import DATA_TYPES, FIELD_LEVELS
    from utils import slugify

    result = SchemaGenerationResult(raw_json=raw)
    result.schema_name = slugify(str(raw.get("schema_name") or "ai_generated_schema"), fallback="ai_generated_schema")
    result.schema_version = str(raw.get("schema_version") or "1.0").strip() or "1.0"
    result.corpus_type = str(raw.get("corpus_type") or project.project_info.corpus_type or "custom").strip() or "custom"
    result.mode = requested_mode if requested_mode in {"generate_new_schema", "extend_current_schema"} else "extend_current_schema"
    result.warnings = [str(x) for x in raw.get("warnings", []) if str(x).strip()]

    fields = raw.get("fields", [])
    if not isinstance(fields, list):
        result.warnings.append("Model output did not contain a valid fields array.")
        return result

    existing_ids = {f.field_id for f in project.schema.fields}
    existing_tags = {f.xml_tag for f in project.schema.fields}
    seen_ids: set[str] = set()
    seen_tags: set[str] = set()

    for index, item in enumerate(fields, start=1):
        if not isinstance(item, dict):
            result.warnings.append(f"Ignored non-object field suggestion at position {index}.")
            continue
        warnings: list[str] = []
        raw_id = str(item.get("field_id") or item.get("label_en") or item.get("label_zh") or f"field_{index}")
        field_id = slugify(raw_id, fallback=f"field_{index}")
        xml_tag = slugify(str(item.get("xml_tag") or field_id), fallback=field_id)
        if field_id in seen_ids:
            warnings.append(f"Duplicate suggested field_id '{field_id}' was skipped.")
            result.warnings.extend(warnings)
            continue
        if xml_tag in seen_tags:
            xml_tag = field_id
            warnings.append("Duplicate suggested xml_tag was replaced with field_id.")
        data_type = str(item.get("data_type") or "string").strip()
        if data_type not in DATA_TYPES:
            warnings.append(f"Unsupported data_type '{data_type}' was changed to string.")
            data_type = "string"
        level = str(item.get("level") or "text").strip()
        if level not in FIELD_LEVELS:
            warnings.append(f"Unsupported level '{level}' was changed to text.")
            level = "text"
        controlled_values = _as_list(item.get("controlled_values"))
        if data_type == "enum" and not controlled_values:
            warnings.append("Enum field has no controlled_values.")
        try:
            order = int(item.get("order") or index)
        except Exception:  # noqa: BLE001
            order = index
        proposed_action = str(item.get("action") or "add").strip().lower()
        if proposed_action not in {"add", "replace", "skip"}:
            proposed_action = "add"
        if result.mode == "extend_current_schema":
            if field_id in existing_ids or xml_tag in existing_tags:
                proposed_action = "replace" if proposed_action == "replace" else "skip"
        else:
            proposed_action = "add"
        try:
            confidence = float(item.get("confidence") or 0.0)
        except Exception:  # noqa: BLE001
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        metadata_field = MetadataField(
            field_id=field_id,
            label_zh=str(item.get("label_zh") or field_id),
            label_en=str(item.get("label_en") or field_id),
            xml_tag=xml_tag,
            data_type=data_type,
            required=_as_bool(item.get("required"), False),
            repeatable=_as_bool(item.get("repeatable"), False),
            default_value=str(item.get("default_value") or ""),
            controlled_values=controlled_values,
            description_zh=str(item.get("description_zh") or ""),
            description_en=str(item.get("description_en") or ""),
            example=str(item.get("example") or ""),
            level=level,
            parent=str(item.get("parent") or ""),
            order=order,
            visible=_as_bool(item.get("visible"), True),
            editable=_as_bool(item.get("editable"), True),
            sensitive=_as_bool(item.get("sensitive"), False),
            validation_rule=str(item.get("validation_rule") or ""),
        )
        seen_ids.add(field_id)
        seen_tags.add(xml_tag)
        result.candidates.append(
            SchemaCandidate(
                field=metadata_field,
                action=proposed_action,
                rationale=str(item.get("rationale") or ""),
                confidence=confidence,
                warnings=warnings,
            )
        )
        for warning in warnings:
            result.warnings.append(f"{field_id}: {warning}")
    return result


def apply_schema_generation_to_project(
    project: MetadataProject,
    result: SchemaGenerationResult,
    selected_field_ids: set[str] | None = None,
    replace_existing: bool = False,
) -> int:
    from models import MetadataSchema

    selected = selected_field_ids or {c.field.field_id for c in result.candidates}
    chosen = [c for c in result.candidates if c.field.field_id in selected and c.action != "skip"]
    count = 0
    if result.mode == "generate_new_schema":
        schema = MetadataSchema(schema_name=result.schema_name or "ai_generated_schema", schema_version=result.schema_version or "1.0")
        for i, candidate in enumerate(chosen, start=1):
            f = candidate.field
            f.order = i
            schema.add_field(f)
            count += 1
        if count:
            project.schema = schema
            project.project_info.corpus_type = result.corpus_type or project.project_info.corpus_type
            project.touch()
        return count

    for candidate in chosen:
        f = candidate.field
        existing = project.schema.get_field(f.field_id)
        if existing:
            if not replace_existing:
                continue
            project.schema.add_field(f, replace=True)
            count += 1
        elif project.schema.get_field_by_xml_tag(f.xml_tag):
            if not replace_existing:
                continue
            # Avoid replacing by xml_tag through add_field; keep existing field_id safety.
            continue
        else:
            if f.order <= 0:
                f.order = len(project.schema.fields) + 1
            project.schema.add_field(f)
            count += 1
    if count:
        project.schema.reindex()
        project.touch()
    return count


class SchemaGenerationWorker:
    """Run schema generation in a background thread for Tkinter dialogs."""

    def __init__(self, settings: LLMSettings, project: MetadataProject, mode: str, user_requirements: str, source: SourcePayload, callback) -> None:  # noqa: ANN001
        self.settings = settings
        self.project = project
        self.mode = mode
        self.user_requirements = user_requirements
        self.source = source
        self.callback = callback

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            raw = OpenAISchemaClient(self.settings).generate(self.project, self.mode, self.user_requirements, self.source)
            result = normalize_schema_generation(self.project, raw, self.mode)
            result.warnings = self.source.warnings + result.warnings
            self.callback(result, None)
        except Exception as exc:  # noqa: BLE001
            self.callback(None, exc)
