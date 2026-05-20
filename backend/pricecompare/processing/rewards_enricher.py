"""`RewardsEnricher` — annotates each offer with reward-partner info.

It asks a `RewardsProvider` for the current catalog and, for every offer whose
retailer is a partner, fills in the cashback rate and the points earned. This
processor depends on the `RewardsProvider` *interface*, not on OnPoint
specifically (Dependency Inversion).
"""

from __future__ import annotations

from ..models import Offer, ProductQuery
from ..rewards import RewardsProvider
from .base import OfferProcessor


class RewardsEnricher(OfferProcessor):
    """Fills `is_reward_partner`, `reward_rate`, and `reward_points` on offers."""

    def __init__(self, rewards: RewardsProvider) -> None:
        self._rewards = rewards

    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        catalog = await self._rewards.get_catalog()

        for offer in offers:
            rate = catalog.rate_for(offer.platform)
            offer.is_reward_partner = rate is not None
            offer.reward_rate = round(rate, 2) if rate is not None else 0.0
            # points earned ≈ rupee value of the cashback (1 point ≈ ₹1)
            offer.reward_points = max(0, round(offer.price * (rate or 0.0) / 100.0))

        return offers
