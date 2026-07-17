from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from hashlib import blake2s


@dataclass(frozen=True)
class LineSpan:
    number: int
    start: int
    end: int


@dataclass(frozen=True)
class DocumentChunk:
    """A lossless document slice with one non-overlapping editable core.

    Adjacent chunks may repeat a small amount of read-only context, but every
    source character belongs to exactly one editable core. This lets callers
    scan arbitrarily large files without merging documents or applying the
    same model edit twice.
    """

    chunk_id: str
    text: str
    start_offset: int
    end_offset: int
    core_start_offset: int
    core_end_offset: int
    first_line: int
    last_line: int
    core_first_line: int
    core_last_line: int
    start_column: int
    end_column: int
    core_start_column: int
    core_end_column: int
    source_hash: str

    @property
    def character_count(self) -> int:
        return len(self.text)


def build_line_spans(text: str) -> list[LineSpan]:
    if not text:
        return []
    pieces = text.splitlines(keepends=True)
    if not pieces:
        pieces = [text]
    covered = sum(len(piece) for piece in pieces)
    if covered < len(text):
        pieces.append(text[covered:])
    spans: list[LineSpan] = []
    offset = 0
    for number, piece in enumerate(pieces, 1):
        spans.append(LineSpan(number, offset, offset + len(piece)))
        offset += len(piece)
    return spans


def _line_starts(spans: list[LineSpan]) -> list[int]:
    return [span.start for span in spans]


def line_number_at_offset(spans: list[LineSpan], offset: int) -> int:
    if not spans:
        return 1
    starts = _line_starts(spans)
    index = bisect_right(starts, max(0, offset)) - 1
    return spans[min(len(spans) - 1, max(0, index))].number


def line_column_at_offset(spans: list[LineSpan], offset: int) -> tuple[int, int]:
    if not spans:
        return 1, 0
    line = line_number_at_offset(spans, offset)
    span = spans[line - 1]
    return line, max(0, offset - span.start)


def line_range_offsets(spans: list[LineSpan], first_line: int, last_line: int) -> tuple[int, int] | None:
    if not spans or first_line < 1 or last_line < first_line or last_line > len(spans):
        return None
    return spans[first_line - 1].start, spans[last_line - 1].end


def _bounded_context(
    text_length: int,
    core_start: int,
    core_end: int,
    desired_start: int,
    desired_end: int,
    max_chars: int,
) -> tuple[int, int]:
    core_length = core_end - core_start
    room = max(0, max_chars - core_length)
    left_wanted = max(0, core_start - desired_start)
    right_wanted = max(0, desired_end - core_end)
    left = min(left_wanted, room // 2)
    right = min(right_wanted, room - left)
    remaining = room - left - right
    if remaining:
        extra_left = min(left_wanted - left, remaining)
        left += extra_left
        remaining -= extra_left
    if remaining:
        right += min(right_wanted - right, remaining)
    return max(0, core_start - left), min(text_length, core_end + right)


def build_document_chunks(
    text: str,
    max_chars: int,
    overlap_lines: int = 2,
    overlap_chars: int = 192,
) -> list[DocumentChunk]:
    """Split text into full-coverage, line-aware chunks.

    Normal lines stay intact. A single minified HTML/JSON line that exceeds
    the request budget is divided by character position and receives a small
    character overlap. Context is read-only; editable cores never overlap.
    """

    if not text:
        return []
    budget = max(256, int(max_chars))
    overlap_lines = max(0, int(overlap_lines))
    overlap_chars = max(0, min(int(overlap_chars), budget // 4))
    reserve = min(2048, max(64, budget // 8))
    core_budget = max(128, budget - reserve)
    spans = build_line_spans(text)
    cores: list[tuple[int, int, int, int, int, int]] = []
    # (core_start, core_end, first_line_index, last_line_index,
    #  desired_context_start, desired_context_end)
    index = 0
    while index < len(spans):
        span = spans[index]
        line_length = span.end - span.start
        if line_length > core_budget:
            cursor = span.start
            while cursor < span.end:
                core_end = min(span.end, cursor + core_budget)
                desired_start = max(span.start, cursor - overlap_chars)
                desired_end = min(span.end, core_end + overlap_chars)
                cores.append((cursor, core_end, index, index, desired_start, desired_end))
                cursor = core_end
            index += 1
            continue

        first = index
        core_start = span.start
        core_end = span.end
        index += 1
        while index < len(spans):
            candidate = spans[index]
            candidate_length = candidate.end - candidate.start
            if candidate_length > core_budget or candidate.end - core_start > core_budget:
                break
            core_end = candidate.end
            index += 1
        last = index - 1
        context_first = max(0, first - overlap_lines)
        context_last = min(len(spans) - 1, last + overlap_lines)
        # A neighboring "line" in minified HTML may contain hundreds of
        # thousands of characters. Keep line-count semantics but cap context
        # bytes per side so overlap cannot dominate API traffic.
        context_cap = min(768, max(128, budget // 20))
        cores.append(
            (
                core_start,
                core_end,
                first,
                last,
                max(spans[context_first].start, core_start - context_cap),
                min(spans[context_last].end, core_end + context_cap),
            )
        )

    chunks: list[DocumentChunk] = []
    for position, (core_start, core_end, first, last, desired_start, desired_end) in enumerate(cores, 1):
        start, end = _bounded_context(
            len(text), core_start, core_end, desired_start, desired_end, budget
        )
        first_line, start_column = line_column_at_offset(spans, start)
        final_probe = max(start, end - 1)
        last_line, end_column = line_column_at_offset(spans, final_probe)
        if end > start:
            end_column += 1
        core_first_line, core_start_column = line_column_at_offset(spans, core_start)
        core_final_probe = max(core_start, core_end - 1)
        core_last_line, core_end_column = line_column_at_offset(spans, core_final_probe)
        if core_end > core_start:
            core_end_column += 1
        chunks.append(
            DocumentChunk(
                chunk_id=f"C{position:05d}",
                text=text[start:end],
                start_offset=start,
                end_offset=end,
                core_start_offset=core_start,
                core_end_offset=core_end,
                first_line=first_line,
                last_line=last_line,
                core_first_line=core_first_line,
                core_last_line=core_last_line,
                start_column=start_column,
                end_column=end_column,
                core_start_column=core_start_column,
                core_end_column=core_end_column,
                source_hash=blake2s(text[start:end].encode("utf-8"), digest_size=8).hexdigest(),
            )
        )
    return chunks


def locate_chunk_fragment(
    text: str,
    spans: list[LineSpan],
    chunk: DocumentChunk,
    fragment: str,
    start_line: int,
    end_line: int,
    occurrence: int = 1,
) -> tuple[int, int] | None:
    """Resolve an exact model fragment inside its claimed line range.

    The returned start must belong to this chunk's unique editable core. Line
    claims are verified against the source rather than trusted.
    """

    if not fragment or occurrence < 1:
        return None
    line_range = line_range_offsets(spans, start_line, end_line)
    if line_range is None:
        return None
    search_start = max(chunk.start_offset, line_range[0])
    search_end = min(chunk.end_offset, line_range[1])
    if search_end <= search_start:
        return None
    found = -1
    cursor = search_start
    for _ in range(occurrence):
        found = text.find(fragment, cursor, search_end)
        if found < 0:
            return None
        cursor = found + len(fragment)
    end = found + len(fragment)
    if not (chunk.core_start_offset <= found < chunk.core_end_offset):
        return None
    if end > chunk.end_offset:
        return None
    actual_start = line_number_at_offset(spans, found)
    actual_end = line_number_at_offset(spans, max(found, end - 1))
    if actual_start != start_line or actual_end != end_line:
        return None
    return found, end


def locate_chunk_fragment_candidates(
    text: str,
    chunk: DocumentChunk,
    fragment: str,
    limit: int = 501,
) -> list[tuple[int, int]]:
    """Return exact fragment occurrences owned by one chunk's editable core.

    Model-supplied line and occurrence metadata is useful as a hint, but some
    compatible providers number the visible ``<document>`` block from one
    rather than using the global line range in the prompt.  Candidate recovery
    therefore relies only on exact source characters and the application-owned
    editable core.  Callers must reject a result when more than one candidate
    remains after applying reliable line hints.
    """

    if not fragment or limit < 1:
        return []
    candidates: list[tuple[int, int]] = []
    cursor = chunk.start_offset
    while cursor < chunk.end_offset and len(candidates) < limit:
        found = text.find(fragment, cursor, chunk.end_offset)
        if found < 0:
            break
        end = found + len(fragment)
        if chunk.core_start_offset <= found < chunk.core_end_offset and end <= chunk.end_offset:
            candidates.append((found, end))
        cursor = found + max(1, len(fragment))
    return candidates


def occurrence_for_span(text: str, fragment: str, target_start: int) -> int | None:
    if not fragment or target_start < 0:
        return None
    occurrence = 0
    cursor = 0
    while True:
        found = text.find(fragment, cursor)
        if found < 0:
            return None
        occurrence += 1
        if found == target_start:
            return occurrence
        if found > target_start:
            return None
        cursor = found + len(fragment)
