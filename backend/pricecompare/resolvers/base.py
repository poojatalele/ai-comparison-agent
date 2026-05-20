"""The `ProductResolver` abstraction.

Each resolver is a *strategy* for turning raw user input into a `ProductQuery`.
Returning `None` means "not my job" — the chain then tries the next resolver.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from ..models import ProductQuery

_URL_RE = re.compile(r"https?://", re.I)


def is_url(text: str) -> bool:
    """True if the text looks like an http(s) URL."""
    return bool(_URL_RE.match(text.strip()))


class ProductResolver(ABC):
    """Strategy interface: produce a `ProductQuery`, or `None` if not applicable."""

    @abstractmethod
    async def resolve(self, raw_input: str) -> ProductQuery | None:
        """Attempt to resolve `raw_input`. Return `None` to defer to the next."""
        raise NotImplementedError
