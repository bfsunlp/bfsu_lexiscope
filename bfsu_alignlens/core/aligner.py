from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np

from .datatypes import AlignmentUnit, Segment
from .embedding_models import DEFAULT_LABSE, DEFAULT_MINILM, EmbeddingModelManager, cosine_similarity_matrix

Progress = Optional[Callable[[str, float], None]]


@dataclass
class AlignmentParams:
    max_window: int = 5
    skip_penalty: float = -0.30
    empty_penalty: float = -0.30
    length_penalty_weight: float = 0.02
    paragraph_distance_penalty: float = 0.04
    min_similarity_threshold: float = 0.55
    high_confidence_threshold: float = 0.70
    low_similarity_match_penalty: float = 0.25
    # Sentence-level precision controls. These do not alter segmentation;
    # they only constrain how many already segmented units DP may merge into
    # one alignment cell.
    sentence_max_merge_units: int = 3
    sentence_allow_2_to_2: bool = True
    sentence_merge_penalty: float = 0.25
    sentence_strict_fine_alignment: bool = True
    max_gap: int = 5
    allow_cross_paragraph: bool = True
    residual_matching: bool = True
    strict_monotonic: bool = True
    batch_size: int = 32
    device: str = 'auto'
    model_mode: str = 'fused'  # minilm, labse, fused, custom
    custom_model: str = ''
    primary_model: str = DEFAULT_LABSE
    secondary_model: str = 'intfloat/multilingual-e5-base'
    use_secondary_model: bool = True
    dp_cpu_workers: int = 0
    # Large-document safeguard. Full window-DP over every source/target block
    # becomes prohibitively slow after GPU encoding. For large files AlignLens
    # switches to a banded sentence-level Transformer DP that finishes in
    # practical time while preserving monotonic alignment.
    large_doc_threshold: int = 2_000_000  # m*n sentence-pair threshold
    dp_band_size: int = 240              # sentence-level band half width
    dp_search_mode: str = 'full'         # auto | full | banded
    alignment_level: str = 'sentence'    # sentence | paragraph


def generate_window_blocks(segments: List[Segment], max_window: int = 5) -> Tuple[List[str], List[Tuple[int, int]], List[Tuple[int, int]]]:
    blocks: List[str] = []
    indices: List[Tuple[int, int]] = []
    para_spans: List[Tuple[int, int]] = []
    n = len(segments)
    for i in range(n):
        for w in range(1, min(max_window, n - i) + 1):
            chunk = segments[i:i+w]
            text = ' '.join(s.text for s in chunk)
            blocks.append(text)
            indices.append((i, i+w))
            para_spans.append((chunk[0].paragraph_id, chunk[-1].paragraph_id))
    return blocks, indices, para_spans


def _length_penalty(src_text: str, tgt_text: str, weight: float) -> float:
    if not weight:
        return 0.0
    a, b = max(len(src_text), 1), max(len(tgt_text), 1)
    ratio = abs(a - b) / max(a, b)
    return -weight * ratio


def _apply_low_similarity_residual_preference(score: float, adj: float, params: AlignmentParams, src_units: int = 1, tgt_units: int = 1) -> float:
    """Make weak matches lose to explicit 1:0 / 0:1 residual rows.

    This is intentionally precision-first: if a candidate match is below the
    configured threshold, AlignLens should prefer blank-cell residual rows over
    forcing a misleading source-target pair into the same row.  The original
    text is still preserved in the resulting alignment table.
    """
    threshold = float(getattr(params, 'min_similarity_threshold', 0.55) or 0.55)
    if score >= threshold:
        return adj
    penalty = float(getattr(params, 'low_similarity_match_penalty', 0.25) or 0.25)
    adj -= penalty
    residual_score = int(src_units) * float(getattr(params, 'skip_penalty', -0.4) or -0.4) + int(tgt_units) * float(getattr(params, 'empty_penalty', -0.4) or -0.4)
    # Keep weak matches slightly worse than leaving the units unmatched.
    return min(adj, residual_score - 0.05)



def _effective_max_window(params: AlignmentParams) -> int:
    """Return the DP window cap without changing segmentation results.

    For sentence alignment, large windows can combine several already-correct
    sentence segments into one large cell.  AlignLens therefore keeps the
    segment list untouched but caps the number of segments DP may merge.
    """
    max_window = max(1, int(getattr(params, 'max_window', 1) or 1))
    if str(getattr(params, 'alignment_level', 'sentence') or 'sentence').lower() == 'sentence':
        cap = max(1, int(getattr(params, 'sentence_max_merge_units', 3) or 3))
        return min(max_window, cap)
    return max_window


def _sentence_merge_allowed(params: AlignmentParams, src_units: int, tgt_units: int) -> bool:
    if str(getattr(params, 'alignment_level', 'sentence') or 'sentence').lower() != 'sentence':
        return True
    if not bool(getattr(params, 'sentence_strict_fine_alignment', True)):
        return True
    cap = max(1, int(getattr(params, 'sentence_max_merge_units', 3) or 3))
    if src_units > cap or tgt_units > cap:
        return False
    # In fine sentence mode, 2:2 often hides two separate 1:1 alignments in one
    # large row; allow 1:2 and 2:1, but disallow 2:2 unless explicitly enabled.
    if src_units > 1 and tgt_units > 1 and not bool(getattr(params, 'sentence_allow_2_to_2', True)):
        return False
    return True


def _sentence_merge_penalty(params: AlignmentParams, src_units: int, tgt_units: int) -> float:
    if str(getattr(params, 'alignment_level', 'sentence') or 'sentence').lower() != 'sentence':
        return 0.0
    extra = max(0, int(src_units) - 1) + max(0, int(tgt_units) - 1)
    if extra <= 0:
        return 0.0
    penalty = float(getattr(params, 'sentence_merge_penalty', 0.25) or 0.0)
    return -penalty * extra

def _paragraph_penalty(src_para: Tuple[int, int], tgt_para: Tuple[int, int], weight: float, allow_cross: bool) -> float:
    if not weight:
        return 0.0
    dist = abs(src_para[0] - tgt_para[0]) + abs(src_para[1] - tgt_para[1])
    if not allow_cross and dist > 2:
        return -9999.0
    return -weight * dist


def identify_uncovered(spans: Iterable[Tuple[int, int]], total: int) -> List[int]:
    covered = set()
    for s, e in spans:
        for i in range(s, e):
            covered.add(i)
    return [i for i in range(total) if i not in covered]


def segment_position_token(seg: Segment, level: str = 'sentence') -> str:
    level = (level or 'sentence').lower()
    if level == 'paragraph':
        return f"P{int(seg.paragraph_id or 0)}"
    return f"P{int(seg.paragraph_id or 0)}:S{int(seg.sentence_id or 0)}"


def position_tokens(segments: List[Segment], start: int, end: int, level: str = 'sentence') -> List[str]:
    return [segment_position_token(s, level) for s in segments[start:end]]


def _make_unit(
    group_id: str,
    source_col: str,
    target_col: str,
    src_text: str,
    tgt_text: str,
    source_ids: List[int],
    target_ids: List[int],
    score: float,
    status: str,
    issue: str,
    level: str,
    source_positions: Optional[List[str]] = None,
    target_positions: Optional[List[str]] = None,
) -> AlignmentUnit:
    return AlignmentUnit(
        0, group_id, {source_col: src_text, target_col: tgt_text}, source_ids, {target_col: target_ids},
        round(float(score), 4), {target_col: round(float(score), 4)}, status, issue,
        source_lang=source_col, alignment_level=level,
        positions={source_col: source_positions or [], target_col: target_positions or []},
    )


def deduplicate_alignment_units(rows: List[AlignmentUnit]) -> List[AlignmentUnit]:
    """Remove only true duplicate alignment rows while preserving every source/target unit.

    Earlier versions used displayed text as the duplicate key.  That can delete
    legitimate repeated sentences or paragraphs, which is unsafe for corpus
    alignment.  This version treats rows as duplicates only when they point to
    the same source ids and the same target ids.  Rows without ids are kept
    unless both ids and displayed content are identical.
    """
    seen = set()
    out: List[AlignmentUnit] = []
    for u in rows:
        tgt_key = tuple(sorted((k, tuple(v or [])) for k, v in (u.target_ids or {}).items()))
        has_ids = bool(u.source_ids or any(v for _, v in tgt_key))
        if has_ids:
            key = (u.group_id, u.alignment_level, tuple(u.source_ids or []), tgt_key)
        else:
            seg_key = tuple(sorted((k, ' '.join((v or '').split())) for k, v in (u.segments or {}).items()))
            key = (u.group_id, u.alignment_level, tuple(), tuple(), seg_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    for idx, u in enumerate(out, 1):
        u.row_id = idx
    return out



def _split_oversized_sentence_units(
    rows: List[AlignmentUnit],
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    source_col: str,
    target_col: str,
    group_id: str,
    params: AlignmentParams,
) -> List[AlignmentUnit]:
    """Protect sentence alignment from paragraph-like overmerged cells.

    This is a post-DP guard only.  It does not change segmentation results or
    run any additional splitting.  If an older project, stale cache, or an
    overly permissive DP path creates a sentence-level cell containing more
    sentence ids than allowed, the cell is unfolded into smaller 1:1 / 1:0 /
    0:1 rows so that every original sentence remains visible and editable.
    """
    if str(getattr(params, 'alignment_level', 'sentence') or 'sentence').lower() != 'sentence':
        return rows
    cap = max(1, int(getattr(params, 'sentence_max_merge_units', 3) or 3))
    out: List[AlignmentUnit] = []
    changed = False
    for u in rows:
        sids = [int(x) for x in (u.source_ids or []) if int(x) > 0]
        tids = [int(x) for x in (u.target_ids or {}).get(target_col, []) if int(x) > 0]
        if len(sids) <= cap and len(tids) <= cap:
            out.append(u)
            continue
        changed = True
        max_len = max(len(sids), len(tids), 1)
        for k in range(max_len):
            sid = sids[k] if k < len(sids) else None
            tid = tids[k] if k < len(tids) else None
            src_text = src_segments[sid - 1].text if sid and 0 <= sid - 1 < len(src_segments) else ''
            tgt_text = tgt_segments[tid - 1].text if tid and 0 <= tid - 1 < len(tgt_segments) else ''
            issue = 'overmerged_sentence_cell_split'
            status = 'needs_review'
            score = float(u.similarity or 0.0) if src_text and tgt_text else (params.skip_penalty if src_text else params.empty_penalty)
            out.append(_make_unit(
                group_id, source_col, target_col, src_text, tgt_text,
                [sid] if sid else [], [tid] if tid else [], score, status, issue, 'sentence',
                position_tokens(src_segments, sid - 1, sid, 'sentence') if sid else [],
                position_tokens(tgt_segments, tid - 1, tid, 'sentence') if tid else [],
            ))
    if not changed:
        return rows
    for idx, u in enumerate(out, 1):
        u.row_id = idx
    return out


def _model_name_from_mode(params: AlignmentParams) -> str:
    mode = (params.model_mode or 'minilm').lower()
    if mode == 'labse':
        return DEFAULT_LABSE
    if mode == 'custom' and params.custom_model:
        return params.custom_model
    if mode in {'primary', 'single'}:
        return params.primary_model or DEFAULT_MINILM
    return DEFAULT_MINILM


def _fused_model_list(params: AlignmentParams) -> List[str]:
    first = params.primary_model or DEFAULT_MINILM
    second = params.secondary_model or DEFAULT_LABSE
    models = [first]
    if bool(getattr(params, 'use_secondary_model', True)) and second and second != first:
        models.append(second)
    return models


def _encode_texts_for_mode(texts: List[str], params: AlignmentParams, embedder: EmbeddingModelManager) -> np.ndarray:
    mode = (params.model_mode or 'minilm').lower()
    if mode == 'fused':
        return embedder.encode_fused(texts, _fused_model_list(params), params.batch_size)
    return embedder.encode(texts, _model_name_from_mode(params), params.batch_size)


def _configure_cpu_threads(params: AlignmentParams) -> None:
    workers = int(getattr(params, 'dp_cpu_workers', 0) or 0)
    if workers <= 0:
        return
    try:
        import os
        for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = str(workers)
    except Exception:
        pass
    try:
        import torch  # type: ignore
        torch.set_num_threads(max(1, workers))
    except Exception:
        pass


def _mean_norm(arr: np.ndarray, start: int, end: int) -> np.ndarray:
    vec = np.mean(arr[start:end], axis=0)
    norm = np.linalg.norm(vec) + 1e-12
    return vec / norm


def _band_bounds(i: int, m: int, n: int, band: int) -> Tuple[int, int]:
    if m <= 0:
        return 0, n
    center = int(round(i * n / max(m, 1)))
    pad = max(8, int(band))
    return max(0, center - pad), min(n, center + pad)


def _update_score(dp: Dict[Tuple[int, int], float], back: Dict[Tuple[int, int], Tuple[int, int, str, int, int, float]],
                  key: Tuple[int, int], value: float, prev: Tuple[int, int, str, int, int, float]) -> None:
    if value > dp.get(key, -1e12):
        dp[key] = value
        back[key] = prev


def _align_bilingual_transformer_fast(
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    source_lang: str,
    target_lang: str,
    group_id: str,
    params: AlignmentParams,
    embedder: EmbeddingModelManager,
    progress: Progress = None,
) -> List[AlignmentUnit]:
    """Fast monotonic Transformer alignment for large documents.

    The original full window DP creates every source-window/target-window
    similarity and then performs a very large Python DP pass. Large files can
    therefore finish GPU encoding but appear to hang during the CPU DP stage.
    This path encodes individual sentences and runs a banded DP with 1-1, 1-2,
    and 2-1 transitions. It is intentionally conservative and monotonic.
    """
    m, n = len(src_segments), len(tgt_segments)
    if progress:
        progress('Large-document fast mode: encoding source sentences', 0.10)
    src_texts = [s.text for s in src_segments]
    tgt_texts = [s.text for s in tgt_segments]
    emb_s = _encode_texts_for_mode(src_texts, params, embedder)
    if progress:
        progress('Large-document fast mode: encoding target sentences', 0.30)
    emb_t = _encode_texts_for_mode(tgt_texts, params, embedder)
    band = max(40, int(getattr(params, 'dp_band_size', 240) or 240))
    dp: Dict[Tuple[int, int], float] = {(0, 0): 0.0}
    back: Dict[Tuple[int, int], Tuple[int, int, str, int, int, float]] = {}

    def in_band(ii: int, jj: int) -> bool:
        lo, hi = _band_bounds(ii, m, n, band + 4)
        return lo <= jj <= hi or (ii == m and jj == n)

    if progress:
        progress('Large-document fast mode: banded dynamic programming', 0.42)
    for i in range(m + 1):
        if progress and m:
            progress('Large-document fast mode: banded dynamic programming', 0.42 + 0.54 * i / max(m, 1))
        lo, hi = _band_bounds(i, m, n, band + 4)
        if i == 0:
            lo = 0
        if i == m:
            hi = n
        for j in range(lo, hi + 1):
            cur = dp.get((i, j))
            if cur is None:
                continue
            if i < m and in_band(i + 1, j):
                _update_score(dp, back, (i + 1, j), cur + params.skip_penalty, (i, j, 'src_skip', i, j, params.skip_penalty))
            if j < n and in_band(i, j + 1):
                _update_score(dp, back, (i, j + 1), cur + params.empty_penalty, (i, j, 'tgt_skip', i, j, params.empty_penalty))
            if i < m and j < n and in_band(i + 1, j + 1):
                score = float(np.dot(emb_s[i], emb_t[j]))
                adj = score + _length_penalty(src_texts[i], tgt_texts[j], params.length_penalty_weight)
                adj = _apply_low_similarity_residual_preference(score, adj, params, 1, 1)
                _update_score(dp, back, (i + 1, j + 1), cur + adj, (i, j, 'match', i, j, score))
            # Conservative split/merge transitions for common 1-2 and 2-1 cases.
            if i < m and j + 1 < n and _effective_max_window(params) >= 2 and _sentence_merge_allowed(params, 1, 2) and in_band(i + 1, j + 2):
                tv = _mean_norm(emb_t, j, j + 2)
                score = float(np.dot(emb_s[i], tv))
                tgt_text = ' '.join(tgt_texts[j:j+2])
                adj = score + _length_penalty(src_texts[i], tgt_text, params.length_penalty_weight) + _sentence_merge_penalty(params, 1, 2)
                adj = _apply_low_similarity_residual_preference(score, adj, params, 1, 2)
                _update_score(dp, back, (i + 1, j + 2), cur + adj, (i, j, 'match_1_2', i, j, score))
            if i + 1 < m and j < n and _effective_max_window(params) >= 2 and _sentence_merge_allowed(params, 2, 1) and in_band(i + 2, j + 1):
                sv = _mean_norm(emb_s, i, i + 2)
                score = float(np.dot(sv, emb_t[j]))
                src_text = ' '.join(src_texts[i:i+2])
                adj = score + _length_penalty(src_text, tgt_texts[j], params.length_penalty_weight) + _sentence_merge_penalty(params, 2, 1)
                adj = _apply_low_similarity_residual_preference(score, adj, params, 2, 1)
                _update_score(dp, back, (i + 2, j + 1), cur + adj, (i, j, 'match_2_1', i, j, score))
            if i + 1 < m and j + 1 < n and _effective_max_window(params) >= 2 and _sentence_merge_allowed(params, 2, 2) and in_band(i + 2, j + 2):
                sv = _mean_norm(emb_s, i, i + 2)
                tv = _mean_norm(emb_t, j, j + 2)
                score = float(np.dot(sv, tv))
                src_text = ' '.join(src_texts[i:i+2])
                tgt_text = ' '.join(tgt_texts[j:j+2])
                adj = score + _length_penalty(src_text, tgt_text, params.length_penalty_weight) + _sentence_merge_penalty(params, 2, 2)
                adj = _apply_low_similarity_residual_preference(score, adj, params, 2, 2)
                _update_score(dp, back, (i + 2, j + 2), cur + adj, (i, j, 'match_2_2', i, j, score))

    if (m, n) not in dp:
        # Widen once rather than leaving the user with a half-finished task.
        if progress:
            progress('Large-document fast mode: widening band', 0.94)
        params2 = AlignmentParams(**{**params.__dict__, 'dp_band_size': max(band * 2, band + 200), 'large_doc_threshold': 10**18})
        return _align_bilingual_transformer_fast(src_segments, tgt_segments, source_lang, target_lang, group_id, params2, embedder, progress)

    rows: List[AlignmentUnit] = []
    i, j = m, n
    while i > 0 or j > 0:
        prev = back.get((i, j))
        if prev is None:
            if i > 0:
                prev = (i - 1, j, 'src_skip', i - 1, j, params.skip_penalty)
            else:
                prev = (i, j - 1, 'tgt_skip', i, j - 1, params.empty_penalty)
        pi, pj, typ, si, tj, score = prev
        if typ.startswith('match'):
            s0, s1 = pi, i
            t0, t1 = pj, j
            src_text = ' '.join(x.text for x in src_segments[s0:s1])
            tgt_text = ' '.join(x.text for x in tgt_segments[t0:t1])
            status = 'auto_high_confidence' if score >= params.high_confidence_threshold else ('needs_review' if score < params.min_similarity_threshold else 'needs_review')
            issue = 'low_similarity' if score < params.min_similarity_threshold else ''
            rows.append(_make_unit(group_id, source_lang, target_lang, src_text, tgt_text, list(range(s0+1, s1+1)), list(range(t0+1, t1+1)), score, status, issue, getattr(params, 'alignment_level', 'sentence'), position_tokens(src_segments, s0, s1, getattr(params, 'alignment_level', 'sentence')), position_tokens(tgt_segments, t0, t1, getattr(params, 'alignment_level', 'sentence'))))
        elif typ == 'src_skip':
            src_text = src_segments[i - 1].text if i > 0 else ''
            rows.append(_make_unit(group_id, source_lang, target_lang, src_text, '', [i] if i > 0 else [], [], params.skip_penalty, 'empty_or_residual', 'source_residual', getattr(params, 'alignment_level', 'sentence'), position_tokens(src_segments, max(i-1,0), i, getattr(params, 'alignment_level', 'sentence')) if i > 0 else [], []))
        else:
            tgt_text = tgt_segments[j - 1].text if j > 0 else ''
            rows.append(_make_unit(group_id, source_lang, target_lang, '', tgt_text, [], [j] if j > 0 else [], params.empty_penalty, 'empty_or_residual', 'target_residual', getattr(params, 'alignment_level', 'sentence'), [], position_tokens(tgt_segments, max(j-1,0), j, getattr(params, 'alignment_level', 'sentence')) if j > 0 else []))
        i, j = pi, pj
    rows.reverse()
    rows = _split_oversized_sentence_units(rows, src_segments, tgt_segments, source_lang, target_lang, group_id, params)
    for idx, row in enumerate(rows, start=1):
        row.row_id = idx
    if progress:
        progress('Alignment completed', 1.0)
    return rows


def _block_scores(
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    params: AlignmentParams,
    embedder: EmbeddingModelManager,
    progress: Progress = None,
):
    src_blocks, src_idx, src_para = generate_window_blocks(src_segments, _effective_max_window(params))
    tgt_blocks, tgt_idx, tgt_para = generate_window_blocks(tgt_segments, _effective_max_window(params))
    if progress:
        progress('Encoding source and target windows', 0.15)
    emb_s = _encode_texts_for_mode(src_blocks, params, embedder)
    emb_t = _encode_texts_for_mode(tgt_blocks, params, embedder)
    if progress:
        progress('Computing similarity matrix', 0.45)
    sim = cosine_similarity_matrix(emb_s, emb_t)
    return sim, src_blocks, tgt_blocks, src_idx, tgt_idx, src_para, tgt_para


def align_bilingual_transformer(
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    source_lang: str,
    target_lang: str,
    group_id: str,
    params: Optional[AlignmentParams] = None,
    embedder: Optional[EmbeddingModelManager] = None,
    progress: Progress = None,
) -> List[AlignmentUnit]:
    params = params or AlignmentParams()
    _configure_cpu_threads(params)
    embedder = embedder or EmbeddingModelManager(device=params.device, batch_size=params.batch_size)
    m, n = len(src_segments), len(tgt_segments)
    if not m and not n:
        return []
    if not m or not n:
        return manual_align_by_index({source_lang: src_segments, target_lang: tgt_segments}, group_id, source_lang)

    dp_mode = str(getattr(params, 'dp_search_mode', 'auto') or 'auto').lower()
    use_banded = dp_mode in {'banded', 'speed', 'speed_first', 'fast'}
    if dp_mode in {'auto', 'automatic'}:
        use_banded = m * n > int(getattr(params, 'large_doc_threshold', 2_000_000) or 2_000_000)
    # Precision/full mode deliberately keeps the full window-DP path even for
    # large files; users can choose this for heavily reordered or abridged texts.
    if use_banded:
        if progress:
            progress('Using fast banded Transformer alignment', 0.05)
        return _align_bilingual_transformer_fast(src_segments, tgt_segments, source_lang, target_lang, group_id, params, embedder, progress)

    sim, src_blocks, tgt_blocks, src_idx, tgt_idx, src_para, tgt_para = _block_scores(src_segments, tgt_segments, params, embedder, progress)
    if progress:
        progress('Running dynamic programming alignment', 0.60)

    # Store available transitions ending at each DP coordinate to avoid O(m*n*all_windows^2) scanning.
    src_by_end: Dict[int, List[int]] = {}
    tgt_by_end: Dict[int, List[int]] = {}
    for k, (_, e) in enumerate(src_idx):
        src_by_end.setdefault(e, []).append(k)
    for k, (_, e) in enumerate(tgt_idx):
        tgt_by_end.setdefault(e, []).append(k)

    dp = np.full((m + 1, n + 1), -1e12, dtype='float64')
    back: List[List[Optional[Tuple[int, int, str, int, int, float]]]] = [[None for _ in range(n+1)] for _ in range(m+1)]
    dp[0, 0] = 0.0

    for i in range(m + 1):
        if progress and m:
            progress('Dynamic programming alignment', 0.60 + 0.30 * i / max(m, 1))
        for j in range(n + 1):
            if i > 0:
                cand = dp[i-1, j] + params.skip_penalty
                if cand > dp[i, j]:
                    dp[i, j] = cand
                    back[i][j] = (i-1, j, 'src_skip', -1, -1, params.skip_penalty)
            if j > 0:
                cand = dp[i, j-1] + params.empty_penalty
                if cand > dp[i, j]:
                    dp[i, j] = cand
                    back[i][j] = (i, j-1, 'tgt_skip', -1, -1, params.empty_penalty)
            if i in src_by_end and j in tgt_by_end:
                for si in src_by_end[i]:
                    s0, s1 = src_idx[si]
                    if params.max_gap and i - s0 > params.max_window:
                        continue
                    for tj in tgt_by_end[j]:
                        t0, t1 = tgt_idx[tj]
                        if params.max_gap and j - t0 > params.max_window:
                            continue
                        src_units = s1 - s0
                        tgt_units = t1 - t0
                        if not _sentence_merge_allowed(params, src_units, tgt_units):
                            continue
                        score = float(sim[si, tj])
                        adj = score + _length_penalty(src_blocks[si], tgt_blocks[tj], params.length_penalty_weight)
                        adj += _sentence_merge_penalty(params, src_units, tgt_units)
                        adj = _apply_low_similarity_residual_preference(score, adj, params, src_units, tgt_units)
                        adj += _paragraph_penalty(src_para[si], tgt_para[tj], params.paragraph_distance_penalty, params.allow_cross_paragraph)
                        cand = dp[s0, t0] + adj
                        if cand > dp[i, j]:
                            dp[i, j] = cand
                            back[i][j] = (s0, t0, 'match', si, tj, score)

    rows = []
    covered_s, covered_t = [], []
    i, j = m, n
    while i > 0 or j > 0:
        prev = back[i][j]
        if prev is None:
            # Safe fallback.
            if i > 0:
                prev = (i-1, j, 'src_skip', -1, -1, params.skip_penalty)
            else:
                prev = (i, j-1, 'tgt_skip', -1, -1, params.empty_penalty)
        pi, pj, typ, si, tj, score = prev
        if typ == 'match':
            s0, s1 = src_idx[si]
            t0, t1 = tgt_idx[tj]
            covered_s.append((s0, s1)); covered_t.append((t0, t1))
            src_text = ' '.join(x.text for x in src_segments[s0:s1])
            tgt_text = ' '.join(x.text for x in tgt_segments[t0:t1])
            status = 'auto_high_confidence' if score >= params.high_confidence_threshold else ('needs_review' if score < params.min_similarity_threshold else 'needs_review')
            issue = 'low_similarity' if score < params.min_similarity_threshold else ''
            rows.append(_make_unit(group_id, source_lang, target_lang, src_text, tgt_text, list(range(s0+1, s1+1)), list(range(t0+1, t1+1)), score, status, issue, getattr(params, 'alignment_level', 'sentence'), position_tokens(src_segments, s0, s1, getattr(params, 'alignment_level', 'sentence')), position_tokens(tgt_segments, t0, t1, getattr(params, 'alignment_level', 'sentence'))))
        elif typ == 'src_skip':
            src_text = src_segments[i-1].text
            rows.append(_make_unit(group_id, source_lang, target_lang, src_text, '', [i], [], params.skip_penalty, 'empty_or_residual', 'source_residual', getattr(params, 'alignment_level', 'sentence'), position_tokens(src_segments, max(i-1,0), i, getattr(params, 'alignment_level', 'sentence')), []))
        else:
            tgt_text = tgt_segments[j-1].text
            rows.append(_make_unit(group_id, source_lang, target_lang, '', tgt_text, [], [j], params.empty_penalty, 'empty_or_residual', 'target_residual', getattr(params, 'alignment_level', 'sentence'), [], position_tokens(tgt_segments, max(j-1,0), j, getattr(params, 'alignment_level', 'sentence'))))
        i, j = pi, pj

    rows.reverse()
    rows = _split_oversized_sentence_units(rows, src_segments, tgt_segments, source_lang, target_lang, group_id, params)
    for idx, row in enumerate(rows, start=1):
        row.row_id = idx
    if progress:
        progress('Alignment completed', 1.0)
    return rows


def manual_align_by_index(language_segments: Dict[str, List[Segment]], group_id: str, source_lang: str = '', level: str = 'sentence') -> List[AlignmentUnit]:
    langs = list(language_segments.keys())
    if not source_lang and langs:
        source_lang = langs[0]
    max_len = max((len(v) for v in language_segments.values()), default=0)
    rows = []
    for i in range(max_len):
        segs = {lang: (items[i].text if i < len(items) else '') for lang, items in language_segments.items()}
        tgt_ids = {lang: ([i+1] if i < len(items) else []) for lang, items in language_segments.items() if lang != source_lang}
        positions = {lang: ([segment_position_token(items[i], level)] if i < len(items) else []) for lang, items in language_segments.items()}
        rows.append(AlignmentUnit(i+1, group_id, segs, [i+1] if i < len(language_segments.get(source_lang, [])) else [], tgt_ids, 0.0, {}, 'manual_unconfirmed', source_lang=source_lang, alignment_level=level, positions=positions))
    return rows


def combine_multilingual_by_pivot(
    source_lang: str,
    target_results: Dict[str, List[AlignmentUnit]],
    group_id: str,
) -> List[AlignmentUnit]:
    # Merge target-specific bilingual alignments using source_id tuple as a loose pivot.
    buckets: Dict[Tuple[int, ...], AlignmentUnit] = {}
    order: List[Tuple[int, ...]] = []
    for tgt_lang, units in target_results.items():
        for u in units:
            key = tuple(u.source_ids) if u.source_ids else tuple([-100000 - u.row_id])
            if key not in buckets:
                base_segments = {source_lang: u.segments.get(source_lang, '')}
                buckets[key] = AlignmentUnit(0, group_id, base_segments, list(u.source_ids), {}, u.similarity, {}, u.status, source_lang=source_lang, alignment_level=getattr(u, 'alignment_level', 'sentence'), positions={source_lang: list((u.positions or {}).get(source_lang, []))})
                order.append(key)
            buckets[key].segments[tgt_lang] = u.segments.get(tgt_lang, '')
            buckets[key].target_ids[tgt_lang] = u.target_ids.get(tgt_lang, [])
            buckets[key].similarities[tgt_lang] = u.similarities.get(tgt_lang, u.similarity)
            buckets[key].positions[tgt_lang] = list((u.positions or {}).get(tgt_lang, []))
    rows = [buckets[k] for k in order]
    for idx, u in enumerate(rows, 1):
        u.row_id = idx
        if u.similarities:
            u.similarity = round(sum(u.similarities.values())/len(u.similarities), 4)
    return rows


def remap_local_alignment_positions(
    rows: List[AlignmentUnit],
    src_subset: List[Tuple[int, Segment]],
    tgt_subset: List[Tuple[int, Segment]],
    source_col: str,
    target_col: str,
    level: str = 'sentence',
) -> List[AlignmentUnit]:
    for u in rows:
        src_ids_local = list(u.source_ids or [])
        tgt_ids_local = list((u.target_ids or {}).get(target_col, []))
        new_src_ids: List[int] = []
        new_tgt_ids: List[int] = []
        src_pos: List[str] = []
        tgt_pos: List[str] = []
        for local_id in src_ids_local:
            idx = int(local_id) - 1
            if 0 <= idx < len(src_subset):
                original_index, seg = src_subset[idx]
                new_src_ids.append(original_index + 1)
                src_pos.append(segment_position_token(seg, level))
        for local_id in tgt_ids_local:
            idx = int(local_id) - 1
            if 0 <= idx < len(tgt_subset):
                original_index, seg = tgt_subset[idx]
                new_tgt_ids.append(original_index + 1)
                tgt_pos.append(segment_position_token(seg, level))
        u.source_ids = new_src_ids
        u.target_ids[target_col] = new_tgt_ids
        u.positions[source_col] = src_pos
        u.positions[target_col] = tgt_pos
        u.alignment_level = level
    return rows


def align_bilingual_transformer_within_paragraphs(
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    paragraph_rows: List[AlignmentUnit],
    source_col: str,
    target_col: str,
    group_id: str,
    params: Optional[AlignmentParams] = None,
    embedder: Optional[EmbeddingModelManager] = None,
    progress: Progress = None,
) -> List[AlignmentUnit]:
    """Align sentences inside already aligned paragraph pairs.

    Paragraph rows act as monotonic anchors.  Sentence alignment is run only
    within each paragraph-pair window, reducing long-distance mismatches and
    speeding up large documents.
    """
    params = params or AlignmentParams()
    params.alignment_level = 'sentence'
    embedder = embedder or EmbeddingModelManager(device=params.device, batch_size=params.batch_size)
    src_by_para: Dict[int, List[Tuple[int, Segment]]] = {}
    tgt_by_para: Dict[int, List[Tuple[int, Segment]]] = {}
    for idx, seg in enumerate(src_segments):
        src_by_para.setdefault(int(seg.paragraph_id or 0), []).append((idx, seg))
    for idx, seg in enumerate(tgt_segments):
        tgt_by_para.setdefault(int(seg.paragraph_id or 0), []).append((idx, seg))
    out: List[AlignmentUnit] = []
    anchors = [u for u in paragraph_rows if u.group_id == group_id]
    if not anchors:
        return align_bilingual_transformer(src_segments, tgt_segments, source_col, target_col, group_id, params, embedder, progress)
    total = max(len(anchors), 1)
    used_src: set[int] = set()
    used_tgt: set[int] = set()
    for aidx, anchor in enumerate(anchors, 1):
        src_para_ids = [int(x) for x in (anchor.source_ids or []) if int(x) in src_by_para]
        tgt_para_ids = [int(x) for x in (anchor.target_ids or {}).get(target_col, []) if int(x) in tgt_by_para]
        if not src_para_ids and (anchor.positions or {}).get(source_col):
            for token in anchor.positions.get(source_col, []):
                if token.startswith('P'):
                    try: src_para_ids.append(int(token[1:].split(':', 1)[0]))
                    except Exception: pass
        if not tgt_para_ids and (anchor.positions or {}).get(target_col):
            for token in anchor.positions.get(target_col, []):
                if token.startswith('P'):
                    try: tgt_para_ids.append(int(token[1:].split(':', 1)[0]))
                    except Exception: pass
        src_subset = [item for pid in src_para_ids for item in src_by_para.get(pid, [])]
        tgt_subset = [item for pid in tgt_para_ids for item in tgt_by_para.get(pid, [])]
        for idx, _ in src_subset: used_src.add(idx)
        for idx, _ in tgt_subset: used_tgt.add(idx)
        if progress:
            progress(f'Sentence alignment inside paragraph {aidx}/{total}', aidx / total)
        if src_subset or tgt_subset:
            local_src = [seg for _, seg in src_subset]
            local_tgt = [seg for _, seg in tgt_subset]
            local_rows = align_bilingual_transformer(local_src, local_tgt, source_col, target_col, group_id, params, embedder, None)
            out.extend(remap_local_alignment_positions(local_rows, src_subset, tgt_subset, source_col, target_col, 'sentence'))
    # Keep unmatched paragraphs visible for manual review.
    rest_src = [(i, s) for i, s in enumerate(src_segments) if i not in used_src]
    rest_tgt = [(i, s) for i, s in enumerate(tgt_segments) if i not in used_tgt]
    if rest_src or rest_tgt:
        local_rows = manual_align_by_index({source_col: [s for _, s in rest_src], target_col: [s for _, s in rest_tgt]}, group_id, source_col, level='sentence')
        out.extend(remap_local_alignment_positions(local_rows, rest_src, rest_tgt, source_col, target_col, 'sentence'))
    return deduplicate_alignment_units(out)


def compute_alignment_similarities(
    units: List[AlignmentUnit],
    source_col: str,
    target_cols: List[str],
    params: Optional[AlignmentParams] = None,
    embedder: Optional[EmbeddingModelManager] = None,
    progress: Progress = None,
) -> List[AlignmentUnit]:
    """Recompute row-level Transformer similarities after manual edits.

    The function does not change alignment structure.  It encodes the current
    source and target cell contents, updates per-target similarities and stores
    the row mean in ``unit.similarity``.  Empty source/target pairs get a low
    score so they remain visible for review.
    """
    params = params or AlignmentParams()
    _configure_cpu_threads(params)
    embedder = embedder or EmbeddingModelManager(device=params.device, batch_size=params.batch_size)
    target_cols = [c for c in target_cols if c and c != source_col]
    if not units or not source_col or not target_cols:
        return units
    src_texts = [(u.segments.get(source_col, '') or '').strip() for u in units]
    if progress:
        progress('Encoding source cells for similarity recomputation', 0.08)
    src_emb = _encode_texts_for_mode(src_texts, params, embedder) if any(src_texts) else None
    threshold = float(getattr(params, 'min_similarity_threshold', 0.55) or 0.55)
    high = float(getattr(params, 'high_confidence_threshold', 0.70) or 0.70)

    for tidx, tgt_col in enumerate(target_cols, 1):
        if progress:
            progress(f'Encoding target cells for {tgt_col}', 0.08 + 0.82 * (tidx - 1) / max(len(target_cols), 1))
        tgt_texts = [(u.segments.get(tgt_col, '') or '').strip() for u in units]
        tgt_emb = _encode_texts_for_mode(tgt_texts, params, embedder) if any(tgt_texts) else None
        for i, unit in enumerate(units):
            s_txt = src_texts[i]
            t_txt = tgt_texts[i]
            if not s_txt and not t_txt:
                score = 0.0
            elif not s_txt or not t_txt or src_emb is None or tgt_emb is None:
                score = float(getattr(params, 'empty_penalty', -0.4))
            else:
                score = float(np.dot(src_emb[i], tgt_emb[i]))
            unit.similarities[tgt_col] = round(score, 4)

    for idx, unit in enumerate(units, 1):
        unit.row_id = idx
        vals = [v for c, v in unit.similarities.items() if c in target_cols]
        unit.similarity = round(sum(vals) / len(vals), 4) if vals else 0.0
        if not unit.confirmed:
            if any(v < threshold for v in vals) or unit.similarity < threshold:
                unit.status = 'needs_review'
                unit.issue_type = 'low_similarity'
            elif unit.similarity >= high:
                unit.status = 'auto_high_confidence'
                unit.issue_type = ''
            elif unit.status in {'low_similarity', 'manual_unconfirmed', 'manual_split', 'manual_cell_moved', 'manual_cell_merged', 'manual_blank', ''}:
                unit.status = 'needs_review'
                unit.issue_type = ''
    if progress:
        progress('Similarity recomputation completed', 1.0)
    return units
