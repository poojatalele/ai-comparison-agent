"""`ProductMatcher` — keeps only offers that are genuinely the same product.

Keyword shopping search returns whatever shares words: searching a brand's
"sheer body sunscreen spray" pulls in unrelated sunscreens from other brands.

When the query carries a `brand` (it was resolved from a single-brand store's
URL) this step keeps only offers whose title matches that brand *and* enough of
the product description — and returns an empty list when nothing qualifies,
which is the signal that the product is not available at other stores.

Without a brand (a typed search, or a marketplace URL) it is a deliberate no-op:
the shopping engine already did the cross-store matching and there is no
trustworthy brand anchor to tighten it against.
"""

from __future__ import annotations

import math
import re

from ..models import Offer, ProductQuery
from .base import OfferProcessor

# True noise — articles, generic verbs, and size/quantity units. Product-defining
# nouns ("spray", "sunscreen", "headphones", ...) are deliberately NOT here.
_STOPWORDS: frozenset[str] = frozenset(
    "the a an for with and of by in on new buy online "
    "ml g gm gms kg l ltr pcs pack set size x".split()
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    """Lowercase word tokens, minus stopwords and bare numbers (sizes/quantities)."""
    return {
        tok
        for tok in _TOKEN_RE.findall((text or "").lower())
        if tok not in _STOPWORDS and not tok.isdigit()
    }


class ProductMatcher(OfferProcessor):
    """Filters offers down to genuine matches for a brand-anchored query."""

    def __init__(
        self, min_brand_ratio: float = 0.5, product_overlap: float = 0.4
    ) -> None:
        self._min_brand_ratio = min_brand_ratio
        self._product_overlap = product_overlap

    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        if not query.brand:
            return offers                       # no brand anchor -> stay lenient

        brand_tk = _tokens(query.brand)
        if not brand_tk:
            return offers

        product_tk = _tokens(query.text) - brand_tk
        brand_need = max(1, math.ceil(len(brand_tk) * self._min_brand_ratio))
        product_need = (
            max(1, math.ceil(len(product_tk) * self._product_overlap))
            if product_tk
            else 0
        )

        matched = [
            offer
            for offer in offers
            if self._is_match(_tokens(offer.title), brand_tk, product_tk,
                              brand_need, product_need)
        ]
        # An empty list is intentional — it means "not available elsewhere".
        return matched

    @staticmethod
    def _is_match(
        title_tk: set[str],
        brand_tk: set[str],
        product_tk: set[str],
        brand_need: int,
        product_need: int,
    ) -> bool:
        """True when a title shares enough brand *and* product tokens."""
        return (
            len(brand_tk & title_tk) >= brand_need
            and len(product_tk & title_tk) >= product_need
        )
