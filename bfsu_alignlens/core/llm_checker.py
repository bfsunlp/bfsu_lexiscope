from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .datatypes import AlignmentUnit, LLMSuggestion
from .llm_aligner import OpenAILLMClient
from .prompt_manager import get_prompt, render_prompt
from .language_registry import display_name

CHECK_SYSTEM_PROMPT = get_prompt('LLM_CHECK_SYSTEM', 'You are a conservative multilingual alignment verification assistant. Return valid JSON only.')

ALLOWED_OPERATIONS = {
    'mark_needs_review',
    'manual_check',
    'confirm_row',
    'add_note',
    'merge_with_previous',
    'merge_with_next',
    'move_source_up',
    'move_source_down',
    'move_target_up',
    'move_target_down',
    'move_cell_up',
    'move_cell_down',
    'split_source',
    'split_target',
    'split_cell',
    'no_action',
}

SEGMENTATION_ISSUES = {
    'bad_segmentation',
    'over_segmented',
    'under_segmented',
    'not_minimal_alignment_unit',
    'wrong_row_match',
    'missing_source_or_target',
    'possible_row_shift',
    'multi_target_mismatch',
    'manual_confirmation_needed',
    'alignment_ok',
}



def _suggestion_language_label(code: str) -> tuple[str, str]:
    code = (code or 'en').strip()
    if code in {'auto', 'interface'}:
        code = 'en'
    if code == 'zh_sim':
        return code, 'Simplified Chinese (简体中文)'
    if code == 'zh_tra':
        return code, 'Traditional Chinese (繁體中文)'
    return code, display_name(code, 'en', with_code=True) if code else 'English'


def _clip_text(text: str, limit: int = 360) -> str:
    text = (text or '').replace('\r', ' ').strip()
    if len(text) <= limit:
        return text
    return text[:limit] + ' …'


def _row_block(row: AlignmentUnit, columns: Sequence[str], source_col: str, target_cols: Sequence[str]) -> str:
    """Detailed row block for LLM validation.

    Intentionally does not include Transformer similarity values.  The LLM
    should reason from text, segmentation, row order and adjacent context only.
    """
    lines = [
        f"ROW {row.row_id}",
        f"GROUP {row.group_id}",
        f"STATUS {row.status}",
        f"ISSUE {row.issue_type}",
        f"ALIGNMENT_LEVEL {getattr(row, 'alignment_level', '') or ''}",
        f"SOURCE_COLUMN {source_col}",
        f"SOURCE_TEXT {_clip_text(row.segments.get(source_col, ''))}",
    ]
    for col in target_cols:
        lines.append(f"TARGET_COLUMN {col}")
        lines.append(f"TARGET_TEXT {_clip_text(row.segments.get(col, ''))}")
    if row.note:
        lines.append(f"USER_NOTE {_clip_text(row.note, 220)}")
    return '\n'.join(lines)


def _global_outline(rows: List[AlignmentUnit], source_col: str, target_cols: Sequence[str], limit_per_text: int = 100) -> str:
    """Compact whole-editor map for global row-order reasoning."""
    lines: List[str] = []
    for r in rows:
        src = _clip_text(r.segments.get(source_col, ''), limit_per_text)
        tgt_bits = []
        for col in target_cols:
            text = _clip_text(r.segments.get(col, ''), limit_per_text)
            tgt_bits.append(f"{col}: {text}")
        lines.append(f"ROW {r.row_id}: SRC: {src} || " + " || ".join(tgt_bits))
    return '\n'.join(lines)


def _neighbour_context(all_rows: List[AlignmentUnit], focus_rows: List[AlignmentUnit], source_col: str, target_cols: Sequence[str], window: int = 3) -> str:
    if not all_rows or not focus_rows:
        return ''
    focus_ids = {int(r.row_id) for r in focus_rows}
    wanted: set[int] = set()
    for rid in focus_ids:
        for j in range(rid - window, rid + window + 1):
            if 1 <= j <= len(all_rows):
                wanted.add(j)
    context_rows = [r for r in all_rows if int(r.row_id) in wanted]
    return _global_outline(context_rows, source_col, target_cols, limit_per_text=150)


def build_check_prompt(
    rows: List[AlignmentUnit],
    source_col: str,
    target_cols: List[str],
    min_confidence: float = 0.75,
    all_rows: List[AlignmentUnit] | None = None,
    suggestion_language: str = 'en',
) -> str:
    columns = [source_col] + list(target_cols)
    all_rows = all_rows or rows
    row_blocks = '\n\n'.join(_row_block(r, columns, source_col, target_cols) for r in rows)
    outline = _global_outline(all_rows, source_col, target_cols)
    neighbours = _neighbour_context(all_rows, rows, source_col, target_cols)
    focus_ids = ', '.join(str(r.row_id) for r in rows)
    suggestion_language_code, suggestion_language_name = _suggestion_language_label(suggestion_language)
    return render_prompt(
        'LLM_CHECK_USER',
        'Inspect FOCUS ROWS: $focus_ids. Return JSON suggestions only.\n$row_blocks',
        focus_ids=focus_ids,
        suggestion_language_code=suggestion_language_code,
        suggestion_language_name=suggestion_language_name,
        min_confidence=f'{min_confidence:.2f}',
        allowed_issue_types=', '.join(sorted(SEGMENTATION_ISSUES)),
        allowed_operations=', '.join(sorted(ALLOWED_OPERATIONS)),
        outline=outline,
        neighbours=neighbours,
        row_blocks=row_blocks,
    )


def _safe_int_list(values: Iterable) -> List[int]:
    out: List[int] = []
    for x in values or []:
        try:
            out.append(int(x))
        except Exception:
            continue
    return out




def row_signature(row: AlignmentUnit, source_col: str = '', target_cols: Sequence[str] | None = None) -> str:
    """Compact stable signature used to re-resolve LLM suggestions after row edits."""
    cols: List[str] = []
    if source_col:
        cols.append(source_col)
    if target_cols:
        cols.extend([c for c in target_cols if c and c not in cols])
    if not cols:
        cols = sorted((row.segments or {}).keys())
    parts = []
    for col in cols:
        txt = ' '.join((row.segments.get(col, '') or '').split())[:80]
        parts.append(f'{col}:{txt}')
    return '||'.join(parts)


def _needs_fallback_suggestion(row: AlignmentUnit, source_col: str, target_cols: Sequence[str]) -> bool:
    status = (row.status or '').lower()
    issue = (row.issue_type or '').lower()
    if status in {'needs_review', 'empty_or_residual', 'llm_low_confidence', 'llm_parse_fallback'}:
        return True
    if issue in {'source_residual', 'target_residual', 'low_similarity', 'missing_source_or_target'}:
        return True
    if not (row.segments.get(source_col, '') or '').strip():
        return True
    for col in target_cols:
        if not (row.segments.get(col, '') or '').strip():
            return True
    return False
def _normalize_suggestion(
    item: Dict,
    row_map: Dict[int, AlignmentUnit],
    valid_cols: set[str],
    default_group_id: str,
    source_col: str = '',
    target_cols: Sequence[str] | None = None,
    focus_rows: Sequence[AlignmentUnit] | None = None,
    batch_no: int = 0,
) -> LLMSuggestion | None:
    try:
        raw_row_id = int(item.get('row_id', 0) or 0)
    except Exception:
        return None

    # Round 23: LLMs sometimes return row numbers relative to the current
    # focus batch even when the prompt asks for absolute editor row ids.  This
    # used to make earlier batches disappear or appear duplicated, because
    # only the last batch happened to use absolute row ids.  First accept an
    # absolute row id; otherwise map 1..len(focus_rows) to the corresponding
    # absolute row in the current batch.
    row_id = raw_row_id
    if row_id not in row_map and focus_rows and 1 <= raw_row_id <= len(focus_rows):
        try:
            row_id = int(focus_rows[raw_row_id - 1].row_id)
            item['_relative_row_id'] = raw_row_id
        except Exception:
            row_id = raw_row_id
    if row_id not in row_map:
        return None
    anchor_row = row_map[row_id]
    op = str(item.get('suggested_operation') or 'no_action').strip().lower()
    if op not in ALLOWED_OPERATIONS:
        op = 'manual_check'
    col = str(item.get('column_key') or '').strip()
    if col and col not in valid_cols:
        col = ''
    try:
        confidence = float(item.get('confidence', 0.0) or 0.0)
    except Exception:
        confidence = 0.0
    problem = str(item.get('problem') or '').strip()
    reason = str(item.get('reason') or '').strip()
    issue_type = str(item.get('issue_type') or 'manual_confirmation_needed').strip()
    if issue_type not in SEGMENTATION_ISSUES:
        issue_type = 'manual_confirmation_needed'
    if not problem and op != 'no_action':
        problem = 'LLM suggests checking this alignment row, but did not provide a detailed problem statement.'
    if not reason and op != 'no_action':
        reason = 'No explicit reason returned; please inspect this row manually.'
    affected = [x for x in _safe_int_list(item.get('affected_rows', [])) if x in row_map]
    if row_id not in affected:
        affected = [row_id] + affected
    severity = str(item.get('severity') or 'medium').lower()
    if severity not in {'low', 'medium', 'high'}:
        severity = 'medium'
    return LLMSuggestion(
        row_id=row_id,
        group_id=str(item.get('group_id') or default_group_id or ''),
        column_key=col,
        issue_type=issue_type,
        severity=severity,
        problem=problem,
        suggested_operation=op,
        affected_rows=affected,
        confidence=max(0.0, min(1.0, confidence)),
        reason=reason,
        anchor_uid=getattr(anchor_row, 'unit_id', '') or '',
        anchor_signature=row_signature(anchor_row, source_col, target_cols),
        current_row_id=row_id,
        batch_no=int(batch_no or 0),
        relative_row_id=int(item.get('_relative_row_id') or 0),
    )


def llm_check_rows(
    rows: List[AlignmentUnit],
    client: OpenAILLMClient,
    source_col: str = '',
    target_cols: List[str] | None = None,
    batch_size: int = 40,
    min_confidence: float = 0.75,
    progress=None,
    cancel_event=None,
    global_context: bool = True,
    suggestion_language: str = 'en',
) -> List[LLMSuggestion]:
    """Validate alignment rows with an LLM in suggestion-only mode.

    This function intentionally does not calculate Transformer similarity and
    does not create low-similarity heuristics.  It asks the LLM to reason from
    the current editor's text, row order, segmentation granularity and local/
    global context, then validates that returned operations are structural and
    refer only to existing row ids and column keys.
    """
    if not rows:
        return []
    if not source_col:
        keys = list(rows[0].segments.keys())
        source_col = next((k for k in keys if k.startswith('source_')), keys[0] if keys else '')
    if target_cols is None:
        keys = []
        for r in rows:
            for k in r.segments.keys():
                if k not in keys:
                    keys.append(k)
        target_cols = [k for k in keys if k != source_col]
    valid_cols = set([source_col] + list(target_cols or []))
    out: List[LLMSuggestion] = []
    seen: set[tuple[int, str, str, str, str]] = set()
    bs = max(5, int(batch_size or 40))
    total = max(1, (len(rows) + bs - 1) // bs)
    for batch_no, offset in enumerate(range(0, len(rows), bs), 1):
        if cancel_event is not None and cancel_event.is_set():
            break
        chunk = rows[offset:offset+bs]
        row_map = {int(r.row_id): r for r in chunk}
        default_gid = chunk[0].group_id if chunk else ''
        if progress:
            progress(f'LLM checking alignment operations for rows {offset + 1}-{offset + len(chunk)} / {len(rows)}', min(0.98, batch_no / total))
        prompt = build_check_prompt(chunk, source_col, list(target_cols or []), min_confidence=min_confidence, all_rows=rows if global_context else chunk, suggestion_language=suggestion_language)
        data = client.chat_json(CHECK_SYSTEM_PROMPT, prompt)
        # Round 23: when the whole-editor outline is long, some API responses
        # can become malformed or omit the suggestions key.  Retry that batch
        # with the same focus rows plus neighbour context only; do not discard
        # earlier batches and do not let the last batch overwrite them.
        if (not isinstance(data, dict) or 'suggestions' not in data) and global_context:
            data = client.chat_json(
                CHECK_SYSTEM_PROMPT,
                build_check_prompt(chunk, source_col, list(target_cols or []), min_confidence=min_confidence, all_rows=chunk, suggestion_language=suggestion_language),
            )
        if cancel_event is not None and cancel_event.is_set():
            break
        for item in data.get('suggestions', []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            s = _normalize_suggestion(item, row_map, valid_cols, default_gid, source_col, target_cols or [], focus_rows=chunk, batch_no=batch_no)
            if not s or s.suggested_operation == 'no_action':
                continue
            # Preserve batch metadata in the suggestion dict produced later;
            # this is useful for debugging multi-batch LLM validation.
            try:
                setattr(s, '_batch_no', batch_no)
            except Exception:
                pass
            key = (int(s.row_id or 0), str(s.column_key or ''), str(s.issue_type or ''), str(s.suggested_operation or ''), str(s.problem or ''))
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
    return out
