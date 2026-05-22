"""Geo math — straight-line distance between two coordinates."""

from __future__ import annotations

import math

from .models import GeoPoint

_EARTH_RADIUS_KM = 6371.0


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle (straight-line) distance between two points, in kilometres.

    The haversine formula — accurate enough for "how far is this store", and
    free: pure arithmetic, no API call.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lng, b.lat, b.lng))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))
