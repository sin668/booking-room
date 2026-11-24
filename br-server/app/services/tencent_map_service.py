import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_json(url: str, params: dict) -> dict | None:
    # WebServiceAPI 若按 IP 白名单鉴权，浏览器直连会被拒绝，必须由服务端转发
    if not settings.TENCENT_MAP_KEY:
        return None

    try:
        async with httpx.AsyncClient(
            timeout=settings.TENCENT_MAP_GEOCODE_TIMEOUT_SECONDS, trust_env=False
        ) as client:
            response = await client.get(url, params={**params, "key": settings.TENCENT_MAP_KEY})
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Tencent map request failed: %s", exc)
        return None

    if data.get("status") != 0:
        logger.info(
            "Tencent map returned status=%s message=%s",
            data.get("status"),
            data.get("message"),
        )
        return None
    return data


async def geocode_address(
    address: str, city_name: str | None = None
) -> tuple[float, float] | None:
    """Resolve a free-text address to GCJ-02 coordinates via Tencent LBS.

    Returns None when the key is missing, the request fails, or no location is
    resolved, so callers can keep saving without coordinates.
    """
    query = " ".join(part for part in (city_name, address) if part).strip()
    if not query:
        return None

    data = await _get_json(settings.TENCENT_MAP_GEOCODE_URL, {"address": query})
    if not data:
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


async def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """Resolve GCJ-02 coordinates to a readable address, None when unavailable."""
    data = await _get_json(
        settings.TENCENT_MAP_GEOCODE_URL, {"location": f"{latitude},{longitude}"}
    )
    if not data:
        return None

    result = data.get("result") or {}
    address = (result.get("formatted_addresses") or {}).get("recommend") or result.get(
        "address"
    )
    return str(address) if address else None


async def suggest_places(keyword: str, city_name: str | None = None) -> list[dict]:
    """Search places by keyword, returning [] when unavailable."""
    query = keyword.strip()
    if not query:
        return []

    params: dict = {"keyword": query}
    if city_name:
        params["region"] = city_name
    data = await _get_json(settings.TENCENT_MAP_SUGGESTION_URL, params)
    if not data:
        return []

    places = []
    for item in data.get("data") or []:
        location = item.get("location") or {}
        try:
            places.append(
                {
                    "title": str(item.get("title") or ""),
                    "address": str(item.get("address") or ""),
                    "latitude": float(location["lat"]),
                    "longitude": float(location["lng"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return places
