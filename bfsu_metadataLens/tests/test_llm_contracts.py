from metadatalens.config import SettingsStore
from metadatalens.llm import parse_json_object


def test_json_parser_accepts_wrapped_json():
    assert parse_json_object('text {"a": 1} tail')["a"] == 1


def test_all_provider_defaults_loaded(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = store.load()
    for provider in ("openai", "deepseek", "qwen", "claude", "gemini"):
        cfg = settings.provider(provider)
        assert cfg.base_url
        assert cfg.model


def test_default_settings_language_is_english(tmp_path):
    settings = SettingsStore(tmp_path / "settings.json").load()
    assert settings.language == "en_US"
