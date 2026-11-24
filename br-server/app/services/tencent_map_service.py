import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def geocode_address(
    address: str, city_name: str | None = None
) -> tuple[float, float] | None:
    """Resolve a free-text address to GCJ-02 coordinates via Tencent LBS.

    Returns None when the key is missing, the request fails, or no location is
    resolved, so callers can keep saving without coordinates.
    """
    query = " ".join(part for part in (city_name, address) if part).strip()
    if not settings.TENCENT_MAP_KEY or not query:
        return None

    params = {"address": query, "key": settings.TENCENT_MAP_KEY}
    try:
        async with httpx.AsyncClient(
            timeout=settings.TENCENT_MAP_GEOCODE_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(settings.TENCENT_MAP_GEOCODE_URL, params=params)
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Tencent geocode request failed: %s", exc)
        return None

    if data.get("status") != 0:
        logger.info(
            "Tencent geocode returned status=%s message=%s",
            data.get("status"),
            data.get("message"),
        )
        return None

    location = (data.get("result") or {}).get("location") or {}
    latitude = location.get("lat")
    longitude = location.get("lng")
    if latitude is None or longitude is None:
        return None

    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None
