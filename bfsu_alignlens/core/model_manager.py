from __future__ import annotations

import shutil
import json
from pathlib import Path
from typing import Callable, Dict, List

from .embedding_models import set_model_env
from .utils import resource_path, format_bytes
from .segmentation_profiles import segmentation_model_catalog

PRESET_SENTENCE_MODELS = [
    ('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'Default speed-first multilingual model'),
    ('sentence-transformers/LaBSE', 'High-accuracy multilingual model'),
    ('sentence-transformers/distiluse-base-multilingual-cased-v2', 'Light multilingual model'),
    ('intfloat/multilingual-e5-small', 'E5 small multilingual retrieval model'),
    ('intfloat/multilingual-e5-base', 'E5 base multilingual retrieval model'),
]


def model_root(path: str = '') -> Path:
    return set_model_env(path or str(resource_path('models')))


def _hf_cache_name(model_name: str) -> str:
    return 'models--' + model_name.replace('/', '--').replace('\\', '--')


def _safe_model_name(model_name: str) -> str:
    return model_name.replace('/', '_').replace('\\', '_')


def _looks_like_sentence_model(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    markers = [
        'modules.json',
        'config_sentence_transformers.json',
        'sentence_bert_config.json',
        'config.json',
    ]
    if any((path / m).exists() for m in markers):
        return True
    # Imported models sometimes keep the actual model one level deeper.
    try:
        for child in path.iterdir():
            if child.is_dir() and any((child / m).exists() for m in markers):
                return True
    except Exception:
        pass
    return False


def model_local_path(model_name: str, root: str = '') -> Path:
    """Return the legacy/direct import destination for a model.

    SentenceTransformer.download(cache_folder=...) uses HuggingFace's
    models--org--name/snapshots/<hash> layout, while AlignLens also supports
    manually imported direct folders named org_name.  This function intentionally
    returns the direct import destination; detection below checks both layouts.
    """
    r = model_root(root) / 'sentence_transformers'
    return r / _safe_model_name(model_name)


def candidate_model_paths(model_name: str, root: str = '') -> List[Path]:
    """All local locations where SentenceTransformer may have stored a model."""
    r = model_root(root)
    candidates: List[Path] = []
    direct = r / 'sentence_transformers' / _safe_model_name(model_name)
    candidates.append(direct)
    hf_name = _hf_cache_name(model_name)
    for base in [
        r / 'sentence_transformers',
        r / 'hf_home' / 'hub',
        r / 'transformers',
    ]:
        repo = base / hf_name
        candidates.append(repo)
        snap_dir = repo / 'snapshots'
        if snap_dir.exists():
            try:
                snapshots = sorted([p for p in snap_dir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
                candidates.extend(snapshots)
            except Exception:
                pass
    # Remove duplicates while keeping order.
    seen = set()
    out: List[Path] = []
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            out.append(p)
            seen.add(key)
    return out


def find_local_model(model_name: str, root: str = '') -> Path | None:
    for p in candidate_model_paths(model_name, root):
        if _looks_like_sentence_model(p):
            return p
        if p.exists() and (p / 'snapshots').exists():
            try:
                for snap in sorted((p / 'snapshots').iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if _looks_like_sentence_model(snap):
                        return snap
            except Exception:
                pass
    return None




def segmenter_root(root: str = '') -> Path:
    return model_root(root) / 'segmenters'


def _package_available(pkg: str) -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec(pkg) is not None
    except Exception:
        return False


def stanza_model_exists(lang: str, root: str = '') -> bool:
    base = segmenter_root(root) / 'stanza'
    # Stanza stores resources.json and language/model folders under the model dir.
    if (base / lang).exists():
        return True
    if (base / 'resources.json').exists():
        try:
            txt = (base / 'resources.json').read_text(encoding='utf-8', errors='ignore')
            return f'"{lang}"' in txt
        except Exception:
            return True
    return False


def spacy_model_local_path(model: str, root: str = '') -> Path:
    return segmenter_root(root) / 'spacy' / model


def spacy_model_exists(model: str, root: str = '') -> bool:
    if not model:
        return False
    local = spacy_model_local_path(model, root)
    if (local / 'config.cfg').exists() or (local / 'meta.json').exists() or (local / 'alignlens_spacy_model.json').exists():
        return True
    return _package_available(model)


def hanlp_model_exists(model: str = 'UD_CTB_EOS_MUL') -> bool:
    # Avoid loading the large model during refresh. If hanlp is importable, the
    # selected model can be downloaded/loaded on demand.
    return _package_available('hanlp')


def segmentation_model_exists(engine: str, model: str, root: str = '') -> bool:
    engine = (engine or '').lower()
    if engine == 'stanza':
        return stanza_model_exists(model, root)
    if engine == 'spacy':
        return spacy_model_exists(model, root)
    if engine == 'hanlp':
        return hanlp_model_exists(model)
    return False

def cache_size(root: str = '') -> int:
    r = model_root(root)
    total = 0
    for p in r.rglob('*'):
        if p.is_file():
            try:
                total += p.stat().st_size
            except Exception:
                pass
    return total


def list_status(root: str = '') -> List[Dict]:
    rows = []
    for name, desc in PRESET_SENTENCE_MODELS:
        found = find_local_model(name, root)
        expected = model_local_path(name, root)
        rows.append({
            'name': name,
            'type': 'SentenceTransformer',
            'description': desc,
            'path': str(found or expected),
            'exists': found is not None,
        })
    for item in segmentation_model_catalog():
        engine = item.get('engine', '')
        model = item.get('model', '')
        exists = segmentation_model_exists(engine, model, root)
        local_path = spacy_model_local_path(model, root) if engine == 'spacy' else segmenter_root(root)
        rows.append({
            'name': item['name'],
            'type': item['type'],
            'description': item.get('description', 'Segmentation model'),
            'path': str(local_path),
            'exists': exists,
            'downloadable': item.get('downloadable', False),
        })
    return rows


def download_sentence_model(model_name: str, root: str = '', device: str = 'cpu', progress: Callable[[str, float], None] | None = None):
    root_path = model_root(root)
    if progress:
        progress(f'Preparing to download/load {model_name}', 0.05)
    from sentence_transformers import SentenceTransformer  # type: ignore
    SentenceTransformer(model_name, cache_folder=str(root_path / 'sentence_transformers'), device=device)
    found = find_local_model(model_name, root)
    if progress:
        progress(f'Model is available: {model_name}', 1.0)
    return str(found or root_path)




def download_stanza_model(lang: str, root: str = '', progress: Callable[[str, float], None] | None = None):
    if progress:
        progress(f'Downloading Stanza tokenizer for {lang}', 0.05)
    import stanza  # type: ignore
    dest = segmenter_root(root) / 'stanza'
    dest.mkdir(parents=True, exist_ok=True)
    stanza.download(lang=lang, model_dir=str(dest), processors='tokenize', verbose=False)
    if progress:
        progress(f'Stanza model is available: {lang}', 1.0)
    return str(dest)


def download_spacy_model(model: str, root: str = '', progress: Callable[[str, float], None] | None = None):
    """Install a spaCy pipeline and mirror it into models/segmenters/spacy/.

    spaCy's official downloader installs pipelines as Python packages in the
    active environment, so users do not normally see a new folder under the
    application's models directory.  AlignLens keeps that installation, but it
    also serializes a local copy/marker into models/segmenters/spacy/<model>/ so
    the Model Manager can show the model as locally available and source builds
    have a visible model record next to Stanza/HanLP assets.
    """
    if progress:
        progress(f'Downloading spaCy pipeline {model}', 0.05)
    import subprocess, sys
    import spacy  # type: ignore
    dest = spacy_model_local_path(model, root)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', model])
    except Exception as exc:
        # If the package is already importable, still create the local mirror.
        if not _package_available(model):
            raise exc
    if progress:
        progress(f'Loading spaCy pipeline {model}', 0.65)
    try:
        nlp = spacy.load(model)
        nlp.to_disk(dest)
    except Exception:
        # Some pipelines or environments may not serialize cleanly.  Keep a
        # small marker so the user can still see that the spaCy package exists.
        marker = {
            'model': model,
            'installed_as_python_package': _package_available(model),
            'note': 'spaCy pipelines are installed as Python packages; AlignLens created this local record for model management.',
        }
        (dest / 'alignlens_spacy_model.json').write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding='utf-8')
    if progress:
        progress(f'spaCy model is available: {model}', 1.0)
    return str(dest)


def download_hanlp_model(model: str = 'UD_CTB_EOS_MUL', root: str = '', progress: Callable[[str, float], None] | None = None):
    if progress:
        progress(f'Loading/downloading HanLP model {model}', 0.05)
    import hanlp  # type: ignore
    hanlp.load(model)
    if progress:
        progress(f'HanLP model is available: {model}', 1.0)
    return model


def download_segmentation_model(name: str, root: str = '', progress: Callable[[str, float], None] | None = None):
    if name.startswith('stanza:'):
        return download_stanza_model(name.split(':', 1)[1], root, progress)
    if name.startswith('spacy:'):
        return download_spacy_model(name.split(':', 1)[1], root, progress)
    if name.startswith('hanlp:'):
        return download_hanlp_model(name.split(':', 1)[1], root, progress)
    raise RuntimeError(f'Unsupported segmentation model entry: {name}')

def delete_sentence_model(model_name: str, root: str = '') -> bool:
    removed = False
    for p in candidate_model_paths(model_name, root):
        # Only delete folders inside the configured model root.
        try:
            if p.exists() and model_root(root).resolve() in [p.resolve(), *p.resolve().parents]:
                if p.name == 'snapshots':
                    continue
                shutil.rmtree(p, ignore_errors=True)
                removed = True
        except Exception:
            pass
    return removed


def import_local_model(src: str, model_name: str, root: str = '') -> str:
    srcp = Path(src)
    if not srcp.exists():
        raise RuntimeError(f'Local model path does not exist: {src}')
    dest = model_local_path(model_name or srcp.name, root)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(srcp, dest)
    return str(dest)
