"""Application settings.

`Settings` is an immutable value object built once from environment variables.
The core never reads `os.environ` directly — it receives a `Settings` instance,
which keeps it testable and side-effect free.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """All tunable knobs for the price-comparison agent."""

    # --- price provider (SerpAPI) ---
    serpapi_key: str = ""
    serpapi_timeout: float = 30.0

    # --- product-page fetching (for URL resolution) ---
    http_timeout: float = 9.0

    # --- OnPoint rewards ---
    onpoint_api_url: str = "https://on-points.com/api/v1/store/featured"
    rewards_cache_ttl: int = 3600          # seconds
    rewards_http_timeout: float = 8.0

    # --- marketplace scope ---
    country: str = "in"
    language: str = "en"
    location: str = "India"

    # --- result shaping ---
    max_results: int = 15

    @property
    def live_prices_enabled(self) -> bool:
        """True when a SerpAPI key is present — otherwise we serve demo data."""
        return bool(self.serpapi_key)

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables, falling back to defaults."""

        def _num(key: str, default, cast):
            raw = os.getenv(key)
            try:
                return cast(raw) if raw not in (None, "") else default
            except (TypeError, ValueError):
                return default

        return cls(
            serpapi_key=os.getenv("SERPAPI_KEY", "").strip(),
            serpapi_timeout=_num("SERPAPI_TIMEOUT", 30.0, float),
            http_timeout=_num("HTTP_TIMEOUT", 9.0, float),
            onpoint_api_url=os.getenv("ONPOINT_API_URL", cls.onpoint_api_url),
            rewards_cache_ttl=_num("REWARDS_CACHE_TTL", 3600, int),
            country=os.getenv("MARKET_COUNTRY", cls.country),
            language=os.getenv("MARKET_LANGUAGE", cls.language),
            location=os.getenv("MARKET_LOCATION", cls.location),
            max_results=_num("MAX_RESULTS", 15, int),
        )
