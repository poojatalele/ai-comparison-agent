"""`StoreLocatorService` — orchestrates a brand + city outlet lookup.

It validates the brand, asks a `StoreLocator` for outlets, works out the
reference point (the user's GPS, or the city centre), and ranks the outlets by
straight-line distance. It owns no I/O logic — collaborators are injected.
"""

from __future__ import annotations

from .brands import BrandDirectory
from .geo import haversine_km
from .models import GeoPoint, StoreLocation, StoreLocatorResult
from .providers import StoreLocator


class StoreLocatorService:
    """Coordinates brand validation, outlet lookup, and distance ranking."""

    def __init__(self, locator: StoreLocator, brands: BrandDirectory) -> None:
        self._locator = locator
        self._brands = brands

    def brand_names(self) -> list[str]:
        """The supported brand list (for the UI dropdown)."""
        return self._brands.names()

    async def find(
        self, brand_raw: str, city: str, user_point: GeoPoint | None
    ) -> StoreLocatorResult:
        """Find a brand's outlets in a city, ranked nearest-first.

        Raises `BrandNotSupportedError` for an unknown brand and `LocatorError`
        if the places provider fails.
        """
        brand = self._brands.resolve(brand_raw)        # -> BrandNotSupportedError
        city = (city or "").strip()

        stores = await self._locator.find_stores(brand, city)
        reference, source = await self._reference_point(city, user_point, stores)

        for store in stores:
            store.distance_km = round(haversine_km(reference, store.location), 1)
        stores.sort(key=lambda s: s.distance_km if s.distance_km is not None else 1e9)

        return StoreLocatorResult(
            brand=brand.name,
            city=city,
            earn_rate=brand.earn_rate,
            reference=reference,
            reference_source=source,
            stores=stores,
            data_source=self._locator.name,
        )

    async def _reference_point(
        self, city: str, user_point: GeoPoint | None, stores: list[StoreLocation]
    ) -> tuple[GeoPoint, str]:
        """The point distances are measured from: the user's GPS, else the city
        centre, else the first store (so the ranking still works)."""
        if user_point is not None:
            return user_point, "gps"
        centre = await self._locator.geocode_city(city)
        if centre is not None:
            return centre, "city-centre"
        if stores:
            return stores[0].location, "city-centre"
        return GeoPoint(0.0, 0.0), "city-centre"
