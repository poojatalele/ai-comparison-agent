"""`FallbackPriceProvider` — a decorator that chains two providers.

It tries a primary provider and, if that returns *no* offers, transparently
falls back to a secondary one. Auth/network failures from the primary are NOT
swallowed — they propagate so the user sees a real error instead of silent
demo data.

This is the Decorator pattern: it *is* a `PriceProvider` and wraps others, so
callers stay unaware that any fallback is happening.
"""

from __future__ import annotations

from .base import PriceProvider, ProviderResult


class FallbackPriceProvider(PriceProvider):
    """Use `primary`; if it yields zero offers, use `fallback` instead."""

    def __init__(self, primary: PriceProvider, fallback: PriceProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    @property
    def name(self) -> str:
        return f"{self._primary.name}+{self._fallback.name}"

    async def search(self, query: str) -> ProviderResult:
        # A ProviderError from the primary intentionally propagates.
        result = await self._primary.search(query)
        if result.offers:
            return result
        return await self._fallback.search(query)
