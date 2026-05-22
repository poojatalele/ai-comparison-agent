"""Settings for the store-locator feature.

An immutable value object built once from environment variables — the core
never reads `os.environ` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StoreLocatorSettings:
    """Tunable knobs for the store locator."""

    google_api_key: str = ""
    request_timeout: float = 12.0
    max_stores: int = 20
    region_code: str = "IN"

    @property
    def live_enabled(self) -> bool:
        """True when a Google key is present — otherwise we serve demo data."""
        return bool(self.google_api_key)

    @classmethod
    def from_env(cls) -> "StoreLocatorSettings":
        def _num(key: str, default, cast):
            raw = os.getenv(key)
            try:
                return cast(raw) if raw not in (None, "") else default
            except (TypeError, ValueError):
                return default

        return cls(
            google_api_key=os.getenv("GOOGLE_PLACES_API_KEY", "").strip(),
            request_timeout=_num("PLACES_TIMEOUT", 12.0, float),
            max_stores=_num("MAX_STORES", 20, int),
            region_code=os.getenv("MARKET_REGION", "IN"),
        )
