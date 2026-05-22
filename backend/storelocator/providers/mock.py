"""`MockStoreLocator` — deterministic demo outlets, no API key required.

Lets the whole feature run end-to-end offline. Outlets are derived from a hash
of brand + city, so the same query always yields the same stores.
"""

from __future__ import annotations

import hashlib

from ..brands import Brand
from ..models import GeoPoint, StoreLocation
from .base import StoreLocator

# Approximate centres of major Indian cities — for placing demo outlets.
_CITY_CENTRES: dict[str, GeoPoint] = {
    "mumbai": GeoPoint(19.0760, 72.8777),
    "delhi": GeoPoint(28.6139, 77.2090),
    "new delhi": GeoPoint(28.6139, 77.2090),
    "bengaluru": GeoPoint(12.9716, 77.5946),
    "bangalore": GeoPoint(12.9716, 77.5946),
    "hyderabad": GeoPoint(17.3850, 78.4867),
    "chennai": GeoPoint(13.0827, 80.2707),
    "kolkata": GeoPoint(22.5726, 88.3639),
    "pune": GeoPoint(18.5204, 73.8567),
    "ahmedabad": GeoPoint(23.0225, 72.5714),
    "jaipur": GeoPoint(26.9124, 75.7873),
}
_DEFAULT_CENTRE = GeoPoint(19.0760, 72.8777)  # Mumbai

_AREAS = (
    "Phoenix Mall", "MG Road", "High Street", "City Centre Mall", "Forum Mall",
    "Central Plaza", "Linking Road", "Brigade Road", "Sector 18", "Galleria Market",
)


class MockStoreLocator(StoreLocator):
    """Generates plausible, deterministic outlets for any brand + city."""

    @property
    def name(self) -> str:
        return "mock"

    async def find_stores(self, brand: Brand, city: str) -> list[StoreLocation]:
        centre = self._centre(city)
        seed = int(
            hashlib.md5(f"{brand.name}|{city}".lower().encode()).hexdigest(), 16
        )
        count = 4 + (seed % 4)  # 4–7 outlets

        stores: list[StoreLocation] = []
        for i in range(count):
            s = seed >> (i * 7)
            # spread outlets within ~±7 km of the city centre
            dlat = ((s % 1400) - 700) / 10000.0
            dlng = (((s >> 11) % 1400) - 700) / 10000.0
            area = _AREAS[(s >> 5) % len(_AREAS)]
            stores.append(
                StoreLocation(
                    brand=brand.name,
                    name=brand.name,
                    address=f"{brand.name}, {area}, {city.title()}",
                    location=GeoPoint(
                        lat=round(centre.lat + dlat, 6),
                        lng=round(centre.lng + dlng, 6),
                    ),
                    place_id=f"mock-{seed % 10**9}-{i}",
                    rating=round(3.7 + ((s >> 3) % 12) / 10.0, 1),  # 3.7–4.8
                    open_now=bool((s >> 2) & 1),
                )
            )
        return stores

    async def geocode_city(self, city: str) -> GeoPoint:
        return self._centre(city)

    @staticmethod
    def _centre(city: str) -> GeoPoint:
        return _CITY_CENTRES.get((city or "").strip().lower(), _DEFAULT_CENTRE)
