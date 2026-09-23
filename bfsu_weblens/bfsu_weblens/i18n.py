# -*- coding: utf-8 -*-
"""Small compatibility translation helper for BFSU WebLens.

The PySide6 interface owns its complete translation table in ui/main_window.py.
This module is intentionally minimal so older external helpers that import ``t``
continue to work without reintroducing retired Tk/CustomTkinter controls.
"""
from __future__ import annotations

TEXTS = {
    "en": {
        "app_title": "BFSU WebLens",
        "collection_browser": "Collection browser",
        "hide_browser": "Do not show the collection browser window",
        "page_delay": "Page-turn wait range (seconds)",
    },
    "zh_sim": {
        "app_title": "BFSU WebLens",
        "collection_browser": "采集浏览器",
        "hide_browser": "不显示采集浏览器界面",
        "page_delay": "翻页等待范围（秒）",
    },
    "zh_tra": {
        "app_title": "BFSU WebLens",
        "collection_browser": "採集瀏覽器",
        "hide_browser": "不顯示採集瀏覽器介面",
        "page_delay": "翻頁等待範圍（秒）",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    table = TEXTS.get(lang, TEXTS["en"])
    value = table.get(key, TEXTS["en"].get(key, key))
    return value.format(**kwargs) if kwargs else value
