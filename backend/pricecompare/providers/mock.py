"""`MockPriceProvider` — deterministic demo data, no API key required.

Lets the whole flow run end-to-end offline. Prices are derived from a hash of
the query, so the same search always yields the same (stable) results.
"""

from __future__ import annotations

import hashlib
import urllib.parse

from ..models import Offer
from .base import PriceProvider, ProviderResult

# (store name, rating, delivery copy) for the synthetic dataset.
_DEMO_STORES = (
    ("Amazon.in", 4.4, "FREE delivery by tomorrow"),
    ("Flipkart", 4.3, "Delivery in 2-3 days"),
    ("Croma", 4.1, "Delivery in 3-5 days"),
    ("Reliance Digital", 4.2, "Free delivery"),
    ("Tata CLiQ", 4.0, "Delivery in 4-6 days"),
    ("Vijay Sales", 3.9, "Delivery in 3-5 days"),
)


class MockPriceProvider(PriceProvider):
    """Generates plausible, deterministic offers for any query."""

    @property
    def name(self) -> str:
        return "mock"

    async def search(self, query: str) -> ProviderResult:
        seed = int(hashlib.md5(query.lower().encode()).hexdigest(), 16)
        base = 2000 + (seed % 90000)          # ₹2,000 – ₹92,000

        offers = []
        for i, (store, rating, delivery) in enumerate(_DEMO_STORES):
            spread = ((seed >> (i * 5)) % 22) - 8      # -8% .. +13%
            price = round(base * (1 + spread / 100.0) / 10) * 10
            offers.append(
                Offer(
                    platform=store,
                    title=query,
                    price=float(price),
                    url="https://www.google.com/search?q="
                        + urllib.parse.quote(f"{query} {store}"),
                    thumbnail=None,
                    rating=rating,
                    reviews=200 + (seed >> i) % 9000,
                    delivery=delivery,
                )
            )
        return ProviderResult(offers=offers, source=self.name)
