"""`SerpApiPriceProvider` — live prices via SerpAPI's Google Shopping engine.

Google Shopping already matches the same product across retailers, so this one
call does the hard cross-store matching for us. Scoped to a single marketplace
(country / language / currency) via the constructor.
"""

from __future__ import annotations

import httpx

from ..errors import ProviderError
from ..models import Offer
from .base import PriceProvider, ProviderResult


def _as_float(value: object) -> float | None:
    """Coerce a messy upstream value to float, or None if it can't be."""
    try:
        return float(value) if value is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    """Coerce a messy upstream value to int (e.g. SerpAPI may send 4.4)."""
    try:
        return int(float(value)) if value is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class SerpApiPriceProvider(PriceProvider):
    """Queries SerpAPI's `google_shopping` engine."""

    _ENDPOINT = "https://serpapi.com/search.json"

    def __init__(
        self,
        api_key: str,
        timeout: float = 30.0,
        country: str = "in",
        language: str = "en",
        location: str = "India",
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._country = country
        self._language = language
        self._location = location

    @property
    def name(self) -> str:
        return "serpapi"

    async def search(self, query: str) -> ProviderResult:
        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": self._country,
            "hl": self._language,
            "location": self._location,
            "google_domain": f"google.co.{self._country}",
            "api_key": self._api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._ENDPOINT, params=params)
        except httpx.RequestError:
            raise ProviderError(
                "Couldn't reach the price provider — check your internet connection."
            )

        try:
            data = resp.json()
        except ValueError:
            data = {}

        self._raise_for_api_error(resp.status_code, data)

        offers = [
            self._to_offer(item, query)
            for item in data.get("shopping_results", [])
            if item.get("extracted_price") is not None
        ]
        return ProviderResult(offers=offers, source=self.name)

    @staticmethod
    def _raise_for_api_error(status_code: int, data: dict) -> None:
        """Translate SerpAPI failures into a clean `ProviderError` (no key leak)."""
        error = data.get("error")
        if status_code == 401 or (
            isinstance(error, str) and "api key" in error.lower()
        ):
            raise ProviderError(
                "SerpAPI rejected the key. Put a valid 64-character SERPAPI_KEY "
                "in server/.env — get one at https://serpapi.com/manage-api-key"
            )
        if error:
            raise ProviderError(f"Price provider error: {error}")
        if status_code >= 400:
            raise ProviderError(f"Price provider returned HTTP {status_code}.")

    @staticmethod
    def _to_offer(item: dict, fallback_title: str) -> Offer:
        # SerpAPI fields are loosely typed — coerce them to the domain's types
        # here so the rest of the core can trust an `Offer`.
        return Offer(
            platform=(item.get("source") or "Store").strip(),
            title=item.get("title") or fallback_title,
            price=float(item["extracted_price"]),
            url=item.get("link") or item.get("product_link") or "#",
            thumbnail=item.get("thumbnail"),
            rating=_as_float(item.get("rating")),
            reviews=_as_int(item.get("reviews")),
            delivery=item.get("delivery") or None,
        )
