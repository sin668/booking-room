"""API tests for homepage and study room endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_room import StudyRoom


class TestStudyRoomAPI:
    async def test_room_type_filter(self, client: AsyncClient, db_session: AsyncSession):
        db_session.add(StudyRoom(name="Study Room", address="Addr A", status="open", min_price=10.00, room_type="study"))
        db_session.add(StudyRoom(name="Training Room", address="Addr B", status="open", min_price=50.00, room_type="training"))
        await db_session.flush()

        resp = await client.get("/api/v1/rooms?room_type=study")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Study Room"

    async def test_room_type_in_response(self, client: AsyncClient, db_session: AsyncSession):
        db_session.add(StudyRoom(name="Test Room", address="Addr", status="open", min_price=10.00, room_type="training"))
        await db_session.flush()

        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        assert resp.json()["items"][0]["room_type"] == "training"
