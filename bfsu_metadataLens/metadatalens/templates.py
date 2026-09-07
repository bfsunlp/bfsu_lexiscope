from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from .config import SYSTEM_TEMPLATE_DIR, USER_TEMPLATE_DIR
from .models import MetadataSchema
from .schema_manager import load_schema_xml, save_schema_xml
from .utils import slugify


@dataclass(frozen=True)
class TemplateItem:
    name: str
    path: Path
    schema: MetadataSchema
    source: str  # system | user
    corpus_type: str

    @property
    def read_only(self) -> bool:
        return self.source == "system"


def infer_corpus_type(path: Path, schema: MetadataSchema) -> str:
    text = f"{path.stem} {schema.schema_name}".lower()
    aliases = (
        ("multiple_translations", "multiple_translations"),
        ("multilingual", "multilingual_parallel"),
        ("bilingual", "bilingual_parallel"),
        ("monolingual", "monolingual"),
        ("comparable", "comparable"),
        ("learner", "learner"),
        ("spoken", "spoken"),
    )
    for needle, value in aliases:
        if needle in text:
            return value
    return "custom"


class TemplateLibrary:
    def __init__(self) -> None:
        SYSTEM_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        USER_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        self.system: list[TemplateItem] = []
        self.user: list[TemplateItem] = []
        self.refresh()

    def refresh(self) -> None:
        self.system = self._read_dir(SYSTEM_TEMPLATE_DIR, "system")
        self.user = self._read_dir(USER_TEMPLATE_DIR, "user")

    def _read_dir(self, directory: Path, source: str) -> list[TemplateItem]:
        items: list[TemplateItem] = []
        for path in sorted(directory.glob("*.xml")):
            try:
                schema = load_schema_xml(path)
            except Exception:
                continue
            name = schema.schema_name.strip() or path.stem
            items.append(TemplateItem(name, path, schema, source, infer_corpus_type(path, schema)))
        return items

    def clone_schema(self, item: TemplateItem) -> MetadataSchema:
        return deepcopy(item.schema)

    def save_user_template(self, schema: MetadataSchema, preferred_name: str | None = None, *, overwrite: bool = False) -> Path:
        USER_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        base = slugify(preferred_name or schema.schema_name or "user_template", fallback="user_template")
        path = USER_TEMPLATE_DIR / f"{base}.xml"
        if path.exists() and not overwrite:
            index = 2
            while (USER_TEMPLATE_DIR / f"{base}_{index}.xml").exists():
                index += 1
            path = USER_TEMPLATE_DIR / f"{base}_{index}.xml"
        save_schema_xml(schema, path)
        self.refresh()
        return path

    def delete_user_template(self, item: TemplateItem) -> None:
        if item.source != "user":
            raise PermissionError("System templates are read-only and cannot be deleted.")
        item.path.unlink(missing_ok=True)
        self.refresh()
