"""`GooglePlacesStoreLocator` — live outlet data via the Google Places API (New).

Uses the v1 `places:searchText` endpoint. The Google Cloud project must have
**Places API (New)** enabled with billing.
"""

from __future__ import annotations

import httpx

from ..brands import Brand
from ..errors import LocatorError
from ..models import GeoPoint, StoreLocation
from .base import StoreLocator

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Only the fields we need — a tight field mask keeps the call cheap and fast.
_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.currentOpeningHours.openNow"
)


def _as_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class GooglePlacesStoreLocator(StoreLocator):
    """Finds outlets via Google Places Text Search."""

    def __init__(
        self,
        api_key: str,
        timeout: float = 12.0,
        region_code: str = "IN",
        max_stores: int = 20,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._region_code = region_code
        self._max_stores = max_stores

    @property
    def name(self) -> str:
        return "google"

    async def find_stores(self, brand: Brand, city: str) -> list[StoreLocation]:
        query = f"{brand.search_query} {city}".strip()
        places = await self._search_text(query, self._max_stores)

        stores: list[StoreLocation] = []
        for place in places:
            loc = place.get("location") or {}
            lat, lng = loc.get("latitude"), loc.get("longitude")
            if lat is None or lng is None:
                continue
            stores.append(
                StoreLocation(
                    brand=brand.name,
                    name=(place.get("displayName") or {}).get("text") or brand.name,
                    address=place.get("formattedAddress") or "",
                    location=GeoPoint(lat=float(lat), lng=float(lng)),
                    place_id=place.get("id") or "",
                    rating=_as_float(place.get("rating")),
                    open_now=(place.get("currentOpeningHours") or {}).get("openNow"),
                )
            )
        return stores

    async def geocode_city(self, city: str) -> GeoPoint | None:
        places = await self._search_text(f"{city}, India", max_results=1)
        if not places:
            return None
        loc = places[0].get("location") or {}
        lat, lng = loc.get("latitude"), loc.get("longitude")
        if lat is None or lng is None:
            return None
        return GeoPoint(lat=float(lat), lng=float(lng))

    async def _search_text(self, text_query: str, max_results: int) -> list[dict]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": _FIELD_MASK,
        }
        body = {
            "textQuery": text_query,
            "regionCode": self._region_code,
            "maxResultCount": max(1, min(max_results, 20)),
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(_SEARCH_URL, headers=headers, json=body)
        except httpx.RequestError:
            raise LocatorError(
                "Couldn't reach Google Places — check your internet connection."
            )

        if resp.status_code != 200:
            raise LocatorError(self._error_message(resp))

        try:
            return resp.json().get("places", [])
        except ValueError:
            raise LocatorError("Google Places returned an unreadable response.")

    @staticmethod
    def _error_message(resp: httpx.Response) -> str:
        """Turn a Google API failure into a clean message (no key leak — the key
        travels in a header, never the URL)."""
        status, detail = "", ""
        try:
            error = resp.json().get("error", {})
            status = error.get("status", "")
            detail = error.get("message", "")
        except ValueError:
            detail = resp.text[:200]

        if resp.status_code in (401, 403) or status in (
            "PERMISSION_DENIED",
            "UNAUTHENTICATED",
        ):
            return (
                "Google rejected the request. Check GOOGLE_PLACES_API_KEY and make "
                "sure 'Places API (New)' is enabled with billing on the project."
            )
        return f"Google Places error ({resp.status_code} {status}): {detail}".strip()
