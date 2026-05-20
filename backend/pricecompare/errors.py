"""Domain-level exception hierarchy.

Keeping these separate from the web layer means the core never raises
HTTP-specific errors; the server layer translates them into status codes.
"""

from __future__ import annotations


class PriceCompareError(Exception):
    """Base class for every error raised by the price-comparison core."""


class ResolutionError(PriceCompareError):
    """Raised when the user input cannot be turned into a product query.

    Maps to an HTTP 422 — the request was understood but unusable.
    """


class ProviderError(PriceCompareError):
    """Raised when a price provider fails (network, auth, or bad response).

    Maps to an HTTP 502 — an upstream dependency let us down.
    """
