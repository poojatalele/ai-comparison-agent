"""The `OfferProcessor` abstraction and the `ProcessingPipeline` that runs them.

Result post-processing is modelled as a pipeline of small, single-responsibility
steps. Reordering, adding, or removing a step is a one-line change to the
pipeline's list — no step needs to know about any other (Open/Closed).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Offer, ProductQuery


class OfferProcessor(ABC):
    """One transform over the list of offers (filter, sort, annotate, ...)."""

    @abstractmethod
    async def process(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        """Return a new (or mutated) list of offers."""
        raise NotImplementedError


class ProcessingPipeline:
    """Runs an ordered sequence of `OfferProcessor`s."""

    def __init__(self, processors: list[OfferProcessor]) -> None:
        self._processors = processors

    async def run(self, offers: list[Offer], query: ProductQuery) -> list[Offer]:
        for processor in self._processors:
            offers = await processor.process(offers, query)
        return offers
