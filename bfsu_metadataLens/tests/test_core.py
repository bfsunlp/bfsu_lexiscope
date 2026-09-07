from pathlib import Path

from metadatalens.config import APP_NAME, PROVIDER_DEFAULTS
from metadatalens.models import MetadataRecord
from metadatalens.repository import XMLRepository
from metadatalens.templates import TemplateLibrary
from metadatalens.validators import validate_schema


def test_identity_and_providers():
    assert APP_NAME == "BFSU MetadataLens"
    assert {"openai", "deepseek", "qwen", "claude", "gemini"} <= set(PROVIDER_DEFAULTS)


def test_system_templates_are_short_and_valid():
    lib = TemplateLibrary()
    assert len(lib.system) == 7
    assert all("default_schema" not in item.name.lower() for item in lib.system)
    assert all(item.read_only for item in lib.system)
    for item in lib.system:
        assert not [m for m in validate_schema(item.schema) if m.level == "error"]


def test_monolingual_has_no_translation_fields():
    lib = TemplateLibrary()
    item = next(x for x in lib.system if x.corpus_type == "monolingual")
    ids = set(item.schema.field_ids())
    assert "translator" not in ids
    assert "translated_title" not in ids


def test_project_roundtrip(tmp_path: Path):
    lib = TemplateLibrary()
    item = next(x for x in lib.system if x.corpus_type == "monolingual")
    repo = XMLRepository()
    project = repo.new_project("Demo", "monolingual", lib.clone_schema(item), "zh_CN")
    rec = project.add_record(MetadataRecord())
    rec.set_value("title", "Demo title")
    path = tmp_path / "demo.xml"
    repo.save_project(project, path, backup=False)
    loaded = repo.load_project(path)
    assert loaded.records[0].get_value("title") == "Demo title"
