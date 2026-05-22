"""The supported-brand directory.

The feature is intentionally scoped to a fixed brand list. The directory
validates user input against it and resolves loose spellings to a canonical
brand — so "mcdonalds", "McDonald's" and "Mc Donalds" all map to "McDonalds".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import BrandNotSupportedError


@dataclass(frozen=True)
class Brand:
    """A supported brand: display name, places-search query, and onpoints rate."""

    name: str            # canonical display name
    search_query: str    # what to send to the places API (city is appended)
    earn_rate: float     # onpoints earn %, from OnPoint's gift-card catalogue


def _b(name: str, earn_rate: float, search_query: str | None = None) -> Brand:
    return Brand(name=name, earn_rate=earn_rate, search_query=search_query or name)


# The fixed, supported brand list. `earn_rate` is the onpoints % from OnPoint's
# gift-card catalogue; brands absent from that catalogue carry an estimated rate.
_BRANDS: tuple[Brand, ...] = (
    _b("Starbucks", 10.0),
    _b("KFC", 4.8),
    _b("McDonalds", 11.2, "McDonald's"),
    _b("Pizza Hut", 7.2),
    _b("Decathlon", 6.4),                        # estimated
    _b("Tanishq", 2.0),
    _b("Bhima Jewellery", 2.4),
    _b("PC Jeweller", 4.0),
    _b("Lifestyle", 4.0, "Lifestyle Stores"),    # disambiguate the generic word
    _b("Max Fashion", 6.4),
    _b("V-Mart", 3.6),                           # estimated
    _b("Vijay Sales", 5.2),                      # estimated
    _b("Manyavar", 7.6),                         # estimated
    _b("Marriott Hotels", 6.4),
    _b("The Leela", 8.8),
    _b("Titan Eye Plus", 5.6),
    _b("Hush Puppies", 7.0),
    _b("Forever New", 7.2),
    _b("Armani Exchange", 11.2),
    _b("Superdry", 11.2),
    _b("Tumi", 11.2),
    _b("Absolute Barbecues", 7.2),
    _b("Himalaya Wellness", 4.8),                # estimated
    _b("Trends Man", 4.4),
    _b("Trends Junior", 4.4),
)


def _key(text: str) -> str:
    """Normalize a brand string for loose matching (drop case + punctuation)."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


class BrandDirectory:
    """Validates and resolves brand names against the supported list."""

    def __init__(self, brands: tuple[Brand, ...] = _BRANDS) -> None:
        self._brands = brands
        self._by_key: dict[str, Brand] = {}
        for brand in brands:
            self._by_key[_key(brand.name)] = brand
            self._by_key.setdefault(_key(brand.search_query), brand)

    def resolve(self, raw: str) -> Brand:
        """Return the matching `Brand`, or raise `BrandNotSupportedError`."""
        brand = self._by_key.get(_key(raw))
        if brand is None:
            raise BrandNotSupportedError(
                f"'{raw}' is not a supported brand."
            )
        return brand

    def names(self) -> list[str]:
        """Every supported brand's display name (for the UI dropdown)."""
        return [brand.name for brand in self._brands]
