from __future__ import annotations

import base64
import html
import json
import mimetypes
import re
import socket
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .config import PROVIDER_DEFAULTS, Settings
from .models import DATA_TYPES, FIELD_LEVELS, MetadataField, MetadataProject, MetadataRecord, MetadataSchema
from .utils import safe_read_text, slugify

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore[assignment]

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm"}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}

EXTRACT_SYSTEM_PROMPT = """You are a schema-bound metadata extraction assistant for BFSU MetadataLens.
The active project information and active metadata schema supplied in INPUT_JSON are authoritative.
Use ONLY field_id values present in project_context.schema.fields. Never create or rename a field.
Respect each field's data type, required/repeatable flags, controlled vocabulary, examples, level,
description and validation rule. Use current_record.existing_values only as context; preserve an
existing value unless source evidence clearly supports a better value. Prefer explicit evidence.
If uncertain, leave the value empty rather than inventing metadata. Return one JSON object only,
with keys record_id, record_type, fields, warnings and overall_confidence. Each fields[field_id]
item must contain value, confidence, evidence, reasoning_note and source."""

SCHEMA_SYSTEM_PROMPT = """You design metadata schemas for linguistic and corpus research in BFSU MetadataLens.
The active project information and existing schema supplied in INPUT_JSON are authoritative context.
Return one JSON object only. Use practical, non-redundant fields. Supported data_type values are:
string, integer, float, date, year, boolean, enum, long_text, language_code, file_path. Supported levels:
corpus, subcorpus, text, version, file, speaker, segment, alignment, relation, project. Every field must
include field_id, label_zh, label_en, xml_tag, data_type, required, repeatable, default_value,
controlled_values, description_zh, description_en, example, level, parent, order, visible, editable,
sensitive, validation_rule, rationale and confidence."""


class LLMCancelledError(RuntimeError):
    """Raised when the UI has cancelled an LLM job."""


class LLMRequestError(RuntimeError):
    """Remote-provider error retaining provider/status/detail for friendly UI messages."""

    def __init__(self, provider: str, detail: str, status: int | None = None) -> None:
        self.provider = provider
        self.detail = detail
        self.status = status
        super().__init__(detail)


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
    overall_confidence: float = 0.0


@dataclass
class SchemaCandidate:
    field: MetadataField
    action: str = "add"
    rationale: str = ""
    confidence: float = 0.0


@dataclass
class SchemaGenerationResult:
    schema_name: str = "AI Schema"
    schema_version: str = "1.0"
    candidates: list[SchemaCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs) -> None:  # noqa: ANN001
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
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip() + " ")

    def text(self) -> str:
        value = html.unescape("".join(self.parts))
        value = re.sub(r"[ \t\r\f\v]+", " ", value)
        return re.sub(r"\n\s*\n+", "\n\n", value).strip()


def _check_cancel(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise LLMCancelledError("LLM operation cancelled by user.")


def truncate_text(text: str, max_chars: int) -> tuple[str, list[str]]:
    if len(text) <= max_chars:
        return text, []
    head = max_chars // 2
    tail = max_chars - head
    return (
        text[:head] + "\n\n[...TRUNCATED...]\n\n" + text[-tail:],
        [f"Source text truncated from {len(text)} to {max_chars} characters."],
    )


def read_pasted_text(text: str, max_chars: int = 60000) -> SourcePayload:
    text, warnings = truncate_text(text, max_chars)
    return SourcePayload("pasted_text", text=text, warnings=warnings)


def read_webpage(url: str, max_chars: int = 60000) -> SourcePayload:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are supported.")
    req = urllib.request.Request(url, headers={"User-Agent": "BFSU-MetadataLens/3.2"})
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as resp:  # noqa: S310
        raw = resp.read()
        content_type = resp.headers.get("Content-Type", "")
    charset = "utf-8"
    match = re.search(r"charset=([^;]+)", content_type, re.I)
    if match:
        charset = match.group(1).strip()
    text = raw.decode(charset, errors="replace")
    if "html" in content_type.lower() or "<html" in text[:1000].lower():
        parser = _HTMLTextExtractor()
        parser.feed(text)
        text = parser.text()
    text, warnings = truncate_text(text, max_chars)
    return SourcePayload("webpage", text=text, url=url, mime_type=content_type, warnings=warnings)


def read_source_file(path: Path, max_chars: int = 60000) -> SourcePayload:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return SourcePayload(
            "image_file",
            file_path=path,
            file_name=path.name,
            mime_type=mime,
            binary_base64=base64.b64encode(path.read_bytes()).decode("ascii"),
            is_image=True,
        )
    if suffix in SUPPORTED_PDF_EXTENSIONS:
        warnings: list[str] = []
        text = ""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages: list[str] = []
            for i, page in enumerate(reader.pages[:30], 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(f"\n[PDF page {i}]\n{page_text}")
            text = "\n".join(pages).strip()
            if len(reader.pages) > 30:
                warnings.append("Only the first 30 PDF pages were locally extracted.")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Local PDF text extraction failed: {exc}")
        if text:
            text, more = truncate_text(text, max_chars)
            return SourcePayload("pdf_text", text=text, file_path=path, file_name=path.name, mime_type=mime, warnings=warnings + more)
        return SourcePayload(
            "pdf_file",
            file_path=path,
            file_name=path.name,
            mime_type=mime,
            binary_base64=base64.b64encode(path.read_bytes()).decode("ascii"),
            is_pdf_file_input=True,
            warnings=warnings,
        )
    if suffix in {".html", ".htm"}:
        parser = _HTMLTextExtractor()
        parser.feed(safe_read_text(path))
        text, warnings = truncate_text(parser.text(), max_chars)
        return SourcePayload("html_file", text=text, file_path=path, file_name=path.name, mime_type=mime, warnings=warnings)
    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        text, warnings = truncate_text(safe_read_text(path), max_chars)
        return SourcePayload("text_file", text=text, file_path=path, file_name=path.name, mime_type=mime, warnings=warnings)
    raise ValueError(f"Unsupported file type: {suffix}")


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
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("The model response did not contain a JSON object.")
    return json.loads(match.group(0))


def _http_error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return str(exc)
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                return str(err.get("message") or err.get("code") or body)
            if err:
                return str(err)
            return str(data.get("message") or body)
    except Exception:  # noqa: BLE001
        pass
    return body[:1600] or str(exc)


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
    provider: str,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    _check_cancel(cancel_event)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise LLMRequestError(provider, _http_error_detail(exc), status=int(exc.code)) from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise LLMRequestError(provider, f"Network/timeout error: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise LLMRequestError(provider, f"API request failed: {exc}") from exc
    _check_cancel(cancel_event)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMRequestError(provider, "The provider returned a non-JSON HTTP response.") from exc


class ProviderClient:
    def __init__(self, settings: Settings, provider: str | None = None) -> None:
        self.settings = settings
        self.provider = (provider or settings.active_provider).lower()
        self.cfg = settings.provider(self.provider)
        if not self.cfg.api_key.strip():
            label = PROVIDER_DEFAULTS.get(self.provider, {}).get("label", self.provider)
            raise LLMRequestError(self.provider, f"API key is not configured for {label}.")

    def request_json(
        self,
        system_prompt: str,
        prompt: dict[str, Any],
        source: SourcePayload | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        _check_cancel(cancel_event)
        user_text = "Return JSON only. INPUT_JSON:\n" + json.dumps(prompt, ensure_ascii=False, indent=2)
        if self.provider == "openai":
            result = self._openai(system_prompt, user_text, source, cancel_event)
        elif self.provider in {"deepseek", "qwen"}:
            result = self._openai_compatible(system_prompt, user_text, source, cancel_event)
        elif self.provider == "claude":
            result = self._claude(system_prompt, user_text, source, cancel_event)
        elif self.provider == "gemini":
            result = self._gemini(system_prompt, user_text, source, cancel_event)
        else:
            raise LLMRequestError(self.provider, f"Unsupported provider: {self.provider}")
        _check_cancel(cancel_event)
        return result

    def _openai(self, system_prompt: str, user_text: str, source: SourcePayload | None, cancel_event: threading.Event | None) -> dict[str, Any]:
        if OpenAI is None:
            raise LLMRequestError("openai", "The openai package is required. Run: pip install openai")
        _check_cancel(cancel_event)
        client = OpenAI(
            api_key=self.cfg.api_key.strip(),
            base_url=self.cfg.base_url.rstrip("/"),
            timeout=float(self.settings.request_timeout),
            max_retries=1,
        )
        content: list[dict[str, Any]] = [{"type": "input_text", "text": user_text}]
        if source and source.is_image:
            content.append({"type": "input_image", "image_url": f"data:{source.mime_type};base64,{source.binary_base64}"})
        elif source and source.is_pdf_file_input:
            content.append({"type": "input_file", "filename": source.file_name or "document.pdf", "file_data": f"data:{source.mime_type};base64,{source.binary_base64}"})
        try:
            response = client.responses.create(
                model=self.cfg.model,
                instructions=system_prompt,
                input=[{"role": "user", "content": content}],
                text={"format": {"type": "json_object"}},
            )
            _check_cancel(cancel_event)
            return parse_json_object(getattr(response, "output_text", "") or "")
        except LLMCancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None)
            detail = str(getattr(exc, "message", "") or exc)
            raise LLMRequestError("openai", detail, status=status if isinstance(status, int) else None) from exc

    def _openai_compatible(self, system_prompt: str, user_text: str, source: SourcePayload | None, cancel_event: threading.Event | None) -> dict[str, Any]:
        # Qwen's OpenAI-compatible endpoint accepts data-URL images. DeepSeek's
        # default Flash model is intentionally treated as text-first; scanned
        # PDFs/images should use OpenAI, Qwen-VL, Claude or Gemini instead.
        if source and source.is_pdf_file_input:
            raise LLMRequestError(self.provider, f"{PROVIDER_DEFAULTS[self.provider]['label']} cannot use this scanned/image-only PDF in the current compatibility mode. Use a PDF with extractable text or select OpenAI/Claude/Gemini.")
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        if source and source.is_image:
            if self.provider != "qwen":
                raise LLMRequestError(self.provider, f"{PROVIDER_DEFAULTS[self.provider]['label']} is configured as a text-first model. Use a text/PDF-with-extractable-text source or select a multimodal provider.")
            user_content: Any = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:{source.mime_type};base64,{source.binary_base64}"}},
            ]
        else:
            user_content = user_text
        messages.append({"role": "user", "content": user_content})
        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        data = _post_json(url, {"Authorization": f"Bearer {self.cfg.api_key.strip()}"}, payload, self.settings.request_timeout, self.provider, cancel_event)
        try:
            return parse_json_object(data["choices"][0]["message"]["content"])
        except Exception as exc:  # noqa: BLE001
            raise LLMRequestError(self.provider, f"Unexpected provider response structure: {exc}") from exc

    def _claude(self, system_prompt: str, user_text: str, source: SourcePayload | None, cancel_event: threading.Event | None) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        if source and source.is_image:
            content.insert(0, {"type": "image", "source": {"type": "base64", "media_type": source.mime_type, "data": source.binary_base64}})
        elif source and source.is_pdf_file_input:
            content.insert(0, {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": source.binary_base64}})
        payload = {
            "model": self.cfg.model,
            "max_tokens": 8192,
            "temperature": 0.1,
            "system": system_prompt,
            "messages": [{"role": "user", "content": content}],
        }
        data = _post_json(
            self.cfg.base_url.rstrip("/") + "/v1/messages",
            {"x-api-key": self.cfg.api_key.strip(), "anthropic-version": "2023-06-01"},
            payload,
            self.settings.request_timeout,
            "claude",
            cancel_event,
        )
        text = "\n".join(item.get("text", "") for item in data.get("content", []) if item.get("type") == "text")
        try:
            return parse_json_object(text)
        except Exception as exc:  # noqa: BLE001
            raise LLMRequestError("claude", f"Claude returned an unexpected response: {exc}") from exc

    def _gemini(self, system_prompt: str, user_text: str, source: SourcePayload | None, cancel_event: threading.Event | None) -> dict[str, Any]:
        parts: list[dict[str, Any]] = [{"text": user_text}]
        if source and (source.is_image or source.is_pdf_file_input):
            parts.insert(0, {"inlineData": {"mimeType": source.mime_type, "data": source.binary_base64}})
        model = urllib.parse.quote(self.cfg.model, safe="")
        url = f"{self.cfg.base_url.rstrip('/')}/models/{model}:generateContent?key={urllib.parse.quote(self.cfg.api_key.strip())}"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        }
        data = _post_json(url, {}, payload, self.settings.request_timeout, "gemini", cancel_event)
        try:
            text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            return parse_json_object(text)
        except Exception as exc:  # noqa: BLE001
            raise LLMRequestError("gemini", f"Gemini returned an unexpected response: {exc}") from exc


def schema_prompt_fields(project: MetadataProject) -> list[dict[str, Any]]:
    return [
        {
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
            "visible": f.visible,
            "editable": f.editable,
            "validation_rule": f.validation_rule,
            "sensitive": f.sensitive,
        }
        for f in project.schema.sorted_fields(visible_only=True)
    ]


def project_prompt_context(project: MetadataProject) -> dict[str, Any]:
    """Return the active project + schema context sent with every metadata request."""
    info = project.project_info
    return {
        "project": {
            "project_id": info.project_id,
            "project_name": info.project_name,
            "corpus_type": info.corpus_type,
            "interface_language": info.interface_language,
            "created_at": info.created_at,
            "updated_at": info.updated_at,
            "record_count": len(project.records),
        },
        "schema": {
            "schema_id": project.schema.schema_id,
            "schema_name": project.schema.schema_name,
            "schema_version": project.schema.schema_version,
            "field_count": len(project.schema.fields),
            "fields": schema_prompt_fields(project),
        },
    }


def build_extraction_prompt(project: MetadataProject, record: MetadataRecord, source: SourcePayload) -> dict[str, Any]:
    """Build a schema-bound prompt. Kept public for tests and future UI extensions."""
    return {
        "task": "extract_metadata_for_current_record",
        "binding_rule": "Use only field IDs defined in project_context.schema.fields and interpret the source within the active project context.",
        "project_context": project_prompt_context(project),
        "current_record": {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "existing_values": {f.field_id: record.get_values(f.field_id) for f in project.schema.fields},
        },
        "source": {
            "source_kind": source.source_kind,
            "file_name": source.file_name,
            "url": source.url,
            "mime_type": source.mime_type,
            "text": source.text,
        },
    }


def extract_metadata(
    settings: Settings,
    project: MetadataProject,
    record: MetadataRecord,
    source: SourcePayload,
    provider: str | None = None,
    cancel_event: threading.Event | None = None,
) -> ExtractionResult:
    _check_cancel(cancel_event)
    prompt = build_extraction_prompt(project, record, source)
    raw = ProviderClient(settings, provider).request_json(EXTRACT_SYSTEM_PROMPT, prompt, source, cancel_event)
    _check_cancel(cancel_event)
    result = ExtractionResult(
        record_id=str(raw.get("record_id", "") or ""),
        record_type=str(raw.get("record_type", "") or ""),
        warnings=list(source.warnings) + [str(x) for x in raw.get("warnings", []) if str(x).strip()],
    )
    try:
        result.overall_confidence = float(raw.get("overall_confidence", 0) or 0)
    except Exception:  # noqa: BLE001
        pass
    fields = raw.get("fields", {}) if isinstance(raw.get("fields", {}), dict) else {}
    for fid, payload in fields.items():
        field_def = project.schema.get_field(fid)
        if not field_def:
            result.warnings.append(f"Ignored non-schema field: {fid}")
            continue
        if not isinstance(payload, dict):
            payload = {"value": payload}
        value = payload.get("value", "")
        if field_def.repeatable and not isinstance(value, list):
            value = [x.strip() for x in str(value).split(";") if x.strip()]
        if not field_def.repeatable and isinstance(value, list):
            value = next((x for x in value if str(x).strip()), "")
        if value in (None, "", []):
            continue
        try:
            confidence = max(0.0, min(1.0, float(payload.get("confidence", 0) or 0)))
        except Exception:  # noqa: BLE001
            confidence = 0.0
        result.fields[fid] = ExtractedField(
            fid,
            value,
            confidence,
            str(payload.get("evidence", "") or ""),
            str(payload.get("reasoning_note", "") or ""),
            str(payload.get("source", "") or ""),
        )
    return result


def apply_extraction(
    project: MetadataProject,
    record: MetadataRecord,
    result: ExtractionResult,
    *,
    overwrite: bool = False,
    selected: set[str] | None = None,
) -> int:
    count = 0
    for fid, item in result.fields.items():
        if selected is not None and fid not in selected:
            continue
        if record.get_value(fid).strip() and not overwrite:
            continue
        record.set_value(fid, item.value)
        count += 1
    if result.record_type:
        record.record_type = result.record_type
    if count:
        project.touch()
    return count


def generate_schema(
    settings: Settings,
    project: MetadataProject,
    requirements: str,
    source: SourcePayload,
    mode: str = "extend_current_schema",
    provider: str | None = None,
    cancel_event: threading.Event | None = None,
) -> SchemaGenerationResult:
    existing = [
        {
            key: getattr(f, key)
            for key in (
                "field_id", "label_zh", "label_en", "xml_tag", "data_type", "required", "repeatable",
                "default_value", "controlled_values", "description_zh", "description_en", "example", "level",
                "parent", "order", "visible", "editable", "sensitive", "validation_rule",
            )
        }
        for f in project.schema.sorted_fields()
    ]
    prompt = {
        "task": "generate_or_extend_metadata_schema",
        "mode": mode,
        "project_context": project_prompt_context(project),
        "existing_schema_fields": existing,
        "user_requirements": requirements,
        "source": {
            "source_kind": source.source_kind,
            "file_name": source.file_name,
            "url": source.url,
            "mime_type": source.mime_type,
            "text": source.text,
        },
    }
    raw = ProviderClient(settings, provider).request_json(SCHEMA_SYSTEM_PROMPT, prompt, source, cancel_event)
    _check_cancel(cancel_event)
    result = SchemaGenerationResult(
        schema_name=str(raw.get("schema_name", "AI Schema") or "AI Schema"),
        schema_version=str(raw.get("schema_version", "1.0") or "1.0"),
        warnings=list(source.warnings) + [str(x) for x in raw.get("warnings", [])],
    )
    seen: set[str] = set()
    fields = raw.get("fields", []) if isinstance(raw.get("fields", []), list) else []
    for i, item in enumerate(fields, 1):
        if not isinstance(item, dict):
            continue
        fid = slugify(str(item.get("field_id", f"field_{i}")), fallback=f"field_{i}")
        if fid in seen:
            continue
        seen.add(fid)
        dtype = str(item.get("data_type", "string"))
        dtype = dtype if dtype in DATA_TYPES else "string"
        level = str(item.get("level", "text"))
        level = level if level in FIELD_LEVELS else "text"
        field_def = MetadataField(
            field_id=fid,
            label_zh=str(item.get("label_zh", fid)),
            label_en=str(item.get("label_en", fid)),
            xml_tag=slugify(str(item.get("xml_tag", fid)), fallback=fid),
            data_type=dtype,
            required=bool(item.get("required", False)),
            repeatable=bool(item.get("repeatable", False)),
            default_value=str(item.get("default_value", "") or ""),
            controlled_values=[str(x) for x in item.get("controlled_values", []) if str(x).strip()] if isinstance(item.get("controlled_values", []), list) else [],
            description_zh=str(item.get("description_zh", "") or ""),
            description_en=str(item.get("description_en", "") or ""),
            example=str(item.get("example", "") or ""),
            level=level,
            parent=str(item.get("parent", "") or ""),
            order=int(item.get("order", i) or i),
            visible=bool(item.get("visible", True)),
            editable=bool(item.get("editable", True)),
            sensitive=bool(item.get("sensitive", False)),
            validation_rule=str(item.get("validation_rule", "") or ""),
        )
        try:
            confidence = float(item.get("confidence", 0) or 0)
        except Exception:  # noqa: BLE001
            confidence = 0.0
        result.candidates.append(
            SchemaCandidate(
                field_def,
                str(item.get("action", "add") or "add"),
                str(item.get("rationale", "") or ""),
                max(0.0, min(1.0, confidence)),
            )
        )
    return result


def apply_schema_generation(
    project: MetadataProject,
    result: SchemaGenerationResult,
    *,
    mode: str,
    selected: set[str] | None = None,
    replace_existing: bool = False,
) -> int:
    chosen = [candidate for candidate in result.candidates if selected is None or candidate.field.field_id in selected]
    if mode == "generate_new_schema":
        project.schema = MetadataSchema(schema_name=result.schema_name, schema_version=result.schema_version)
    count = 0
    for candidate in chosen:
        existing = project.schema.get_field(candidate.field.field_id)
        if existing and not replace_existing:
            continue
        project.schema.add_field(candidate.field, replace=bool(existing))
        count += 1
    project.schema.reindex()
    if count or mode == "generate_new_schema":
        project.touch()
    return count


def friendly_llm_error(exc: Exception, provider: str, language: str = "zh_CN") -> str:
    """Convert provider/network exceptions into a concise actionable user message."""
    label = PROVIDER_DEFAULTS.get(provider, {}).get("label", provider or "LLM")
    status = getattr(exc, "status", None)
    detail = getattr(exc, "detail", None) or str(exc)
    lower = detail.lower()
    zh = language.startswith("zh")

    if isinstance(exc, LLMCancelledError):
        return "任务已由用户停止。" if zh else "The task was stopped by the user."
    if status == 401 or "invalid api key" in lower or "api key is not configured" in lower or "authentication" in lower or "unauthorized" in lower:
        lead = f"{label} API Key 未配置或无效。请检查“大模型接口设置”中的 API Key。" if zh else f"The {label} API key is missing or invalid. Check it in LLM Provider Settings."
    elif status == 403 or "permission" in lower or "forbidden" in lower:
        lead = f"{label} 拒绝了当前请求。请检查模型访问权限、账号区域或 API 权限。" if zh else f"{label} rejected the request. Check model access, account region, and API permissions."
    elif status == 429 or "rate limit" in lower or "quota" in lower or "insufficient" in lower or "balance" in lower:
        lead = f"{label} 当前额度不足或达到调用频率限制。请检查余额/配额，稍后重试。" if zh else f"{label} quota/rate limit was reached. Check balance or quota and retry later."
    elif status == 404 or "model_not_found" in lower or "model not found" in lower:
        lead = f"{label} 未找到所填写的模型或接口地址。请检查模型名称与 Base URL。" if zh else f"{label} could not find the configured model or endpoint. Check the model name and Base URL."
    elif status is not None and int(status) >= 500:
        lead = f"{label} 远程服务暂时不可用（HTTP {status}）。请稍后重试。" if zh else f"{label} is temporarily unavailable (HTTP {status}). Try again later."
    elif "timeout" in lower or "timed out" in lower:
        lead = f"连接 {label} 超时。请检查网络，或在网络稳定后重试。" if zh else f"The connection to {label} timed out. Check the network and retry."
    elif "network" in lower or "urlopen" in lower or "name resolution" in lower or "connection" in lower:
        lead = f"无法连接 {label}。请检查网络、代理设置和 API Base URL。" if zh else f"Could not connect to {label}. Check the network, proxy settings, and API Base URL."
    elif "json" in lower or "response structure" in lower or "unexpected response" in lower:
        lead = f"{label} 返回了程序无法解析的结果。建议重试，或更换模型。" if zh else f"{label} returned a response that could not be parsed. Retry or use another model."
    else:
        lead = f"{label} 调用失败。请检查接口设置后重试。" if zh else f"The {label} request failed. Check provider settings and retry."

    detail_label = "技术信息" if zh else "Technical details"
    return f"{lead}\n\n{detail_label}: {detail[:1200]}"
