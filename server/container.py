"""Composition root — the single place that picks and wires concrete classes.

Every other module depends on abstractions (`PriceProvider`, `RewardsProvider`,
`OfferProcessor`, ...). Only this file knows which concrete implementations
exist and how they fit together. Swapping in a new provider is a change *here*
and nowhere else.

`get_service()` is cached, so the service — and the in-memory caches inside it —
lives for the process, and FastAPI can inject it via `Depends`.
"""

from __future__ import annotations

from functools import lru_cache

from pricecompare.config import Settings
from pricecompare.origin import OriginScraper
from pricecompare.processing import (
    NoiseFilter,
    ProcessingPipeline,
    ProductMatcher,
    Ranker,
    RewardsEnricher,
    StoreNormalizer,
)
from pricecompare.providers import (
    FallbackPriceProvider,
    MockPriceProvider,
    PriceProvider,
    SerpApiPriceProvider,
)
from pricecompare.resolvers import (
    PageTitleResolver,
    PlainTextResolver,
    QueryResolver,
    UrlSlugResolver,
)
from pricecompare.retailers import RetailerDirectory
from pricecompare.rewards import OnPointRewardsProvider
from pricecompare.service import PriceComparisonService


@lru_cache
def get_settings() -> Settings:
    """The process-wide `Settings`, read once from the environment."""
    return Settings.from_env()


@lru_cache
def _get_directory() -> RetailerDirectory:
    """The known-retailer directory (used for normalization + trust tiering)."""
    return RetailerDirectory()


@lru_cache
def _get_rewards() -> OnPointRewardsProvider:
    """The OnPoint rewards provider — one shared instance so its cache is reused
    by both the pipeline's enricher and the service's origin enrichment."""
    settings = get_settings()
    return OnPointRewardsProvider(
        api_url=settings.onpoint_api_url,
        cache_ttl=settings.rewards_cache_ttl,
        timeout=settings.rewards_http_timeout,
    )


def _build_resolver(settings: Settings) -> QueryResolver:
    # Order matters: cheap checks first; the slow page fetch only when needed.
    # The directory lets URL resolvers fold the brand into the search query.
    directory = _get_directory()
    return QueryResolver(
        [
            PlainTextResolver(),                    # typed product names
            UrlSlugResolver(min_words=3, directory=directory),  # strong slug
            PageTitleResolver(timeout=settings.http_timeout, directory=directory),
            UrlSlugResolver(min_words=1, directory=directory),  # lenient fallback
        ]
    )


def _build_provider(settings: Settings) -> PriceProvider:
    mock = MockPriceProvider()
    if not settings.live_prices_enabled:
        return mock                                 # no key -> demo data only

    serpapi = SerpApiPriceProvider(
        api_key=settings.serpapi_key,
        timeout=settings.serpapi_timeout,
        country=settings.country,
        language=settings.language,
        location=settings.location,
    )
    # Live prices, but fall back to demo data if a search returns nothing.
    return FallbackPriceProvider(primary=serpapi, fallback=mock)


def _build_pipeline(settings: Settings) -> ProcessingPipeline:
    return ProcessingPipeline(
        [
            NoiseFilter(),                          # drop accessories / refurb / outliers
            ProductMatcher(),                       # keep only genuine same-product matches
            StoreNormalizer(_get_directory()),      # canonical names + trust tier + logos
            Ranker(max_results=settings.max_results),  # dedupe, sort, cap
            RewardsEnricher(_get_rewards()),        # add OnPoint cashback + onpoints
        ]
    )


@lru_cache
def get_service() -> PriceComparisonService:
    """Build (once) the fully-wired `PriceComparisonService`."""
    settings = get_settings()
    return PriceComparisonService(
        resolver=_build_resolver(settings),
        provider=_build_provider(settings),
        pipeline=_build_pipeline(settings),
        origin_scraper=OriginScraper(
            directory=_get_directory(), timeout=settings.http_timeout
        ),
        rewards=_get_rewards(),                     # also enriches the origin store
    )
