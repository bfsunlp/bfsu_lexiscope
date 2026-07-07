from __future__ import annotations

from typing import Dict, List
from .datatypes import AlignmentUnit, FileRecord, Segment


def compute_statistics(files: List[FileRecord], segments_by_file: Dict[str, List[Segment]], alignments: List[AlignmentUnit], low_threshold: float = 0.65) -> Dict:
    langs = sorted({f.lang for f in files if f.lang})
    lang_stats = {lang: {'files': 0, 'chars': 0, 'sentences': 0} for lang in langs}
    for f in files:
        if not f.lang:
            continue
        lang_stats.setdefault(f.lang, {'files': 0, 'chars': 0, 'sentences': 0})
        lang_stats[f.lang]['files'] += 1
        lang_stats[f.lang]['chars'] += f.char_count
        lang_stats[f.lang]['sentences'] += len(segments_by_file.get(f.file_id, [])) or f.sentence_count
    sims = [a.similarity for a in alignments if isinstance(a.similarity, (int, float))]
    return {
        'file_count': len(files),
        'language_count': len(langs),
        'group_count': len({f.group_id for f in files}),
        'sentence_count': sum(len(v) for v in segments_by_file.values()),
        'alignment_unit_count': len(alignments),
        'average_similarity': round(sum(sims)/len(sims), 4) if sims else 0,
        'low_similarity_rows': sum(1 for a in alignments if a.similarity < low_threshold),
        'empty_rows': sum(1 for a in alignments if any(not v for v in a.segments.values())),
        'residual_rows': sum(1 for a in alignments if 'residual' in a.status or 'residual' in a.issue_type),
        'confirmed_ratio': round(sum(1 for a in alignments if a.confirmed)/len(alignments), 4) if alignments else 0,
        'llm_suggestion_rows': sum(1 for a in alignments if a.llm_suggestion),
        'languages': lang_stats,
    }
