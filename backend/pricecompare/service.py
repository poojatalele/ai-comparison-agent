"""`PriceComparisonService` — the orchestrator and single public entry point.

It wires the collaborators together but owns none of their logic:

    resolve the query  ->  (search a provider  ‖  inspect the origin URL)
                       ->  run the processing pipeline
                       ->  enrich the origin with reward info

Every collaborator is injected as an abstraction (Dependency Inversion), so the
service is trivial to unit-test with fakes and never changes when an
implementation is swapped.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from .models import ComparisonResult, Offer, OriginListing, RewardSummary
from .origin import OriginScraper
from .processing import ProcessingPipeline
from .providers import PriceProvider, ProviderResult
from .resolvers import QueryResolver
from .rewards import RewardsProvider


class PriceComparisonService:
    """Coordinates resolution, price search, origin inspection, processing."""

    def __init__(
        self,
        resolver: QueryResolver,
        provider: PriceProvider,
        pipeline: ProcessingPipeline,
        origin_scraper: OriginScraper | None = None,
        rewards: RewardsProvider | None = None,
    ) -> None:
        self._resolver = resolver
        self._provider = provider
        self._pipeline = pipeline
        self._origin_scraper = origin_scraper
        self._rewards = rewards

    async def compare(self, raw_input: str) -> ComparisonResult:
        """Run one full price comparison for the given user input.

        Raises `ResolutionError` if the input is unusable and `ProviderError`
        if the price source fails — both defined in `pricecompare.errors`.
        """
        query = await self._resolver.resolve(raw_input)

        # The price search and the origin-URL inspection are independent —
        # run them concurrently.
        search, origin = await self._search_and_inspect(query)
        offers = await self._pipeline.run(search.offers, query)
        origin = await self._enrich_origin(origin)

        return ComparisonResult(
            query=query,
            offers=offers,
            data_source=search.source,
            reward_summary=self._summarize_rewards(offers),
            origin=origin,
            thumbnail=next((o.thumbnail for o in offers if o.thumbnail), None),
        )

    async def _search_and_inspect(
        self, query
    ) -> tuple[ProviderResult, OriginListing | None]:
        """Run the price search and (when there is a URL) the origin scrape."""
        if query.source_url and self._origin_scraper is not None:
            return await asyncio.gather(
                self._provider.search(query.text),
                self._origin_scraper.inspect(query.source_url),
            )
        return await self._provider.search(query.text), None

    async def _enrich_origin(
        self, origin: OriginListing | None
    ) -> OriginListing | None:
        """Tag the origin store with reward info if it is itself a partner.

        This is why a pasted Myntra link still shows Myntra's cashback even
        when Myntra is absent from the price-search results.
        """
        if origin is None or self._rewards is None:
            return origin
        catalog = await self._rewards.get_catalog()
        rate = catalog.rate_for(origin.store)
        if rate is None:
            return origin
        return replace(
            origin,
            is_reward_partner=True,
            reward_rate=round(rate, 2),
            reward_points=catalog.points_for(origin.store, origin.price),
        )

    @staticmethod
    def _summarize_rewards(offers: list[Offer]) -> RewardSummary:
        """Roll up the best rewards opportunity across all offers."""
        partners = sorted(
            (o for o in offers if o.reward_points > 0),
            key=lambda o: o.reward_points,
            reverse=True,
        )
        return RewardSummary(
            partner_count=len(partners),
            max_points=partners[0].reward_points if partners else 0,
            best_store=partners[0].platform if partners else None,
        )
