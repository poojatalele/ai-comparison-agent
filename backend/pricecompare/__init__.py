"""pricecompare — an extensible price-comparison agent core.

A framework-agnostic package: it knows nothing about HTTP, FastAPI, or how it
is hosted. Drive it through `PriceComparisonService`.
"""

from __future__ import annotations

from .config import Settings
from .errors import PriceCompareError, ProviderError, ResolutionError
from .models import ComparisonResult, Offer, OriginListing, ProductQuery, RewardSummary
from .service import PriceComparisonService

__all__ = [
    "Settings",
    "PriceCompareError",
    "ProviderError",
    "ResolutionError",
    "ComparisonResult",
    "Offer",
    "OriginListing",
    "ProductQuery",
    "RewardSummary",
    "PriceComparisonService",
]
