"""API routes for the store-locator feature.

Translates the store-locator domain errors into HTTP status codes — the only
place in this feature that knows about HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from storelocator.errors import BrandNotSupportedError, LocatorError
from storelocator.models import GeoPoint
from storelocator.service import StoreLocatorService

from ..container import get_store_service
from ..schemas import StoreLocatorResponse, StoreQueryRequest

router = APIRouter(prefix="/api", tags=["store-locator"])


@router.get("/brands")
def brands(service: StoreLocatorService = Depends(get_store_service)) -> dict:
    """The supported brand list — used to populate the UI dropdown."""
    return {"brands": service.brand_names()}


@router.post("/stores", response_model=StoreLocatorResponse)
async def stores(
    request: StoreQueryRequest,
    service: StoreLocatorService = Depends(get_store_service),
) -> StoreLocatorResponse:
    """Find a brand's outlets in a city, ranked nearest-first."""
    user_point = (
        GeoPoint(lat=request.lat, lng=request.lng)
        if request.lat is not None and request.lng is not None
        else None
    )
    try:
        result = await service.find(request.brand, request.city, user_point)
    except BrandNotSupportedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LocatorError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return StoreLocatorResponse.from_domain(result)
