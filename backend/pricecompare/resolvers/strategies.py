"""Concrete `ProductResolver` strategies.

Three ways to obtain a searchable product name:

* `PlainTextResolver` — the user typed a name directly.
* `UrlSlugResolver`   — derive the name from a pasted URL's path slug (fast).
* `PageTitleResolver` — fetch the pasted page and read its <title> (accurate).

Each is independently testable and can be reordered or swapped without touching
the others (Open/Closed).
"""

from __future__ import annotations

import html as _html
import re
import urllib.parse

import httpx

from ..models import ProductQuery, ResolvedVia
from ..web import BROWSER_HEADERS
from .base import ProductResolver, is_url


class PlainTextResolver(ProductResolver):
    """Handles anything that is *not* a URL — i.e. a typed product name."""

    async def resolve(self, raw_input: str) -> ProductQuery | None:
        raw = raw_input.strip()
        if is_url(raw):
            return None
        return ProductQuery(text=raw, resolved_via=ResolvedVia.SEARCH_TERM)


class UrlSlugResolver(ProductResolver):
    """Extracts a product name from the URL path (Amazon/Flipkart-style slugs).

    Only accepts the slug when it has at least `min_words` words — so it can be
    used twice in a chain: strict first (skip the slow page fetch when the slug
    is already good), then lenient as a last-resort fallback.
    """

    def __init__(self, min_words: int = 3) -> None:
        self._min_words = min_words

    async def resolve(self, raw_input: str) -> ProductQuery | None:
        raw = raw_input.strip()
        if not is_url(raw):
            return None
        slug = self._slug_from_url(raw)
        if slug and len(slug) > 4 and len(slug.split()) >= self._min_words:
            return ProductQuery(
                text=slug, resolved_via=ResolvedVia.URL_SLUG, source_url=raw
            )
        return None

    @staticmethod
    def _humanize(slug: str) -> str:
        s = re.sub(r"\.(html?|aspx?|php)$", "", slug, flags=re.I)
        s = urllib.parse.unquote(s)
        s = re.sub(r"[-_+]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()[:160]

    @classmethod
    def _slug_from_url(cls, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError:
            return ""
        segments = [s for s in parsed.path.split("/") if s]

        # Amazon ".../<slug>/dp/<ASIN>", Flipkart ".../<slug>/p/<id>", etc.
        for marker in ("dp", "p", "product", "pd", "buy"):
            if marker in segments:
                i = segments.index(marker)
                if i > 0 and not re.fullmatch(r"[A-Z0-9]{8,14}", segments[i - 1]):
                    return cls._humanize(segments[i - 1])

        # Otherwise: the longest path segment that is not an opaque id.
        candidates = [
            s for s in segments
            if len(s) > 3 and not re.fullmatch(r"[A-Za-z0-9]{8,}", s)
        ]
        if candidates:
            return cls._humanize(max(candidates, key=len))

        # Last resort: a search query parameter on the URL.
        params = urllib.parse.parse_qs(parsed.query)
        for key in ("q", "query", "k", "search"):
            if params.get(key):
                return params[key][0][:160]
        return ""


class PageTitleResolver(ProductResolver):
    """Fetches the pasted page and reads its og:title / twitter:title / <title>."""

    def __init__(self, timeout: float = 9.0) -> None:
        self._timeout = timeout

    async def resolve(self, raw_input: str) -> ProductQuery | None:
        raw = raw_input.strip()
        if not is_url(raw):
            return None
        title = await self._fetch_title(raw)
        if not title:
            return None
        return ProductQuery(
            text=self._clean_title(title),
            resolved_via=ResolvedVia.PAGE_TITLE,
            source_url=raw,
        )

    async def _fetch_title(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, follow_redirects=True, headers=BROWSER_HEADERS
            ) as client:
                resp = await client.get(url)
            page = resp.text
        except Exception:
            return ""

        patterns = (
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
            r"<title[^>]*>([^<]+)</title>",
        )
        for pattern in patterns:
            match = re.search(pattern, page, re.I | re.S)
            if match:
                title = _html.unescape(match.group(1)).strip()
                low = title.lower()
                if len(title) > 3 and "robot" not in low and "are you a human" not in low:
                    return title
        return ""

    @staticmethod
    def _clean_title(title: str) -> str:
        """Strip marketplace boilerplate (" - Amazon.in", " | Flipkart", ...)."""
        text = re.sub(r"\s+", " ", _html.unescape(title or "")).strip()
        for sep in (" | ", " : ", " - ", " – "):
            if sep in text:
                head, tail = text.split(sep, 1)
                if re.search(
                    r"amazon|flipkart|croma|myntra|ajio|reliance|tata cliq|"
                    r"snapdeal|buy online|best price|shopsy|jiomart",
                    tail, re.I,
                ):
                    text = head
        text = re.sub(r"^(buy|shop)\s+", "", text, flags=re.I)
        return text.strip()[:160]
