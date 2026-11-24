import pytest

from app.core.config import settings
from app.services import tencent_map_service


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload, **_kwargs):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, _url, params=None):
        return FakeResponse(self._payload)


def _patch_client(monkeypatch, payload):
    monkeypatch.setattr(
        tencent_map_service.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(payload, **kwargs),
    )
    monkeypatch.setattr(settings, "TENCENT_MAP_KEY", "test-key")


@pytest.mark.asyncio
async def test_geocode_returns_coordinates(monkeypatch):
    _patch_client(
        monkeypatch,
        {
            "status": 0,
            "result": {"location": {"lat": 23.1291, "lng": 113.2644}},
        },
    )

    assert await tencent_map_service.geocode_address("广州市天河区") == pytest.approx(
        (23.1291, 113.2644)
    )


@pytest.mark.asyncio
async def test_geocode_skips_without_key(monkeypatch):
    _patch_client(monkeypatch, {"status": 0})
    monkeypatch.setattr(settings, "TENCENT_MAP_KEY", "")

    assert await tencent_map_service.geocode_address("广州市天河区") is None


@pytest.mark.asyncio
async def test_geocode_returns_none_on_api_error(monkeypatch):
    _patch_client(monkeypatch, {"status": 311, "message": "key格式错误"})

    assert await tencent_map_service.geocode_address("广州市天河区") is None


@pytest.mark.asyncio
async def test_geocode_returns_none_on_missing_location(monkeypatch):
    _patch_client(monkeypatch, {"status": 0, "result": {}})

    assert await tencent_map_service.geocode_address("广州市天河区") is None
