"""Rewards: reward-partner cashback rates used to estimate points earned."""

from __future__ import annotations

from .base import RewardCatalog, RewardsProvider
from .onpoint import OnPointRewardsProvider

__all__ = ["RewardCatalog", "RewardsProvider", "OnPointRewardsProvider"]
