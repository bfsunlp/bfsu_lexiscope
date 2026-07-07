LANGUAGES = [
    {"code": "zh_sim", "zh_sim": "简体中文", "zh_tra": "簡體中文", "en": "Simplified Chinese", "native": "简体中文", "display": "简体中文", "tmx": "zh-CN", "stanza": "zh"},
    {"code": "zh_tra", "zh_sim": "繁体中文", "zh_tra": "繁體中文", "en": "Traditional Chinese", "native": "繁體中文", "display": "繁體中文", "tmx": "zh-Hant", "stanza": "zh-hant"},
    {"code": "en", "zh_sim": "英语", "zh_tra": "英語", "en": "English", "native": "English", "display": "English", "tmx": "en", "stanza": "en"},
    {"code": "de", "zh_sim": "德语", "zh_tra": "德語", "en": "German", "native": "Deutsch", "display": "Deutsch", "tmx": "de", "stanza": "de"},
    {"code": "fr", "zh_sim": "法语", "zh_tra": "法語", "en": "French", "native": "Français", "display": "Français", "tmx": "fr", "stanza": "fr"},
    {"code": "es", "zh_sim": "西班牙语", "zh_tra": "西班牙語", "en": "Spanish", "native": "Español", "display": "Español", "tmx": "es", "stanza": "es"},
    {"code": "ru", "zh_sim": "俄语", "zh_tra": "俄語", "en": "Russian", "native": "Русский", "display": "Русский", "tmx": "ru", "stanza": "ru"},
    {"code": "ja", "zh_sim": "日语", "zh_tra": "日語", "en": "Japanese", "native": "日本語", "display": "日本語", "tmx": "ja", "stanza": "ja"},
    {"code": "ko", "zh_sim": "韩语", "zh_tra": "韓語", "en": "Korean", "native": "한국어", "display": "한국어", "tmx": "ko", "stanza": "ko"},
    {"code": "pt", "zh_sim": "葡萄牙语", "zh_tra": "葡萄牙語", "en": "Portuguese", "native": "Português", "display": "Português", "tmx": "pt", "stanza": "pt"},
    {"code": "it", "zh_sim": "意大利语", "zh_tra": "義大利語", "en": "Italian", "native": "Italiano", "display": "Italiano", "tmx": "it", "stanza": "it"},
    {"code": "nl", "zh_sim": "荷兰语", "zh_tra": "荷蘭語", "en": "Dutch", "native": "Nederlands", "display": "Nederlands", "tmx": "nl", "stanza": "nl"},
    {"code": "ar", "zh_sim": "阿拉伯语", "zh_tra": "阿拉伯語", "en": "Arabic", "native": "العربية", "display": "العربية", "tmx": "ar", "stanza": "ar"},
    {"code": "tr", "zh_sim": "土耳其语", "zh_tra": "土耳其語", "en": "Turkish", "native": "Türkçe", "display": "Türkçe", "tmx": "tr", "stanza": "tr"},
    {"code": "vi", "zh_sim": "越南语", "zh_tra": "越南語", "en": "Vietnamese", "native": "Tiếng Việt", "display": "Tiếng Việt", "tmx": "vi", "stanza": "vi"},
    {"code": "th", "zh_sim": "泰语", "zh_tra": "泰語", "en": "Thai", "native": "ไทย", "display": "ไทย", "tmx": "th", "stanza": "th"},
    {"code": "pl", "zh_sim": "波兰语", "zh_tra": "波蘭語", "en": "Polish", "native": "Polski", "display": "Polski", "tmx": "pl", "stanza": "pl"},
    {"code": "sv", "zh_sim": "瑞典语", "zh_tra": "瑞典語", "en": "Swedish", "native": "Svenska", "display": "Svenska", "tmx": "sv", "stanza": "sv"},
]

LANGUAGE_CODES = [x["code"] for x in LANGUAGES]
LANGUAGE_MAP = {x["code"]: x for x in LANGUAGES}


def native_name(code: str, with_code: bool = False) -> str:
    """Return the language name in that language's own writing system."""
    entry = LANGUAGE_MAP.get(code)
    if not entry:
        return code
    name = entry.get("native") or entry.get("display") or entry.get("en") or code
    return f"{name} / {code}" if with_code else name


def display_name(code: str, ui_lang: str = "en", with_code: bool = False, native: bool = False) -> str:
    entry = LANGUAGE_MAP.get(code)
    if not entry:
        return code
    if native:
        return native_name(code, with_code=with_code)
    name = entry.get(ui_lang, entry.get("en", code))
    return f"{name} / {code}" if with_code else name


def column_display_name(column_key: str, files=None, ui_lang: str = "en") -> str:
    """Return a GUI-language-aware column label.

    Import selectors may still show native language names, but the main GUI and
    alignment-result headers should follow the selected interface language.
    """
    source_label = "Source" if ui_lang == "en" else ("源語" if ui_lang == "zh_tra" else "源语")
    target_label = "Target" if ui_lang == "en" else ("譯語" if ui_lang == "zh_tra" else "译语")

    def role_for(record) -> str:
        if getattr(record, "alignment_role", "") == "source":
            return source_label
        idx = int(getattr(record, "target_index", 1) or 1)
        return f"{target_label} {idx}"

    if files:
        matches = [f for f in files if getattr(f, "column_key", "") == column_key]
        if matches:
            f = matches[0]
            base = f"{role_for(f)} · {display_name(getattr(f, 'lang', ''), ui_lang, with_code=False)}"
            filenames = [getattr(x, 'filename', '') for x in matches if getattr(x, 'filename', '')]
            if len(filenames) == 1:
                return f"{base} · {filenames[0]}"
            return base
    if column_key.startswith("source_"):
        return source_label + " · " + display_name(column_key.replace("source_", ""), ui_lang, with_code=False)
    if column_key.startswith("target_"):
        parts = column_key.split("_", 2)
        lang = parts[-1] if len(parts) >= 3 else column_key
        idx = parts[1] if len(parts) >= 3 else ""
        return f"{target_label} {idx} · {display_name(lang, ui_lang, with_code=False)}"
    return display_name(column_key, ui_lang, with_code=False)


def language_options(ui_lang: str = "en", with_code: bool = False, native: bool = True):
    """Return language selector labels.

    Selectors now use each language's own display name by default, so the import
    dialog consistently shows 简体中文、繁體中文、English、Deutsch、Français, etc.
    """
    if native:
        return [native_name(x["code"], with_code=with_code) for x in LANGUAGES]
    return [display_name(x["code"], ui_lang, with_code=with_code) for x in LANGUAGES]


def code_from_display(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    for code, entry in LANGUAGE_MAP.items():
        names = {
            code,
            entry.get("en", ""),
            entry.get("zh_sim", ""),
            entry.get("zh_tra", ""),
            entry.get("native", ""),
            entry.get("display", ""),
        }
        if value in names or value.endswith("/ " + code) or value.endswith("/" + code):
            return code
    return value.split("/")[-1].strip()


def tmx_code(code: str) -> str:
    if code.startswith("source_"):
        code = code.replace("source_", "")
    elif code.startswith("target_"):
        parts = code.split("_", 2)
        code = parts[-1] if len(parts) >= 3 else code
    return LANGUAGE_MAP.get(code, {}).get("tmx", code)
