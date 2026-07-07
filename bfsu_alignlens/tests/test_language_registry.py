from core.language_registry import language_options, code_from_display


def test_language_options_are_native_names():
    opts = language_options('zh_sim')[:8]
    assert opts == ['简体中文', '繁體中文', 'English', 'Deutsch', 'Français', 'Español', 'Русский', '日本語']
    assert code_from_display('繁體中文') == 'zh_tra'
    assert code_from_display('Deutsch') == 'de'
