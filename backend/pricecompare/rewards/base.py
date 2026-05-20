"""The `RewardsProvider` abstraction and the `RewardCatalog` value object.

`RewardCatalog` owns the (slightly fuzzy) logic of matching a retailer name to
a partner brand — keeping that knowledge in one place. `RewardsProvider` is the
interface for *where* the catalog comes from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RewardCatalog:
    """Maps reward-partner brand names to their cashback percentage."""

    rates: dict[str, float]

    def rate_for(self, store_name: str) -> float | None:
        """Cashback % for a retailer, or `None` if it is not a partner.

        Matching is fuzzy on purpose: a Google Shopping `source` like
        "luxe.ajio.com" or "Amazon.in" must still match "ajio" / "amazon india".
        """
        haystack = store_name.lower()
        for name, pct in self.rates.items():
            brand = name.replace(" india", "").strip()
            if brand and brand in haystack:
                return pct
        return None

    def points_for(self, store_name: str, price: float | None) -> int:
        """Reward points earned at a store for a price (≈ rupee value of cashback)."""
        rate = self.rate_for(store_name)
        if rate is None or not price or price <= 0:
            return 0
        return max(0, round(price * rate / 100.0))


class RewardsProvider(ABC):
    """Interface for a source of reward-partner cashback rates."""

    @abstractmethod
    async def get_catalog(self) -> RewardCatalog:
        """Return the current `RewardCatalog` (implementations may cache it)."""
        raise NotImplementedError
