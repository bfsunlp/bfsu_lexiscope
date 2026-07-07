from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List

from .datatypes import AlignmentUnit


class MultiTxtOptions:
    def __init__(self, include_line_numbers=True, include_header=True, include_similarity=True, include_status=True,
                 include_note=True, include_position_info=False, missing_placeholder='', merge_separator=' ', encoding='utf-8', newline='\n',
                 create_subfolders=True, one_file_per_language=True, one_aligned_file=True, write_index=True):
        self.include_line_numbers = include_line_numbers
        self.include_header = include_header
        self.include_similarity = include_similarity
        self.include_status = include_status
        self.include_note = include_note
        self.include_position_info = include_position_info
        self.missing_placeholder = missing_placeholder
        self.merge_separator = merge_separator
        self.encoding = encoding
        self.newline = '\r\n' if newline.upper() == 'CRLF' else '\n'
        self.create_subfolders = create_subfolders
        self.one_file_per_language = one_file_per_language
        self.one_aligned_file = one_aligned_file
        self.write_index = write_index


def group_units(units: List[AlignmentUnit]) -> Dict[str, List[AlignmentUnit]]:
    groups: Dict[str, List[AlignmentUnit]] = {}
    for u in units:
        groups.setdefault(u.group_id or 'set_001', []).append(u)
    return groups


def _position_summary(unit: AlignmentUnit) -> str:
    parts = []
    for col, vals in (getattr(unit, 'positions', {}) or {}).items():
        if vals:
            parts.append(f"{col}:{','.join(str(v) for v in vals)}")
    return ' | '.join(parts)


def export_multi_txt(units: List[AlignmentUnit], output_dir: str, options: MultiTxtOptions | None = None, project_name: str = 'alignlens') -> List[Path]:
    options = options or MultiTxtOptions()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for group_id, rows in group_units(units).items():
        gdir = root / group_id if options.create_subfolders else root
        gdir.mkdir(parents=True, exist_ok=True)
        langs = []
        for r in rows:
            for lang in r.segments.keys():
                if lang not in langs:
                    langs.append(lang)
        if options.one_aligned_file:
            p = gdir / f'{group_id}_all_aligned.txt'
            with p.open('w', encoding=options.encoding, newline='') as f:
                header = ['row_id'] + langs + ['similarity', 'status', 'note']
                if options.include_header:
                    f.write('\t'.join(header) + options.newline)
                for r in rows:
                    cells = [str(r.row_id)] + [r.segments.get(lang, options.missing_placeholder) or options.missing_placeholder for lang in langs]
                    cells += [f'{r.similarity:.4f}', r.status, r.note]
                    f.write('\t'.join(cells) + options.newline)
            written.append(p)
        if options.one_file_per_language:
            for lang in langs:
                p = gdir / f'{group_id}_{lang}.txt'
                with p.open('w', encoding=options.encoding, newline='') as f:
                    for r in rows:
                        val = r.segments.get(lang, '') or options.missing_placeholder
                        if options.include_line_numbers:
                            f.write(f'{r.row_id}\t{val}' + options.newline)
                        else:
                            f.write(val + options.newline)
                written.append(p)
        if options.write_index:
            p = gdir / f'{group_id}_index.tsv'
            with p.open('w', encoding=options.encoding, newline='') as f:
                writer = csv.writer(f, delimiter='\t', lineterminator=options.newline)
                writer.writerow(['group_id', 'row_id', 'languages', 'similarity', 'status', 'note'])
                for r in rows:
                    writer.writerow([group_id, r.row_id, ','.join(langs), f'{r.similarity:.4f}', r.status, r.note])
            written.append(p)
    return written
