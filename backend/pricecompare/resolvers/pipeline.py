"""`QueryResolver` — a Chain of Responsibility over `ProductResolver` strategies.

It walks an ordered list of resolvers and returns the first `ProductQuery`
produced. New resolution strategies are added by inserting into the list — no
existing code changes (Open/Closed).
"""

from __future__ import annotations

from ..errors import ResolutionError
from ..models import ProductQuery
from .base import ProductResolver


class QueryResolver:
    """Runs resolvers in priority order until one yields a `ProductQuery`."""

    def __init__(self, resolvers: list[ProductResolver]) -> None:
        if not resolvers:
            raise ValueError("QueryResolver needs at least one resolver")
        self._resolvers = resolvers

    async def resolve(self, raw_input: str) -> ProductQuery:
        if not raw_input or not raw_input.strip():
            raise ResolutionError("Please paste a product link or type a product name.")

        for resolver in self._resolvers:
            query = await resolver.resolve(raw_input)
            if query is not None:
                return query

        raise ResolutionError("Couldn't read that link — paste the product name instead.")
