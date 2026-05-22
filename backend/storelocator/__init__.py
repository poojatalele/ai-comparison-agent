"""storelocator — find a brand's physical outlets near a user.

A self-contained domain package: it knows nothing about HTTP or FastAPI. Drive
it through `StoreLocatorService`. Mirrors the hexagonal style of `pricecompare`.
"""

from __future__ import annotations

from .brands import Brand, BrandDirectory
from .config import StoreLocatorSettings
from .errors import BrandNotSupportedError, LocatorError, StoreLocatorError
from .models import GeoPoint, StoreLocation, StoreLocatorResult
from .service import StoreLocatorService

__all__ = [
    "Brand",
    "BrandDirectory",
    "StoreLocatorSettings",
    "StoreLocatorError",
    "BrandNotSupportedError",
    "LocatorError",
    "GeoPoint",
    "StoreLocation",
    "StoreLocatorResult",
    "StoreLocatorService",
]
