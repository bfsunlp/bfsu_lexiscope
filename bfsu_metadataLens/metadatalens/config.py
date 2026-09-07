from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "BFSU MetadataLens"
APP_VERSION = "3.5.5"
SETTINGS_SCHEMA_VERSION = 4


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller 6 onedir builds normally place bundled data under
        # sys._MEIPASS (typically the _internal directory). Fall back to the
        # executable directory for layouts that keep data beside the EXE.
        bundled = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)).resolve()
        if (bundled / "assets").exists() or (bundled / "templates").exists():
            return bundled
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_config_dir() -> Path:
    """Return the per-user configuration directory, never the app folder.

    API keys and user templates live under the current operating-system user
    profile. Copying or zipping the installed/application directory therefore
    never carries the user's credentials with it.
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "BFSU_MetadataLens"
    return Path.home() / ".bfsu_metadatalens"


SYSTEM_TEMPLATE_DIR = app_root() / "templates" / "system"
USER_TEMPLATE_DIR = user_config_dir() / "templates" / "user"
CONFIG_DIR = user_config_dir()
SETTINGS_PATH = CONFIG_DIR / "settings.json"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"


PROVIDER_DEFAULTS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.4-nano",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    },
    "qwen": {
        "label": "千问 / Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3-vl-flash",
    },
    "claude": {
        "label": "Claude",
        "base_url": "https://api.anthropic.com",
        "model": "claude-haiku-4-5-20251001",
    },
    "gemini": {
        "label": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.5-flash-lite",
    },
}

LEGACY_PROVIDER_MODELS = {
    "openai": {"gpt-5.4-mini-2026-03-17"},
    "deepseek": {"deepseek-chat"},
    "qwen": {"qwen-plus", "qwen3.7-flash"},
    "claude": {"claude-sonnet-4-20250514"},
    "gemini": {"gemini-2.5-flash"},
}


@dataclass
class ProviderSettings:
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@dataclass
class Settings:
    settings_schema_version: int = SETTINGS_SCHEMA_VERSION
    # First launch is English. Once the user switches language, the preference
    # is stored in the per-user settings file and reused on later launches.
    language: str = "en_US"
    appearance: str = "light"
    window_geometry: str = "1540x940"
    sidebar_width: int = 460
    list_pane_ratio: float = 0.70
    active_provider: str = "openai"
    max_source_chars: int = 60000
    request_timeout: int = 180
    providers: dict[str, ProviderSettings] = field(default_factory=dict)

    def provider(self, name: str | None = None) -> ProviderSettings:
        key = (name or self.active_provider or "openai").lower()
        if key not in self.providers:
            default = PROVIDER_DEFAULTS.get(key, PROVIDER_DEFAULTS["openai"])
            self.providers[key] = ProviderSettings(base_url=default["base_url"], model=default["model"])
        return self.providers[key]


class SettingsStore:
    """Store ordinary settings and API credentials separately in user space.

    `settings.json` contains no API keys. Credentials are written only to
    `credentials.json` in the operating-system user's configuration directory.
    Neither file resides in the source/install directory or in project XML.
    """

    def __init__(self, path: Path | None = None, credentials_path: Path | None = None) -> None:
        self.path = path or SETTINGS_PATH
        self.credentials_path = credentials_path or (
            CREDENTIALS_PATH if path is None else self.path.with_name("credentials.json")
        )

    def _default_providers(self) -> dict[str, ProviderSettings]:
        return {
            key: ProviderSettings(base_url=value["base_url"], model=value["model"])
            for key, value in PROVIDER_DEFAULTS.items()
        }

    def _load_credentials(self) -> dict[str, str]:
        if not self.credentials_path.exists():
            return {}
        try:
            raw = json.loads(self.credentials_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        providers = raw.get("providers", raw)
        if not isinstance(providers, dict):
            return {}
        return {str(k): str(v or "") for k, v in providers.items() if str(v or "").strip()}

    def _save_credentials(self, settings: Settings) -> None:
        keys = {
            key: cfg.api_key.strip()
            for key, cfg in settings.providers.items()
            if cfg.api_key.strip()
        }
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        if not keys:
            try:
                self.credentials_path.unlink(missing_ok=True)
            except TypeError:  # Python < 3.8 compatibility guard
                if self.credentials_path.exists():
                    self.credentials_path.unlink()
            return
        payload = {"providers": keys}
        self.credentials_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(self.credentials_path, 0o600)
        except OSError:
            pass

    def load(self) -> Settings:
        providers = self._default_providers()
        settings = Settings(providers=providers)
        legacy_keys: dict[str, str] = {}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            if isinstance(data, dict):
                settings.language = str(data.get("language", settings.language))
                if settings.language not in {"zh_CN", "en_US"}:
                    settings.language = "en_US"
                settings.appearance = str(data.get("appearance", settings.appearance))
                settings.window_geometry = str(data.get("window_geometry", settings.window_geometry))
                settings.sidebar_width = max(450, int(data.get("sidebar_width", settings.sidebar_width) or settings.sidebar_width))
                try:
                    ratio = float(data.get("list_pane_ratio", settings.list_pane_ratio) or settings.list_pane_ratio)
                except Exception:
                    ratio = settings.list_pane_ratio
                settings.list_pane_ratio = min(0.78, max(0.62, ratio))
                settings.active_provider = str(data.get("active_provider", settings.active_provider)).lower()
                settings.max_source_chars = int(data.get("max_source_chars", settings.max_source_chars) or settings.max_source_chars)
                settings.request_timeout = int(data.get("request_timeout", settings.request_timeout) or settings.request_timeout)
                raw_providers = data.get("providers", {})
                if isinstance(raw_providers, dict):
                    for key, raw in raw_providers.items():
                        if not isinstance(raw, dict):
                            continue
                        default = PROVIDER_DEFAULTS.get(key, PROVIDER_DEFAULTS["openai"])
                        raw_model = str(raw.get("model", default["model"])) or default["model"]
                        if raw_model in LEGACY_PROVIDER_MODELS.get(key, set()):
                            raw_model = default["model"]
                        providers[key] = ProviderSettings(
                            api_key="",
                            base_url=str(raw.get("base_url", default["base_url"])) or default["base_url"],
                            model=raw_model,
                        )
                        # v3.2 and earlier stored keys in settings.json. Read
                        # them once for transparent migration, but never write
                        # them back to settings.json.
                        old_key = str(raw.get("api_key", "") or "").strip()
                        if old_key:
                            legacy_keys[key] = old_key
        settings.providers = providers
        credentials = self._load_credentials()
        for key, api_key in {**legacy_keys, **credentials}.items():
            settings.provider(key).api_key = api_key
        settings.provider(settings.active_provider)
        if legacy_keys:
            # Complete the migration immediately: move legacy keys to the
            # local credentials file and rewrite settings.json without keys.
            try:
                self.save(settings)
            except OSError:
                pass
        return settings

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(settings)
        # API keys must never be serialized into ordinary application settings.
        for provider in data.get("providers", {}).values():
            if isinstance(provider, dict):
                provider.pop("api_key", None)
        data["settings_schema_version"] = SETTINGS_SCHEMA_VERSION
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._save_credentials(settings)

    def delete_all_api_keys(self, settings: Settings | None = None) -> None:
        target = settings or self.load()
        for cfg in target.providers.values():
            cfg.api_key = ""
        try:
            self.credentials_path.unlink(missing_ok=True)
        except TypeError:
            if self.credentials_path.exists():
                self.credentials_path.unlink()
        # Also rewrite settings.json so any pre-v3.3 legacy key fields are
        # stripped during migration.
        self.save(target)
