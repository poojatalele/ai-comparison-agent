"""Domain errors for the store-locator feature.

Kept HTTP-agnostic — the server layer maps them to status codes.
"""

from __future__ import annotations


class StoreLocatorError(Exception):
    """Base class for every store-locator error."""


class BrandNotSupportedError(StoreLocatorError):
    """The requested brand is not in the supported list. Maps to HTTP 422."""


class LocatorError(StoreLocatorError):
    """The places provider failed — network, auth, or bad response. HTTP 502."""
