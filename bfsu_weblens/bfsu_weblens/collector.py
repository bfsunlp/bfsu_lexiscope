# -*- coding: utf-8 -*-
"""Browser-only Google/Baidu search collection core for BFSU WebLens.

The collector intentionally leaves pagination depth and per-page result count to
the search engine. WebLens opens the initial search URL in Chrome/Edge, follows
the engine-rendered Next link, and stops when the engine no longer offers a next
page or when a genuine empty result page is reached. No Requests/HTTP search
backend, page-count ceiling, or per-page result-size directive is used.
"""
from __future__ import annotations

import html as html_lib
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict, replace
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, quote, urljoin

from bs4 import BeautifulSoup

from .browser_manager import detect_browser_installations, ensure_driver
from .platform_paths import user_data_root

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_name", "fbclid", "gclid", "mc_cid", "mc_eid", "igshid", "ref", "ref_src"
}

GOOGLE_RESULT_HOST_BLACKLIST = {
    "accounts.google.com",
    "support.google.com",
    "policies.google.com",
    "myaccount.google.com",
    "ogs.google.com",
    "ssl.gstatic.com",
    "www.gstatic.com",
}

BAIDU_RESULT_HOST_BLACKLIST = {
    "www.baidu.com",
    "m.baidu.com",
    "news.baidu.com",
    "tieba.baidu.com",
    "zhidao.baidu.com",
    "wenku.baidu.com",
    "image.baidu.com",
    "map.baidu.com",
    "haokan.baidu.com",
}

BAIDU_BEIJING_TZ = timezone(timedelta(hours=8))

@dataclass
class CollectorConfig:
    query_mode: str
    query_terms: list[str]
    raw_query: str
    site_filters: list[str]
    search_vertical: str  # news | web
    fetch_backend: str    # selenium_chrome | selenium_edge
    language_lr: str      # e.g. lang_en|lang_fr
    country_cr: str       # e.g. countryUS|countryUK
    safe: str
    disable_filter: bool
    date_filter_enabled: bool
    start_date: date
    end_date: date
    day_step: int
    page_delay_min_ms: int
    page_delay_max_ms: int
    timeout_seconds: int
    user_agent: str
    browser_wait_ms: int = 5000
    browser_headless: bool = False
    browser_driver_path: str = ""
    browser_binary_path: str = ""
    save_debug_html: bool = True
    debug_dir: str = "weblens_debug_html"
    # Baidu is integrated through the same crawler pipeline. Existing Google
    # settings keep their original meaning; this field is ignored by Google.
    baidu_sort: str = "focus"  # focus | time

@dataclass
class SearchRecord:
    collected_at: str
    query: str
    search_vertical: str
    shard_start: str
    shard_end: str
    page: int
    rank: int
    title: str
    link: str
    source: str
    published_time: str
    snippet: str
    search_url: str
    language_lr: str
    country_cr: str
    search_engine: str = "google"
    source_filter: str = ""
    sort_mode: str = ""
    site_limit: str = ""
    actual_domain: str = ""
    query_raw: str = ""
    date_filter_type: str = "custom_range"
    date_start: str = ""
    date_end: str = ""
    start_ts: str = ""
    end_ts: str = ""
    baidu_gpc: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class CrawlEvent:
    event_type: str
    message: str
    record: Optional[SearchRecord] = None
    data: Optional[dict] = None

class StopCrawl(Exception):
    pass

class NetworkAccessError(Exception):
    pass

class BrowserStartupError(Exception):
    """Raised when Selenium cannot start the browser/driver session."""
    pass

def split_text_terms(text: str) -> list[str]:
    if not text:
        return []
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ";" in line:
            parts.extend([p.strip() for p in line.split(";") if p.strip()])
        else:
            parts.append(line)
    return parts

def quote_phrase(term: str) -> str:
    term = term.strip().strip('"')
    return f'"{term}"'

def build_site_query(site_filters: list[str]) -> str:
    cleaned = []
    for item in site_filters or []:
        s = item.strip()
        if not s:
            continue
        if s.startswith("site:"):
            s = s[5:].strip()
        s = s.replace("https://", "").replace("http://", "").strip("/")
        if s:
            cleaned.append(s)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"site:{cleaned[0]}"
    return " OR ".join(f"site:{s}" for s in cleaned)

def build_query(query_mode: str, query_terms: list[str], raw_query: str, site_filters: list[str]) -> str:
    mode = query_mode.lower().strip()
    terms = [t.strip() for t in query_terms if t and t.strip()]
    if mode == "raw":
        q = raw_query.strip()
    elif mode == "single":
        q = terms[0] if terms else ""
    elif mode == "any":
        q = " OR ".join(terms)
    elif mode == "all":
        q = " ".join(terms)
    elif mode == "phrase":
        q = quote_phrase(terms[0]) if terms else ""
    elif mode == "phrase_any":
        q = " OR ".join(quote_phrase(t) for t in terms)
    else:
        q = " ".join(terms)
    site_expr = build_site_query(site_filters)
    if site_expr and "site:" not in q:
        q = f"({q}) ({site_expr})" if (q and " OR " in site_expr) else f"{q} {site_expr}".strip()
    return q

def google_date(d: date) -> str:
    return f"{d.month}/{d.day}/{d.year}"


def is_baidu_vertical(vertical: str) -> bool:
    return (vertical or "").lower().startswith("baidu_")

def baidu_vertical_kind(vertical: str) -> str:
    v = (vertical or "").lower().strip()
    if v == "baidu_news" or v == "baidu_news_media":
        return "news"
    if v == "baidu_web":
        return "web"
    return v or "web"

def baidu_source_filter(vertical: str) -> str:
    return "media" if (vertical or "").lower().strip() == "baidu_news_media" else "all"

def baidu_sort_value(cfg: CollectorConfig) -> str:
    s = (getattr(cfg, "baidu_sort", "") or "focus").lower().strip()
    return "time" if s in {"time", "date", "rtt4", "4"} else "focus"

def baidu_ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=BAIDU_BEIJING_TZ).timestamp())

def baidu_gpc(shard_start: date, shard_end: date) -> tuple[str, int, int]:
    start_ts = baidu_ts(shard_start)
    end_ts = baidu_ts(shard_end + timedelta(days=1))
    return f"stf={start_ts},{end_ts}|stftype=2", start_ts, end_ts

def display_search_engine(vertical: str) -> str:
    return "baidu" if is_baidu_vertical(vertical) else "google"

def display_vertical(vertical: str) -> str:
    return baidu_vertical_kind(vertical) if is_baidu_vertical(vertical) else ((vertical or "news").lower())

def _legacy_lr_value(language_lr: str) -> str:
    """Convert documented lr values into the older tbs lr form used by the original script.

    Original script example: tbs=lr:lang_1en,ctr:countryUS,cdr:1,...
    GUI stores documented values such as lang_en or lang_en|lang_fr.
    """
    if not language_lr:
        return ""
    parts = []
    for item in language_lr.split("|"):
        item = item.strip()
        if not item:
            continue
        if item.startswith("lang_1"):
            parts.append(item)
        elif item.startswith("lang_"):
            parts.append("lang_1" + item[5:])
        else:
            parts.append(item)
    return "|".join(parts)


def build_search_url(cfg: CollectorConfig, shard_start: date, shard_end: date) -> str:
    """Build the *initial* engine URL without page-size or page-limit directives.

    WebLens deliberately does not send ``num``/``rn`` or its own pagination
    offsets. The first result page therefore uses the search engine's current
    default page size. Further pages are discovered from the engine-provided
    Next link in the rendered page rather than calculated by WebLens.

    """
    q = build_query(cfg.query_mode, cfg.query_terms, cfg.raw_query, cfg.site_filters)
    vertical = (cfg.search_vertical or "news").lower().strip()

    if is_baidu_vertical(vertical):
        params = {
            "ie": "utf-8",
            "wd": q,
        }
        if baidu_vertical_kind(vertical) == "news":
            params["tn"] = "news"
            params["cl"] = "2"
            if baidu_source_filter(vertical) == "media":
                params["medium"] = "1"
            params["rtt"] = "4" if baidu_sort_value(cfg) == "time" else "1"
        else:
            params["tn"] = "baidu"
        if cfg.date_filter_enabled:
            gpc_value, _start_ts, _end_ts = baidu_gpc(shard_start, shard_end)
            params["gpc"] = gpc_value
            params["tfflag"] = "1"
        return "https://www.baidu.com/s?" + urlencode(params)

    google_vertical = "news" if vertical in {"news", "google_news"} else "web"
    params = {"q": q}
    if cfg.date_filter_enabled:
        params["tbs"] = f"cdr:1,cd_min:{google_date(shard_start)},cd_max:{google_date(shard_end)}"
    if google_vertical == "news":
        params["tbm"] = "nws"
    if cfg.language_lr:
        params["lr"] = cfg.language_lr
        if "lang_zh-CN" in cfg.language_lr and "lang_zh-TW" in cfg.language_lr:
            params["c2coff"] = "0"
    if cfg.country_cr:
        params["cr"] = cfg.country_cr
    if cfg.safe:
        params["safe"] = cfg.safe
    if cfg.disable_filter:
        params["filter"] = "0"
    return "https://www.google.com/search?" + urlencode(params)

def expand_search_tasks(cfg: CollectorConfig) -> list[CollectorConfig]:
    """Expand one user configuration into concrete search tasks.

    Baidu's multiple-term mode intentionally searches each term separately
    because Baidu no longer supports the earlier OR syntax reliably. Google
    keeps its existing query semantics. The helper is shared by automatic and
    manual collection so both modes generate exactly the same initial queries.
    """
    baidu_sequential = (
        is_baidu_vertical(getattr(cfg, "search_vertical", ""))
        and (getattr(cfg, "query_mode", "") or "").lower().strip() == "any"
    )
    terms = [term.strip() for term in (getattr(cfg, "query_terms", None) or []) if term and term.strip()]
    if baidu_sequential:
        return [replace(cfg, query_mode="single", query_terms=[term], raw_query="") for term in terms]
    return [cfg]


def split_date_range(start: date, end: date, day_step: int) -> list[tuple[date, date]]:
    """Split an inclusive date range into search slices.

    day_step=0 is a deliberate no-slicing mode: the whole date range is
    searched as one slice.  day_step>=1 keeps the earlier fixed-width slicing
    behaviour.  This lets Baidu use broad date ranges by default while Google
    can still default to weekly slices.
    """
    day_step = int(day_step or 0)
    if day_step <= 0:
        return [(start, end)]
    chunks = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=day_step - 1), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks

def normalize_url_for_dedup(url: str) -> str:
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        clean_qs = {k: v for k, v in qs.items() if k not in TRACKING_PARAMS and not k.startswith("utm_")}
        query = urlencode({k: v[0] if v else "" for k, v in sorted(clean_qs.items())})
        path = parsed.path.rstrip("/") or parsed.path
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", query, ""))
    except Exception:
        return url.strip()

def is_google_news_redirect_url(url: str) -> bool:
    """Return True for Google News opaque result redirects such as /goto?url=CAES....

    Current Google News result pages may expose the real story through a Google
    ``/goto`` redirect whose ``url`` value is an opaque token rather than the
    destination URL.  These are *result links*, not Google interface/navigation
    links, so they must survive collection.  Destination-page downloading will
    follow the redirect and can then replace the stored link with the final URL.
    """
    if not url:
        return False
    try:
        parsed = urlparse(html_lib.unescape(url.strip()))
    except Exception:
        return False
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()
    if not (host == "google.com" or host.endswith(".google.com") or re.search(r"(^|\.)google\.[a-z.]+$", host)):
        return False
    if path != "/goto":
        return False
    token = parse_qs(parsed.query).get("url", [""])[0]
    return bool(token)


def unwrap_google_url(href: str) -> str:
    if not href:
        return ""
    href = html_lib.unescape(href.strip())
    if href.startswith("/url?") or href.startswith("/interstitial?"):
        qs = parse_qs(urlparse(href).query)
        return qs.get("q", qs.get("url", [""]))[0]
    if href.startswith("/goto?"):
        # Google News now frequently returns opaque /goto result links.  If the
        # query value is already a real URL, unwrap it; otherwise preserve the
        # redirect as a usable result link instead of discarding the card.
        qs = parse_qs(urlparse(href).query)
        target = qs.get("url", [""])[0]
        if target.startswith(("http://", "https://")):
            return target
        return "https://www.google.com" + href if target else ""
    if href.startswith("/search?") or href.startswith("#"):
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("http"):
        # Some Google redirect URLs are absolute.
        parsed = urlparse(href)
        if re.search(r"(^|\.)google\.[a-z.]+$", parsed.netloc.lower()) or parsed.netloc.lower().endswith(".google.com") or parsed.netloc.lower() == "google.com":
            if parsed.path.startswith("/url"):
                qs = parse_qs(parsed.query)
                return qs.get("q", qs.get("url", [""]))[0]
            if parsed.path == "/goto":
                qs = parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if target.startswith(("http://", "https://")):
                    return target
                return href if target else ""
        return href
    return ""


def unwrap_baidu_url(href: str) -> str:
    """Normalize Baidu result hrefs without trying to bypass redirects."""
    if not href:
        return ""
    href = html_lib.unescape(href.strip())
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://www.baidu.com" + href
    if href.startswith(("http://", "https://")):
        return href
    return ""

def is_baidu_redirect_url(url: str) -> bool:
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        path = (p.path or "").lower()
        return host.endswith("baidu.com") and path.startswith("/link")
    except Exception:
        return False

def is_baidu_search_or_nav_url(url: str) -> bool:
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        path = (p.path or "").lower()
    except Exception:
        return False
    if not host.endswith("baidu.com"):
        return False
    if path.startswith("/link"):
        return False
    if host == "baijiahao.baidu.com":
        return False
    return True

def host_matches_site_filter(url: str, site_filters: list[str]) -> bool:
    if not site_filters:
        return True
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if not host:
        return False
    for item in site_filters:
        site = item.strip().lower()
        if not site:
            continue
        if site.startswith("site:"):
            site = site[5:].strip()
        site = site.replace("https://", "").replace("http://", "").strip("/")
        if site.startswith("."):
            if host.endswith(site):
                return True
        else:
            if host == site or host.endswith("." + site) or host.endswith(site):
                return True
    return False

def is_google_host(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if not host:
        return False
    if host in GOOGLE_RESULT_HOST_BLACKLIST:
        return True
    # Exclude Google's own search/navigation/assets.  In Google result pages,
    # links such as Home, Maps, Images, News, Products, Preferences, and Account
    # links may appear on every page and must not be counted as valid corpus
    # discovery results.  Use a broad Google-domain filter here because the
    # crawler's purpose is to collect the destination pages, not Google UI links.
    if host == "google.com" or host.endswith(".google.com"):
        return True
    if re.search(r"(^|\.)google\.[a-z.]+$", host):
        return True
    return host.endswith(".gstatic.com") or host.endswith(".googleusercontent.com")

def is_valid_result_url(url: str, site_filters: list[str] | None = None) -> bool:
    """Return True only for external result URLs worth counting as crawl results.

    This prevents stable Google/navigation links such as Home, Maps, Images,
    preferences, support, policies, javascript anchors, mailto links, etc. from
    keeping pagination alive after real result pages have ended.
    """
    if not url:
        return False
    url = unwrap_google_url(url) or unwrap_baidu_url(url)
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
    except Exception:
        return False
    if not host:
        return False
    # Google News opaque /goto links are principal result links.  Keep them
    # even though their host belongs to Google; all other Google-owned links are
    # still treated as search-engine UI/navigation and excluded.
    if is_google_news_redirect_url(url):
        return True
    if is_google_host(url):
        return False
    if is_baidu_search_or_nav_url(url):
        return False
    if path in {"/", ""} and any(x in host for x in ("google", "gstatic", "baidu")):
        return False
    bad_schemes = ("javascript:", "mailto:", "tel:")
    if url.lower().startswith(bad_schemes):
        return False
    if site_filters and not host_matches_site_filter(url, site_filters):
        if not is_baidu_redirect_url(url):
            return False
    return True

def _has_result_card_markers(html: str) -> bool:
    """Return True when the page contains recognizable Google result-card markers.

    Important: Google result pages may contain strings such as ``sorry`` inside
    scripts, images, or unrelated URLs.  Those should not be treated as a block
    page when real result cards are already present.
    """
    if not html:
        return False
    decoded = _decode_google_escapes(html)
    markers = (
        'class="WlydOe"',
        "class='WlydOe'",
        'WlydOe',
        'jsname="YKoRaf"',
        "jsname='YKoRaf'",
        'data-news-cluster-id',
        'id="rso"',
        'class="MjjYud"',
    )
    return any(m in html for m in markers) or any(m in decoded for m in markers)


def sleep_random_ms(min_ms: int, max_ms: int, stop_checker: Optional[Callable[[], bool]] = None) -> None:
    min_ms = max(0, int(min_ms))
    max_ms = max(min_ms, int(max_ms))
    total = random.randint(min_ms, max_ms)
    slept = 0
    while slept < total:
        if stop_checker and stop_checker():
            raise StopCrawl()
        step = min(250, total - slept)
        time.sleep(step / 1000.0)
        slept += step



def _decode_google_escapes(text: str) -> str:
    """Decode common Google inline-HTML escaping without corrupting Unicode text."""
    if not text:
        return ""
    out = html_lib.unescape(text)
    replacements = {
        r"\x3c": "<", r"\x3C": "<", r"\u003c": "<", r"\u003C": "<",
        r"\x3e": ">", r"\x3E": ">", r"\u003e": ">", r"\u003E": ">",
        r"\x22": '"', r"\u0022": '"',
        r"\x27": "'", r"\u0027": "'",
        r"\x3d": "=", r"\x3D": "=", r"\u003d": "=", r"\u003D": "=",
        r"\x26": "&", r"\u0026": "&",
        r"\x2f": "/", r"\x2F": "/", r"\u002f": "/", r"\u002F": "/",
        r"\/": "/",
    }
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _html_variants(html: str) -> list[str]:
    """Return parse variants for literal, entity-escaped, and JS-escaped HTML."""
    variants = []
    for item in [html, html_lib.unescape(html), _decode_google_escapes(html)]:
        if item and item not in variants:
            variants.append(item)
    return variants


def _strip_tags(fragment: str) -> str:
    if not fragment:
        return ""
    soup = BeautifulSoup(fragment, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


def _regex_first(fragment: str, patterns: list[str], max_len: int = 500) -> str:
    for pat in patterns:
        m = re.search(pat, fragment, flags=re.I | re.S)
        if m:
            raw = m.group(1)
            text = _strip_tags(raw)
            if text:
                return text[:max_len]
    return ""


def _extract_news_cards_by_regex(html: str) -> list[tuple[str, str, str, str, str]]:
    """Regex fallback for Google News cards.

    This covers both legacy and current Google News anchors, including:
    <a jsname="YKoRaf" class="aJWbwf" href="https://www.google.../goto?url=CAES...">
      ... .n0jPhd ... .UqSP2b ... .OSrXXb ...
    </a>

    It also works when the HTML is entity-escaped or stored in JavaScript with
    \x3c / \u003c style escapes.
    """
    records = []
    seen = set()
    anchor_patterns = [
        # Current Google News (2026-09) uses a[jsname="YKoRaf"].aJWbwf with
        # an opaque google.* /goto?url=CAES... href.  Keep YKoRaf independent of
        # the legacy WlydOe class so the parser matches both variants.
        r'<a\b(?=[^>]*\bjsname=["\']YKoRaf["\'])(?P<attrs>[^>]*)>(?P<body>.*?)</a>',
        r'<a\b(?=[^>]*\bclass=["\'][^"\']*\bWlydOe\b[^"\']*["\'])(?P<attrs>[^>]*)>(?P<body>.*?)</a>',
    ]
    for text in _html_variants(html):
        for pat in anchor_patterns:
            for m in re.finditer(pat, text, flags=re.I | re.S):
                attrs = m.group("attrs") or ""
                body = m.group("body") or ""
                href_m = re.search(r'\bhref=["\']([^"\']+)["\']', attrs, flags=re.I | re.S)
                ping_m = re.search(r'\bping=["\']([^"\']+)["\']', attrs, flags=re.I | re.S)
                href = html_lib.unescape(href_m.group(1)) if href_m else ""
                if (not href or href.startswith("#")) and ping_m:
                    href = html_lib.unescape(ping_m.group(1))
                target = unwrap_google_url(href)
                if not target and ping_m:
                    target = unwrap_google_url(html_lib.unescape(ping_m.group(1)))
                if not is_valid_result_url(target):
                    continue
                key = normalize_url_for_dedup(target)
                if key in seen:
                    continue
                seen.add(key)
                title = _regex_first(body, [
                    r'<div\b[^>]*class=["\'][^"\']*\bn0jPhd\b[^"\']*["\'][^>]*>(.*?)</div>',
                    r'<div\b[^>]*role=["\']heading["\'][^>]*>(.*?)</div>',
                    r'<h3\b[^>]*>(.*?)</h3>',
                ], 500)
                source = _regex_first(body, [
                    r'<div\b[^>]*class=["\'][^"\']*\bMgUUmf\b[^"\']*["\'][^>]*>.*?<span\b[^>]*>(.*?)</span>',
                    r'<span\b[^>]*class=["\'][^"\']*\bNUnG9d\b[^"\']*["\'][^>]*>(.*?)</span>',
                ], 120)
                snippet = _regex_first(body, [
                    r'<div\b[^>]*class=["\'][^"\']*\bUqSP2b\b[^"\']*["\'][^>]*>(.*?)</div>',
                    r'<div\b[^>]*class=["\'][^"\']*\bGI74Re\b[^"\']*["\'][^>]*>(.*?)</div>',
                    r'<div\b[^>]*class=["\'][^"\']*\bVwiC3b\b[^"\']*["\'][^>]*>(.*?)</div>',
                ], 800)
                published = _regex_first(body, [
                    r'<div\b[^>]*class=["\'][^"\']*\bOSrXXb\b[^"\']*["\'][^>]*>(.*?)</div>',
                    r'<span\b[^>]*data-ts=["\'][^"\']+["\'][^>]*>(.*?)</span>',
                ], 100)
                if not title:
                    title = _strip_tags(body)[:500]
                records.append((title, target, source, published, snippet))
    return records


def classify_no_result_page(html: str) -> str:
    decoded_raw = _decode_google_escapes(html)
    if "WlydOe" in html or "YKoRaf" in html or "WlydOe" in decoded_raw or "YKoRaf" in decoded_raw:
        return "Result-card markers are present, but no usable records survived parsing/filtering. Check site/domain filters and the saved debug HTML."
    lower = html.lower()
    decoded = decoded_raw.lower()
    checks = [lower, decoded]
    if any("unusual traffic" in t or "detected unusual traffic" in t or "g-recaptcha" in t or "captcha-form" in t for t in checks):
        return "Google returned an unusual-traffic / verification page. Reduce frequency, change network, or retry later."
    if any("consent.google" in t or "before you continue" in t or "同意" in t and "google" in t for t in checks):
        return "Google returned a consent page rather than a result page. The program now sends consent cookies, but this may still vary by region/IP."
    if any("/httpservice/retry/enablejs" in t or "enablejs" in t or "如果系統沒有在數秒鐘後將您重新導向" in t for t in checks):
        return "Google returned a JavaScript/redirect shell. The visible browser page can show results, but the raw HTTP response contains no result cards."
    if any("did not match any documents" in t or "找不到和您查詢" in t or "沒有任何結果" in t for t in checks):
        return "Google says there are no matching documents for the current slice and restrictions."
    return "The downloaded HTML does not contain recognizable result-card anchors. This may be an A/B layout, a consent/login shell, or an IP-specific Google response."


def save_debug_html_if_needed(cfg: CollectorConfig, html: str, shard_start: date, shard_end: date, page_number: int) -> str:
    if not getattr(cfg, "save_debug_html", True):
        return ""
    try:
        from pathlib import Path
        debug_dir = Path(getattr(cfg, "debug_dir", "weblens_debug_html") or "weblens_debug_html")
        debug_dir.mkdir(parents=True, exist_ok=True)
        path = debug_dir / f"google_debug_{shard_start.isoformat()}_{shard_end.isoformat()}_p{page_number}.html"
        path.write_text(html, encoding="utf-8", errors="replace")
        return str(path)
    except Exception:
        return ""

def _first_text(container, selectors: list[str], max_len: int = 300) -> str:
    if not container:
        return ""
    for selector in selectors:
        for node in container.select(selector):
            text = " ".join(node.get_text(" ", strip=True).split())
            if text and len(text) <= max_len:
                return text
    return ""

def extract_source_time_snippet(container) -> tuple[str, str, str]:
    text = " ".join(container.get_text(" ", strip=True).split()) if container else ""
    source = _first_text(container, [
        ".MgUUmf.NUnG9d span", ".MgUUmf.NUnG9d", "span.NUnG9d", "div.CEMjEf span",
        "span.wEwyrc", "div.MgUUmf span", "span.OSrXXb", "cite",
    ], 90)
    published = _first_text(container, [".OSrXXb", ".rbYSKb", "span.f", "span.LEwnzc"], 80)
    snippet = _first_text(container, [".UqSP2b", ".GI74Re", ".VwiC3b", ".IsZvec", "div.Y3v8qd"], 800)
    if not snippet:
        snippet = text[:800] if text else ""
    if not published:
        time_patterns = [
            r"\b\d+\s+(?:minutes?|hours?|days?|weeks?|months?|years?)\s+ago\b",
            r"\b\d+\s+(?:分鐘前|小時前|天前|週前|月前|年前|分钟前|小时前|周前)\b",
            r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
            r"\b\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}\b",
        ]
        for pat in time_patterns:
            m = re.search(pat, text, flags=re.I)
            if m:
                published = m.group(0)
                break
    return source, published, snippet

def nearest_result_container(a_tag):
    # News-tab results are often anchored by a.WlydOe and contain .SoAPf.
    if not a_tag:
        return None
    for selector in ["div.SoaBEf", "div.SoaBEf", "div.lSfe4c", "div.MjjYud", "div.g", "article"]:
        try:
            node = a_tag.find_parent(selector)
            if node:
                return node
        except Exception:
            pass
    node = a_tag
    best = None
    for _ in range(10):
        if not node or not getattr(node, "parent", None):
            break
        node = node.parent
        if getattr(node, "name", None) in {"div", "article"}:
            text = node.get_text(" ", strip=True)
            if len(text) > 30:
                best = node
                # Avoid climbing all the way to the whole page.
                if len(text) > 80:
                    return node
    return best or getattr(a_tag, "parent", None) or a_tag

def _extract_title(a_tag, container) -> str:
    title = _first_text(container, [".n0jPhd", "div[role='heading']", "h3", ".MBeuO"], 500)
    if title:
        return title
    if a_tag:
        title = " ".join(a_tag.get_text(" ", strip=True).split())
        # For news anchors, full anchor text may include source + title + snippet;
        # keep it only as fallback.
        if title:
            return title[:500]
    return ""

def _candidate_anchors(soup: BeautifulSoup):
    # Ordered from most specific to broadest. This list covers the user-provided
    # Google News HTML variant where a.WlydOe contains direct source links.
    selectors = [
        "a.WlydOe",             # Google News title card link
        "a[jsname='YKoRaf']",    # Google News title link variant
        "a[jsname='UWckNb']",    # Google web-result title link variant
        "#rso a:has(h3)",        # normal organic web result
        "#rso a[href]",          # resilient fallback for current Google A/B layouts
        "div.MjjYud a[href]",    # grouped organic result container
        "div.g a[href]",
        "a:has(h3)",
        "a[href^='/url?']",
    ]
    seen_ids = set()
    for selector in selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            nodes = []
        for a in nodes:
            ident = id(a)
            if ident in seen_ids:
                continue
            seen_ids.add(ident)
            yield a

    # Keep the HTML parser aligned with the broader live-DOM readiness check
    # used after human verification. Some Google A/B layouts place the result
    # heading inside an anchor, while others place the anchor immediately above
    # or below the h3 node.
    try:
        heading_nodes = soup.select("#search h3, #rso h3, div.MjjYud h3")
    except Exception:
        heading_nodes = []
    for h3 in heading_nodes:
        a = h3.find_parent("a", href=True) or h3.find("a", href=True)
        if not a:
            parent = getattr(h3, "parent", None)
            if parent is not None:
                a = parent.find("a", href=True)
        if not a:
            continue
        ident = id(a)
        if ident in seen_ids:
            continue
        seen_ids.add(ident)
        yield a

def diagnose_result_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    decoded = _decode_google_escapes(html)
    decoded_soup = BeautifulSoup(decoded, "html.parser") if decoded != html else soup
    usable_candidates = count_external_result_candidates(html, "news")
    return {
        "a_WlydOe": len(soup.select("a.WlydOe")),
        "a_YKoRaf": len(soup.select("a[jsname='YKoRaf']")),
        "a_UWckNb": len(soup.select("a[jsname='UWckNb']")),
        "h3": len(soup.select("h3")),
        "url_redirects": len(soup.select("a[href^='/url?']")),
        "http_anchors": len(soup.select("a[href^='http']")),
        "decoded_a_WlydOe": len(decoded_soup.select("a.WlydOe")),
        "decoded_a_YKoRaf": len(decoded_soup.select("a[jsname='YKoRaf']")),
        "raw_YKoRaf": len(re.findall(r"YKoRaf", html)),
        "raw_WlydOe": len(re.findall(r"WlydOe", html)),
        "regex_news_cards": len(_extract_news_cards_by_regex(html)),
        "html_length": len(html),
        "usable_result_candidates": usable_candidates,
        "reason": (f"Detected {usable_candidates} usable result link(s)." if usable_candidates else classify_no_result_page(html)),
    }

def _extract_links_like_original(html: str, prefer_news: bool = True, site_filters: list[str] | None = None) -> list[tuple[str, str, str, str, str]]:
    """Very conservative fallback copied from the user's original working crawler.

    It extracts URLs from a.WlydOe, /url?q=..., and h3 anchors.  When the
    richer card parser fails but the older URL-only method finds links, WebLens
    still records a usable item instead of returning an empty page.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[tuple[str, str, str, str, str]] = []

    if prefer_news:
        for a in soup.select("a.WlydOe"):
            href = a.get("href")
            if href:
                title = _extract_title(a, nearest_result_container(a)) or a.get_text(" ", strip=True) or href
                source, published, snippet = extract_source_time_snippet(nearest_result_container(a))
                candidates.append((title, href, source, published, snippet))

    for a in soup.select('a[href^="/url?"]'):
        href = a.get("href")
        if not href:
            continue
        target = parse_qs(urlparse(href).query).get("q", [""])[0]
        if target:
            title = a.get_text(" ", strip=True) or target
            candidates.append((title, target, "", "", ""))

    for h3 in soup.select("h3"):
        a = h3.find("a", href=True)
        if a:
            href = a.get("href")
            title = h3.get_text(" ", strip=True) or href
            candidates.append((title, href, "", "", ""))

    seen = set()
    out = []
    for title, u, source, published, snippet in candidates:
        u = unwrap_google_url(u)
        if not is_valid_result_url(u, site_filters):
            continue
        key = normalize_url_for_dedup(u)
        if key in seen:
            continue
        seen.add(key)
        out.append((title or u, u, source, published, snippet))
    return out


def _baidu_container_for(node):
    current = node
    for _ in range(8):
        if current is None:
            break
        classes = " ".join(current.get("class", []) or []) if hasattr(current, "get") else ""
        if current.name == "div" and ("result" in classes or "c-container" in classes or current.get("data-click") or current.get("data-tools")):
            return current
        current = current.parent
    return node.parent if getattr(node, "parent", None) else node

def _baidu_text(container) -> str:
    try:
        return " ".join(container.get_text(" ", strip=True).split())
    except Exception:
        return ""

def _baidu_data_tools(container) -> dict:
    import json as _json
    current = container
    for _ in range(4):
        if current is None:
            break
        raw = current.get("data-tools") if hasattr(current, "get") else ""
        if raw:
            try:
                data = _json.loads(html_lib.unescape(raw))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        current = current.parent
    return {}

def _baidu_source_time_snippet(container, title: str = "") -> tuple[str, str, str]:
    text = _baidu_text(container)
    title = (title or "").strip()
    compact = text.replace(title, " ", 1).strip() if title and text.startswith(title) else text
    time_patterns = [
        r"(\d{4}年\d{1,2}月\d{1,2}日\s*\d{0,2}:?\d{0,2})",
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*\d{0,2}:?\d{0,2})",
        r"(\d{1,2}月\d{1,2}日\s*\d{0,2}:?\d{0,2})",
        r"(\d+\s*(?:分钟|小時|小时|天)前)",
        r"(昨天\s*\d{0,2}:?\d{0,2}|前天\s*\d{0,2}:?\d{0,2})",
    ]
    published = ""
    for pat in time_patterns:
        m = re.search(pat, compact)
        if m:
            published = " ".join(m.group(1).split())
            break
    source = ""
    for sel in [".c-color-gray", ".c-color-gray2", ".c-author", ".c-source", ".source", ".c-gap-right"]:
        try:
            for n in container.select(sel):
                s = n.get_text(" ", strip=True)
                if s and not re.search(r"百度|快照|广告", s):
                    s = re.sub(r"\s+", " ", s)
                    if published and published in s:
                        s = s.replace(published, " ").strip(" -_·|，, ")
                    if s and len(s) <= 40:
                        source = s
                        break
            if source:
                break
        except Exception:
            pass
    if not source and published and published in compact:
        before = compact.split(published, 1)[0]
        tokens = [x.strip(" -_·|，, ") for x in re.split(r"\s+", before) if x.strip()]
        if tokens:
            source = tokens[-1][-40:]
    snippet = compact
    if published:
        snippet = snippet.replace(published, " ")
    if source:
        snippet = snippet.replace(source, " ", 1)
    snippet = re.sub(r"\s+", " ", snippet).strip(" -_·|，, ")
    if len(snippet) > 500:
        snippet = snippet[:500]
    return source, published, snippet

def _actual_domain(url: str) -> str:
    try:
        if is_google_news_redirect_url(url):
            return ""
        host = urlparse(url).netloc.lower().lstrip("www.")
        if host.endswith("baidu.com") and is_baidu_redirect_url(url):
            return ""
        return host
    except Exception:
        return ""

def _baidu_result_anchors(soup: BeautifulSoup):
    """Yield principal anchors from Baidu result cards, excluding page chrome/footer links."""
    seen_nodes: set[int] = set()
    selectors = (
        "h3 a[href]",
        "a.c-title[href]",
        "div.result a[href]",
        "div.c-container a[href]",
        "div[data-tools] a[href]",
    )
    for selector in selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            nodes = []
        for a in nodes:
            ident = id(a)
            if ident in seen_nodes:
                continue
            seen_nodes.add(ident)
            # Generic links inside a result card can include source/profile links.
            # Prefer the title anchor; otherwise keep only the first usable anchor
            # from that card by letting record-level URL deduplication collapse it.
            yield a


def extract_baidu_records_from_html(html: str, cfg: CollectorConfig, search_url: str, shard_start: date, shard_end: date, page_number: int) -> list[SearchRecord]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in _baidu_result_anchors(soup):
        href = unwrap_baidu_url(a.get("href"))
        if not href or not is_valid_result_url(href, cfg.site_filters):
            continue
        container = _baidu_container_for(a)
        tools = _baidu_data_tools(container)
        title = " ".join(a.get_text(" ", strip=True).split())
        if not title:
            h3 = a.find_parent("h3")
            title = " ".join(h3.get_text(" ", strip=True).split()) if h3 else ""
        if tools.get("title") and (not title or len(str(tools.get("title"))) > len(title)):
            title = str(tools.get("title"))
        tool_url = str(tools.get("url") or tools.get("mu") or "").strip()
        if tool_url and tool_url.startswith(("http://", "https://")):
            href = tool_url
        if not is_valid_result_url(href, cfg.site_filters):
            continue
        source, published, snippet = _baidu_source_time_snippet(container, title)
        if tools.get("source") and not source:
            source = str(tools.get("source"))
        if tools.get("time") and not published:
            published = str(tools.get("time"))
        candidates.append((title or href, href, source, published, snippet, _actual_domain(href)))

    records = []
    seen = set()
    collected_at = datetime.now().isoformat(timespec="seconds")
    query = build_query(cfg.query_mode, cfg.query_terms, cfg.raw_query, cfg.site_filters)
    if cfg.date_filter_enabled:
        gpc_value, start_ts, end_ts = baidu_gpc(shard_start, shard_end)
    else:
        gpc_value, start_ts, end_ts = "", 0, 0
    source_filter = baidu_source_filter(cfg.search_vertical)
    sort_mode = baidu_sort_value(cfg) if baidu_vertical_kind(cfg.search_vertical) == "news" else "default"
    site_limit = "; ".join([s.strip() for s in cfg.site_filters or [] if s.strip()])
    rank = 0
    for title, link, source, published, snippet, actual_domain in candidates:
        key = normalize_url_for_dedup(link)
        if key in seen:
            continue
        seen.add(key)
        rank += 1
        records.append(SearchRecord(
            collected_at=collected_at,
            query=query,
            search_vertical=baidu_vertical_kind(cfg.search_vertical),
            shard_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            shard_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
            page=page_number,
            rank=rank,
            title=title,
            link=link,
            source=source,
            published_time=published,
            snippet=snippet,
            search_url=search_url,
            language_lr="",
            country_cr="",
            search_engine="baidu",
            source_filter=source_filter,
            sort_mode=sort_mode,
            site_limit=site_limit,
            actual_domain=actual_domain,
            query_raw=query,
            date_filter_type="custom_range" if cfg.date_filter_enabled else "none",
            date_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            date_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
            start_ts=str(start_ts) if cfg.date_filter_enabled else "",
            end_ts=str(end_ts) if cfg.date_filter_enabled else "",
            baidu_gpc=gpc_value if cfg.date_filter_enabled else "",
        ))
    return records

def extract_records_from_html(html: str, cfg: CollectorConfig, search_url: str, shard_start: date, shard_end: date, page_number: int) -> list[SearchRecord]:
    if is_baidu_vertical(getattr(cfg, "search_vertical", "")):
        return extract_baidu_records_from_html(html, cfg, search_url, shard_start, shard_end, page_number)
    candidates = []
    for html_variant in _html_variants(html):
        soup = BeautifulSoup(html_variant, "html.parser")
        for a in _candidate_anchors(soup):
            href = a.get("href")
            # Google News cards often contain both href and ping. Try both.
            target = unwrap_google_url(href)
            if (not target or not target.startswith("http")) and a.get("ping"):
                target = unwrap_google_url(a.get("ping"))
            if not is_valid_result_url(target, cfg.site_filters):
                continue
            container = nearest_result_container(a)
            title = _extract_title(a, container) or target
            source, published, snippet = extract_source_time_snippet(container)
            candidates.append((title, target, source, published, snippet))
    # Regex fallback for Google News card HTML and JS/entity-escaped variants.
    candidates.extend(_extract_news_cards_by_regex(html))
    if not candidates:
        candidates.extend(_extract_links_like_original(html, prefer_news=(cfg.search_vertical == "news"), site_filters=cfg.site_filters))

    records = []
    seen = set()
    collected_at = datetime.now().isoformat(timespec="seconds")
    query = build_query(cfg.query_mode, cfg.query_terms, cfg.raw_query, cfg.site_filters)
    rank = 0
    for title, link, source, published, snippet in candidates:
        if not is_valid_result_url(link, cfg.site_filters):
            continue
        key = normalize_url_for_dedup(link)
        if key in seen:
            continue
        seen.add(key)
        rank += 1
        records.append(SearchRecord(
            collected_at=collected_at,
            query=query,
            search_vertical=cfg.search_vertical,
            shard_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            shard_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
            page=page_number,
            rank=rank,
            title=title,
            link=link,
            source=source,
            published_time=published,
            snippet=snippet,
            search_url=search_url,
            language_lr=cfg.language_lr,
            country_cr=cfg.country_cr,
            search_engine="google",
            source_filter="",
            sort_mode="",
            site_limit="; ".join([s.strip() for s in cfg.site_filters or [] if s.strip()]),
            actual_domain=_actual_domain(link),
            query_raw=query,
            date_filter_type="custom_range" if cfg.date_filter_enabled else "none",
            date_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            date_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
        ))
    return records



def extract_google_records_from_live_dom(driver, cfg: CollectorConfig, search_url: str, shard_start: date, shard_end: date, page_number: int) -> list[SearchRecord]:
    """Fallback record extraction directly from the currently rendered Google DOM.

    This performs no navigation. It is used when Selenium can visibly see real
    result cards but a serialized-HTML parser returns zero records, for example
    after a human-verification flow or a Google A/B DOM update.
    """
    if is_baidu_vertical(getattr(cfg, "search_vertical", "")):
        return []
    script = r'''
const visible = (el) => {
  if (!el) return false;
  const st = window.getComputedStyle(el);
  if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};
const text = (root, selectors) => {
  for (const sel of selectors) {
    const el = root.querySelector(sel);
    if (el) {
      const t = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
      if (t) return t;
    }
  }
  return '';
};
let anchors = Array.from(document.querySelectorAll(
  'a[jsname="YKoRaf"][href], a.WlydOe[href], a[jsname="UWckNb"][href], #rso a[href]'
));
const seen = new Set();
const out = [];
for (const a of anchors) {
  if (!visible(a)) continue;
  const href = String(a.href || '');
  if (!href || seen.has(href)) continue;
  const title = text(a, ['.n0jPhd', '[role="heading"]', 'h3', '.MBeuO']);
  if (!title && !a.querySelector('h3,[role="heading"],.n0jPhd,.MBeuO')) continue;
  seen.add(href);
  let root = a;
  for (let i = 0; i < 7 && root && root.parentElement; i++) {
    if (root.matches && (root.matches('[data-news-doc-id]') || root.matches('.MjjYud,.g,article,.SoaBEf'))) break;
    root = root.parentElement;
  }
  root = root || a;
  out.push({
    href,
    title: title || (a.innerText || '').trim().replace(/\s+/g, ' '),
    source: text(root, ['.MgUUmf.NUnG9d span', '.MgUUmf.NUnG9d', '.MgUUmf span', 'span.NUnG9d', 'cite']),
    published: text(root, ['.OSrXXb', '.rbYSKb', 'span[data-ts]', 'span.f', 'span.LEwnzc']),
    snippet: text(root, ['.UqSP2b', '.GI74Re', '.VwiC3b', '.IsZvec', 'div.Y3v8qd'])
  });
}
return out;
'''
    try:
        rows = driver.execute_script(script) or []
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    records: list[SearchRecord] = []
    seen: set[str] = set()
    collected_at = datetime.now().isoformat(timespec="seconds")
    query = build_query(cfg.query_mode, cfg.query_terms, cfg.raw_query, cfg.site_filters)
    for row in rows:
        if not isinstance(row, dict):
            continue
        link = unwrap_google_url(str(row.get("href") or ""))
        if not is_valid_result_url(link, cfg.site_filters):
            continue
        key = normalize_url_for_dedup(link)
        if not key or key in seen:
            continue
        seen.add(key)
        title = " ".join(str(row.get("title") or "").split()) or link
        source = " ".join(str(row.get("source") or "").split())[:120]
        published = " ".join(str(row.get("published") or "").split())[:100]
        snippet = " ".join(str(row.get("snippet") or "").split())[:800]
        records.append(SearchRecord(
            collected_at=collected_at,
            query=query,
            search_vertical=cfg.search_vertical,
            shard_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            shard_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
            page=page_number,
            rank=len(records) + 1,
            title=title,
            link=link,
            source=source,
            published_time=published,
            snippet=snippet,
            search_url=search_url,
            language_lr=cfg.language_lr,
            country_cr=cfg.country_cr,
            search_engine="google",
            source_filter="",
            sort_mode="",
            site_limit="; ".join([x.strip() for x in cfg.site_filters or [] if x.strip()]),
            actual_domain=_actual_domain(link),
            query_raw=query,
            date_filter_type="custom_range" if cfg.date_filter_enabled else "none",
            date_start=shard_start.isoformat() if cfg.date_filter_enabled else "",
            date_end=shard_end.isoformat() if cfg.date_filter_enabled else "",
        ))
    return records





def looks_like_google_block_html(html: str, final_url: str = "") -> bool:
    final_url_l = (final_url or "").lower()
    text = (html or "").lower()

    # A final /sorry/ URL is reliable; a bare "/sorry/" occurrence inside a
    # normal SearchResultsPage is not.  The uploaded debug HTML showed real
    # WlydOe/YKoRaf result cards but was falsely classified as blocked because
    # a generic /sorry/ string occurred elsewhere in the page.
    if "/sorry/" in final_url_l or "google.com/sorry" in final_url_l:
        return True

    if _has_result_card_markers(html or ""):
        return False

    markers = [
        "our systems have detected unusual traffic",
        "unusual traffic from your computer network",
        "to continue, please type the characters",
        "detected unusual traffic",
        "g-recaptcha",
        "captcha-form",
    ]
    return any(m in text for m in markers)


def _candidate_browser_binary_paths(cfg: CollectorConfig, backend: str) -> list[Path]:
    """Return browser executables using the shared cross-platform manager."""
    candidates: list[Path] = []
    explicit = (getattr(cfg, "browser_binary_path", "") or "").strip().strip('"')
    if explicit:
        candidates.append(Path(explicit))
    project_root = Path(__file__).resolve().parent.parent
    for inst in detect_browser_installations(backend, app_root=project_root):
        candidates.append(Path(inst.path))
    out: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            key = os.path.normcase(str(candidate.expanduser().resolve()))
        except Exception:
            key = os.path.normcase(str(candidate))
        if key not in seen:
            seen.add(key)
            out.append(candidate)
    return out


def resolve_browser_binary_path(cfg: CollectorConfig, backend: str) -> Path | None:
    """Find Chrome/Edge browser executable path, if available."""
    for p in _candidate_browser_binary_paths(cfg, backend):
        try:
            if p.expanduser().exists() and p.expanduser().is_file():
                return p.expanduser().resolve()
        except Exception:
            continue
    return None


def _candidate_driver_paths(cfg: CollectorConfig, backend: str) -> list[Path]:
    """Return possible local webdriver paths in priority order."""
    names = ["chromedriver.exe", "chromedriver"] if backend != "selenium_edge" else ["msedgedriver.exe", "msedgedriver"]
    candidates: list[Path] = []

    explicit = (getattr(cfg, "browser_driver_path", "") or "").strip().strip('"')
    if explicit:
        candidates.append(Path(explicit))

    # Project root in source layout: <root>/bfsu_weblens/collector.py -> <root>
    project_root = Path(__file__).resolve().parent.parent
    cwd = Path.cwd()
    bases = [user_data_root(), project_root, cwd]
    # PyInstaller runtime temp dir, if any
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bases.insert(0, Path(meipass))

    for base in bases:
        for name in names:
            candidates.append(base / "tools" / name)
            candidates.append(base / name)

    # PATH fallback. Selenium can handle this itself, but logging the resolved
    # value makes diagnostics clearer.
    for name in names:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    # Deduplicate while preserving order.
    out: list[Path] = []
    seen = set()
    for c in candidates:
        try:
            key = str(c.expanduser().resolve())
        except Exception:
            key = str(c)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def resolve_driver_path(cfg: CollectorConfig, backend: str) -> Path | None:
    """Find a usable local ChromeDriver/EdgeDriver path, if available."""
    for p in _candidate_driver_paths(cfg, backend):
        try:
            if p.expanduser().exists() and p.expanduser().is_file():
                return p.expanduser().resolve()
        except Exception:
            continue
    return None


def create_selenium_driver(cfg: CollectorConfig):
    """Create a Selenium browser driver lazily.

    Priority order:
    1. Explicit path from GUI;
    2. Project-local tools/chromedriver.exe or tools/msedgedriver.exe;
    3. webdriver executable found in PATH;
    4. Selenium Manager automatic driver discovery/download.

    This is important on packaged Windows/macOS builds and on restricted
    networks where Selenium Manager may fail to download a driver automatically.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService
    except Exception as exc:
        raise NetworkAccessError(
            "Selenium browser backend is selected but selenium is not installed. "
            "Install it with: pip install selenium"
        ) from exc

    backend = (getattr(cfg, "fetch_backend", "selenium_chrome") or "selenium_chrome").lower()
    browser_binary_path = resolve_browser_binary_path(cfg, backend)
    configured_driver = resolve_driver_path(cfg, backend)

    # Validate the configured/project-local driver against the selected browser.
    # If it is stale or missing, WebLens downloads a matching driver from the
    # browser vendor before falling back to Selenium Manager.  This prevents a
    # bundled old driver from breaking after Chrome/Edge auto-updates.
    driver_path = None
    if browser_binary_path:
        try:
            app_root = user_data_root()
            prepared = ensure_driver(
                backend, str(browser_binary_path),
                explicit_driver_path=str(configured_driver or ""),
                app_root=app_root, allow_download=True,
                timeout=max(30, int(getattr(cfg, "timeout_seconds", 20) or 20)),
            )
            if prepared.compatible and prepared.driver_path:
                driver_path = Path(prepared.driver_path)
        except Exception:
            driver_path = None
    elif configured_driver:
        # A manually chosen driver remains usable when Selenium is allowed to
        # discover the browser installation itself.
        driver_path = configured_driver

    if backend == "selenium_edge":
        options = EdgeOptions()
        if browser_binary_path:
            options.binary_location = str(browser_binary_path)
        options.add_argument("--window-size=1280,900")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=en-US")
        if getattr(cfg, "browser_headless", False):
            options.add_argument("--headless=new")
        if driver_path:
            service = EdgeService(executable_path=str(driver_path))
            return webdriver.Edge(service=service, options=options)
        return webdriver.Edge(options=options)

    options = ChromeOptions()
    if browser_binary_path:
        options.binary_location = str(browser_binary_path)
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-US")
    if getattr(cfg, "browser_headless", False):
        options.add_argument("--headless=new")
    if driver_path:
        service = ChromeService(executable_path=str(driver_path))
        return webdriver.Chrome(service=service, options=options)
    return webdriver.Chrome(options=options)


MANUAL_VERIFICATION_POLL_SECONDS = 2.0
MANUAL_VERIFICATION_LOG_SECONDS = 15.0
MANUAL_VERIFICATION_CLEAR_CONFIRMATIONS = 2


def _selenium_page_snapshot(driver, fallback_url: str = "") -> tuple[str, str]:
    """Read the currently displayed browser page without navigating anywhere.

    Prefer the live DOM's ``documentElement.outerHTML`` over ``page_source``.
    After a human-verification challenge Google can update the visible result
    page asynchronously; ``page_source`` may briefly lag behind what the user
    already sees in the browser.
    """
    html_text = ""
    try:
        html_text = driver.execute_script(
            "return document.documentElement ? document.documentElement.outerHTML : '';"
        ) or ""
    except Exception:
        html_text = ""
    if not html_text:
        html_text = driver.page_source or ""
    current_url = getattr(driver, "current_url", fallback_url) or fallback_url
    return html_text, current_url


def _live_result_dom_state(driver, vertical: str) -> dict:
    """Inspect the browser's live DOM without navigation.

    This is intentionally broader than the HTML parser used to build final
    records. Its only job is to decide whether a real search-result page is
    visibly present after a CAPTCHA/verification flow.
    """
    is_baidu = is_baidu_vertical(vertical)
    script = r'''
const isBaidu = arguments[0];
const visible = (el) => {
  if (!el) return false;
  const st = window.getComputedStyle(el);
  if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};
const absHref = (a) => {
  try { return a && a.href ? String(a.href) : ''; } catch(e) { return ''; }
};
let headings = [];
let anchors = [];
if (isBaidu) {
  headings = Array.from(document.querySelectorAll('div.result h3, div.c-container h3, h3.t'));
  anchors = Array.from(document.querySelectorAll('div.result h3 a[href], div.c-container h3 a[href], a.c-title[href]'));
} else {
  headings = Array.from(document.querySelectorAll('#search h3, #rso h3, div.MjjYud h3'));
  anchors = Array.from(document.querySelectorAll('a[jsname=\"UWckNb\"][href], a.WlydOe[href], a[jsname=\"YKoRaf\"][href]'));
  for (const h of headings) {
    const a = h.closest('a[href]') || h.querySelector('a[href]') || (h.parentElement && h.parentElement.closest ? h.parentElement.closest('a[href]') : null);
    if (a) anchors.push(a);
  }
}
headings = headings.filter(visible);
anchors = anchors.filter(visible);
const hrefs = [];
const seen = new Set();
for (const a of anchors) {
  const href = absHref(a);
  if (!href || seen.has(href)) continue;
  seen.add(href);
  hrefs.push(href);
}
return {
  visible_headings: headings.length,
  principal_links: hrefs.length,
  sample_links: hrefs.slice(0, 5),
  ready_state: document.readyState || ''
};
'''
    try:
        state = driver.execute_script(script, bool(is_baidu)) or {}
        if not isinstance(state, dict):
            state = {}
    except Exception:
        state = {}
    return {
        "visible_headings": int(state.get("visible_headings", 0) or 0),
        "principal_links": int(state.get("principal_links", 0) or 0),
        "sample_links": list(state.get("sample_links", []) or []),
        "ready_state": str(state.get("ready_state", "") or ""),
    }


def looks_like_baidu_verification_html(html: str, final_url: str = "") -> bool:
    """Detect Baidu human-verification / security-check pages conservatively."""
    url_l = (final_url or "").lower()
    text = (html or "").lower()
    if any(token in url_l for token in ("wappass.baidu.com", "verify.baidu.com", "passport.baidu.com/v", "seccaptcha")):
        return True
    markers = (
        "百度安全验证",
        "安全验证",
        "请完成下方验证",
        "请完成验证",
        "验证码",
        "seccaptcha",
        "captcha",
        "verify.baidu.com",
        "wappass.baidu.com",
    )
    # Avoid treating ordinary pages as verification merely because a script
    # bundle contains a generic captcha string; require either a stronger
    # Chinese/security marker or a verification host/form pattern.
    strong = markers[:5] + markers[6:]
    return any(m.lower() in text for m in strong) or ("captcha" in text and "verify" in text)


def looks_like_engine_verification(html: str, final_url: str, vertical: str) -> bool:
    if is_baidu_vertical(vertical):
        return looks_like_baidu_verification_html(html, final_url)
    return looks_like_google_block_html(html, final_url)


def _has_explicit_no_result_state(html_text: str, vertical: str) -> bool:
    """Return True only for an explicit engine no-result message.

    A normal ``/search`` URL or a large HTML document is *not* sufficient.
    Immediately after a CAPTCHA is cleared Google can expose the search shell
    several seconds before the result cards are inserted into the DOM. Treating
    that transient shell as a completed page caused WebLens to parse zero links
    and terminate an otherwise valid collection task.
    """
    lower = (html_text or "").lower()
    markers = (
        "did not match any documents",
        "no results found",
        "your search did not match any documents",
        "找不到和您查询",
        "找不到和您查詢",
        "没有任何结果",
        "沒有任何結果",
        "抱歉没有找到",
        "抱歉，未找到",
        "没有找到相关结果",
        "未找到相关结果",
    )
    return any(marker in lower for marker in markers)


def _page_has_normal_search_state(html_text: str, current_url: str, vertical: str) -> bool:
    """Return True only when the post-verification search page is *ready*.

    Readiness deliberately requires a real result-card URL (or an explicit
    engine no-result message). Merely returning to Google/Baidu's search URL is
    not enough because both engines can render an intermediate shell first.
    """
    if looks_like_engine_verification(html_text, current_url, vertical):
        return False
    if count_external_result_candidates(html_text, vertical) > 0:
        return True
    return _has_explicit_no_result_state(html_text, vertical)


def wait_for_manual_verification(
    driver,
    cfg: CollectorConfig,
    stop_checker: Callable[[], bool] | None = None,
    page_number: int | None = None,
    initial_url: str = "",
):
    """Wait for the user to complete a browser verification challenge.

    While verification remains present WebLens performs no navigation action:
    it does not call ``get()``, ``refresh()``, click Next, restart the browser,
    or open another URL. It only reads the already-open page so it can detect
    when the user has completed the challenge. Once the normal search page is
    stable for two polls, parsing resumes *without refreshing the page*.
    """
    poll_seconds = MANUAL_VERIFICATION_POLL_SECONDS
    poll_ms = int(poll_seconds * 1000)
    page_hint = f" on page {page_number}" if page_number else ""
    yield CrawlEvent(
        "verification_wait",
        f"Human verification detected{page_hint}. Collection is paused on the current browser page. "
        "Complete the verification manually. WebLens will not refresh, paginate, restart the browser, "
        "or open another page while verification remains active.",
        data={"page_number": page_number, "url": initial_url, "poll_seconds": poll_seconds},
    )
    clear_streak = 0
    verification_cleared_seen = False
    last_heartbeat = time.monotonic()
    while True:
        if stop_checker and stop_checker():
            raise StopCrawl()
        try:
            html_text, current_url = _selenium_page_snapshot(driver, initial_url)
        except Exception as exc:
            raise NetworkAccessError(
                "The collection browser was closed or became unavailable while waiting for human verification."
            ) from exc
        live_state = _live_result_dom_state(driver, cfg.search_vertical)
        live_result_count = max(
            int(live_state.get("visible_headings", 0) or 0),
            int(live_state.get("principal_links", 0) or 0),
        )
        parsed_candidate_count = count_external_result_candidates(html_text, cfg.search_vertical)
        explicit_no_result = _has_explicit_no_result_state(html_text, cfg.search_vertical)

        # Result-first priority: once the live browser visibly contains real
        # search-result headings/links, stale CAPTCHA strings or scripts in the
        # HTML must not keep WebLens trapped in the verification wait loop.
        verification_active = looks_like_engine_verification(html_text, current_url, cfg.search_vertical)
        if live_result_count > 0 or parsed_candidate_count > 0:
            verification_active = False

        if not verification_active and not verification_cleared_seen:
            verification_cleared_seen = True
            yield CrawlEvent(
                "log",
                f"Human-verification page has cleared{page_hint}. Waiting for the real search-result DOM to become stable before resuming.",
            )

        normal_ready = (live_result_count > 0) or (parsed_candidate_count > 0) or explicit_no_result
        if not verification_active and normal_ready:
            clear_streak += 1
        else:
            clear_streak = 0

        if clear_streak >= MANUAL_VERIFICATION_CLEAR_CONFIRMATIONS:
            html_text, current_url = _selenium_page_snapshot(driver, current_url)
            yield CrawlEvent(
                "verification_passed",
                "Human verification completed and the live search-result DOM is stable. Collection will resume from the page already open in the browser.",
                data={
                    "page_number": page_number,
                    "url": current_url,
                    "live_results": live_result_count,
                    "parsed_candidates": parsed_candidate_count,
                },
            )
            return html_text, current_url
        now = time.monotonic()
        if now - last_heartbeat >= MANUAL_VERIFICATION_LOG_SECONDS:
            phase = "verification challenge still detected" if verification_active else "verification cleared; waiting for result DOM"
            yield CrawlEvent(
                "log",
                f"Verification wait{page_hint}: {phase}; live_results={live_result_count}, "
                f"parsed_candidates={parsed_candidate_count}, explicit_no_result={explicit_no_result}, "
                f"ready_state={live_state.get('ready_state','')}, url={current_url}. "
                "No browser navigation has been sent.",
            )
            last_heartbeat = now
        sleep_random_ms(poll_ms, poll_ms, stop_checker)


def fetch_html_with_selenium(driver, url: str, cfg: CollectorConfig, stop_checker: Callable[[], bool] | None = None) -> tuple[str, str]:
    """Load one search-result page in the selected collection browser."""
    try:
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:
        raise NetworkAccessError("Selenium is not available. Install it with: pip install selenium") from exc
    if stop_checker and stop_checker():
        raise StopCrawl()
    driver.get(url)
    timeout = max(1, int(cfg.timeout_seconds))
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") in {"interactive", "complete"}
        )
    except Exception:
        pass
    # Google/Baidu often finish building result cards after readyState becomes
    # complete.  Wait for a real result marker, a known no-result message, or a
    # verification page before taking page_source.  This avoids parsing the
    # transient shell that previously produced an empty Result Preview.
    try:
        WebDriverWait(driver, min(timeout, 12)).until(lambda d: bool(d.execute_script(r"""
            const body = (document.body && document.body.innerText) || '';
            const hasResult = !!document.querySelector(
              '#rso h3, #rso a[href], a[jsname="UWckNb"], a.WlydOe, a[jsname="YKoRaf"], div.result h3, div.c-container h3'
            );
            const terminal = /no results|did not match|找不到|没有任何结果|沒有任何結果|抱歉.*(?:没有|未找到)|captcha|安全验证|unusual traffic/i.test(body);
            return hasResult || terminal;
        """)))
    except Exception:
        pass
    wait_ms = max(0, int(getattr(cfg, "browser_wait_ms", 5000) or 0))
    if wait_ms:
        sleep_random_ms(wait_ms, wait_ms, stop_checker)
    return _selenium_page_snapshot(driver, url)


def _normalized_next_candidate(href: str, current_url: str, vertical: str) -> str:
    if not href:
        return ""
    href = html_lib.unescape(str(href).strip())
    if href.lower().startswith(("javascript:", "mailto:", "#")):
        return ""
    candidate = urljoin(current_url, href)
    try:
        p = urlparse(candidate)
        host = (p.hostname or "").lower()
        path = (p.path or "").lower()
    except Exception:
        return ""
    if is_baidu_vertical(vertical):
        if not host.endswith("baidu.com") or path != "/s":
            return ""
    else:
        google_host = host == "google.com" or host.endswith(".google.com") or bool(re.search(r"(^|\.)google\.[a-z.]+$", host))
        if not google_host or not path.startswith("/search"):
            return ""
    return candidate


def find_engine_next_page_url(html_text: str, current_url: str, vertical: str) -> str:
    """Read the search engine's own Next link; WebLens never calculates page offsets."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    candidates = []
    if is_baidu_vertical(vertical):
        # Baidu commonly marks the paging anchors with class="n" and uses
        # Chinese labels. Use hrefs already generated by Baidu itself.
        candidates.extend(soup.select("a.n[href]"))
        candidates.extend(soup.select("a[aria-label][href]"))
    else:
        candidates.extend(soup.select("a#pnnext[href]"))
        candidates.extend(soup.select("a[rel='next'][href]"))
        candidates.extend(soup.select("a[aria-label][href]"))
    candidates.extend(soup.find_all("a", href=True))

    seen = set()
    for a in candidates:
        marker = " ".join([
            str(a.get("id") or ""),
            " ".join(a.get("class") or []),
            str(a.get("aria-label") or ""),
            a.get_text(" ", strip=True),
        ]).strip().lower()
        if is_baidu_vertical(vertical):
            is_next = any(x in marker for x in ("下一页", "下一頁", "next page", "next")) or ("n" in (a.get("class") or []) and "上一" not in marker)
        else:
            is_next = (a.get("id") == "pnnext") or ("next" in marker) or ("下一页" in marker) or ("下一頁" in marker)
        if not is_next:
            continue
        candidate = _normalized_next_candidate(a.get("href", ""), current_url, vertical)
        if candidate and candidate not in seen:
            return candidate
        seen.add(candidate)
    return ""


def count_external_result_candidates(html_text: str, vertical: str) -> int:
    """Count usable links that occur in recognizable search-result cards only.

    Current Google News opaque ``/goto`` result redirects count as usable result
    links even though their hostname belongs to Google.

    Engine-owned navigation, footer, account, policy, map/image tabs, and other
    page-chrome anchors are deliberately ignored even when they point outside
    the search engine. This makes a genuine empty result page terminate
    collection instead of being kept alive by interface links.
    """
    if not html_text:
        return 0
    try:
        soup = BeautifulSoup(html_text, "html.parser")
    except Exception:
        return 0
    anchors = _baidu_result_anchors(soup) if is_baidu_vertical(vertical) else _candidate_anchors(soup)
    seen: set[str] = set()
    for a in anchors:
        href = a.get("href", "")
        url = unwrap_baidu_url(href) if is_baidu_vertical(vertical) else unwrap_google_url(href)
        if not url and is_baidu_vertical(vertical):
            url = unwrap_google_url(href)
        if not url or not is_valid_result_url(url):
            continue
        key = normalize_url_for_dedup(url)
        if key:
            seen.add(key)
    return len(seen)


def crawl(cfg: CollectorConfig, stop_checker: Callable[[], bool] | None = None) -> Iterable[CrawlEvent]:
    """Collect search results only through a real Chrome/Edge browser.

    Pagination is engine-led: WebLens loads the initial query without page-size
    or maximum-page parameters and then follows the engine's own Next link until
    that link disappears or a genuine empty result page is reached. There is no
    software-side page-count ceiling.

    Baidu's ``any`` query mode is deliberately different from Google's OR mode:
    each non-empty input line becomes an independent search task. WebLens fully
    traverses one Baidu term before moving to the next and never emits an OR
    expression for that mode.
    """
    fetch_backend = (getattr(cfg, "fetch_backend", "selenium_chrome") or "selenium_chrome").lower()
    if fetch_backend not in {"selenium_chrome", "selenium_edge"}:
        raise BrowserStartupError("Search collection supports only Chrome or Edge browser mode.")

    seen_global: set[str] = set()
    driver = None
    backend_name = "Edge" if fetch_backend == "selenium_edge" else "Chrome"

    baidu_sequential = (
        is_baidu_vertical(getattr(cfg, "search_vertical", ""))
        and (getattr(cfg, "query_mode", "") or "").lower().strip() == "any"
    )
    search_tasks = expand_search_tasks(cfg)

    if not search_tasks:
        yield CrawlEvent("done", "No search terms were provided.")
        return

    yield CrawlEvent("log", "Collection browser User-Agent is not overridden; WebLens uses the selected Chrome/Edge browser default.")
    yield CrawlEvent("log", f"Collection browser: {backend_name}")
    yield CrawlEvent("log", "Search collection uses browser-rendered pages only; the Requests/HTTP search backend has been removed.")
    yield CrawlEvent("log", "Page size and maximum page count are controlled by the search engine. WebLens sends neither setting.")
    yield CrawlEvent("log", "Pagination follows the search engine's own Next link; WebLens does not calculate page offsets.")
    yield CrawlEvent("log", "Page, slice-transition, and transient-error waits all use the same page-delay range.")
    if baidu_sequential:
        yield CrawlEvent("log", f"Baidu multiple-term mode: {len(search_tasks)} term(s) will be searched one by one; no OR expression will be sent.")

    def start_selenium_driver(page_number: int | None = None):
        try:
            return create_selenium_driver(cfg)
        except Exception as exc:
            page_hint = f" before page {page_number}" if page_number else ""
            raise BrowserStartupError(
                f"{exc}\n\nCould not start the {backend_name} collection browser{page_hint}. "
                "Open Settings > Browser & Selenium, select an installed browser, and run Detect / update driver. "
                "The browser and WebDriver configuration is shared by all search-engine collectors. "
                "If vendor download access is unavailable, use the official download buttons in that settings dialog."
            ) from exc

    try:
        resolved_driver = resolve_driver_path(cfg, fetch_backend)
        resolved_binary = resolve_browser_binary_path(cfg, fetch_backend)
        if resolved_driver:
            yield CrawlEvent("log", f"Configured {backend_name} driver candidate: {resolved_driver}. WebLens will verify compatibility before use.")
        else:
            yield CrawlEvent("log", f"No driver is pinned. WebLens will locate or download a driver matching the selected {backend_name} version automatically.")
        if resolved_binary:
            yield CrawlEvent("log", f"Using {backend_name} browser binary: {resolved_binary}")
        else:
            yield CrawlEvent("log", f"No explicit {backend_name} browser binary selected; Selenium will use the system installation.")

        driver = start_selenium_driver(1)
        yield CrawlEvent("log", f"{backend_name} collection browser started. It will remain open for the task unless the user stops collection.")

        if cfg.date_filter_enabled:
            base_date_slices = split_date_range(cfg.start_date, cfg.end_date, cfg.day_step)
            yield CrawlEvent("log", f"Date restriction enabled. Date slices per search task: {len(base_date_slices)}")
        else:
            today = date.today()
            base_date_slices = [(today, today)]
            yield CrawlEvent("log", "No date restriction: WebLens sends no date-range parameter to the search engine.")

        total_units = max(1, len(search_tasks) * len(base_date_slices))
        global_unit_index = 0
        terminate_all = False

        for query_index, task_cfg in enumerate(search_tasks, start=1):
            if stop_checker and stop_checker():
                raise StopCrawl()
            query_label = build_query(task_cfg.query_mode, task_cfg.query_terms, task_cfg.raw_query, task_cfg.site_filters)
            if baidu_sequential:
                yield CrawlEvent("log", f"Baidu term [{query_index}/{len(search_tasks)}]: {query_label}")

            terminate_current_query_after_empty = False
            for slice_index, (shard_start, shard_end) in enumerate(base_date_slices, start=1):
                if stop_checker and stop_checker():
                    raise StopCrawl()
                global_unit_index += 1
                if task_cfg.date_filter_enabled:
                    slice_text = f"{shard_start} ~ {shard_end}"
                else:
                    slice_text = "No date restriction"
                if baidu_sequential:
                    slice_message = f"[{query_index}/{len(search_tasks)}] {query_label} · {slice_text}"
                else:
                    slice_message = (
                        f"[{slice_index}/{len(base_date_slices)}] {slice_text}"
                        if task_cfg.date_filter_enabled else slice_text
                    )
                yield CrawlEvent(
                    "slice",
                    slice_message,
                    data={"slice_index": global_unit_index, "slice_total": total_units},
                )

                current_url = build_search_url(task_cfg, shard_start, shard_end)
                page_number = 1
                seen_page_signatures: set[tuple[str, ...]] = set()
                visited_page_urls: set[str] = set()

                while True:
                    if stop_checker and stop_checker():
                        raise StopCrawl()
                    normalized_page_url = normalize_url_for_dedup(current_url)
                    if normalized_page_url in visited_page_urls:
                        yield CrawlEvent("log", "The search engine returned a previously visited pagination URL. Stop the current search unit to avoid a loop.")
                        break
                    visited_page_urls.add(normalized_page_url)
                    yield CrawlEvent("log", f"Loading result page {page_number} using the search engine's current default pagination.")

                    try:
                        html_text, final_url = fetch_html_with_selenium(driver, current_url, task_cfg, stop_checker)
                    except StopCrawl:
                        raise
                    except Exception as exc:
                        yield CrawlEvent("log", f"Browser page-load error: {exc}. Waiting with the normal page-delay setting before one retry.")
                        sleep_random_ms(task_cfg.page_delay_min_ms, task_cfg.page_delay_max_ms, stop_checker)
                        try:
                            html_text, final_url = fetch_html_with_selenium(driver, current_url, task_cfg, stop_checker)
                        except StopCrawl:
                            raise
                        except Exception as retry_exc:
                            raise NetworkAccessError(str(retry_exc)) from retry_exc

                    yield CrawlEvent("log", f"Browser loaded page {page_number}; html_len={len(html_text)}")

                    if looks_like_engine_verification(html_text, final_url, task_cfg.search_vertical):
                        debug_path = save_debug_html_if_needed(task_cfg, html_text, shard_start, shard_end, page_number)
                        if debug_path:
                            yield CrawlEvent("log", f"Human-verification page detected. Debug HTML saved to: {debug_path}")
                        html_text, final_url = yield from wait_for_manual_verification(
                            driver,
                            task_cfg,
                            stop_checker=stop_checker,
                            page_number=page_number,
                            initial_url=final_url,
                        )
                        yield CrawlEvent("log", f"Resuming page {page_number} after human verification.")

                    page_records = extract_records_from_html(html_text, task_cfg, final_url or current_url, shard_start, shard_end, page_number)
                    candidate_count = count_external_result_candidates(html_text, task_cfg.search_vertical)
                    if not page_records and not is_baidu_vertical(task_cfg.search_vertical):
                        live_records = extract_google_records_from_live_dom(
                            driver, task_cfg, final_url or current_url, shard_start, shard_end, page_number
                        )
                        if live_records:
                            page_records = live_records
                            candidate_count = max(candidate_count, len(live_records))
                            yield CrawlEvent(
                                "log",
                                f"Recovered {len(live_records)} Google result record(s) directly from the live browser DOM after the HTML parser returned none.",
                            )

                    if not page_records and candidate_count == 0:
                        debug_path = save_debug_html_if_needed(task_cfg, html_text, shard_start, shard_end, page_number)
                        msg = f" Debug HTML saved to: {debug_path}." if debug_path else ""
                        if baidu_sequential:
                            yield CrawlEvent(
                                "log",
                                f"Result page {page_number} contains no usable search-result links. Current Baidu term is complete; continue with the next term if any.{msg}",
                            )
                            terminate_current_query_after_empty = True
                        else:
                            yield CrawlEvent(
                                "log",
                                f"Result page {page_number} contains no usable search-result links. Stop the collection task immediately.{msg}",
                            )
                            terminate_all = True
                        break

                    if not page_records and candidate_count > 0:
                        debug_path = save_debug_html_if_needed(task_cfg, html_text, shard_start, shard_end, page_number)
                        msg = f" Debug HTML saved to: {debug_path}." if debug_path else ""
                        yield CrawlEvent(
                            "log",
                            f"Page {page_number} contains {candidate_count} usable result-link candidate(s), but none could be converted into valid records. "
                            f"Stop this search unit rather than treating search-engine UI links as results.{msg}",
                        )
                        break

                    signature = tuple(normalize_url_for_dedup(r.link) for r in page_records)
                    if signature and signature in seen_page_signatures:
                        yield CrawlEvent("log", "The search engine repeated the same result set. Stop the current search unit to avoid a pagination loop.")
                        break
                    if signature:
                        seen_page_signatures.add(signature)

                    new_count = 0
                    for rec in page_records:
                        key = normalize_url_for_dedup(rec.link)
                        if not key or key in seen_global:
                            continue
                        seen_global.add(key)
                        new_count += 1
                        yield CrawlEvent("record", rec.title, record=rec)
                    yield CrawlEvent("log", f"Page {page_number}: {len(page_records)} valid records, {new_count} new after global deduplication.")

                    next_url = find_engine_next_page_url(html_text, final_url or current_url, task_cfg.search_vertical)
                    if not next_url:
                        yield CrawlEvent("log", "The search engine did not provide another result-page link. Current search unit is complete.")
                        break
                    if normalize_url_for_dedup(next_url) in visited_page_urls:
                        yield CrawlEvent("log", "The search engine's Next link points to an already visited page. Current search unit is complete.")
                        break

                    sleep_random_ms(task_cfg.page_delay_min_ms, task_cfg.page_delay_max_ms, stop_checker)
                    current_url = next_url
                    page_number += 1

                if terminate_all or terminate_current_query_after_empty:
                    break

                if slice_index < len(base_date_slices):
                    yield CrawlEvent("log", "Waiting before the next date slice using the same page-delay range.")
                    sleep_random_ms(task_cfg.page_delay_min_ms, task_cfg.page_delay_max_ms, stop_checker)

            if terminate_all:
                yield CrawlEvent("log", "Collection ended because the browser returned a genuine empty search-result page.")
                break
            if baidu_sequential and query_index < len(search_tasks):
                yield CrawlEvent("log", "Current Baidu term is complete. Waiting with the normal page-delay range before the next term.")
                sleep_random_ms(task_cfg.page_delay_min_ms, task_cfg.page_delay_max_ms, stop_checker)

        yield CrawlEvent("done", "Crawl finished.")
    finally:
        if driver is not None:
            try:
                driver.quit()
                yield CrawlEvent("log", "Collection browser closed.")
            except Exception:
                pass

