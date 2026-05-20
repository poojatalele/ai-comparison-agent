"""`StoreNormalizer` — canonicalizes retailer names and tiers them by trust.

Search results name the same store many different ways ("Purplle.com – Beauty
Online", "Purplle.com – Purplle Shopping", ...). This step collapses them to
one canonical name *before* `Ranker` dedupes — which is what fixes duplicate
rows. It also tags each offer as a recommended (known) retailer or an "other"
store, and attaches a logo.
"""

from __future__ import annotations

import re

from ..models import Offer, ProductQuery
from ..retailers import RetailerDirectory
from ..web import domain_from_url, favicon_url
from .base import OfferProcessor

# Matches a leading "brand.tld" so domain-style names become a plain label.
_TLD_RE = re.compile(
    r"^(?:www\.)?([a-z0-9][a-z0-9-]*)\.(?:com|in|co\.in|net|org|shop|store|app)\b",
    re.I,
)
_SUFFIX_SEPARATORS = (" – ", " — ", " - ", " | ", " · ")


def _clean_unknown_name(raw: str) -> str:
    """Tidy an unknown store's name: drop storefront suffixes, de-domain it."""
    name = (raw or "Store").strip()
    for separator in _SUFFIX_SEPARATORS:
        if separator in name:
            name = name.split(separator, 1)[0].strip()
    match = _TLD_RE.match(name)
    if match:
        label = match.group(1)
        return label[:1].upper() + label[1:]
    return name


class StoreNormalizer(OfferProcessor):
    """Sets a canonical store name, trust tier, and logo on every offer."""

    def __init__(self, directory: RetailerDirectory) -> None:
        self._directory = directory

    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        for offer in offers:
            retailer = self._directory.match(offer.platform)
            if retailer is not None:
                # A known retailer — canonical name, trusted, known-domain logo.
                offer.platform = retailer.canonical
                offer.is_recommended = True
                offer.logo_url = favicon_url(retailer.domain)
            else:
                # An unknown store — tidy the name, demote it, logo from its URL.
                offer.platform = _clean_unknown_name(offer.platform)
                offer.is_recommended = False
                offer.logo_url = favicon_url(domain_from_url(offer.url))
        return offers
