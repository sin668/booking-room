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


@pytest.mark.asyncio
async def test_reverse_geocode_returns_recommend_address(monkeypatch):
    _patch_client(
        monkeypatch,
        {
            "status": 0,
            "result": {
                "address": "广东省广州市天河区",
                "formatted_addresses": {"recommend": "天河体育中心"},
            },
        },
    )

    assert await tencent_map_service.reverse_geocode(23.1291, 113.2644) == "天河体育中心"


@pytest.mark.asyncio
async def test_reverse_geocode_falls_back_to_address(monkeypatch):
    _patch_client(monkeypatch, {"status": 0, "result": {"address": "广东省广州市天河区"}})

    assert await tencent_map_service.reverse_geocode(23.1291, 113.2644) == "广东省广州市天河区"


@pytest.mark.asyncio
async def test_reverse_geocode_skips_without_key(monkeypatch):
    _patch_client(monkeypatch, {"status": 0})
    monkeypatch.setattr(settings, "TENCENT_MAP_KEY", "")

    assert await tencent_map_service.reverse_geocode(23.1291, 113.2644) is None


@pytest.mark.asyncio
async def test_suggest_places_returns_items(monkeypatch):
    _patch_client(
        monkeypatch,
        {
            "status": 0,
            "data": [
                {
                    "title": "光谷大道",
                    "address": "湖北省武汉市洪山区",
                    "location": {"lat": 30.5051, "lng": 114.4101},
                },
                {"title": "缺少坐标", "address": "无"},
            ],
        },
    )

    places = await tencent_map_service.suggest_places("光谷大道")

    assert places == [
        {
            "title": "光谷大道",
            "address": "湖北省武汉市洪山区",
            "latitude": pytest.approx(30.5051),
            "longitude": pytest.approx(114.4101),
        }
    ]


@pytest.mark.asyncio
async def test_suggest_places_returns_empty_on_api_error(monkeypatch):
    _patch_client(monkeypatch, {"status": 199, "message": "此key未开启WebserviceAPI功能"})

    assert await tencent_map_service.suggest_places("光谷大道") == []
