from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .datatypes import Segment
from .segmentation_profiles import SegmentationProfile, profile_for_language
from .utils import resource_path
from .hardware import resolve_device

ABBREVIATIONS = {
    'en': {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'St.', 'Jr.', 'Sr.', 'e.g.', 'i.e.', 'etc.', 'vs.', 'Fig.', 'No.'},
    'de': {'Dr.', 'Prof.', 'bzw.', 'z.B.', 'd.h.', 'usw.', 'bspw.', 'Nr.'},
    'fr': {'M.', 'Mme.', 'Dr.', 'Pr.', 'p.ex.', 'etc.'},
    'es': {'Sr.', 'Sra.', 'Dr.', 'Dra.', 'etc.', 'p.ej.'},
    'it': {'Sig.', 'Sig.ra', 'Dott.', 'Prof.', 'ecc.'},
    'pt': {'Sr.', 'Sra.', 'Dr.', 'Dra.', 'Prof.', 'etc.'},
    'nl': {'dhr.', 'mevr.', 'dr.', 'prof.', 'enz.'},
    'ru': {'г.', 'ул.', 'д.', 'т.д.', 'т.п.'},
}

# Covers CJK and common European punctuation while protecting abbreviations/decimals.
SENT_END = r'[。！？!?\.]+["”’\)\]\}»›]*'
_STANZA_PIPELINES: Dict[Tuple[str, str, str], object] = {}
_SPACY_PIPELINES: Dict[Tuple[str, str], object] = {}
_HANLP_SPLITTERS: Dict[Tuple[str, str], object] = {}


def _protect_abbreviations(text: str, lang: str, protect_abbreviations: bool = True, protect_decimals: bool = True) -> Tuple[str, dict]:
    repl = {}
    if protect_abbreviations:
        for i, abbr in enumerate(ABBREVIATIONS.get(lang, set())):
            key = f'§ABBR{i}§'
            if abbr in text:
                text = text.replace(abbr, key)
                repl[key] = abbr
    if protect_decimals:
        text = re.sub(r'(\d)\.(\d)', r'\1§DOT§\2', text)
    return text, repl


def _restore(text: str, repl: dict) -> str:
    text = text.replace('§DOT§', '.')
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def normalize_ocr_breaks(text: str) -> str:
    """Conservative OCR/PDF line-break normalization.

    Blank lines remain paragraph boundaries. Single line breaks inside a paragraph
    are converted to spaces, except CJK line breaks where no extra space is useful.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    parts = re.split(r'(\n\s*\n+)', text)
    out = []
    for part in parts:
        if re.match(r'\n\s*\n+', part):
            out.append(part)
        else:
            # Remove hyphenation at line ends in Latin text, then normalize single line breaks.
            part = re.sub(r'([A-Za-z])\-\n([A-Za-z])', r'\1\2', part)
            part = re.sub(r'(?<=[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af])\n(?=[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af])', '', part)
            part = re.sub(r'(?<!\n)\n(?!\n)', ' ', part)
            out.append(part)
    return ''.join(out)


def split_punctuation(paragraph: str, lang: str, protect_abbreviations: bool = True, protect_decimals: bool = True) -> List[Tuple[str, int, int]]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    protected, repl = _protect_abbreviations(paragraph, lang, protect_abbreviations, protect_decimals)
    spans = []
    start = 0
    for m in re.finditer(SENT_END, protected):
        end = m.end()
        piece = protected[start:end].strip()
        if piece:
            restored = _restore(piece, repl)
            spans.append((restored, start, end))
        start = end
    tail = protected[start:].strip()
    if tail:
        spans.append((_restore(tail, repl), start, len(protected)))
    if len(spans) == 0:
        spans = [(_restore(protected, repl), 0, len(protected))]
    return spans


def _model_root(settings: Dict | None = None) -> Path:
    root = (settings or {}).get('model_root') or 'models'
    p = Path(str(root))
    if not p.is_absolute():
        p = resource_path(str(root))
    return p


def _segmenter_device(settings: Dict | None = None) -> str:
    """Resolve the preferred device for neural segmenters.

    By default, segmentation models follow AlignLens' global device setting:
    CUDA is used when available, otherwise the function returns CPU. Users can
    disable segmentation GPU usage or override the segmenter device separately.
    """
    cfg = settings or {}
    if not bool(cfg.get('use_segmentation_gpu', True)):
        return 'cpu'
    requested = str(cfg.get('segmentation_device') or cfg.get('device') or 'auto')
    return resolve_device(requested)


def _gpu_id_from_device(device: str) -> int:
    if device.startswith('cuda'):
        try:
            return int(device.split(':', 1)[1])
        except Exception:
            return 0
    return -1


def split_with_stanza(text: str, lang: str, settings: Dict | None = None, stanza_lang: str = '') -> List[str]:
    import stanza  # type: ignore
    code = stanza_lang or ('zh-hans' if lang == 'zh_sim' else ('zh-hant' if lang == 'zh_tra' else lang))
    model_dir = str(_model_root(settings) / 'segmenters' / 'stanza')
    device = _segmenter_device(settings)
    key = (code, model_dir, device)
    if key not in _STANZA_PIPELINES:
        use_gpu = device.startswith('cuda')
        # Stanza versions differ slightly in supported keyword arguments. Prefer
        # explicit device routing, then gracefully fall back while keeping CPU mode
        # functional on machines without CUDA.
        try:
            _STANZA_PIPELINES[key] = stanza.Pipeline(
                lang=code,
                processors='tokenize',
                dir=model_dir,
                tokenize_no_ssplit=False,
                verbose=False,
                use_gpu=use_gpu,
                device=device if use_gpu else 'cpu',
            )
        except TypeError:
            try:
                _STANZA_PIPELINES[key] = stanza.Pipeline(
                    lang=code,
                    processors='tokenize',
                    dir=model_dir,
                    tokenize_no_ssplit=False,
                    verbose=False,
                    use_gpu=use_gpu,
                )
            except TypeError:
                _STANZA_PIPELINES[key] = stanza.Pipeline(lang=code, processors='tokenize', dir=model_dir, tokenize_no_ssplit=False, verbose=False)
        except Exception:
            if use_gpu:
                # If a CUDA attempt fails because the local model/framework cannot
                # use GPU, retry once on CPU rather than failing segmentation.
                cpu_key = (code, model_dir, 'cpu')
                if cpu_key not in _STANZA_PIPELINES:
                    _STANZA_PIPELINES[cpu_key] = stanza.Pipeline(lang=code, processors='tokenize', dir=model_dir, tokenize_no_ssplit=False, verbose=False, use_gpu=False)
                _STANZA_PIPELINES[key] = _STANZA_PIPELINES[cpu_key]
            else:
                raise
    doc = _STANZA_PIPELINES[key](text)  # type: ignore[operator]
    return [sent.text.strip() for sent in getattr(doc, 'sentences', []) if getattr(sent, 'text', '').strip()]


def split_with_hanlp(text: str, model_name: str = 'UD_CTB_EOS_MUL', settings: Dict | None = None) -> List[str]:
    import hanlp  # type: ignore
    device = _segmenter_device(settings)
    key = (model_name, device)
    if key not in _HANLP_SPLITTERS:
        gpu_id = _gpu_id_from_device(device)
        if gpu_id >= 0:
            try:
                _HANLP_SPLITTERS[key] = hanlp.load(model_name, devices=gpu_id)
            except TypeError:
                _HANLP_SPLITTERS[key] = hanlp.load(model_name)
            except Exception:
                cpu_key = (model_name, 'cpu')
                if cpu_key not in _HANLP_SPLITTERS:
                    _HANLP_SPLITTERS[cpu_key] = hanlp.load(model_name)
                _HANLP_SPLITTERS[key] = _HANLP_SPLITTERS[cpu_key]
        else:
            _HANLP_SPLITTERS[key] = hanlp.load(model_name)
    splitter = _HANLP_SPLITTERS[key]
    return [str(x).strip() for x in splitter(text) if str(x).strip()]  # type: ignore[operator]


def split_with_spacy(text: str, model_name: str = '', lang: str = 'en', settings: Dict | None = None) -> List[str]:
    import spacy  # type: ignore
    key = model_name or f'{lang}_core_web_sm'
    model_root = (settings or {}).get('model_root') or str(resource_path('models'))
    local_path = Path(model_root) / 'segmenters' / 'spacy' / key
    load_key = str(local_path) if (local_path / 'config.cfg').exists() else key
    device = _segmenter_device(settings)
    cache_key = (load_key, device)
    if cache_key not in _SPACY_PIPELINES:
        gpu_id = _gpu_id_from_device(device)
        if gpu_id >= 0:
            try:
                spacy.prefer_gpu(gpu_id)
            except Exception:
                pass
        try:
            nlp = spacy.load(load_key)
        except Exception:
            # A blank tokenizer + sentencizer gives a reliable rule fallback if
            # a trained spaCy pipeline is not installed.
            blank_lang = 'zh' if lang in {'zh_sim', 'zh_tra'} else lang
            nlp = spacy.blank(blank_lang if blank_lang else 'xx')
            if 'sentencizer' not in nlp.pipe_names:
                nlp.add_pipe('sentencizer')
        if 'sentencizer' not in nlp.pipe_names and 'parser' not in nlp.pipe_names:
            nlp.add_pipe('sentencizer')
        _SPACY_PIPELINES[cache_key] = nlp
    doc = _SPACY_PIPELINES[cache_key](text)  # type: ignore[operator]
    return [s.text.strip() for s in doc.sents if s.text.strip()]


def _engine_sequence(lang: str, mode: str, settings: Dict | None, profile: SegmentationProfile | None) -> List[str]:
    prof = profile or profile_for_language(settings or {}, lang)
    mode = (mode or prof.sentence_engine or 'auto').lower()
    if mode in {'punctuation', 'rule'}:
        return ['punctuation']
    if mode in {'line', 'paragraph', 'none'}:
        return [mode]
    if mode == 'auto':
        first = (prof.sentence_engine or '').lower()
        if first and first != 'auto':
            seq = [first]
        elif lang in {'zh_sim', 'zh_tra'}:
            seq = ['hanlp', 'stanza']
        else:
            seq = ['stanza']
        if 'spacy' not in seq and prof.spacy_model:
            seq.append('spacy')
        seq.append(prof.fallback_engine or 'punctuation')
        seq.append('punctuation')
        # Preserve order and remove duplicates.
        out = []
        for x in seq:
            if x not in out:
                out.append(x)
        return out
    seq = [mode]
    fb = (prof.fallback_engine or 'punctuation').lower()
    if fb not in seq:
        seq.append(fb)
    if 'punctuation' not in seq:
        seq.append('punctuation')
    return seq


def _split_sentence_units(para: str, lang: str, mode: str, settings: Dict | None, profile: SegmentationProfile, fallback_to_punctuation: bool = True) -> List[Tuple[str, int, int]]:
    last_error: Exception | None = None
    for engine in _engine_sequence(lang, mode, settings, profile):
        try:
            if engine in {'punctuation', 'rule'}:
                return split_punctuation(para, lang, profile.protect_abbreviations, profile.protect_decimals)
            if engine == 'line':
                return [(x.strip(), 0, len(x)) for x in para.split('\n') if x.strip()]
            if engine in {'paragraph', 'none'}:
                return [(para, 0, len(para))]
            if engine == 'hanlp':
                units = []
                for s in split_with_hanlp(para, profile.hanlp_model, settings):
                    local = para.find(s)
                    units.append((s, max(local, 0), max(local, 0) + len(s)))
                if units:
                    return units
            if engine == 'stanza':
                units = []
                for s in split_with_stanza(para, lang, settings, profile.stanza_lang):
                    local = para.find(s)
                    units.append((s, max(local, 0), max(local, 0) + len(s)))
                if units:
                    return units
            if engine == 'spacy':
                units = []
                for s in split_with_spacy(para, profile.spacy_model, lang, settings):
                    local = para.find(s)
                    units.append((s, max(local, 0), max(local, 0) + len(s)))
                if units:
                    return units
        except Exception as exc:
            last_error = exc
            continue
    if fallback_to_punctuation:
        return split_punctuation(para, lang, profile.protect_abbreviations, profile.protect_decimals)
    if last_error:
        raise last_error
    return [(para, 0, len(para))]


def split_text(
    text: str,
    lang: str,
    file_id: str = '',
    mode: str = 'punctuation',
    paragraph_aware: bool = True,
    split_by_line: bool = False,
    split_by_paragraph: bool = False,
    fallback_to_punctuation: bool = True,
    settings: Dict | None = None,
    profile: SegmentationProfile | None = None,
) -> List[Segment]:
    prof = profile or profile_for_language(settings or {}, lang)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if prof.normalize_ocr_breaks and not split_by_line:
        text = normalize_ocr_breaks(text)
    if split_by_line:
        paragraphs = [(i, line.strip(), 0) for i, line in enumerate(text.split('\n')) if line.strip()]
    else:
        parts = re.split(r'\n\s*\n+', text) if paragraph_aware else [text]
        paragraphs = []
        cursor = 0
        for i, p in enumerate(parts):
            pos = text.find(p, cursor)
            paragraphs.append((i, p.strip(), max(pos, 0)))
            cursor = max(pos, cursor) + len(p)

    segments: List[Segment] = []
    global_sid = 1
    actual_engine = 'paragraph' if (split_by_paragraph or mode == 'paragraph') else (mode or prof.sentence_engine or 'auto')
    for pid, para, base in paragraphs:
        if not para:
            continue
        if split_by_paragraph or mode == 'paragraph':
            units = [(para, 0, len(para))]
        else:
            units = _split_sentence_units(para, lang, mode, settings, prof, fallback_to_punctuation)
        for local_sid, (sent, st, ed) in enumerate(units, start=1):
            sent = re.sub(r'\s+', ' ', sent).strip()
            if not sent:
                continue
            seg = Segment(
                seg_id=f'{file_id or "text"}_{global_sid}',
                file_id=file_id,
                lang=lang,
                text=sent,
                paragraph_id=pid + 1,
                sentence_id=local_sid,
                char_start=base + st,
                char_end=base + ed,
            )
            # Optional metadata fields exist in newer projects; setattr keeps old tests/projects compatible.
            setattr(seg, 'segmenter_engine', actual_engine)
            setattr(seg, 'segmenter_model', prof.stanza_lang if actual_engine == 'stanza' else (prof.spacy_model if actual_engine == 'spacy' else prof.hanlp_model if actual_engine == 'hanlp' else ''))
            segments.append(seg)
            global_sid += 1
    return segments


def segments_to_texts(segments: Iterable[Segment]) -> List[str]:
    return [s.text for s in segments]
