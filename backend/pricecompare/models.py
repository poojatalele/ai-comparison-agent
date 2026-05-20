"""Domain models — the vocabulary shared by every layer of the core.

These are plain dataclasses with no behaviour and no I/O. Note the deliberately
*generic* naming (`reward_points`, not `onpoints`): OnPoint is one possible
rewards integration, so OnPoint-specific terms live only at the edges.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResolvedVia(str, Enum):
    """How a `ProductQuery` was derived from the raw user input."""

    SEARCH_TERM = "search-term"   # the user typed a product name
    URL_SLUG = "url-slug"         # extracted from a pasted URL's path
    PAGE_TITLE = "page-title"     # scraped from a pasted page's <title>


@dataclass(frozen=True)
class ProductQuery:
    """A normalized, searchable product query."""

    text: str
    resolved_via: ResolvedVia
    source_url: str | None = None


@dataclass(frozen=True)
class OriginListing:
    """The store the user *came from* — the retailer behind a pasted URL.

    Used to anchor the comparison ("you came from here"). Carries reward fields
    too, so an origin that is itself a reward partner shows its cashback.
    """

    store: str
    url: str
    price: float | None = None
    logo_url: str | None = None
    is_reward_partner: bool = False
    reward_rate: float = 0.0     # cashback %
    reward_points: int = 0       # onpoints (0 when the origin price is unknown)


@dataclass
class Offer:
    """A single retailer's listing for a product.

    The first block of fields is filled by a `PriceProvider`; the second block
    is filled as the offer flows through the processing pipeline.
    """

    # --- raw, straight from the price provider ---
    platform: str
    title: str
    price: float
    url: str
    thumbnail: str | None = None
    rating: float | None = None
    reviews: int | None = None
    delivery: str | None = None

    # --- derived, by the processing pipeline ---
    is_cheapest: bool = False
    is_reward_partner: bool = False
    reward_rate: float = 0.0     # cashback %, e.g. 6.75
    reward_points: int = 0       # onpoints earned (≈ rupee value of cashback)
    logo_url: str | None = None  # merchant logo
    is_recommended: bool = True  # known/trusted retailer vs. an obscure one


@dataclass(frozen=True)
class RewardSummary:
    """A roll-up of the rewards opportunity across all offers."""

    partner_count: int
    max_points: int
    best_store: str | None


@dataclass(frozen=True)
class ComparisonResult:
    """The complete output of one price-comparison run."""

    query: ProductQuery
    offers: list[Offer]
    data_source: str             # which provider produced the offers
    reward_summary: RewardSummary
    origin: OriginListing | None = None
    thumbnail: str | None = None
    currency: str = "INR"
