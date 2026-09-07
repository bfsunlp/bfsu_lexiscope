from metadatalens.i18n import I18N


def test_i18n_defaults_to_english():
    assert I18N().language == "en_US"


def test_guide_and_about_are_language_specific():
    zh = I18N("zh_CN")
    en = I18N("en_US")
    assert "使用说明" in zh.t("guide_text")
    assert "Getting started" not in zh.t("guide_text")
    assert "User Guide" in en.t("guide_text")
    assert "一、开始使用" not in en.t("guide_text")
    assert "开发者" in zh.t("about_text")
    assert "Developer" not in zh.t("about_text")
    assert "Developer" in en.t("about_text")
    assert "开发者" not in en.t("about_text")


def test_v340_template_and_url_labels_are_bilingual():
    zh = I18N("zh_CN")
    en = I18N("en_US")
    assert "导入" in zh.t("apply_selected_template")
    assert "Import" in en.t("apply_selected_template")
    assert "URL" in zh.t("batch_import_urls_text")
    assert "URL" in en.t("batch_import_urls_text")
    assert "规范名称" == zh.t("schema_name")
    assert "Schema Name" == en.t("schema_name")
