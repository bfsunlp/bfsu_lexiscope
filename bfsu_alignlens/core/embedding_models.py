from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

from .utils import resource_path
from .hardware import resolve_device


DEFAULT_MINILM = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
DEFAULT_LABSE = 'sentence-transformers/LaBSE'


def set_model_env(model_root: Optional[str] = None) -> Path:
    root = Path(model_root).expanduser() if model_root else resource_path('models')
    # A settings value of "models" should mean the models folder beside the
    # AlignLens program, not whichever folder the user happened to start Python
    # from. Absolute paths are still respected.
    if not root.is_absolute():
        root = resource_path(root)
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('HF_HOME', str(root / 'hf_home'))
    os.environ.setdefault('SENTENCE_TRANSFORMERS_HOME', str(root / 'sentence_transformers'))
    os.environ.setdefault('TRANSFORMERS_CACHE', str(root / 'transformers'))
    os.environ.setdefault('HANLP_HOME', str(root / 'hanlp'))
    os.environ.setdefault('STANZA_RESOURCES_DIR', str(root / 'stanza'))
    return root


class EmbeddingModelManager:
    def __init__(self, model_root: Optional[str] = None, device: str = 'auto', batch_size: int = 32):
        self.model_root = set_model_env(model_root)
        self.device = resolve_device(device)
        self.batch_size = batch_size
        self._models: Dict[str, object] = {}

    def set_device(self, device: str):
        self.device = resolve_device(device)

    def load(self, model_name: str):
        model_name = model_name or DEFAULT_MINILM
        cache_key = f'{model_name}|{self.device}'
        if cache_key in self._models:
            return self._models[cache_key]
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:
            raise RuntimeError('sentence-transformers is not installed. Please run: pip install sentence-transformers torch') from exc
        model = SentenceTransformer(model_name, cache_folder=str(self.model_root / 'sentence_transformers'), device=self.device)
        self._models[cache_key] = model
        return model

    def encode(self, texts: List[str], model_name: str, batch_size: Optional[int] = None) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1), dtype='float32')
        model = self.load(model_name)
        batch_size = batch_size or self.batch_size
        emb = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(emb, dtype='float32')

    def encode_fused(self, texts: List[str], models: Optional[List[str]] = None, batch_size: Optional[int] = None) -> np.ndarray:
        models = models or [DEFAULT_MINILM, DEFAULT_LABSE]
        arrays = [self.encode(texts, m, batch_size=batch_size) for m in models]
        # Different sentence-transformer models can have different embedding
        # dimensions (e.g. MiniLM=384, LaBSE=768). Averaging such arrays raises
        # a NumPy inhomogeneous-shape error.  Concatenating normalized embeddings
        # preserves information from each model and works across dimensions.
        valid = [np.asarray(a, dtype='float32') for a in arrays if getattr(a, 'ndim', 0) == 2 and a.shape[0] == len(texts)]
        if not valid:
            return np.zeros((len(texts), 1), dtype='float32')
        arr = np.concatenate(valid, axis=1) if len(valid) > 1 else valid[0]
        norm = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
        return arr / norm


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if a.size == 0 or b.size == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype='float32')
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return np.matmul(a_norm, b_norm.T)
