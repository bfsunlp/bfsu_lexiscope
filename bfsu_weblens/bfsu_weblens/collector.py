# -*- coding: utf-8 -*-
"""Google Search collection core for BFSU WebLens.

This module is intentionally conservative and auditable:
- it builds reproducible Google Search / Google News-tab URLs;
- it splits long date ranges into date slices;
- it parses both current and older Google result-page HTML variants;
- it exposes diagnostic messages when a page contains possible result anchors but
  no records pass parsing / filtering.
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
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, quote

import requests
from bs4 import BeautifulSoup

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
    fetch_backend: str    # requests | selenium_chrome | selenium_edge
    language_lr: str      # e.g. lang_en|lang_fr
    country_cr: str       # e.g. countryUS|countryUK
    safe: str
    disable_filter: bool
    start_date: date
    end_date: date
    day_step: int
    max_pages: int
    per_page: int
    page_delay_min_ms: int
    page_delay_max_ms: int
    slice_delay_min_ms: int
    slice_delay_max_ms: int
    error_delay_min_ms: int
    error_delay_max_ms: int
    timeout_seconds: int
    max_retries: int
    user_agent: str
    post_fetch_wait_ms: int = 800
    browser_wait_ms: int = 3500
    browser_headless: bool = False
    browser_driver_path: str = ""
    browser_binary_path: str = ""
    empty_page_retry_count: int = 2
    empty_page_retry_wait_ms: int = 1500
    save_debug_html: bool = True
    debug_dir: str = "weblens_debug_html"
    selenium_restart_pages: int = 4
    no_new_pages_limit: int = 1
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


def build_search_url(cfg: CollectorConfig, shard_start: date, shard_end: date, start_offset: int) -> str:
    """Build a reproducible search URL for Google or Baidu."""
    q = build_query(cfg.query_mode, cfg.query_terms, cfg.raw_query, cfg.site_filters)
    vertical = (cfg.search_vertical or "news").lower().strip()

    if is_baidu_vertical(vertical):
        rn = max(1, min(int(cfg.per_page or 10), 50))
        params = {
            "ie": "utf-8",
            "wd": q,
            "pn": str(max(0, int(start_offset or 0))),
            "rn": str(rn),
        }
        if baidu_vertical_kind(vertical) == "news":
            params["tn"] = "news"
            params["cl"] = "2"
            if baidu_source_filter(vertical) == "media":
                params["medium"] = "1"
            params["rtt"] = "4" if baidu_sort_value(cfg) == "time" else "1"
        else:
            params["tn"] = "baidu"
        gpc_value, _start_ts, _end_ts = baidu_gpc(shard_start, shard_end)
        params["gpc"] = gpc_value
        params["tfflag"] = "1"
        return "https://www.baidu.com/s?" + urlencode(params)

    google_vertical = "news" if vertical in {"news", "google_news"} else "web"
    params = {
        "q": q,
        "num": str(cfg.per_page),
        "tbs": f"cdr:1,cd_min:{google_date(shard_start)},cd_max:{google_date(shard_end)}",
    }
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
    if start_offset > 0:
        params["start"] = str(start_offset)
    return "https://www.google.com/search?" + urlencode(params)

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

def unwrap_google_url(href: str) -> str:
    if not href:
        return ""
    href = html_lib.unescape(href.strip())
    if href.startswith("/url?") or href.startswith("/interstitial?"):
        qs = parse_qs(urlparse(href).query)
        return qs.get("q", qs.get("url", [""]))[0]
    if href.startswith("/search?") or href.startswith("#"):
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("http"):
        # Some Google redirect URLs are absolute.
        parsed = urlparse(href)
        if "google." in parsed.netloc.lower() and parsed.path.startswith("/url"):
            qs = parse_qs(parsed.query)
            return qs.get("q", qs.get("url", [""]))[0]
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

def looks_like_google_block_page(resp: requests.Response) -> bool:
    final_url = (resp.url or "").lower()
    text = (resp.text or "").lower()

    # A final /sorry/ URL is a strong signal. A raw occurrence of /sorry/ in
    # page scripts is not strong enough, because normal result pages can contain
    # such strings.
    if "/sorry/" in final_url or "google.com/sorry" in final_url:
        return True

    # Do not flag pages as blocked if actual result-card markers are present.
    if _has_result_card_markers(resp.text or ""):
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

def build_browser_headers(user_agent: str, referer: str | None = None) -> dict:
    """Return browser-like headers for Google result pages.

    Google often returns different HTML to Python's default requests headers than
    to Chrome/Edge. These headers do not bypass access controls, but they reduce
    the chance of receiving a minimal shell page that contains no result cards.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7",
        # requests fully downloads the HTTP body before resp.text is parsed.
        # We intentionally avoid advertising br unless brotli support exists in
        # the user's Python environment.
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if not referer else "same-origin",
        "Sec-Fetch-User": "?1",
        # Helps avoid the Google consent shell in some regions while keeping the
        # request transparent and auditable.
        "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+667; SOCS=CAESHAgBEhIaAB",
    }
    if referer:
        headers["Referer"] = referer
    return headers


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

    This specifically covers anchors like:
    <a jsname="YKoRaf" class="WlydOe" href="..."> ... .n0jPhd ... .UqSP2b ... .OSrXXb ... </a>

    It also works when the HTML is entity-escaped or stored in JavaScript with
    \x3c / \u003c style escapes.
    """
    records = []
    seen = set()
    anchor_patterns = [
        r'<a\b(?=[^>]*\bjsname=["\']YKoRaf["\'])(?=[^>]*\bclass=["\'][^"\']*\bWlydOe\b[^"\']*["\'])(?P<attrs>[^>]*)>(?P<body>.*?)</a>',
        r'<a\b(?=[^>]*\bclass=["\'][^"\']*\bWlydOe\b[^"\']*["\'])(?=[^>]*\bjsname=["\']YKoRaf["\'])(?P<attrs>[^>]*)>(?P<body>.*?)</a>',
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
        "a.WlydOe",             # current Google News title card link
        "a[jsname='YKoRaf']",    # Google News title link variant
        "a[jsname='UWckNb']",    # web-result title link variant
        "a:has(h3)",             # fallback for web results; supported by soupsieve
        "a[href^='/url?']",
        "a[href^='http']",
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

def diagnose_result_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    decoded = _decode_google_escapes(html)
    decoded_soup = BeautifulSoup(decoded, "html.parser") if decoded != html else soup
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
        "reason": classify_no_result_page(html),
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
        host = urlparse(url).netloc.lower().lstrip("www.")
        if host.endswith("baidu.com") and is_baidu_redirect_url(url):
            return ""
        return host
    except Exception:
        return ""

def extract_baidu_records_from_html(html: str, cfg: CollectorConfig, search_url: str, shard_start: date, shard_end: date, page_number: int) -> list[SearchRecord]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    seen_nodes = set()
    for a in list(soup.select("h3 a[href]")) + list(soup.select("a[href]")):
        if id(a) in seen_nodes:
            continue
        seen_nodes.add(id(a))
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
    gpc_value, start_ts, end_ts = baidu_gpc(shard_start, shard_end)
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
            shard_start=shard_start.isoformat(),
            shard_end=shard_end.isoformat(),
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
            date_filter_type="custom_range",
            date_start=shard_start.isoformat(),
            date_end=shard_end.isoformat(),
            start_ts=str(start_ts),
            end_ts=str(end_ts),
            baidu_gpc=gpc_value,
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
            shard_start=shard_start.isoformat(),
            shard_end=shard_end.isoformat(),
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
            date_filter_type="custom_range",
            date_start=shard_start.isoformat(),
            date_end=shard_end.isoformat(),
        ))
    return records


def should_retry_empty_result(diag: dict) -> bool:
    """Return True when an empty parse likely reflects a transient/shell page.

    A genuine no-result page should not be retried repeatedly. A page with no
    recognizable result anchors, very few outbound HTTP links, or a JS/consent
    shell is a better retry candidate.
    """
    reason = (diag.get("reason") or "").lower()
    marker_total = (
        int(diag.get("a_WlydOe", 0))
        + int(diag.get("a_YKoRaf", 0))
        + int(diag.get("a_UWckNb", 0))
        + int(diag.get("h3", 0))
        + int(diag.get("url_redirects", 0))
        + int(diag.get("decoded_a_WlydOe", 0))
        + int(diag.get("decoded_a_YKoRaf", 0))
        + int(diag.get("regex_news_cards", 0))
        + int(diag.get("raw_WlydOe", 0))
        + int(diag.get("raw_YKoRaf", 0))
    )
    if "no matching documents" in reason or "no matching" in reason or "沒有" in reason and "結果" in reason:
        return False
    if "javascript/redirect shell" in reason or "consent page" in reason or "unusual-traffic" in reason:
        return True
    if marker_total == 0:
        return True
    # Markers exist but parsing failed: one retry can help if Google served a
    # partially altered response; filtering may still remove all records later.
    return True

def get_retry_after_ms(resp: requests.Response) -> Optional[int]:
    value = resp.headers.get("Retry-After")
    if not value:
        return None
    try:
        return int(value) * 1000
    except ValueError:
        return None


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
    """Return possible Chrome/Edge browser executable paths in priority order."""
    candidates: list[Path] = []

    explicit = (getattr(cfg, "browser_binary_path", "") or "").strip().strip('"')
    if explicit:
        candidates.append(Path(explicit))

    env = os.environ
    pf = Path(env.get("PROGRAMFILES", r"C:\Program Files"))
    pfx86 = Path(env.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
    local = Path(env.get("LOCALAPPDATA", "")) if env.get("LOCALAPPDATA") else None

    if backend == "selenium_edge":
        candidates.extend([
            pf / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            pfx86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ])
        if local:
            candidates.append(local / "Microsoft" / "Edge" / "Application" / "msedge.exe")
        path_found = shutil.which("msedge") or shutil.which("msedge.exe")
    else:
        candidates.extend([
            pf / "Google" / "Chrome" / "Application" / "chrome.exe",
            pfx86 / "Google" / "Chrome" / "Application" / "chrome.exe",
            pf / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
            pfx86 / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
            pf / "Google" / "Chrome Beta" / "Application" / "chrome.exe",
            pfx86 / "Google" / "Chrome Beta" / "Application" / "chrome.exe",
            pf / "Google" / "Chrome for Testing" / "Application" / "chrome.exe",
            pfx86 / "Google" / "Chrome for Testing" / "Application" / "chrome.exe",
        ])
        if local:
            candidates.extend([
                local / "Google" / "Chrome" / "Application" / "chrome.exe",
                local / "Google" / "Chrome Dev" / "Application" / "chrome.exe",
                local / "Google" / "Chrome Beta" / "Application" / "chrome.exe",
                local / "Google" / "Chrome SxS" / "Application" / "chrome.exe",
                local / "Google" / "Chrome for Testing" / "Application" / "chrome.exe",
            ])
        path_found = shutil.which("chrome") or shutil.which("chrome.exe")

    if path_found:
        candidates.append(Path(path_found))

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
    bases = [project_root, cwd]
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

    This is important on Windows and on restricted networks where Selenium
    Manager may fail to download a driver automatically.
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
    driver_path = resolve_driver_path(cfg, backend)
    browser_binary_path = resolve_browser_binary_path(cfg, backend)

    if backend == "selenium_edge":
        options = EdgeOptions()
        if browser_binary_path:
            options.binary_location = str(browser_binary_path)
        options.add_argument(f"--user-agent={cfg.user_agent}")
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
    options.add_argument(f"--user-agent={cfg.user_agent}")
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

def fetch_html_with_selenium(driver, url: str, cfg: CollectorConfig, stop_checker: Callable[[], bool] | None = None) -> tuple[str, str]:
    """Load a Google result page in a real browser and return page_source.

    Unlike requests, Selenium executes Google's client-side JavaScript and can
    therefore see the result cards when Google sends a redirect / JS shell to raw
    HTTP clients. The extra wait is intentional: Google News cards may appear
    shortly after document.readyState becomes complete.
    """
    try:
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:
        raise NetworkAccessError("Selenium is not available. Install it with: pip install selenium") from exc

    driver.get(url)
    try:
        WebDriverWait(driver, max(1, int(cfg.timeout_seconds))).until(
            lambda d: d.execute_script("return document.readyState") in {"interactive", "complete"}
        )
    except Exception:
        # Continue anyway: page_source may still contain useful diagnostics.
        pass
    wait_ms = max(0, int(getattr(cfg, "browser_wait_ms", 3500) or 0))
    if wait_ms:
        sleep_random_ms(wait_ms, wait_ms, stop_checker)
    return driver.page_source or "", getattr(driver, "current_url", url)


def crawl(cfg: CollectorConfig, stop_checker: Callable[[], bool] | None = None) -> Iterable[CrawlEvent]:
    fetch_backend = (getattr(cfg, "fetch_backend", "selenium_chrome") or "selenium_chrome").lower()
    use_browser = fetch_backend in {"selenium_chrome", "selenium_edge"}
    seen_global = set()
    session = None
    driver = None
    last_referer = "https://www.google.com/"
    selenium_pages_per_session = max(0, int(getattr(cfg, "selenium_restart_pages", 4) or 0))
    no_new_pages_limit = max(1, int(getattr(cfg, "no_new_pages_limit", 1) or 1))

    yield CrawlEvent("log", f"User-Agent: {cfg.user_agent}")
    yield CrawlEvent("log", f"Fetch backend: {fetch_backend}")
    yield CrawlEvent("log", "URL mode selector removed: WebLens now uses Google lr/cr parameters directly for precision-oriented filtering.")
    if use_browser:
        yield CrawlEvent("log", "Browser backend enabled: Selenium will open a real Chrome/Edge window and parse the rendered DOM.")
        if selenium_pages_per_session > 0:
            yield CrawlEvent("log", f"Selenium session restart policy: close and reopen the browser every {selenium_pages_per_session} page(s).")
        yield CrawlEvent("log", f"Pagination stop policy: stop a date slice after {no_new_pages_limit} consecutive page(s) with no new valid result links.")
    else:
        yield CrawlEvent("log", "Requests backend enabled: requests is synchronous, but it cannot execute JavaScript-rendered Google result pages.")

    backend_name = "Edge" if fetch_backend == "selenium_edge" else "Chrome"

    def start_selenium_driver(page_number: int | None = None):
        try:
            return create_selenium_driver(cfg)
        except Exception as exc:
            expected_driver = "tools/msedgedriver.exe" if fetch_backend == "selenium_edge" else "tools/chromedriver.exe"
            expected_binary = "msedge.exe" if fetch_backend == "selenium_edge" else "chrome.exe"
            page_hint = f" before page {page_number}" if page_number else ""
            raise BrowserStartupError(
                f"{exc}\n\nCould not start Selenium {backend_name}{page_hint}. The driver was found or attempted, but the browser executable may be missing or installed in a non-standard path. "
                f"Choose the browser program itself in Browser binary path, for example Chrome's chrome.exe or Edge's msedge.exe. "
                f"Driver path should point to {expected_driver}; browser binary path should point to {expected_binary}. "
                f"Also check browser/driver major-version compatibility and Windows security permissions."
            ) from exc

    def close_selenium_driver():
        nonlocal driver
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
            driver = None

    try:
        if use_browser:
            resolved_driver = resolve_driver_path(cfg, fetch_backend)
            resolved_binary = resolve_browser_binary_path(cfg, fetch_backend)
            if resolved_driver:
                yield CrawlEvent("log", f"Using local {backend_name} driver: {resolved_driver}")
            else:
                expected = "tools/msedgedriver.exe" if fetch_backend == "selenium_edge" else "tools/chromedriver.exe"
                yield CrawlEvent("log", f"No local {backend_name} driver found. Falling back to Selenium Manager. Expected local path: {expected}")
            if resolved_binary:
                yield CrawlEvent("log", f"Using {backend_name} browser binary: {resolved_binary}")
            else:
                yield CrawlEvent("log", f"No explicit/local {backend_name} browser binary found. Selenium will try the system default installation path.")
            # The browser is started lazily at the first page and restarted every N pages.
            # This reduces long-session fingerprint accumulation and makes page 5+ less likely
            # to inherit a browser state that triggers Google verification.
        else:
            headers = build_browser_headers(cfg.user_agent)
            session = requests.Session()
            session.headers.update(headers)
            try:
                session.get("https://www.google.com/", headers=build_browser_headers(cfg.user_agent), timeout=cfg.timeout_seconds)
            except Exception:
                pass

        date_slices = split_date_range(cfg.start_date, cfg.end_date, cfg.day_step)
        yield CrawlEvent("log", f"Total date slices: {len(date_slices)}")
        for slice_index, (shard_start, shard_end) in enumerate(date_slices, start=1):
            if stop_checker and stop_checker():
                raise StopCrawl()
            yield CrawlEvent(
                "slice",
                f"[{slice_index}/{len(date_slices)}] {shard_start} ~ {shard_end}",
                data={"slice_index": slice_index, "slice_total": len(date_slices)},
            )
            seen_page_signatures = set()
            consecutive_no_new_pages = 0
            for page_idx in range(cfg.max_pages):
                if stop_checker and stop_checker():
                    raise StopCrawl()
                page_stride = max(1, min(int(cfg.per_page or 10), 50)) if is_baidu_vertical(cfg.search_vertical) else 10
                start_offset = page_idx * page_stride
                page_number = page_idx + 1
                url = build_search_url(cfg, shard_start, shard_end, start_offset)
                yield CrawlEvent("log", f"Requesting page {page_number}: {url}")

                html_text = ""
                final_url = url

                if use_browser:
                    if driver is None:
                        driver = start_selenium_driver(page_number)
                        yield CrawlEvent("log", f"Selenium {backend_name} browser started for page {page_number}. Do not close the browser window while crawling.")
                    try:
                        html_text, final_url = fetch_html_with_selenium(driver, url, cfg, stop_checker)
                        yield CrawlEvent("log", f"Browser loaded page {page_number}. final_url={final_url}; html_len={len(html_text)}")
                    except Exception as exc:
                        raise NetworkAccessError(str(exc)) from exc
                    if looks_like_google_block_html(html_text, final_url):
                        debug_path = save_debug_html_if_needed(cfg, html_text, shard_start, shard_end, page_number)
                        yield CrawlEvent("blocked", f"Google block / verification page detected in browser backend. Debug HTML saved to: {debug_path}")
                        return
                else:
                    resp = None
                    page_headers = build_browser_headers(cfg.user_agent, referer=last_referer)
                    for attempt in range(cfg.max_retries + 1):
                        try:
                            resp = session.get(url, headers=page_headers, timeout=cfg.timeout_seconds)
                        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ProxyError, requests.exceptions.SSLError) as exc:
                            if attempt >= cfg.max_retries:
                                raise NetworkAccessError(str(exc)) from exc
                            yield CrawlEvent("log", f"Network error, retrying: {exc}")
                            sleep_random_ms(cfg.error_delay_min_ms, cfg.error_delay_max_ms, stop_checker)
                            continue
                        except requests.RequestException as exc:
                            if attempt >= cfg.max_retries:
                                raise NetworkAccessError(str(exc)) from exc
                            yield CrawlEvent("log", f"Request error, retrying: {exc}")
                            sleep_random_ms(cfg.error_delay_min_ms, cfg.error_delay_max_ms, stop_checker)
                            continue
                        if resp.status_code == 200:
                            break
                        if resp.status_code == 429:
                            retry_ms = get_retry_after_ms(resp)
                            if retry_ms is not None:
                                yield CrawlEvent("log", f"HTTP 429. Retry-After: {retry_ms} ms")
                                sleep_random_ms(retry_ms, retry_ms, stop_checker)
                            else:
                                yield CrawlEvent("log", "HTTP 429. Cooling down.")
                                sleep_random_ms(cfg.error_delay_min_ms, cfg.error_delay_max_ms, stop_checker)
                            continue
                        if attempt >= cfg.max_retries:
                            yield CrawlEvent("log", f"HTTP {resp.status_code}; stop current slice.")
                            break
                        yield CrawlEvent("log", f"HTTP {resp.status_code}; retrying.")
                        sleep_random_ms(cfg.error_delay_min_ms, cfg.error_delay_max_ms, stop_checker)
                    if resp is None or resp.status_code != 200:
                        break
                    last_referer = url
                    if looks_like_google_block_page(resp):
                        yield CrawlEvent("blocked", "Google block / unusual-traffic page detected. Stop task.")
                        return
                    if getattr(cfg, "post_fetch_wait_ms", 0) > 0:
                        yield CrawlEvent("log", f"Post-fetch wait before parsing: {cfg.post_fetch_wait_ms} ms")
                        sleep_random_ms(cfg.post_fetch_wait_ms, cfg.post_fetch_wait_ms, stop_checker)
                    html_text = resp.text

                page_records = extract_records_from_html(html_text, cfg, url, shard_start, shard_end, page_number)
                diag = diagnose_result_page(html_text) if not page_records else None

                empty_retry_count = int(getattr(cfg, "empty_page_retry_count", 0) or 0)
                empty_retry_wait_ms = int(getattr(cfg, "empty_page_retry_wait_ms", 0) or 0)
                retry_i = 0
                while not page_records and retry_i < empty_retry_count and should_retry_empty_result(diag or {}):
                    retry_i += 1
                    yield CrawlEvent(
                        "log",
                        f"No result cards parsed. Empty-page retry {retry_i}/{empty_retry_count} "
                        f"after {empty_retry_wait_ms} ms. Reason: {(diag or {}).get('reason', '')}"
                    )
                    if empty_retry_wait_ms > 0:
                        sleep_random_ms(empty_retry_wait_ms, empty_retry_wait_ms, stop_checker)
                    try:
                        if use_browser:
                            if driver is None:
                                driver = start_selenium_driver(page_number)
                                yield CrawlEvent("log", f"Selenium {backend_name} browser restarted for empty-page retry on page {page_number}.")
                            html_text, final_url = fetch_html_with_selenium(driver, url, cfg, stop_checker)
                        else:
                            retry_headers = build_browser_headers(cfg.user_agent, referer=last_referer)
                            resp = session.get(url, headers=retry_headers, timeout=cfg.timeout_seconds)
                            if resp.status_code != 200:
                                yield CrawlEvent("log", f"Empty-page retry returned HTTP {resp.status_code}.")
                                break
                            if looks_like_google_block_page(resp):
                                yield CrawlEvent("blocked", "Google block / unusual-traffic page detected during empty-page retry. Stop task.")
                                return
                            html_text = resp.text
                            if getattr(cfg, "post_fetch_wait_ms", 0) > 0:
                                sleep_random_ms(cfg.post_fetch_wait_ms, cfg.post_fetch_wait_ms, stop_checker)
                        page_records = extract_records_from_html(html_text, cfg, url, shard_start, shard_end, page_number)
                        diag = diagnose_result_page(html_text) if not page_records else None
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ProxyError, requests.exceptions.SSLError) as exc:
                        yield CrawlEvent("log", f"Empty-page retry network error: {exc}")
                        break
                    except Exception as exc:
                        yield CrawlEvent("log", f"Empty-page retry error: {exc}")
                        break

                if not page_records:
                    diag = diag or diagnose_result_page(html_text)
                    debug_path = save_debug_html_if_needed(cfg, html_text, shard_start, shard_end, page_number)
                    debug_msg = f" Debug HTML saved to: {debug_path}." if debug_path else ""
                    consecutive_no_new_pages += 1
                    yield CrawlEvent(
                        "log",
                        "No valid result records parsed on page "
                        f"{page_number}. Diagnostics: "
                        f"a.WlydOe={diag['a_WlydOe']}, YKoRaf={diag['a_YKoRaf']}, "
                        f"decoded_a.WlydOe={diag['decoded_a_WlydOe']}, decoded_YKoRaf={diag['decoded_a_YKoRaf']}, "
                        f"raw_WlydOe={diag['raw_WlydOe']}, raw_YKoRaf={diag['raw_YKoRaf']}, "
                        f"regex_news_cards={diag['regex_news_cards']}, "
                        f"UWckNb={diag['a_UWckNb']}, h3={diag['h3']}, "
                        f"/url?={diag['url_redirects']}, http_links={diag['http_anchors']}, "
                        f"html_len={diag['html_length']}. Reason: {diag['reason']}"
                        f"{debug_msg} Consecutive no-new pages: {consecutive_no_new_pages}/{no_new_pages_limit}."
                    )
                    if consecutive_no_new_pages >= no_new_pages_limit:
                        yield CrawlEvent("log", f"Stop current slice: {consecutive_no_new_pages} consecutive page(s) produced no new valid result links.")
                        break
                    if page_idx + 1 < cfg.max_pages:
                        sleep_random_ms(cfg.page_delay_min_ms, cfg.page_delay_max_ms, stop_checker)
                    continue

                signature = tuple(normalize_url_for_dedup(r.link) for r in page_records)
                if signature in seen_page_signatures:
                    yield CrawlEvent("log", "Repeated page detected. Stop current slice.")
                    break
                seen_page_signatures.add(signature)

                new_count = 0
                for rec in page_records:
                    key = normalize_url_for_dedup(rec.link)
                    if key in seen_global:
                        continue
                    seen_global.add(key)
                    new_count += 1
                    yield CrawlEvent("record", f"{rec.title}", record=rec)
                yield CrawlEvent("log", f"Page {page_number}: {len(page_records)} valid records, {new_count} new.")
                if new_count == 0:
                    consecutive_no_new_pages += 1
                    yield CrawlEvent("log", f"Page {page_number} added no new valid links after deduplication. Consecutive no-new pages: {consecutive_no_new_pages}/{no_new_pages_limit}.")
                    if consecutive_no_new_pages >= no_new_pages_limit:
                        yield CrawlEvent("log", f"Stop current slice: {consecutive_no_new_pages} consecutive page(s) produced no new valid result links.")
                        break
                else:
                    consecutive_no_new_pages = 0

                if page_idx + 1 < cfg.max_pages:
                    restart_due = bool(use_browser and selenium_pages_per_session > 0 and page_number % selenium_pages_per_session == 0)
                    if restart_due:
                        next_page = page_number + 1
                        yield CrawlEvent(
                            "checkpoint",
                            f"Checkpoint after page {page_number}: current results will be saved, Selenium will close and restart before page {next_page}.",
                            data={"slice_index": slice_index, "page_number": page_number, "next_page": next_page},
                        )
                        close_selenium_driver()
                        yield CrawlEvent("log", f"Selenium browser closed after page {page_number}; next request will start a fresh browser session at page {next_page}.")
                    sleep_random_ms(cfg.page_delay_min_ms, cfg.page_delay_max_ms, stop_checker)
            if slice_index < len(date_slices):
                if use_browser and driver is not None:
                    yield CrawlEvent("checkpoint", f"Checkpoint after date slice {slice_index}: current results will be saved before the next date slice.", data={"slice_index": slice_index})
                    close_selenium_driver()
                    yield CrawlEvent("log", "Selenium browser closed between date slices; next slice will start a fresh browser session.")
                sleep_random_ms(cfg.slice_delay_min_ms, cfg.slice_delay_max_ms, stop_checker)
        yield CrawlEvent("done", "Crawl finished.")
    finally:
        if use_browser and driver is not None:
            try:
                driver.quit()
                yield CrawlEvent("log", "Selenium browser closed.")
            except Exception:
                pass
