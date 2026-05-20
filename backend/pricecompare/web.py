"""Shared HTTP helpers for outbound requests.

A single source of truth for the browser-like headers used when fetching
product pages and partner APIs, plus small URL/logo utilities.
"""

from __future__ import annotations

import urllib.parse

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def domain_from_url(url: str) -> str:
    """Return the bare host of a URL ('www.' stripped), or '' if unparseable."""
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def favicon_url(domain: str) -> str | None:
    """A small logo URL for a domain, via Google's public favicon service."""
    if not domain:
        return None
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
