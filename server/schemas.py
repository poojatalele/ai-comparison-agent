"""API contract — Pydantic models for the request and response.

Kept deliberately separate from the domain models in `pricecompare.models`:
the wire format can evolve independently of the core, FastAPI uses these for
validation and OpenAPI docs, and the field names here are the ones the frontend
expects (`price_value`, `link`, `onpoints`, ...).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from pricecompare.models import ComparisonResult, Offer, OriginListing


class CompareRequest(BaseModel):
    """Body of `POST /api/compare`."""

    input: str = Field(..., description="A product URL or a product name.")


class OfferOut(BaseModel):
    """One retailer offer, as sent to the browser."""

    platform: str
    title: str
    price_value: float
    link: str
    thumbnail: str | None = None
    logo_url: str | None = None
    rating: float | None = None
    reviews: int | None = None
    delivery: str | None = None
    is_best: bool
    is_recommended: bool
    savings: float
    is_onpoint_partner: bool
    cashback_rate: float
    onpoints: int

    @classmethod
    def from_offer(cls, offer: Offer) -> "OfferOut":
        """Map a domain `Offer` onto the wire shape."""
        return cls(
            platform=offer.platform,
            title=offer.title,
            price_value=offer.price,
            link=offer.url,
            thumbnail=offer.thumbnail,
            logo_url=offer.logo_url,
            rating=offer.rating,
            reviews=offer.reviews,
            delivery=offer.delivery,
            is_best=offer.is_cheapest,
            is_recommended=offer.is_recommended,
            savings=offer.savings,
            is_onpoint_partner=offer.is_reward_partner,
            cashback_rate=offer.reward_rate,
            onpoints=offer.reward_points,
        )


class ProductOut(BaseModel):
    title: str
    thumbnail: str | None = None


class OriginOut(BaseModel):
    """The store the user came from (the pasted URL's retailer)."""

    store: str
    url: str
    price: float | None = None
    logo_url: str | None = None
    is_onpoint_partner: bool = False
    cashback_rate: float = 0.0
    onpoints: int = 0

    @classmethod
    def from_origin(cls, origin: OriginListing) -> "OriginOut":
        return cls(
            store=origin.store,
            url=origin.url,
            price=origin.price,
            logo_url=origin.logo_url,
            is_onpoint_partner=origin.is_reward_partner,
            cashback_rate=origin.reward_rate,
            onpoints=origin.reward_points,
        )


class OnPointOut(BaseModel):
    partner_count: int
    max_onpoints: int
    best_store: str | None = None


class CompareResponse(BaseModel):
    """Body of a successful `POST /api/compare`."""

    query: str
    resolved_via: str
    source_url: str | None = None
    product: ProductOut
    origin: OriginOut | None = None
    store_count: int
    best: OfferOut | None = None
    results: list[OfferOut]
    onpoint: OnPointOut
    currency: str
    data_source: str

    @classmethod
    def from_domain(cls, result: ComparisonResult) -> "CompareResponse":
        """Map a domain `ComparisonResult` onto the API response."""
        offers = [OfferOut.from_offer(o) for o in result.offers]
        summary = result.reward_summary
        return cls(
            query=result.query.text,
            resolved_via=result.query.resolved_via.value,
            source_url=result.query.source_url,
            product=ProductOut(title=result.query.text, thumbnail=result.thumbnail),
            origin=OriginOut.from_origin(result.origin) if result.origin else None,
            store_count=len(offers),
            best=offers[0] if offers else None,
            results=offers,
            onpoint=OnPointOut(
                partner_count=summary.partner_count,
                max_onpoints=summary.max_points,
                best_store=summary.best_store,
            ),
            currency=result.currency,
            data_source=result.data_source,
        )
