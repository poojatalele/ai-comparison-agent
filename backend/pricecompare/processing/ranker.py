"""`Ranker` — dedupes per retailer, sorts cheapest-first, annotates each offer.

After this step every offer carries `is_cheapest`, and the list is trimmed to
a clean, scannable size.
"""

from __future__ import annotations

from ..models import Offer, ProductQuery
from .base import OfferProcessor


class Ranker(OfferProcessor):
    """Keeps the cheapest offer per store, sorts by price, caps the list."""

    def __init__(self, max_results: int = 15) -> None:
        self._max_results = max_results

    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        ranked = self._dedupe_cheapest_per_store(offers)
        ranked.sort(key=lambda o: o.price)

        for index, offer in enumerate(ranked):
            offer.is_cheapest = index == 0          # list is price-sorted

        return ranked[: self._max_results]

    @staticmethod
    def _dedupe_cheapest_per_store(offers: list[Offer]) -> list[Offer]:
        cheapest: dict[str, Offer] = {}
        for offer in offers:
            key = offer.platform.lower()
            if key not in cheapest or offer.price < cheapest[key].price:
                cheapest[key] = offer
        return list(cheapest.values())
