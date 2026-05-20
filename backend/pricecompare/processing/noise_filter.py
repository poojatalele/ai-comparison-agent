"""`NoiseFilter` — drops listings that aren't really the product.

Query-based shopping search is noisy: a search for "iPhone 15" pulls in phone
*cases*, refurbished units, and the odd bundle. This step removes accessories,
refurbished/used items, and price outliers so the comparison stays
apples-to-apples.
"""

from __future__ import annotations

import re

from ..models import Offer, ProductQuery
from .base import OfferProcessor

_ACCESSORY_RE = re.compile(
    r"\b(case|cover|covers|pouch|sleeve|skin|protector|tempered|screen[ -]?guard|"
    r"cable|charger|adapter|adaptor|holder|stand|mount|strap|grip|bumper|"
    r"flip cover|back cover|tempered glass)\b",
    re.I,
)
_REFURB_RE = re.compile(
    r"\b(refurbished|renewed|pre[ -]?owned|second[ -]?hand|open[ -]?box|"
    r"\bused\b|\brefurb\b)\b",
    re.I,
)


class NoiseFilter(OfferProcessor):
    """Removes accessories, refurbished units, and price outliers."""

    def __init__(self, outlier_low: float = 0.5, outlier_high: float = 2.2) -> None:
        self._outlier_low = outlier_low
        self._outlier_high = outlier_high

    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        query_is_accessory = bool(_ACCESSORY_RE.search(query.text))

        kept = []
        for offer in offers:
            title = offer.title or ""
            if _REFURB_RE.search(title):
                continue
            if not query_is_accessory and _ACCESSORY_RE.search(title):
                continue
            kept.append(offer)

        # If the keyword filters were too aggressive, keep the originals.
        if len(kept) < 3:
            kept = list(offers)

        return self._drop_price_outliers(kept)

    def _drop_price_outliers(self, offers: list[Offer]) -> list[Offer]:
        """Keep listings within a sane band around the median price."""
        if len(offers) < 4:
            return offers

        prices = sorted(o.price for o in offers)
        median = prices[len(prices) // 2]
        low, high = median * self._outlier_low, median * self._outlier_high

        within = [o for o in offers if low <= o.price <= high]
        return within if len(within) >= 3 else offers
