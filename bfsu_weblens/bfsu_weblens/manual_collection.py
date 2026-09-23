# -*- coding: utf-8 -*-
"""Manual search-result collection helpers for BFSU WebLens 3.x.

Manual collection deliberately performs no search-engine navigation. WebLens
only generates initial search URLs and parses HTML files that the user saved
from a normal browser after manually paging through search results.
"""
from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse

from .collector import (
    BAIDU_BEIJING_TZ,
    CollectorConfig,
    SearchRecord,
    baidu_vertical_kind,
    build_query,
    build_search_url,
    expand_search_tasks,
    extract_records_from_html,
    is_baidu_vertical,
    split_date_range,
)


@dataclass(frozen=True)
class ManualSearchTask:
    index: int
    total: int
    engine: str
    query: str
    date_label: str
    url: str
    shard_start: date
    shard_end: date

    @property
    def label(self) -> str:
        engine_name = "Baidu" if self.engine == "baidu" else "Google"
        return f"{self.index}/{self.total} · {engine_name} · {self.query or '(empty query)'} · {self.date_label}"


@dataclass(frozen=True)
class SavedPageParseResult:
    path: str
    engine: str
    source_url: str
    records: tuple[SearchRecord, ...]
    warning: str = ""


def generate_manual_search_tasks(cfg: CollectorConfig) -> list[ManualSearchTask]:
    """Generate all initial search URLs implied by the current panel settings.

    This mirrors automatic collection exactly. For Baidu, multiple-term mode
    and multiple site/domain lines are expanded into separate term × domain
    tasks; enabled date slicing adds one initial URL per task/date unit.
    Pagination itself is intentionally left to the user.
    """
    search_tasks = expand_search_tasks(cfg)
    if not search_tasks:
        return []
    if cfg.date_filter_enabled:
        date_slices = split_date_range(cfg.start_date, cfg.end_date, cfg.day_step)
    else:
        today = date.today()
        date_slices = [(today, today)]

    raw: list[tuple[CollectorConfig, date, date, str]] = []
    for task_cfg in search_tasks:
        query = build_query(task_cfg.query_mode, task_cfg.query_terms, task_cfg.raw_query, task_cfg.site_filters)
        if not query.strip():
            continue
        for shard_start, shard_end in date_slices:
            raw.append((task_cfg, shard_start, shard_end, query))

    total = len(raw)
    result: list[ManualSearchTask] = []
    for idx, (task_cfg, shard_start, shard_end, query) in enumerate(raw, 1):
        engine = "baidu" if is_baidu_vertical(task_cfg.search_vertical) else "google"
        date_label = f"{shard_start.isoformat()} ~ {shard_end.isoformat()}" if task_cfg.date_filter_enabled else "No date restriction"
        result.append(
            ManualSearchTask(
                index=idx,
                total=total,
                engine=engine,
                query=query,
                date_label=date_label,
                url=build_search_url(task_cfg, shard_start, shard_end),
                shard_start=shard_start,
                shard_end=shard_end,
            )
        )
    return result


_SAVED_FROM_RE = re.compile(r"<!--\s*saved from url=\(\d+\)(.*?)\s*-->", re.I | re.S)
_CANONICAL_RE = re.compile(r'<link[^>]+rel=["\'](?:canonical|alternate)["\'][^>]+href=["\']([^"\']+)', re.I)
_BASE_RE = re.compile(r'<base[^>]+href=["\']([^"\']+)', re.I)
_CHARSET_RE = re.compile(br"charset\s*=\s*[\"']?([A-Za-z0-9._-]+)", re.I)


def read_saved_html(path: str | Path) -> str:
    p = Path(path)
    data = p.read_bytes()
    encodings: list[str] = []
    match = _CHARSET_RE.search(data[:65536])
    if match:
        try:
            encodings.append(match.group(1).decode("ascii", errors="ignore"))
        except Exception:
            pass
    encodings.extend(["utf-8-sig", "utf-8", "gb18030", "big5", "latin-1"])
    tried: set[str] = set()
    for encoding in encodings:
        key = encoding.lower()
        if not encoding or key in tried:
            continue
        tried.add(key)
        try:
            return data.decode(encoding)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def saved_page_source_url(html_text: str) -> str:
    """Recover the original online URL stored by browser Save Page As."""
    match = _SAVED_FROM_RE.search(html_text or "")
    if match:
        return html_lib.unescape(match.group(1).strip())
    for rx in (_CANONICAL_RE, _BASE_RE):
        match = rx.search(html_text or "")
        if match:
            return html_lib.unescape(match.group(1).strip())
    return ""


def detect_saved_page_engine(html_text: str, source_url: str = "") -> str:
    host = urlparse(source_url).netloc.lower() if source_url else ""
    if "baidu.com" in host:
        return "baidu"
    if host == "google.com" or host.endswith(".google.com") or re.search(r"(^|\.)google\.[a-z.]+$", host):
        return "google"
    text = (html_text or "")[:500000].lower()
    if "google.sn='newssearch'" in text or 'itemtype="http://schema.org/searchresultspage"' in text or "google 搜索" in text:
        return "google"
    if "www.baidu.com" in text or "百度一下" in text or "百度搜索" in text:
        return "baidu"
    return ""


def _parse_google_date_range(tbs: str) -> tuple[date | None, date | None]:
    if not tbs or "cdr:1" not in tbs:
        return None, None
    values: dict[str, str] = {}
    for part in tbs.split(","):
        if ":" in part:
            key, value = part.split(":", 1)
            values[key.strip()] = value.strip()
    def parse(value: str) -> date | None:
        try:
            return datetime.strptime(value, "%m/%d/%Y").date()
        except Exception:
            return None
    return parse(values.get("cd_min", "")), parse(values.get("cd_max", ""))


def _site_filters_from_query(query: str) -> list[str]:
    """Recover explicit site: filters from a saved search URL for metadata."""
    found: list[str] = []
    seen: set[str] = set()
    for value in re.findall(r"(?i)(?:^|[\s(])site:([^\s)]+)", query or ""):
        item = value.strip().strip('"\'').rstrip(".,;:")
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            found.append(item)
    return found


def _parse_baidu_date_range(gpc: str) -> tuple[date | None, date | None]:
    match = re.search(r"stf=(\d+),(\d+)", gpc or "")
    if not match:
        return None, None
    try:
        start = datetime.fromtimestamp(int(match.group(1)), tz=BAIDU_BEIJING_TZ).date()
        # Baidu's upper bound is the next day's midnight in WebLens URLs.
        end_exclusive = datetime.fromtimestamp(int(match.group(2)), tz=BAIDU_BEIJING_TZ).date()
        end = end_exclusive - timedelta(days=1)
        return start, max(start, end)
    except Exception:
        return None, None


def config_for_saved_page(base_cfg: CollectorConfig, html_text: str, source_url: str) -> tuple[CollectorConfig, date, date]:
    """Adapt current panel settings to metadata encoded in a saved result page."""
    params = parse_qs(urlparse(source_url).query) if source_url else {}
    engine = detect_saved_page_engine(html_text, source_url)
    today = date.today()
    shard_start = base_cfg.start_date if base_cfg.date_filter_enabled else today
    shard_end = base_cfg.end_date if base_cfg.date_filter_enabled else today

    if engine == "baidu":
        query = (params.get("wd") or [""])[0] or build_query(base_cfg.query_mode, base_cfg.query_terms, base_cfg.raw_query, base_cfg.site_filters)
        tn = (params.get("tn") or [""])[0].lower()
        if tn == "news" or "news.baidu" in source_url.lower():
            vertical = "baidu_news_media" if (params.get("medium") or [""])[0] == "1" else "baidu_news"
        else:
            vertical = "baidu_web"
        date_start, date_end = _parse_baidu_date_range((params.get("gpc") or [""])[0])
        date_enabled = bool(date_start and date_end)
        if date_enabled:
            shard_start, shard_end = date_start, date_end
        cfg = replace(
            base_cfg,
            query_mode="raw",
            query_terms=[query] if query else [],
            raw_query=query,
            site_filters=_site_filters_from_query(query),
            search_vertical=vertical,
            date_filter_enabled=date_enabled,
            start_date=shard_start,
            end_date=shard_end,
            baidu_sort="time" if (params.get("rtt") or [""])[0] == "4" else "focus",
        )
        return cfg, shard_start, shard_end

    query = (params.get("q") or [""])[0] or build_query(base_cfg.query_mode, base_cfg.query_terms, base_cfg.raw_query, base_cfg.site_filters)
    vertical = "news" if (params.get("tbm") or [""])[0] == "nws" or "newssearch" in (html_text or "")[:200000].lower() else "web"
    date_start, date_end = _parse_google_date_range((params.get("tbs") or [""])[0])
    date_enabled = bool(date_start and date_end)
    if date_enabled:
        shard_start, shard_end = date_start, date_end
    cfg = replace(
        base_cfg,
        query_mode="raw",
        query_terms=[query] if query else [],
        raw_query=query,
        site_filters=_site_filters_from_query(query),
        search_vertical=vertical,
        language_lr=(params.get("lr") or [base_cfg.language_lr])[0],
        country_cr=(params.get("cr") or [base_cfg.country_cr])[0],
        safe=(params.get("safe") or [base_cfg.safe])[0],
        disable_filter=(params.get("filter") or [""])[0] == "0" or base_cfg.disable_filter,
        date_filter_enabled=date_enabled,
        start_date=shard_start,
        end_date=shard_end,
    )
    return cfg, shard_start, shard_end


def parse_saved_search_page(path: str | Path, base_cfg: CollectorConfig, page_number: int = 1) -> SavedPageParseResult:
    html_text = read_saved_html(path)
    source_url = saved_page_source_url(html_text)
    engine = detect_saved_page_engine(html_text, source_url)
    expected = "baidu" if is_baidu_vertical(base_cfg.search_vertical) else "google"
    if engine and engine != expected:
        return SavedPageParseResult(
            path=str(path),
            engine=engine,
            source_url=source_url,
            records=(),
            warning=f"Saved page belongs to {engine}, but the current panel is {expected}.",
        )
    cfg, shard_start, shard_end = config_for_saved_page(base_cfg, html_text, source_url)
    records = extract_records_from_html(
        html_text,
        cfg,
        source_url or str(path),
        shard_start,
        shard_end,
        max(1, int(page_number)),
    )
    warning = "" if records else "No usable search-result links were found in this HTML file."
    return SavedPageParseResult(
        path=str(path),
        engine=engine or expected,
        source_url=source_url,
        records=tuple(records),
        warning=warning,
    )


def parse_saved_search_pages(paths: Iterable[str | Path], base_cfg: CollectorConfig) -> list[SavedPageParseResult]:
    results: list[SavedPageParseResult] = []
    for index, path in enumerate(paths, 1):
        results.append(parse_saved_search_page(path, base_cfg, page_number=index))
    return results
