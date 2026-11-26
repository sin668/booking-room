"""Integration tests for the daily check-in API."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.checkin import CheckinRecord, UserCheckinStats
from app.services import checkin_service

USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TODAY = date(2026, 11, 26)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(checkin_service, "_today", lambda: TODAY)


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


async def _seed_records(
    db_session: AsyncSession,
    dates: list[date],
    *,
    points: int = 0,
    makeup_cards: int = 2,
    source: str = "daily",
) -> None:
    for day in dates:
        db_session.add(
            CheckinRecord(user_id=USER_ID, checkin_date=day, source=source)
        )
    db_session.add(
        UserCheckinStats(
            user_id=USER_ID,
            points=points,
            makeup_cards=makeup_cards,
        )
    )
    await db_session.flush()


async def _recent_days(count: int) -> list[date]:
    return [TODAY - timedelta(days=offset) for offset in range(count, 0, -1)]


class TestSummary:
    @pytest.mark.asyncio
    async def test_new_user_summary(self, auth_client: AsyncClient):
        resp = await auth_client.get(
            "/api/v1/checkin/summary", params={"month": "2026-11"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["today"] == "2026-11-26"
        assert data["today_signed"] is False
        assert data["streak"] == 0
        assert data["total_days"] == 0
        assert data["points"] == 0
        assert data["makeup_cards"] == 2
        assert len(data["calendar_mark"]) == 30
        assert data["missed_dates"] == []

    @pytest.mark.asyncio
    async def test_streak_counts_today(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, (await _recent_days(2)) + [TODAY], points=15)
        resp = await auth_client.get(
            "/api/v1/checkin/summary", params={"month": "2026-11"}
        )
        data = resp.json()
        assert data["today_signed"] is True
        assert data["streak"] == 3
        assert data["total_days"] == 3
        assert data["points"] == 15
        today_mark = next(
            item for item in data["calendar_mark"] if item["date"] == "2026-11-26"
        )
        assert today_mark["signed"] is True

    @pytest.mark.asyncio
    async def test_streak_counts_from_yesterday_when_today_unsigned(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, [TODAY - timedelta(days=2), TODAY - timedelta(days=1)])
        resp = await auth_client.get(
            "/api/v1/checkin/summary", params={"month": "2026-11"}
        )
        data = resp.json()
        assert data["today_signed"] is False
        assert data["streak"] == 2
        today_mark = next(
            item for item in data["calendar_mark"] if item["date"] == "2026-11-26"
        )
        assert today_mark["missed"] is False

    @pytest.mark.asyncio
    async def test_missed_and_makeup_window(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(
            db_session,
            [date(2026, 9, 1), date(2026, 11, 20), date(2026, 11, 25)],
        )
        resp = await auth_client.get(
            "/api/v1/checkin/summary", params={"month": "2026-11"}
        )
        data = resp.json()

        resp_oct = await auth_client.get(
            "/api/v1/checkin/summary", params={"month": "2026-10"}
        )
        oct_mark = next(
            item
            for item in resp_oct.json()["calendar_mark"]
            if item["date"] == "2026-10-01"
        )
        assert oct_mark["missed"] is True
        assert oct_mark["makeup_eligible"] is False

        recent_missed = next(
            item for item in data["calendar_mark"] if item["date"] == "2026-11-18"
        )
        assert recent_missed["missed"] is True
        assert recent_missed["makeup_eligible"] is True
        assert "2026-11-18" in data["missed_dates"]
        assert "2026-10-01" not in data["missed_dates"]

    @pytest.mark.asyncio
    async def test_summary_requires_month(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/checkin/summary")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_summary_rejects_invalid_month(self, auth_client: AsyncClient):
        for month in ("2026-13", "2026-00", "2026-1"):
            resp = await auth_client.get(
                "/api/v1/checkin/summary", params={"month": month}
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_summary_requires_login(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/checkin/summary", params={"month": "2026-11"}
        )
        assert resp.status_code == 401


class TestCheckIn:
    @pytest.mark.asyncio
    async def test_first_check_in(self, auth_client: AsyncClient):
        resp = await auth_client.post("/api/v1/checkin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reward_points"] == 5
        assert data["reward_cards"] == 0
        assert data["summary"]["today_signed"] is True
        assert data["summary"]["streak"] == 1
        assert data["summary"]["total_days"] == 1
        assert data["summary"]["points"] == 5

    @pytest.mark.asyncio
    async def test_duplicate_check_in(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, [TODAY], points=5)
        resp = await auth_client.post("/api/v1/checkin")
        assert resp.status_code == 400
        assert "今日已签到" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_seventh_day_bonus(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, await _recent_days(6), points=30)
        resp = await auth_client.post("/api/v1/checkin")
        data = resp.json()
        assert data["summary"]["streak"] == 7
        assert data["reward_points"] == 25
        assert data["summary"]["points"] == 55

    @pytest.mark.asyncio
    async def test_thirtieth_day_grants_makeup_card(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, await _recent_days(29), makeup_cards=2)
        resp = await auth_client.post("/api/v1/checkin")
        data = resp.json()
        assert data["summary"]["streak"] == 30
        assert data["reward_points"] == 5
        assert data["reward_cards"] == 1
        assert data["summary"]["makeup_cards"] == 3

    @pytest.mark.asyncio
    async def test_check_in_requires_login(self, client: AsyncClient):
        resp = await client.post("/api/v1/checkin")
        assert resp.status_code == 401


class TestMakeUp:
    @pytest.mark.asyncio
    async def test_make_up_missed_dates(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(
            db_session,
            [date(2026, 10, 1)],
            points=5,
            makeup_cards=2,
        )
        resp = await auth_client.post(
            "/api/v1/checkin/makeup",
            json={"dates": ["2026-11-05", "2026-11-18"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["restored_dates"] == ["2026-11-05", "2026-11-18"]
        assert data["summary"]["makeup_cards"] == 0
        assert data["summary"]["total_days"] == 3
        assert data["summary"]["points"] == 5
        for item in data["summary"]["calendar_mark"]:
            if item["date"] in ("2026-11-05", "2026-11-18"):
                assert item["signed"] is True
                assert item["missed"] is False

    @pytest.mark.asyncio
    async def test_make_up_not_enough_cards(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(
            db_session,
            [date(2026, 10, 1)],
            makeup_cards=1,
        )
        resp = await auth_client.post(
            "/api/v1/checkin/makeup",
            json={"dates": ["2026-11-05", "2026-11-18"]},
        )
        assert resp.status_code == 400
        assert "补签卡不足" in resp.json()["detail"]
        stats = await db_session.get(UserCheckinStats, USER_ID)
        await db_session.refresh(stats)
        assert stats.makeup_cards == 1

    @pytest.mark.asyncio
    async def test_make_up_outside_window(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, [date(2026, 8, 1)])
        resp = await auth_client.post(
            "/api/v1/checkin/makeup", json={"dates": ["2026-09-01"]}
        )
        assert resp.status_code == 400
        assert "超出近 30 天补签范围" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_make_up_existing_date(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(
            db_session, [date(2026, 10, 1), date(2026, 11, 18)]
        )
        resp = await auth_client.post(
            "/api/v1/checkin/makeup", json={"dates": ["2026-11-18"]}
        )
        assert resp.status_code == 400
        assert "已签到" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_make_up_rejects_today(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, [date(2026, 10, 1)])
        resp = await auth_client.post(
            "/api/v1/checkin/makeup", json={"dates": ["2026-11-26"]}
        )
        assert resp.status_code == 400
        assert "不是可补签的历史日期" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_make_up_rejects_duplicate_dates(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        await _seed_records(db_session, [date(2026, 10, 1)])
        resp = await auth_client.post(
            "/api/v1/checkin/makeup",
            json={"dates": ["2026-11-05", "2026-11-05"]},
        )
        assert resp.status_code == 400
        assert "不能重复" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_make_up_without_history(
        self, auth_client: AsyncClient
    ):
        resp = await auth_client.post(
            "/api/v1/checkin/makeup", json={"dates": ["2026-11-18"]}
        )
        assert resp.status_code == 400
        assert "暂无可补签" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_make_up_requires_login(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checkin/makeup", json={"dates": ["2026-11-18"]}
        )
        assert resp.status_code == 401
