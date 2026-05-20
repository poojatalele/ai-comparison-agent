"""`OriginScraper` — inspects the URL the user pasted.

It identifies the *origin*: the store the user came from and, best-effort, the
price shown there. This powers the "you came from here" anchor.

Price extraction prefers JSON-LD `Product.offers.price` (the SEO standard,
reliably the *display* price) and falls back to Open Graph price meta tags.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator

import httpx

from .models import OriginListing
from .retailers import RetailerDirectory
from .web import BROWSER_HEADERS, domain_from_url, favicon_url

_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.I)
_PRICE_META_RE = re.compile(
    r'(?:property|name)=["\'](?:og:price:amount|product:price:amount)["\']', re.I
)
_META_CONTENT_RE = re.compile(r'content=["\']([\d,]+\.?\d*)["\']', re.I)


def _parse_price(raw: object) -> float | None:
    try:
        value = float(str(raw).replace(",", "").strip())
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _iter_offers(data: object) -> Iterator[dict]:
    """Yield every `offers` dict found anywhere in a JSON-LD structure."""
    stack: list[object] = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            offers = node.get("offers")
            if isinstance(offers, dict):
                yield offers
            elif isinstance(offers, list):
                yield from (o for o in offers if isinstance(o, dict))
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))


def _price_from_jsonld(page: str) -> float | None:
    """The most reliable source: JSON-LD `Product.offers.price`."""
    for raw in _JSONLD_RE.findall(page):
        try:
            data = json.loads(raw.strip())
        except (ValueError, TypeError):
            continue
        for offers in _iter_offers(data):
            price = _parse_price(offers.get("price") or offers.get("lowPrice"))
            if price is not None:
                return price
    return None


def _price_from_meta(page: str) -> float | None:
    """Fallback: an Open Graph / product price meta tag (attribute-order safe)."""
    for tag in _META_TAG_RE.findall(page):
        if _PRICE_META_RE.search(tag):
            content = _META_CONTENT_RE.search(tag)
            if content:
                return _parse_price(content.group(1))
    return None


class OriginScraper:
    """Resolves a pasted URL into an `OriginListing` (store name + price)."""

    def __init__(self, directory: RetailerDirectory, timeout: float = 9.0) -> None:
        self._directory = directory
        self._timeout = timeout

    async def inspect(self, url: str) -> OriginListing | None:
        """Return the origin store/price for a URL (price may be `None`)."""
        domain = domain_from_url(url)
        if not domain:
            return None
        return OriginListing(
            store=self._store_name(domain),
            url=url,
            price=await self._extract_price(url),
            logo_url=favicon_url(domain),
        )

    def _store_name(self, domain: str) -> str:
        retailer = self._directory.match(domain)
        if retailer is not None:
            return retailer.canonical
        label = domain.split(".")[0]
        return label[:1].upper() + label[1:]

    async def _extract_price(self, url: str) -> float | None:
        """Best-effort price scrape: JSON-LD first, then price meta tags."""
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, follow_redirects=True, headers=BROWSER_HEADERS
            ) as client:
                resp = await client.get(url)
            page = resp.text
        except Exception:
            return None

        return _price_from_jsonld(page) or _price_from_meta(page)
