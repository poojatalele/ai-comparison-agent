"""The `PriceProvider` abstraction.

A price provider is any source of retailer offers for a product. The rest of
the core depends only on this interface (Dependency Inversion), so adding a new
data source — a different aggregator, a direct scraper — means writing one new
class, with zero changes elsewhere.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models import Offer


@dataclass(frozen=True)
class ProviderResult:
    """Offers returned by a provider, tagged with which provider produced them."""

    offers: list[Offer]
    source: str          # e.g. "serpapi", "mock"


class PriceProvider(ABC):
    """Interface for a source of retailer offers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier for this provider (used as the `data_source`)."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str) -> ProviderResult:
        """Return offers for `query`. Raise `ProviderError` on failure."""
        raise NotImplementedError
