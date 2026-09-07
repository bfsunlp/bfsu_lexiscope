import json
from pathlib import Path

from metadatalens.config import APP_VERSION, PROVIDER_DEFAULTS, SettingsStore
from metadatalens.llm import LLMRequestError, build_extraction_prompt, friendly_llm_error, read_pasted_text
from metadatalens.models import MetadataRecord
from metadatalens.repository import XMLRepository
from metadatalens.templates import TemplateLibrary
from metadatalens.utils import extract_http_urls


def _project():
    lib = TemplateLibrary()
    item = next(x for x in lib.system if x.corpus_type == "monolingual")
    project = XMLRepository().new_project("Prompt Context Test", "monolingual", lib.clone_schema(item), "zh_CN")
    record = project.add_record(MetadataRecord(record_id="TXT_001"))
    record.set_value("title", "Existing title")
    return project, record


def test_v350_identity_and_cost_efficient_defaults():
    assert APP_VERSION == "3.5.5"
    assert PROVIDER_DEFAULTS["openai"]["model"] == "gpt-5.4-nano"
    assert PROVIDER_DEFAULTS["deepseek"]["model"] == "deepseek-v4-flash"
    assert PROVIDER_DEFAULTS["qwen"]["model"] == "qwen3-vl-flash"
    assert PROVIDER_DEFAULTS["claude"]["model"] == "claude-haiku-4-5-20251001"
    assert PROVIDER_DEFAULTS["gemini"]["model"] == "gemini-2.5-flash-lite"


def test_extraction_prompt_contains_project_schema_and_existing_record_values():
    project, record = _project()
    prompt = build_extraction_prompt(project, record, read_pasted_text("sample source"))
    assert prompt["project_context"]["project"]["project_name"] == "Prompt Context Test"
    assert prompt["project_context"]["project"]["corpus_type"] == "monolingual"
    schema_context = prompt["project_context"]["schema"]
    assert schema_context["schema_name"] == project.schema.schema_name
    assert schema_context["field_count"] == len(project.schema.fields)
    assert {field["field_id"] for field in schema_context["fields"]} == set(project.schema.field_ids())
    assert prompt["current_record"]["existing_values"]["title"] == ["Existing title"]


def test_legacy_default_models_migrate_but_custom_models_survive(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openai": {"api_key": "", "base_url": "https://api.openai.com/v1", "model": "gpt-5.4-mini-2026-03-17"},
                    "gemini": {"api_key": "", "base_url": "https://example.invalid", "model": "my-custom-gemini-model"},
                }
            }
        ),
        encoding="utf-8",
    )
    settings = SettingsStore(settings_path).load()
    assert settings.provider("openai").model == "gpt-5.4-nano"
    assert settings.provider("gemini").model == "my-custom-gemini-model"


def test_friendly_llm_error_is_actionable():
    error = LLMRequestError("invalid API key", status=401, detail="invalid API key")
    zh = friendly_llm_error(error, "openai", "zh_CN")
    en = friendly_llm_error(error, "openai", "en_US")
    assert "API Key" in zh and "检查" in zh
    assert "API key" in en and "Check" in en


def test_first_launch_defaults_to_english(tmp_path: Path):
    settings = SettingsStore(tmp_path / "settings.json").load()
    assert settings.language == "en_US"


def test_api_keys_are_saved_only_in_local_credentials_file(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    credentials_path = tmp_path / "credentials.json"
    store = SettingsStore(settings_path, credentials_path)
    settings = store.load()
    settings.provider("openai").api_key = "TEST_OPENAI_KEY"
    settings.provider("gemini").api_key = "TEST_GEMINI_KEY"
    store.save(settings)

    ordinary = settings_path.read_text(encoding="utf-8")
    credentials = credentials_path.read_text(encoding="utf-8")
    assert "TEST_OPENAI_KEY" not in ordinary
    assert "TEST_GEMINI_KEY" not in ordinary
    assert "TEST_OPENAI_KEY" in credentials
    assert "TEST_GEMINI_KEY" in credentials

    reloaded = store.load()
    assert reloaded.provider("openai").api_key == "TEST_OPENAI_KEY"
    assert reloaded.provider("gemini").api_key == "TEST_GEMINI_KEY"

    store.delete_all_api_keys(reloaded)
    assert not credentials_path.exists()
    assert store.load().provider("openai").api_key == ""


def test_legacy_api_key_is_migrated_out_of_settings_json(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"providers": {"openai": {"api_key": "TEST_LEGACY_KEY", "base_url": "https://api.openai.com/v1", "model": "gpt-5.4-nano"}}}),
        encoding="utf-8",
    )
    store = SettingsStore(settings_path)
    settings = store.load()
    assert settings.provider("openai").api_key == "TEST_LEGACY_KEY"
    assert "TEST_LEGACY_KEY" not in settings_path.read_text(encoding="utf-8")
    assert "TEST_LEGACY_KEY" in store.credentials_path.read_text(encoding="utf-8")


def test_extract_http_urls_from_text_preserves_order_and_deduplicates():
    text = """First https://example.org/a.
Second: http://example.com/b?q=1
Duplicate https://example.org/a
Markdown [link](https://example.net/c).
"""
    assert extract_http_urls(text) == [
        "https://example.org/a",
        "http://example.com/b?q=1",
        "https://example.net/c",
    ]


def test_template_clone_can_be_renamed_without_modifying_system_template():
    lib = TemplateLibrary()
    item = lib.system[0]
    original_name = item.schema.schema_name
    clone = lib.clone_schema(item)
    clone.schema_name = "My Renamed Schema"
    assert clone.schema_name == "My Renamed Schema"
    assert item.schema.schema_name == original_name
