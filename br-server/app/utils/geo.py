from __future__ import annotations

import math

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(
    lat1: float | None,
    lng1: float | None,
    lat2: float | None,
    lng2: float | None,
) -> float | None:
    """两个 GCJ-02 坐标之间的球面直线距离（米）；任一坐标非法时返回 None。"""
    try:
        latitude1 = float(lat1)  # type: ignore[arg-type]
        longitude1 = float(lng1)  # type: ignore[arg-type]
        latitude2 = float(lat2)  # type: ignore[arg-type]
        longitude2 = float(lng2)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None

    delta_lat = math.radians(latitude2 - latitude1)
    delta_lng = math.radians(longitude2 - longitude1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(math.radians(latitude1))
        * math.cos(math.radians(latitude2))
        * math.sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(a))
