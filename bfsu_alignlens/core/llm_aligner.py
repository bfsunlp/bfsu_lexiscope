from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

from .datatypes import AlignmentUnit, Segment
from .prompt_manager import get_prompt, render_prompt

SYSTEM_PROMPT = get_prompt('LLM_ALIGNMENT_SYSTEM', 'You are a conservative multilingual alignment assistant. Return valid JSON only.')


def extract_json(text: str) -> Dict:
    if not text:
        return {}
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r'\{.*\}', cleaned, re.S)
    if match:
        blob = match.group(0)
        blob = blob.replace('\ufeff', '')
        try:
            return json.loads(blob)
        except Exception:
            # Common repairs: trailing commas, single quotes.
            repaired = re.sub(r',\s*([}\]])', r'\1', blob)
            repaired = repaired.replace("'", '"')
            try:
                return json.loads(repaired)
            except Exception:
                return {}
    return {}


class OpenAILLMClient:
    """Thin OpenAI client wrapper with Responses API first and Chat fallback.

    The wrapper keeps gpt-5.4-mini as the project default but deliberately does
    not hard-code a model whitelist. Users may enter newer model names such as
    GPT-5.5 variants or any other OpenAI-compatible model available to their
    account. For recent reasoning models that reject temperature or strict JSON
    arguments, the request automatically retries with progressively simpler
    payloads.
    """

    def __init__(
        self,
        api_key: str = '',
        model: str = 'gpt-5.4-mini',
        temperature: float = 0.0,
        timeout: int = 90,
        max_tokens: int = 3000,
        strict_json: bool = True,
        retry_times: int = 1,
    ):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.model = (model or 'gpt-5.4-mini').strip() or 'gpt-5.4-mini'
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.strict_json = bool(strict_json)
        self.retry_times = max(1, int(retry_times or 1))

    def _extract_response_text(self, resp) -> str:
        # OpenAI Responses API exposes output_text in recent SDKs. Keep structural
        # fallbacks so GPT-5.5/newer SDKs and older SDK objects can both work.
        text = getattr(resp, 'output_text', None)
        if text:
            return str(text)
        parts = []
        for item in getattr(resp, 'output', []) or []:
            for content in getattr(item, 'content', []) or []:
                value = getattr(content, 'text', None)
                if value:
                    # Some SDKs expose an object whose .value holds the text.
                    parts.append(str(getattr(value, 'value', value)))
                    continue
                if isinstance(content, dict):
                    if content.get('text'):
                        parts.append(str(content.get('text')))
                    elif content.get('type') == 'output_text' and content.get('content'):
                        parts.append(str(content.get('content')))
        if parts:
            return '\n'.join(parts)
        try:
            choices = getattr(resp, 'choices', []) or []
            if choices:
                return choices[0].message.content or ''
        except Exception:
            pass
        return ''

    def _responses_attempts(self, system_prompt: str, user_prompt: str) -> List[Dict]:
        base = {
            'model': self.model,
            'input': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'max_output_tokens': self.max_tokens,
        }
        attempts: List[Dict] = []
        if self.strict_json:
            attempts.append({**base, 'temperature': self.temperature, 'text': {'format': {'type': 'json_object'}}})
            attempts.append({**base, 'text': {'format': {'type': 'json_object'}}})
        attempts.append({**base, 'temperature': self.temperature})
        attempts.append(dict(base))
        return attempts

    def _chat_attempts(self, system_prompt: str, user_prompt: str) -> List[Dict]:
        chat_base = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        }
        attempts: List[Dict] = []
        for max_key in ('max_completion_tokens', 'max_tokens'):
            if self.strict_json:
                attempts.append({**chat_base, 'temperature': self.temperature, max_key: self.max_tokens, 'response_format': {'type': 'json_object'}})
                attempts.append({**chat_base, max_key: self.max_tokens, 'response_format': {'type': 'json_object'}})
            attempts.append({**chat_base, 'temperature': self.temperature, max_key: self.max_tokens})
            attempts.append({**chat_base, max_key: self.max_tokens})
        return attempts

    def _chat_json_once(self, client, system_prompt: str, user_prompt: str) -> Dict:
        # Prefer the current Responses API for latest GPT models, while keeping
        # Chat Completions fallbacks for older models and SDK versions.
        if hasattr(client, 'responses'):
            last_exc = None
            for kwargs in self._responses_attempts(system_prompt, user_prompt):
                try:
                    resp = client.responses.create(**kwargs)
                    data = extract_json(self._extract_response_text(resp))
                    if data:
                        return data
                except Exception as exc:
                    last_exc = exc
            # Continue to Chat Completions fallback below.

        last_exc = None
        for kwargs in self._chat_attempts(system_prompt, user_prompt):
            try:
                resp = client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ''
                data = extract_json(content)
                if data:
                    return data
            except Exception as exc:
                last_exc = exc
        if last_exc:
            raise RuntimeError(f'OpenAI LLM request failed: {last_exc}')
        return {}

    def chat_json(self, system_prompt: str, user_prompt: str) -> Dict:
        if not self.api_key:
            raise RuntimeError('OpenAI API Key is empty. Please set it in Settings > LLM.')
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise RuntimeError('openai package is not installed. Please run: pip install openai') from exc
        client = OpenAI(api_key=self.api_key, timeout=self.timeout)
        last_error = None
        for _ in range(self.retry_times):
            try:
                data = self._chat_json_once(client, system_prompt, user_prompt)
                if data:
                    return data
            except Exception as exc:
                last_error = exc
        if last_error:
            raise RuntimeError(f'OpenAI LLM request failed: {last_error}')
        return {}


def _numbered(segments: List[Segment]) -> str:
    return '\n'.join(f'{i+1}. {s.text}' for i, s in enumerate(segments))


def build_alignment_prompt(source_lang: str, target_lang: str, src: List[Segment], tgt: List[Segment]) -> str:
    return render_prompt(
        'LLM_ALIGNMENT_USER',
        'Align the following numbered text units. Source language: $source_lang Target language: $target_lang\nSOURCE UNITS:\n$source_units\nTARGET UNITS:\n$target_units',
        source_lang=source_lang,
        target_lang=target_lang,
        source_units=_numbered(src),
        target_units=_numbered(tgt),
    )

def _safe_segment_text(segments: List[Segment], ids: List[int]) -> str:
    return ' '.join(segments[i-1].text for i in ids if 1 <= i <= len(segments))


def _alignment_sort_key(sids: List[int], tids: List[int], src_len: int, tgt_len: int):
    if sids:
        src_pos = min(sids)
    elif tids and tgt_len:
        src_pos = int(round(min(tids) * max(src_len, 1) / max(tgt_len, 1)))
    else:
        src_pos = 10**9
    tgt_pos = min(tids) if tids else int(round(src_pos * max(tgt_len, 1) / max(src_len, 1)))
    return (src_pos, tgt_pos)


def _append_llm_or_residual_row(
    rows: List[AlignmentUnit],
    row_id: int,
    group_id: str,
    source_lang: str,
    target_lang: str,
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    src_offset: int,
    tgt_offset: int,
    sids_local: List[int],
    tids_local: List[int],
    confidence: float,
    status: str,
    note: str,
) -> int:
    src_text = _safe_segment_text(src_segments, sids_local)
    tgt_text = _safe_segment_text(tgt_segments, tids_local)
    rows.append(AlignmentUnit(
        row_id=row_id,
        group_id=group_id,
        segments={source_lang: src_text, target_lang: tgt_text},
        source_ids=[src_offset+i for i in sids_local],
        target_ids={target_lang: [tgt_offset+i for i in tids_local]},
        similarity=round(float(confidence), 4),
        similarities={target_lang: round(float(confidence), 4)},
        status=status,
        note=note,
        source_lang=source_lang,
    ))
    return row_id + 1


def llm_align_bilingual(
    src_segments: List[Segment],
    tgt_segments: List[Segment],
    source_lang: str,
    target_lang: str,
    group_id: str,
    client: OpenAILLMClient,
    batch_size: int = 40,
    min_confidence: float = 0.75,
    max_merge_units: int = 2,
    allow_2_to_2: bool = True,
) -> List[AlignmentUnit]:
    """LLM alignment with hard no-loss coverage repair.

    The LLM may omit difficult units.  AlignLens must never drop text, so every
    source and target segment not used by a validated LLM alignment is emitted
    as a residual 1:0 or 0:1 row.  Duplicate id reuse is ignored for the later
    duplicate occurrence and that segment is also preserved as residual.
    """
    rows: List[AlignmentUnit] = []
    src_offset = 0
    tgt_offset = 0
    row_id = 1
    safe_batch_size = max(10, int(batch_size or 40))
    while src_offset < len(src_segments) or tgt_offset < len(tgt_segments):
        src_batch = src_segments[src_offset:src_offset+safe_batch_size]
        tgt_batch = tgt_segments[tgt_offset:tgt_offset+safe_batch_size]
        if not src_batch and not tgt_batch:
            break
        prompt = build_alignment_prompt(source_lang, target_lang, src_batch, tgt_batch)
        data = client.chat_json(SYSTEM_PROMPT, prompt)
        alignments = data.get('alignments', []) if isinstance(data, dict) else []

        used_src: set[int] = set()
        used_tgt: set[int] = set()
        validated = []
        for item in alignments:
            if not isinstance(item, dict):
                continue
            raw_sids: List[int] = []
            raw_tids: List[int] = []
            for x in item.get('source_ids', []) or []:
                try: v = int(x)
                except Exception: continue
                if 1 <= v <= len(src_batch): raw_sids.append(v)
            for x in item.get('target_ids', []) or []:
                try: v = int(x)
                except Exception: continue
                if 1 <= v <= len(tgt_batch): raw_tids.append(v)
            # Enforce one-use coverage.  Reused ids are not silently dropped;
            # they simply remain uncovered and will be emitted as residual rows.
            sids = [i for i in raw_sids if i not in used_src]
            tids = [i for i in raw_tids if i not in used_tgt]
            if not sids and not tids:
                continue
            # Precision-first fine granularity guard.  The LLM may propose a
            # broad but plausible 3+ alignment.  Do not accept it as a coarse
            # cell; leave the units uncovered so the no-loss residual repair
            # keeps them visible as 1:0 / 0:1 rows for manual review.
            max_units = max(1, int(max_merge_units or 2))
            too_coarse = len(sids) > max_units or len(tids) > max_units
            disallowed_two_by_two = (len(sids) > 1 and len(tids) > 1 and not bool(allow_2_to_2))
            if too_coarse or disallowed_two_by_two:
                continue
            for i in sids: used_src.add(i)
            for i in tids: used_tgt.add(i)
            try: conf = float(item.get('confidence', 0.0) or 0.0)
            except Exception: conf = 0.0
            conf = max(0.0, min(1.0, conf))
            duplicate_use = len(sids) < len(raw_sids) or len(tids) < len(raw_tids)
            low_conf = conf < min_confidence or item.get('low_confidence') or duplicate_use
            status = 'llm_low_confidence' if low_conf else 'llm_aligned'
            reason = str(item.get('reason', '') or '')
            if duplicate_use:
                reason = (reason + ' | ' if reason else '') + 'Duplicate id reuse ignored; uncovered units preserved as residual rows.'
            validated.append((sids, tids, conf, status, reason))

        events = []
        for sids, tids, conf, status, reason in validated:
            events.append((_alignment_sort_key(sids, tids, len(src_batch), len(tgt_batch)), sids, tids, conf, status, reason))
        # Add all uncovered source/target units as visible blank-cell residuals.
        for i in range(1, len(src_batch) + 1):
            if i not in used_src:
                events.append((_alignment_sort_key([i], [], len(src_batch), len(tgt_batch)), [i], [], 0.0, 'empty_or_residual', 'LLM did not align this source unit; kept as 1:0 residual.'))
        for j in range(1, len(tgt_batch) + 1):
            if j not in used_tgt:
                events.append((_alignment_sort_key([], [j], len(src_batch), len(tgt_batch)), [], [j], 0.0, 'empty_or_residual', 'LLM did not align this target unit; kept as 0:1 residual.'))

        if not events:
            limit = max(len(src_batch), len(tgt_batch))
            for i in range(1, limit + 1):
                events.append((_alignment_sort_key([i] if i <= len(src_batch) else [], [i] if i <= len(tgt_batch) else [], len(src_batch), len(tgt_batch)), [i] if i <= len(src_batch) else [], [i] if i <= len(tgt_batch) else [], 0.0, 'llm_parse_fallback', 'LLM returned no usable alignment; kept indexed scaffold.'))

        for _, sids, tids, conf, status, reason in sorted(events, key=lambda x: x[0]):
            row_id = _append_llm_or_residual_row(rows, row_id, group_id, source_lang, target_lang, src_batch, tgt_batch, src_offset, tgt_offset, sids, tids, conf, status, reason)

        src_offset += len(src_batch)
        tgt_offset += len(tgt_batch)
    for i, row in enumerate(rows, 1):
        row.row_id = i
    return rows
