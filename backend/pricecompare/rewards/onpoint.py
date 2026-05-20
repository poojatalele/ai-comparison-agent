"""`OnPointRewardsProvider` — live cashback rates from OnPoint's public API.

Fetches `GET /api/v1/store/featured`, caches the result in memory for a TTL,
and falls back to a baked-in copy of the rates if the API is unreachable.
"""

from __future__ import annotations

import time

import httpx

from ..web import BROWSER_HEADERS
from .base import RewardCatalog, RewardsProvider

# Offline fallback — mirrors the values OnPoint's featured-stores API returns.
_FALLBACK_RATES: dict[str, float] = {
    "adidas": 7.31, "sugar cosmetics": 5.62, "uniqlo": 2.25, "h&m": 3.15,
    "ajio": 6.75, "forest essentials": 15.75, "myntra": 5.62,
    "mokobara": 6.38, "amazon": 0.0,
}


class OnPointRewardsProvider(RewardsProvider):
    """Live OnPoint partner cashback rates, cached for `cache_ttl` seconds."""

    def __init__(
        self,
        api_url: str,
        cache_ttl: int = 3600,
        timeout: float = 8.0,
    ) -> None:
        self._api_url = api_url
        self._cache_ttl = cache_ttl
        self._timeout = timeout
        self._cached: RewardCatalog | None = None
        self._fetched_at = 0.0

    async def get_catalog(self) -> RewardCatalog:
        if self._cached is not None and not self._is_stale():
            return self._cached

        catalog = await self._fetch_catalog()
        if catalog is not None:
            self._cached = catalog
            self._fetched_at = time.monotonic()
            return catalog

        # Fetch failed — reuse a stale cache if we have one, else the fallback.
        return self._cached or RewardCatalog(dict(_FALLBACK_RATES))

    def _is_stale(self) -> bool:
        return (time.monotonic() - self._fetched_at) >= self._cache_ttl

    async def _fetch_catalog(self) -> RewardCatalog | None:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, headers=BROWSER_HEADERS
            ) as client:
                resp = await client.get(self._api_url)
                resp.raise_for_status()
                stores = resp.json().get("stores", [])
        except Exception:
            return None

        rates: dict[str, float] = {}
        for store in stores:
            name = (store.get("name") or "").strip().lower()
            if name and store.get("cashback_type") == "PERCENT":
                rates[name] = float(store.get("cashback_amount") or 0)
        return RewardCatalog(rates) if rates else None
