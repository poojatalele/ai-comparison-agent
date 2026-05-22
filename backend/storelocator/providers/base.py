"""The `StoreLocator` abstraction — a source of brand outlet locations.

The rest of the core depends only on this interface (Dependency Inversion), so
a new outlet data source is one new class with zero changes elsewhere.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..brands import Brand
from ..models import GeoPoint, StoreLocation


class StoreLocator(ABC):
    """Interface for finding a brand's outlets and geocoding a city."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier for this locator (used as the `data_source`)."""
        raise NotImplementedError

    @abstractmethod
    async def find_stores(self, brand: Brand, city: str) -> list[StoreLocation]:
        """Return the brand's outlets in `city`. Raise `LocatorError` on failure."""
        raise NotImplementedError

    @abstractmethod
    async def geocode_city(self, city: str) -> GeoPoint | None:
        """Return the city's centre coordinate (used for the no-GPS fallback)."""
        raise NotImplementedError
