"""Product-query resolution: raw user input -> a searchable `ProductQuery`."""

from __future__ import annotations

from .base import ProductResolver, is_url
from .pipeline import QueryResolver
from .strategies import PageTitleResolver, PlainTextResolver, UrlSlugResolver

__all__ = [
    "ProductResolver",
    "is_url",
    "QueryResolver",
    "PlainTextResolver",
    "UrlSlugResolver",
    "PageTitleResolver",
]
