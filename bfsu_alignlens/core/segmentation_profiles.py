from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

from .language_registry import LANGUAGES, LANGUAGE_MAP, display_name


@dataclass
class SegmentationProfile:
    language: str
    sentence_engine: str = 'auto'     # auto | stanza | spacy | hanlp | rule | punctuation | line | none
    paragraph_engine: str = 'paragraph'
    stanza_lang: str = ''
    spacy_model: str = ''
    hanlp_model: str = 'UD_CTB_EOS_MUL'
    fallback_engine: str = 'punctuation'
    protect_abbreviations: bool = True
    protect_decimals: bool = True
    normalize_ocr_breaks: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)


# spaCy only has downloadable trained pipelines for a subset of AlignLens' languages.
# Stanza is the broad-coverage default for all current AlignLens languages.
SPACY_MODEL_BY_LANG: Dict[str, str] = {
    'zh_sim': 'zh_core_web_sm',
    'zh_tra': 'zh_core_web_sm',
    'en': 'en_core_web_sm',
    'de': 'de_core_news_sm',
    'fr': 'fr_core_news_sm',
    'es': 'es_core_news_sm',
    'ru': 'ru_core_news_sm',
    'ja': 'ja_core_news_sm',
    'ko': 'ko_core_news_sm',
    'pt': 'pt_core_news_sm',
    'it': 'it_core_news_sm',
    'nl': 'nl_core_news_sm',
    'pl': 'pl_core_news_sm',
}


def stanza_lang_for(code: str) -> str:
    # Keep the user's non-political internal names while using model provider codes.
    if code == 'zh_sim':
        return 'zh-hans'
    if code == 'zh_tra':
        return 'zh-hant'
    entry = LANGUAGE_MAP.get(code, {})
    return entry.get('stanza') or code


def default_profile_for_language(code: str) -> SegmentationProfile:
    stanza_code = stanza_lang_for(code)
    # Chinese/Japanese/Korean/Thai/Vietnamese lack reliable whitespace boundaries;
    # model-first is useful, but rule fallback remains available offline.
    if code in {'zh_sim', 'zh_tra'}:
        engine = 'hanlp'  # falls back to Stanza/rule if HanLP is absent
    elif code in {'ja', 'ko', 'th', 'vi', 'ar', 'tr', 'ru', 'pl'}:
        engine = 'stanza'
    else:
        engine = 'stanza'
    return SegmentationProfile(
        language=code,
        sentence_engine=engine,
        paragraph_engine='paragraph',
        stanza_lang=stanza_code,
        spacy_model=SPACY_MODEL_BY_LANG.get(code, ''),
        fallback_engine='punctuation',
    )


def all_default_profiles() -> Dict[str, Dict]:
    return {x['code']: default_profile_for_language(x['code']).to_dict() for x in LANGUAGES}


def profiles_from_settings(settings: Dict) -> Dict[str, Dict]:
    profiles = all_default_profiles()
    user_profiles = settings.get('segmentation_profiles') or {}
    if isinstance(user_profiles, dict):
        for lang, prof in user_profiles.items():
            if lang in profiles and isinstance(prof, dict):
                profiles[lang].update({k: v for k, v in prof.items() if v is not None})
    return profiles


def profile_for_language(settings: Dict, lang: str) -> SegmentationProfile:
    profiles = profiles_from_settings(settings or {})
    data = dict(profiles.get(lang) or default_profile_for_language(lang).to_dict())
    return SegmentationProfile(**{k: data.get(k, getattr(SegmentationProfile(lang), k)) for k in SegmentationProfile.__dataclass_fields__})


def describe_profile(settings: Dict, lang: str, level: str = 'sentence') -> str:
    prof = profile_for_language(settings, lang)
    if level == 'paragraph':
        return 'paragraph'
    engine = (prof.sentence_engine or 'auto').lower()
    if engine == 'stanza':
        return f"Stanza/{prof.stanza_lang or lang}"
    if engine == 'spacy':
        return f"spaCy/{prof.spacy_model or lang}"
    if engine == 'hanlp':
        return f"HanLP/{prof.hanlp_model}"
    if engine in {'rule', 'punctuation'}:
        return 'Rule punctuation'
    return engine


def segmentation_model_catalog() -> List[Dict]:
    """Rows shown in Model Manager: broad Stanza coverage plus optional spaCy/HanLP."""
    rows: List[Dict] = []
    for entry in LANGUAGES:
        code = entry['code']
        prof = default_profile_for_language(code)
        rows.append({
            'name': f"stanza:{prof.stanza_lang}",
            'type': 'Stanza segmenter',
            'language': code,
            'description': f"{display_name(code, 'en')} sentence tokenizer via Stanza",
            'downloadable': True,
            'engine': 'stanza',
            'model': prof.stanza_lang,
        })
        if prof.spacy_model:
            rows.append({
                'name': f"spacy:{prof.spacy_model}",
                'type': 'spaCy segmenter',
                'language': code,
                'description': f"{display_name(code, 'en')} spaCy trained pipeline",
                'downloadable': True,
                'engine': 'spacy',
                'model': prof.spacy_model,
            })
    # Chinese-specific EOS model. HanLP will manage the actual cache internally.
    rows.append({
        'name': 'hanlp:UD_CTB_EOS_MUL',
        'type': 'HanLP segmenter',
        'language': 'zh_sim/zh_tra',
        'description': 'Chinese EOS sentence splitter; falls back to rules if unavailable',
        'downloadable': True,
        'engine': 'hanlp',
        'model': 'UD_CTB_EOS_MUL',
    })
    return rows
