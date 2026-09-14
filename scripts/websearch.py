#!/usr/bin/env python3
"""Web search for the agent, with a read-through disk cache.

Usage:
    python3 scripts/websearch.py "your search query" [--max N]

Returns a JSON array of {title, url, snippet} to stdout — unchanged from the
original keyless version, so anything already calling this keeps working.

Two providers, tried in order:
  1. Serper.dev (Google) when SERPER_API_KEY is set — reliable, no scraping.
  2. DuckDuckGo HTML lite — keyless fallback, rate-limits under load.

Why the cache: an EvoSkill run issues the same handful of queries over and over
(every iteration re-evaluates the same validation questions), and live web
results drift between runs. Without caching, a baseline and a fine-tuned model
are effectively graded on different evidence, which makes small score
differences meaningless. The cache both collapses repeat queries and freezes the
web so runs stay comparable. Failures and empty result sets are never cached, so
a transient error cannot become permanent.

Env:
  SERPER_API_KEY            enables the Serper provider
  EVOSKILL_WEBSEARCH_CACHE  cache directory (default: <repo>/.cache/websearch;
                            set to "" to disable caching)
  EVOSKILL_WEBSEARCH_TTL    seconds before a cache entry is refetched (default: 0 = never)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import httpx

_DDG_URL = "https://html.duckduckgo.com/html/"
_SERPER_URL = "https://google.serper.dev/search"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
}


# ── cache ────────────────────────────────────────────────────────────────────

def _cache_dir() -> Path | None:
    raw = os.environ.get("EVOSKILL_WEBSEARCH_CACHE")
    if raw is None:
        raw = str(Path(__file__).resolve().parent.parent / ".cache" / "websearch")
    raw = raw.strip()
    return Path(raw) if raw else None


def _cache_path(query: str, max_results: int, provider: str) -> Path | None:
    d = _cache_dir()
    if d is None:
        return None
    key = hashlib.sha256(
        f"{provider}|{query.strip().lower()}|{max_results}".encode("utf-8")
    ).hexdigest()[:32]
    return d / f"{key}.json"


def _cache_get(path: Path | None) -> list[dict] | None:
    if path is None or not path.is_file():
        return None
    try:
        entry = json.loads(path.read_text())
        ttl = float(os.environ.get("EVOSKILL_WEBSEARCH_TTL", "0") or 0)
        if ttl > 0 and time.time() - float(entry.get("ts", 0)) > ttl:
            return None
        results = entry.get("results")
        return results if isinstance(results, list) and results else None
    except Exception:
        return None


def _cache_put(path: Path | None, query: str, provider: str, results: list[dict]) -> None:
    # Never cache an empty result set — it is usually a rate limit or a parse
    # failure, and freezing it in would poison every later run.
    if path is None or not results:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(
            {"query": query, "provider": provider, "ts": time.time(), "results": results},
            ensure_ascii=False,
        ))
        os.replace(tmp, path)  # atomic; many agents share this dir
    except Exception:
        pass


# ── providers ────────────────────────────────────────────────────────────────

def search_serper(query: str, max_results: int, api_key: str) -> list[dict]:
    resp = httpx.post(
        _SERPER_URL,
        json={"q": query, "num": max_results},
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()

    results: list[dict] = []
    ab = payload.get("answerBox") or {}
    if ab.get("answer") or ab.get("snippet"):
        results.append({
            "title": ab.get("title", "Answer box"),
            "url": ab.get("link", ""),
            "snippet": ab.get("answer") or ab.get("snippet", ""),
        })
    for item in payload.get("organic") or []:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
        if len(results) >= max_results:
            break
    return results[:max_results]


def search_ddg(query: str, max_results: int) -> list[dict]:
    from bs4 import BeautifulSoup

    resp = httpx.post(
        _DDG_URL,
        data={"q": query, "b": "", "kl": ""},
        headers=_HEADERS,
        timeout=15,
        follow_redirects=True,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select(".result"):
        title_el = item.select_one(".result__a")
        snippet_el = item.select_one(".result__snippet")
        if not title_el:
            continue

        href = title_el.get("href", "")
        if "duckduckgo.com/y.js" in href or "uddg=" in href:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            href = parsed.get("uddg", [href])[0]

        results.append({
            "title": title_el.get_text(strip=True),
            "url": href,
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
        })
        if len(results) >= max_results:
            break

    return results


def search(query: str, max_results: int = 8) -> list[dict]:
    """Cached search: Serper when configured, else DuckDuckGo."""
    api_key = (os.environ.get("SERPER_API_KEY") or "").strip()
    provider = "serper" if api_key else "ddg"

    path = _cache_path(query, max_results, provider)
    cached = _cache_get(path)
    if cached is not None:
        return cached

    errors = []
    if api_key:
        try:
            results = search_serper(query, max_results, api_key)
            if results:
                _cache_put(path, query, "serper", results)
                return results
            errors.append("serper returned no results")
        except Exception as e:
            errors.append(f"serper: {type(e).__name__}: {e}")

    try:
        results = search_ddg(query, max_results)
        if results:
            _cache_put(path, query, "ddg", results)
        return results
    except Exception as e:
        errors.append(f"ddg: {type(e).__name__}: {e}")
        print(f"[websearch] all providers failed: {'; '.join(errors)}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="Web search (Serper when configured, else DuckDuckGo)")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=8, help="Max results (default: 8)")
    args = parser.parse_args()

    results = search(args.query, max_results=args.max)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
