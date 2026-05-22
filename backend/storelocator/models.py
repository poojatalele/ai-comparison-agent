"""Domain models for the store-locator feature.

Plain dataclasses, no behaviour, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    """A latitude/longitude coordinate."""

    lat: float
    lng: float


@dataclass
class StoreLocation:
    """One physical outlet of a brand.

    A `StoreLocator` fills the first block of fields; `distance_km` is filled by
    `StoreLocatorService` once the reference point (the user, or the city
    centre) is known.
    """

    brand: str
    name: str
    address: str
    location: GeoPoint
    place_id: str
    rating: float | None = None
    open_now: bool | None = None
    distance_km: float | None = None


@dataclass(frozen=True)
class StoreLocatorResult:
    """The outcome of one brand + city lookup."""

    brand: str
    city: str
    earn_rate: float             # onpoints % earned with this brand
    reference: GeoPoint          # the point distances were measured from
    reference_source: str        # "gps" | "city-centre"
    stores: list[StoreLocation]  # ranked nearest-first
    data_source: str             # "google" | "mock"
