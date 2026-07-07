from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .datatypes import AlignmentUnit, FileRecord, Segment
from .utils import now_str

VERSION = '1.3.0-round13'


def serialize_project(project_name: str, files: List[FileRecord], segments_by_file: Dict[str, List[Segment]], alignments: List[AlignmentUnit], settings: Dict, suggestions: List[Dict] | None = None, paragraph_segments_by_file: Dict[str, List[Segment]] | None = None, paragraph_alignments: List[AlignmentUnit] | None = None) -> Dict:
    return {
        'software': 'BFSU AlignLens',
        'version': VERSION,
        'project_name': project_name,
        'created_time': settings.get('created_time') or now_str(),
        'modified_time': now_str(),
        'files': [f.to_dict() for f in files],
        'segments_by_file': {k: [s.to_dict() for s in v] for k, v in segments_by_file.items()},
        'alignments': [a.to_dict() for a in alignments],
        'paragraph_segments_by_file': {k: [s.to_dict() for s in v] for k, v in (paragraph_segments_by_file or {}).items()},
        'paragraph_alignments': [a.to_dict() for a in (paragraph_alignments or [])],
        'llm_suggestions': suggestions or [],
        'settings': settings,
    }


def save_project(path: str, project_name: str, files: List[FileRecord], segments_by_file: Dict[str, List[Segment]], alignments: List[AlignmentUnit], settings: Dict, suggestions: List[Dict] | None = None, paragraph_segments_by_file: Dict[str, List[Segment]] | None = None, paragraph_alignments: List[AlignmentUnit] | None = None):
    data = serialize_project(project_name, files, segments_by_file, alignments, settings, suggestions, paragraph_segments_by_file, paragraph_alignments)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load_project(path: str) -> Dict:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    data['files'] = [FileRecord.from_dict(x) for x in data.get('files', [])]
    data['segments_by_file'] = {k: [Segment.from_dict(s) for s in v] for k, v in data.get('segments_by_file', {}).items()}
    data['alignments'] = [AlignmentUnit.from_dict(x) for x in data.get('alignments', [])]
    data['paragraph_segments_by_file'] = {k: [Segment.from_dict(s) for s in v] for k, v in data.get('paragraph_segments_by_file', {}).items()}
    data['paragraph_alignments'] = [AlignmentUnit.from_dict(x) for x in data.get('paragraph_alignments', [])]
    return data
