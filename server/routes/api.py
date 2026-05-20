"""API routes — health check and the price-comparison endpoint.

This module is the *only* place that knows about HTTP status codes. It catches
the core's domain errors and translates each into the right response.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException

from pricecompare.errors import ProviderError, ResolutionError
from pricecompare.service import PriceComparisonService

from ..container import get_service, get_settings
from ..schemas import CompareRequest, CompareResponse

router = APIRouter(prefix="/api", tags=["price-agent"])


def _redact(text: str) -> str:
    """Strip any `api_key=...` a low-level error string might carry."""
    return re.sub(r"api_key=[^&\s'\"]+", "api_key=***", text)


@router.get("/health")
def health() -> dict:
    """Liveness probe; also reports whether live prices are configured."""
    return {"status": "ok", "live_prices": get_settings().live_prices_enabled}


@router.post("/compare", response_model=CompareResponse)
async def compare(
    request: CompareRequest,
    service: PriceComparisonService = Depends(get_service),
) -> CompareResponse:
    """Paste a URL or product name -> ranked retailers + onpoints earned."""
    try:
        result = await service.compare(request.input)
    except ResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=_redact(str(exc)))
    return CompareResponse.from_domain(result)
