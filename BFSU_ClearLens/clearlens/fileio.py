from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from charset_normalizer import from_bytes

from .models import TextFile


TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl", ".xml",
    ".html", ".htm", ".srt", ".vtt", ".log", ".yaml", ".yml", ".ini",
    ".conf", ".cfg", ".tex", ".text",
}

OUTPUT_ENCODINGS = (
    "utf-8", "utf-8-sig", "gb18030", "gbk", "big5", "utf-16", "utf-16-le",
    "utf-16-be", "utf-32", "utf-32-le", "utf-32-be", "shift_jis", "cp949",
    "cp1252", "latin-1", "ascii",
)

COMMON_CJK = set(
    "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经"
    "十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形"
    "相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展"
    "五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战"
    "先回则任取据处理世车社门身受今精华第中文文本两第行页网络整理清洗语言研究资料繁體測試語"
)

DETECTION_ENCODINGS = {
    "gb18030", "gbk", "big5", "big5hkscs", "cp932", "shift_jis", "shift_jis_2004",
    "euc_jp", "euc_jis_2004", "cp949", "euc_kr", "cp1252", "cp1250", "cp1251",
    "cp1253", "cp1255", "cp1256", "cp1257", "iso8859_1", "iso8859_2", "latin_1",
}


def _decode_score(text: str) -> float:
    if not text:
        return 0.0
    score = sum(2.0 for char in text if char in COMMON_CJK)
    score += sum(0.15 for char in text if "\u3400" <= char <= "\u9fff")
    score += sum(1.2 for char in text if "\u3040" <= char <= "\u30ff")
    score += sum(1.2 for char in text if "\uac00" <= char <= "\ud7af")
    score -= sum(4.0 for char in text if ord(char) < 32 and char not in "\n\r\t")
    score -= text.count("\ufffd") * 8.0
    return score


def _decode_bytes(raw: bytes) -> tuple[str, str, float, list[str]]:
    for marker, encoding in (
        (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xff\xfe", "utf-16"),
        (b"\xfe\xff", "utf-16"),
    ):
        if raw.startswith(marker):
            return raw.decode(encoding), encoding, 1.0, []
    try:
        return raw.decode("utf-8"), "utf-8", 1.0, []
    except UnicodeDecodeError:
        pass

    matches = list(from_bytes(raw))
    candidates: list[str] = []
    for match in matches:
        if match.encoding:
            encoding = match.encoding.lower().replace("-", "_")
            if encoding in DETECTION_ENCODINGS and encoding not in candidates:
                candidates.append(encoding)
    for encoding in ("gb18030", "big5", "shift_jis", "cp949", "cp1252", "latin-1"):
        if encoding not in candidates:
            candidates.append(encoding)

    decoded: list[tuple[float, int, str, str]] = []
    for order, encoding in enumerate(candidates):
        try:
            text = raw.decode(encoding, errors="strict")
        except (UnicodeDecodeError, LookupError):
            continue
        prior = {
            "cp1252": 0.6,
            "big5": 0.2,
            "big5hkscs": 0.2,
            "gb18030": 0.15,
            "cp932": 0.15,
            "shift_jis": 0.15,
            "cp949": 0.15,
        }.get(encoding, 0.0)
        rank_bonus = max(0.0, 0.5 - order * 0.05)
        decoded.append((_decode_score(text) + prior + rank_bonus, order, encoding, text))
    if not decoded:
        return raw.decode("utf-8", errors="replace"), "utf-8", 0.0, ["encoding_detection_failed"]

    decoded.sort(key=lambda item: item[0], reverse=True)
    best_score, _order, encoding, text = decoded[0]
    second_score = decoded[1][0] if len(decoded) > 1 else best_score - 3
    gap = max(0.0, best_score - second_score)
    confidence = min(0.95, 0.35 + min(gap, 4.0) * 0.15)
    warnings = [] if confidence >= 0.6 else ["encoding_detection_low_confidence"]
    return text, encoding, confidence, warnings


def discover_text_files(paths: Iterable[Path], recursive: bool = True) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
        elif path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            files.extend(item for item in iterator if item.is_file() and item.suffix.lower() in TEXT_EXTENSIONS)
    return sorted(set(files), key=lambda item: str(item).lower())


def read_text_file(path: Path, source_root: Path | None = None) -> TextFile:
    raw = path.read_bytes()
    if not raw:
        return TextFile(path=path, original_text="", encoding="utf-8", confidence=1.0, source_root=source_root)

    text, encoding, confidence, warnings = _decode_bytes(raw)
    if "\ufffd" in text:
        warnings.append("replacement_character_found")
    return TextFile(
        path=path,
        original_text=text,
        encoding=encoding,
        confidence=confidence,
        source_root=source_root,
        warnings=warnings,
    )


def apply_newline_style(text: str, newline_style: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline_style == "crlf":
        return normalized.replace("\n", "\r\n")
    if newline_style == "cr":
        return normalized.replace("\n", "\r")
    return normalized


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 10000):
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(path)


def build_output_path(
    text_file: TextFile,
    output_dir: Path,
    suffix: str,
    preserve_folders: bool,
    overwrite: bool,
) -> Path:
    relative = text_file.relative_path if preserve_folders else Path(text_file.name)
    target_dir = output_dir / relative.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    extension = relative.suffix or ".txt"
    target = target_dir / f"{relative.stem}{suffix}{extension}"
    return target if overwrite else _unique_path(target)


def write_output_file(
    text: str,
    text_file: TextFile,
    output_dir: Path,
    encoding: str = "utf-8",
    newline_style: str = "lf",
    suffix: str = "_cleaned",
    preserve_folders: bool = True,
    overwrite: bool = False,
) -> Path:
    target = build_output_path(text_file, output_dir, suffix, preserve_folders, overwrite)
    if target.resolve() == text_file.path.resolve():
        raise ValueError("output_path_matches_source")
    rendered = apply_newline_style(text, newline_style)
    target.write_bytes(rendered.encode(encoding, errors="strict"))
    return target


def write_text_path(
    text: str,
    target: Path,
    encoding: str = "utf-8",
    newline_style: str = "lf",
    protected_paths: Iterable[Path] = (),
) -> Path:
    resolved = target.resolve()
    if any(resolved == Path(path).resolve() for path in protected_paths):
        raise ValueError("output_path_matches_source")
    target.parent.mkdir(parents=True, exist_ok=True)
    rendered = apply_newline_style(text, newline_style)
    target.write_bytes(rendered.encode(encoding, errors="strict"))
    return target


def write_cleaned_file(
    text_file: TextFile,
    output_dir: Path,
    encoding: str = "utf-8",
    suffix: str = "_cleaned",
) -> Path:
    return write_output_file(text_file.cleaned_text, text_file, output_dir, encoding=encoding, suffix=suffix)


def export_log_csv(log_rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_rows:
        output_path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in log_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(log_rows)


def export_log_json(log_rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(log_rows, ensure_ascii=False, indent=2), encoding="utf-8")
