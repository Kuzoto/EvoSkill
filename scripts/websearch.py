#!/usr/bin/env python3
"""Keyless web search via DuckDuckGo HTML lite. No API keys required.

Usage:
    python3 scripts/websearch.py "your search query" [--max N]

Returns JSON array of {title, url, snippet} results to stdout.
"""

import argparse
import json
import sys
import urllib.parse

import httpx
from bs4 import BeautifulSoup

_DDG_URL = "https://html.duckduckgo.com/html/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
}


def search(query: str, max_results: int = 8) -> list[dict]:
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


def main():
    parser = argparse.ArgumentParser(description="DuckDuckGo web search (no API key)")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=8, help="Max results (default: 8)")
    args = parser.parse_args()

    results = search(args.query, max_results=args.max)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
