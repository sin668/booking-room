# Booking Study Room Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement seat-based study room booking feature — backend Seat/Booking models + APIs, and frontend booking flow (date/time/seat selection, confirm, orders) matching prototype designs.

**Architecture:** Backend follows existing layered pattern (models → schemas → services → routes). Frontend follows uni-app Vue3 Options API pattern with SCSS. Booking is seat-level (not room-level), with three zones (quiet/keyboard/vip). Two booking entry paths: booking tab and store detail page.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy async / PostgreSQL / Alembic / pytest (backend); uni-app Vue3 / SCSS / uView 2.0 (frontend)

**OpenSpec:** `openspec/changes/booking-study-room-frontend/` contains proposal, design, specs, and tasks.

---

### Task 1: Seat Database Model

**Files:**
- Create: `br-server/app/models/seat.py`
- Modify: `br-server/app/models/__init__.py`
- Test: `br-server/tests/test_seat_model.py`

- [ ] **Step 1: Write the failing test**

```python
# br-server/tests/test_seat_model.py
"""Tests for Seat model."""
import pytest
from app.models.seat import Seat


class TestSeatModel:
    def test_seat_zone_enum_values(self):
        """Seat.zone must accept quiet/keyboard/vip."""
        for zone in ("quiet", "keyboard", "vip"):
            seat = Seat(zone=zone)
            assert seat.zone == zone

    def test_seat_status_default(self):
        """Seat.status defaults to 'available'."""
        seat = Seat(room_id=1, seat_number="A-01", zone="quiet", price_per_hour=6.0, row=1, col=1)
        assert seat.status == "available"

    def test_seat_required_fields(self):
        """Seat requires room_id, seat_number, zone, price_per_hour, row, col."""
        seat = Seat(room_id=1, seat_number="A-01", zone="quiet", price_per_hour=6.0, row=1, col=1)
        assert seat.seat_number == "A-01"
        assert seat.price_per_hour == 6.0
        assert seat.row == 1
        assert seat.col == 1

    def test_seat_floor_default(self):
        """Seat.floor defaults to 3."""
        seat = Seat(room_id=1, seat_number="A-01", zone="quiet", price_per_hour=6.0, row=1, col=1)
        assert seat.floor == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-server && python -m pytest tests/test_seat_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.seat'`

- [ ] **Step 3: Write the Seat model**

```python
# br-server/app/models/seat.py
from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    zone: Mapped[str] = mapped_column(String(20), nullable=False)  # quiet / keyboard / vip
    position: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 靠窗 / 中间 / 独立
    floor: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    price_per_hour: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    col: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 4: Export Seat from models __init__.py**

Add to `br-server/app/models/__init__.py`:

```python
from app.models.seat import Seat
```

Add `"Seat"` to `__all__`.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd br-server && python -m pytest tests/test_seat_model.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add br-server/app/models/seat.py br-server/app/models/__init__.py br-server/tests/test_seat_model.py
git commit -m "feat: add Seat database model"
```

---

### Task 2: Booking Database Model

**Files:**
- Create: `br-server/app/models/booking.py`
- Modify: `br-server/app/models/__init__.py`
- Test: `br-server/tests/test_booking_model.py`

- [ ] **Step 1: Write the failing test**

```python
# br-server/tests/test_booking_model.py
"""Tests for Booking model."""
import pytest
from decimal import Decimal
from app.models.booking import Booking


class TestBookingModel:
    def test_booking_status_default(self):
        """Booking.status defaults to 'confirmed'."""
        booking = Booking(
            seat_id=1, user_id="11111111-2222-3333-4444-555555555555",
            room_id=1, date="2026-05-01", start_time="09:00", end_time="12:00",
            total_price=Decimal("18.00"),
        )
        assert booking.status == "confirmed"

    def test_booking_required_fields(self):
        """Booking requires seat_id, user_id, room_id, date, start_time, end_time, total_price."""
        booking = Booking(
            seat_id=1, user_id="11111111-2222-3333-4444-555555555555",
            room_id=1, date="2026-05-01", start_time="09:00", end_time="12:00",
            total_price=Decimal("18.00"),
        )
        assert booking.seat_id == 1
        assert booking.total_price == Decimal("18.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-server && python -m pytest tests/test_booking_model.py -v`
Expected: FAIL

- [ ] **Step 3: Write the Booking model**

```python
# br-server/app/models/booking.py
import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", nullable=False
    )  # confirmed / cancelled / completed
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

Note: `user_id` is stored as String(36) to match the UUID string format from the auth system.

- [ ] **Step 4: Export Booking from models __init__.py**

Add to `br-server/app/models/__init__.py`:

```python
from app.models.booking import Booking
```

Add `"Booking"` to `__all__`.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd br-server && python -m pytest tests/test_booking_model.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add br-server/app/models/booking.py br-server/app/models/__init__.py br-server/tests/test_booking_model.py
git commit -m "feat: add Booking database model"
```

---

### Task 3: Alembic Migrations

**Files:**
- Create: `br-server/alembic/versions/<auto>_create_seats_and_bookings.py`

- [ ] **Step 1: Generate migration**

```bash
cd br-server && alembic revision --autogenerate -m "create_seats_and_bookings"
```

- [ ] **Step 2: Review the generated migration**

Open the generated file. It should contain:
- `create_table('seats', ...)` with columns: id, room_id, seat_number, zone, position, floor, price_per_hour, status, row, col, created_at, updated_at
- `create_table('bookings', ...)` with columns: id, seat_id, user_id, room_id, date, start_time, end_time, status, total_price, created_at, updated_at
- `create_index('ix_seats_room_id', 'seats', ['room_id'])`
- `create_index('ix_bookings_seat_id', 'bookings', ['seat_id'])`
- `create_index('ix_bookings_user_id', 'bookings', ['user_id'])`
- `create_index('ix_bookings_room_id', 'bookings', ['room_id'])`

- [ ] **Step 3: Apply migration**

```bash
cd br-server && alembic upgrade head
```

- [ ] **Step 4: Verify tables exist**

```bash
cd br-server && python -c "
import asyncio
from app.core.database import engine
from sqlalchemy import text, inspect

async def check():
    async with engine.connect() as conn:
        for table in ['seats', 'bookings']:
            result = await conn.execute(text(f\"SELECT COUNT(*) FROM {table}\"))
            print(f'{table}: OK')

asyncio.run(check())
"
```

- [ ] **Step 5: Commit**

```bash
git add br-server/alembic/versions/
git commit -m "feat: add seats and bookings alembic migration"
```

---

### Task 4: Seat Seed Data Script

**Files:**
- Create: `br-server/app/services/seed_seats.py`

- [ ] **Step 1: Write the seed script**

```python
# br-server/app/services/seed_seats.py
"""Seed seat data for existing study rooms."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat import Seat
from app.models.study_room import StudyRoom

ZONE_CONFIG = {
    "quiet": {"prefix": "A", "rows": 2, "cols_per_row": 7, "price": 6.00, "position": "靠窗"},
    "keyboard": {"prefix": "B", "rows": 2, "cols_per_row": 7, "price": 8.00, "position": "中间"},
    "vip": {"prefix": "D", "rows": 2, "cols_per_row": 6, "price": 12.00, "position": "独立"},
}


async def seed_seats_for_room(db: AsyncSession, room_id: int) -> int:
    """Generate seats for a study room. Returns number of seats created."""
    result = await db.execute(
        select(Seat).where(Seat.room_id == room_id).limit(1)
    )
    if result.scalar_one_or_none():
        return 0  # Already seeded

    count = 0
    for zone, config in ZONE_CONFIG.items():
        for row_idx in range(config["rows"]):
            for col_idx in range(config["cols_per_row"]):
                seat_number = f"{config['prefix']}{col_idx + 1:02d}"
                position = config["position"] if row_idx == 0 else "中间"
                seat = Seat(
                    room_id=room_id,
                    seat_number=seat_number,
                    zone=zone,
                    position=position,
                    floor=3,
                    price_per_hour=config["price"],
                    status="available",
                    row=row_idx,
                    col=col_idx,
                )
                db.add(seat)
                count += 1
    return count


async def seed_all_rooms(db: AsyncSession) -> int:
    """Seed seats for all rooms. Returns total seats created."""
    result = await db.execute(select(StudyRoom))
    rooms = result.scalars().all()
    total = 0
    for room in rooms:
        total += await seed_seats_for_room(db, room.id)
    await db.flush()
    return total
```

- [ ] **Step 2: Run the seed script**

```bash
cd br-server && python -c "
import asyncio
from app.core.database import async_session
from app.services.seed_seats import seed_all_rooms

async def main():
    async with async_session() as db:
        count = await seed_all_rooms(db)
        await db.commit()
        print(f'Created {count} seats')

asyncio.run(main())
"
```

- [ ] **Step 3: Verify seed data**

```bash
cd br-server && python -c "
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT zone, COUNT(*) FROM seats GROUP BY zone'))
        for row in result:
            print(f'{row[0]}: {row[1]} seats')

asyncio.run(check())
"
```

Expected output:
```
quiet: 28 seats
keyboard: 28 seats
vip: 24 seats
```

- [ ] **Step 4: Commit**

```bash
git add br-server/app/services/seed_seats.py
git commit -m "feat: add seat seed data script"
```

---

### Task 5: Seat Schemas

**Files:**
- Create: `br-server/app/schemas/seat.py`

- [ ] **Step 1: Write the schemas**

```python
# br-server/app/schemas/seat.py
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SeatResponse(BaseModel):
    id: int
    room_id: int
    seat_number: str
    zone: str
    position: str | None
    floor: int
    price_per_hour: Decimal
    status: str
    row: int
    col: int
    is_available: bool = True  # Only populated when time filter is applied

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/schemas/seat.py
git commit -m "feat: add Seat Pydantic schemas"
```

---

### Task 6: Seat Service

**Files:**
- Create: `br-server/app/services/seat_service.py`
- Test: `br-server/tests/test_seat_service.py`

- [ ] **Step 1: Write the failing tests**

```python
# br-server/tests/test_seat_service.py
"""Tests for Seat service."""
import pytest
from unittest.mock import AsyncMock
from app.services.seat_service import list_seats, check_seat_available


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestListSeats:
    async def test_list_seats_without_time_filter(self, mock_db):
        """list_seats returns all seats when no time filter."""
        from app.models.seat import Seat
        seat = Seat(
            id=1, room_id=1, seat_number="A-01", zone="quiet",
            position="靠窗", floor=3, price_per_hour=6.0, status="available",
            row=0, col=0,
        )
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [seat]
        mock_db.execute = AsyncMock(return_value=mock_result)

        seats = await list_seats(mock_db, room_id=1)
        assert len(seats) == 1
        assert seats[0].seat_number == "A-01"
        assert seats[0].is_available is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-server && python -m pytest tests/test_seat_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the service**

```python
# br-server/app/services/seat_service.py
from datetime import date, time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.schemas.seat import SeatResponse


async def list_seats(
    db: AsyncSession,
    room_id: int,
    booking_date: date | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
) -> list[SeatResponse]:
    """List seats for a room, optionally with availability for a time slot."""
    result = await db.execute(
        select(Seat).where(Seat.room_id == room_id).order_by(Seat.row, Seat.col)
    )
    seats = result.scalars().all()

    if booking_date is None or start_time is None or end_time is None:
        return [SeatResponse.model_validate(s) for s in seats]

    # Get booked seat_ids for this room/date/time overlap
    booked_result = await db.execute(
        select(Booking.seat_id).where(
            and_(
                Booking.room_id == room_id,
                Booking.date == booking_date,
                Booking.status == "confirmed",
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
        )
    )
    booked_seat_ids = {row[0] for row in booked_result.all()}

    responses = []
    for seat in seats:
        data = SeatResponse.model_validate(seat)
        data.is_available = seat.id not in booked_seat_ids and seat.status == "available"
        responses.append(data)
    return responses
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd br-server && python -m pytest tests/test_seat_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add br-server/app/services/seat_service.py br-server/tests/test_seat_service.py
git commit -m "feat: add Seat service with availability check"
```

---

### Task 7: Seat API Route

**Files:**
- Create: `br-server/app/api/routes/seat.py`
- Modify: `br-server/app/main.py`

- [ ] **Step 1: Write the route**

```python
# br-server/app/api/routes/seat.py
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.seat import SeatResponse
from app.services import seat_service

router = APIRouter(prefix="/api/v1/rooms/{room_id}/seats", tags=["seats"])


@router.get("", response_model=list[SeatResponse])
async def list_seats(
    room_id: int,
    booking_date: date | None = Query(None, alias="date"),
    start_time: time | None = Query(None),
    end_time: time | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[SeatResponse]:
    """List seats for a room, with optional availability check."""
    return await seat_service.list_seats(
        db, room_id=room_id, booking_date=booking_date,
        start_time=start_time, end_time=end_time,
    )
```

- [ ] **Step 2: Register route in main.py**

Add to `br-server/app/main.py` imports:

```python
from app.api.routes.seat import router as seat_router
```

Add after other `app.include_router(...)` calls:

```python
app.include_router(seat_router)
```

- [ ] **Step 3: Write API integration test**

```python
# br-server/tests/test_seat_api.py
"""Integration tests for Seat API."""
import pytest
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from httpx import AsyncClient


@pytest.fixture
async def seeded_room(db_session):
    """Create a study room with seats."""
    room = StudyRoom(
        name="测试自习室", address="测试地址",
        status="open", min_price=6.00,
    )
    db_session.add(room)
    await db_session.flush()
    for i in range(3):
        seat = Seat(
            room_id=room.id, seat_number=f"A-{i+1:02d}", zone="quiet",
            floor=3, price_per_hour=6.0, status="available", row=0, col=i,
        )
        db_session.add(seat)
    await db_session.flush()
    return room


class TestListSeatsAPI:
    async def test_list_seats_success(self, client, seeded_room):
        response = await client.get(f"/api/v1/rooms/{seeded_room.id}/seats/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["seat_number"] == "A-01"

    async def test_list_seats_room_not_found(self, client):
        response = await client.get("/api/v1/rooms/9999/seats/")
        assert response.status_code == 200  # Returns empty list since no filter on room existence
```

- [ ] **Step 4: Run tests**

Run: `cd br-server && python -m pytest tests/test_seat_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add br-server/app/api/routes/seat.py br-server/app/main.py br-server/tests/test_seat_api.py
git commit -m "feat: add Seat API route for listing room seats"
```

---

### Task 8: Booking Schemas

**Files:**
- Create: `br-server/app/schemas/booking.py`

- [ ] **Step 1: Write the schemas**

```python
# br-server/app/schemas/booking.py
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    seat_id: int
    date: date
    start_time: time
    end_time: time


class SeatBrief(BaseModel):
    id: int
    seat_number: str
    zone: str
    position: str | None
    price_per_hour: Decimal

    model_config = ConfigDict(from_attributes=True)


class RoomBrief(BaseModel):
    id: int
    name: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    seat_id: int
    user_id: str
    room_id: int
    date: date
    start_time: time
    end_time: time
    status: str
    total_price: Decimal
    created_at: datetime
    seat: SeatBrief | None = None
    room: RoomBrief | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/schemas/booking.py
git commit -m "feat: add Booking Pydantic schemas"
```

---

### Task 9: Booking Service

**Files:**
- Create: `br-server/app/services/booking_service.py`
- Test: `br-server/tests/test_booking_service.py`

- [ ] **Step 1: Write the failing tests**

```python
# br-server/tests/test_booking_service.py
"""Tests for Booking service."""
import uuid
from datetime import date, time
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom


FIXED_USER_ID = "11111111-2222-3333-4444-555555555555"


class TestCreateBooking:
    async def test_create_booking_success(self, client, db_session):
        """Create booking returns confirmed status."""
        room = StudyRoom(name="测试", address="地址", status="open", min_price=6.0)
        db_session.add(room)
        seat = Seat(
            room_id=1, seat_number="A-01", zone="quiet",
            floor=3, price_per_hour=6.0, status="available", row=0, col=0,
        )
        db_session.add(seat)
        await db_session.flush()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": seat.id, "date": "2026-05-01",
                "start_time": "09:00", "end_time": "12:00",
            },
            headers={"Authorization": f"Bearer {self._make_token()}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["total_price"] == "18.00"

    async def test_create_booking_time_conflict(self, client, db_session):
        """Booking with overlapping time returns 409."""
        room = StudyRoom(name="测试", address="地址", status="open", min_price=6.0)
        db_session.add(room)
        seat = Seat(
            room_id=1, seat_number="A-01", zone="quiet",
            floor=3, price_per_hour=6.0, status="available", row=0, col=0,
        )
        db_session.add(seat)
        booking = Booking(
            seat_id=1, user_id=FIXED_USER_ID, room_id=1,
            date=date(2026, 5, 1), start_time=time(10, 0), end_time=time(12, 0),
            total_price=Decimal("12.00"), status="confirmed",
        )
        db_session.add(booking)
        await db_session.flush()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": seat.id, "date": "2026-05-01",
                "start_time": "09:00", "end_time": "11:00",
            },
            headers={"Authorization": f"Bearer {self._make_token()}"},
        )
        assert response.status_code == 409

    async def test_create_booking_invalid_time_range(self, client, db_session):
        """End time before start time returns 422."""
        room = StudyRoom(name="测试", address="地址", status="open", min_price=6.0)
        db_session.add(room)
        seat = Seat(
            room_id=1, seat_number="A-01", zone="quiet",
            floor=3, price_per_hour=6.0, status="available", row=0, col=0,
        )
        db_session.add(seat)
        await db_session.flush()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": seat.id, "date": "2026-05-01",
                "start_time": "12:00", "end_time": "09:00",
            },
            headers={"Authorization": f"Bearer {self._make_token()}"},
        )
        assert response.status_code == 422
```

- [ ] **Step 2: Write the service**

```python
# br-server/app/services/booking_service.py
from datetime import date, time
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    RoomBrief,
    SeatBrief,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


async def create_booking(
    db: AsyncSession, user_id: str, data: BookingCreate
) -> BookingResponse:
    """Create a booking with conflict detection."""
    if data.end_time <= data.start_time:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="结束时间必须晚于开始时间")

    # Get seat
    seat_result = await db.execute(select(Seat).where(Seat.id == data.seat_id))
    seat = seat_result.scalar_one_or_none()
    if seat is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="座位不存在")
    if seat.status == "maintenance":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="该座位正在维护中")

    # Check time conflict on same seat
    conflict = await db.execute(
        select(Booking).where(
            and_(
                Booking.seat_id == data.seat_id,
                Booking.date == data.date,
                Booking.status == "confirmed",
                Booking.start_time < data.end_time,
                Booking.end_time > data.start_time,
            )
        ).limit(1)
    )
    if conflict.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="该座位该时段已被预约")

    # Calculate price: hours * price_per_hour
    start_seconds = data.start_time.hour * 3600 + data.start_time.minute * 60
    end_seconds = data.end_time.hour * 3600 + data.end_time.minute * 60
    hours = (end_seconds - start_seconds) / 3600
    total_price = Decimal(str(round(float(seat.price_per_hour) * hours, 2)))

    booking = Booking(
        seat_id=data.seat_id,
        user_id=user_id,
        room_id=seat.room_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        total_price=total_price,
        status="confirmed",
    )
    db.add(booking)
    await db.flush()

    return await _build_booking_response(db, booking)


async def list_bookings(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status_filter: str | None = None,
) -> BookingListResponse:
    """List bookings for a user with pagination."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    conditions = [Booking.user_id == user_id]
    if status_filter:
        conditions.append(Booking.status == status_filter)

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(*conditions)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Booking)
        .where(*conditions)
        .order_by(Booking.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    items = []
    for booking in result.scalars().all():
        items.append(await _build_booking_response(db, booking))

    return BookingListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


async def get_booking(
    db: AsyncSession, booking_id: int, user_id: str
) -> BookingResponse:
    """Get a single booking by ID, only if it belongs to the user."""
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="预约不存在")
    return await _build_booking_response(db, booking)


async def cancel_booking(
    db: AsyncSession, booking_id: int, user_id: str
) -> BookingResponse:
    """Cancel a confirmed booking."""
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="预约不存在")
    if booking.status != "confirmed":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="该预约已取消")
    booking.status = "cancelled"
    await db.flush()
    return await _build_booking_response(db, booking)


async def _build_booking_response(db: AsyncSession, booking: Booking) -> BookingResponse:
    """Build a BookingResponse with related seat and room info."""
    seat_result = await db.execute(select(Seat).where(Seat.id == booking.seat_id))
    seat = seat_result.scalar_one_or_none()
    room_result = await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))
    room = room_result.scalar_one_or_none()

    return BookingResponse(
        id=booking.id,
        seat_id=booking.seat_id,
        user_id=booking.user_id,
        room_id=booking.room_id,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        total_price=booking.total_price,
        created_at=booking.created_at,
        seat=SeatBrief.model_validate(seat) if seat else None,
        room=RoomBrief.model_validate(room) if room else None,
    )
```

- [ ] **Step 3: Run tests**

Run: `cd br-server && python -m pytest tests/test_booking_service.py -v`
Expected: PASS (may need conftest adjustment for auth token)

- [ ] **Step 4: Commit**

```bash
git add br-server/app/services/booking_service.py br-server/tests/test_booking_service.py
git commit -m "feat: add Booking service with conflict detection"
```

---

### Task 10: Booking API Route

**Files:**
- Create: `br-server/app/api/routes/booking.py`
- Modify: `br-server/app/main.py`
- Test: `br-server/tests/test_booking_api.py`

- [ ] **Step 1: Write the route**

```python
# br-server/app/api/routes/booking.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse
from app.services import booking_service

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    return await booking_service.create_booking(db, str(user_id), data)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: str | None = Query(None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingListResponse:
    return await booking_service.list_bookings(
        db, str(user_id), page=page, page_size=page_size, status_filter=status
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    return await booking_service.get_booking(db, booking_id, str(user_id))


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    return await booking_service.cancel_booking(db, booking_id, str(user_id))
```

- [ ] **Step 2: Register route in main.py**

Add to imports:

```python
from app.api.routes.booking import router as booking_router
```

Add router:

```python
app.include_router(booking_router)
```

- [ ] **Step 3: Write API integration tests**

```python
# br-server/tests/test_booking_api.py
"""Integration tests for Booking API."""
import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_current_user_id
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom


FIXED_USER_ID = uuid.UUID("11111111-2222-3333-4444-5555555555")


@pytest.fixture
async def auth_client(client):
    """Override auth to return fixed user ID."""
    app.dependency_overrides[get_current_user_id] = lambda: FIXED_USER_ID
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def setup_room_with_seat(db_session):
    room = StudyRoom(name="测试自习室", address="测试地址", status="open", min_price=6.0)
    db_session.add(room)
    seat = Seat(
        room_id=1, seat_number="A-01", zone="quiet",
        floor=3, price_per_hour=6.0, status="available", row=0, col=0,
    )
    db_session.add(seat)
    await db_session.flush()
    return {"room_id": room.id, "seat_id": seat.id}


class TestCreateBooking:
    async def test_success(self, auth_client, setup_room_with_seat):
        response = await auth_client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": setup_room_with_seat["seat_id"],
                "date": "2026-05-01",
                "start_time": "09:00", "end_time": "12:00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["total_price"] == "18.00"

    async def test_unauthorized(self, client, setup_room_with_seat):
        response = await client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": setup_room_with_seat["seat_id"],
                "date": "2026-05-01",
                "start_time": "09:00", "end_time": "12:00",
            },
        )
        assert response.status_code == 401

    async def test_conflict(self, auth_client, db_session, setup_room_with_seat):
        booking = Booking(
            seat_id=setup_room_with_seat["seat_id"],
            user_id=str(FIXED_USER_ID),
            room_id=setup_room_with_seat["room_id"],
            date=date(2026, 5, 1),
            start_time=time(10, 0), end_time=time(12, 0),
            total_price=Decimal("12.00"), status="confirmed",
        )
        db_session.add(booking)
        await db_session.flush()

        response = await auth_client.post(
            "/api/v1/bookings/",
            json={
                "seat_id": setup_room_with_seat["seat_id"],
                "date": "2026-05-01",
                "start_time": "09:00", "end_time": "11:00",
            },
        )
        assert response.status_code == 409


class TestListBookings:
    async def test_success(self, auth_client, db_session, setup_room_with_seat):
        booking = Booking(
            seat_id=setup_room_with_seat["seat_id"],
            user_id=str(FIXED_USER_ID),
            room_id=setup_room_with_seat["room_id"],
            date=date(2026, 5, 1),
            start_time=time(9, 0), end_time=time(12, 0),
            total_price=Decimal("18.00"), status="confirmed",
        )
        db_session.add(booking)
        await db_session.flush()

        response = await auth_client.get("/api/v1/bookings/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    async def test_filter_by_status(self, auth_client, db_session, setup_room_with_seat):
        for s in ["confirmed", "cancelled"]:
            db_session.add(Booking(
                seat_id=setup_room_with_seat["seat_id"],
                user_id=str(FIXED_USER_ID),
                room_id=setup_room_with_seat["room_id"],
                date=date(2026, 5, 1),
                start_time=time(9, 0), end_time=time(10, 0),
                total_price=Decimal("6.00"), status=s,
            ))
        await db_session.flush()

        response = await auth_client.get("/api/v1/bookings/?status=confirmed")
        data = response.json()
        assert data["total"] == 1
```

- [ ] **Step 4: Run tests**

Run: `cd br-server && python -m pytest tests/test_booking_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add br-server/app/api/routes/booking.py br-server/app/main.py br-server/tests/test_booking_api.py
git commit -m "feat: add Booking API routes (create/list/detail/cancel)"
```

---

### Task 11: Backend Code Review Checkpoint

- [ ] **Step 1: Run all backend tests**

```bash
cd br-server && python -m pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 2: Verify API docs**

Start the server and visit `/docs`:

```bash
cd br-server && uvicorn app.main:app --reload
```

Verify endpoints are listed: `GET /api/v1/rooms/{room_id}/seats/`, `POST /api/v1/bookings/`, `GET /api/v1/bookings/`, etc.

---

### Task 12: Frontend API Layer

**Files:**
- Create: `br-app/src/api/seats.js`
- Create: `br-app/src/api/bookings.js`

- [ ] **Step 1: Write seats API**

```javascript
// br-app/src/api/seats.js
import { get } from '@/utils/request'

/**
 * 获取自习室座位列表
 * @param {number} roomId - 自习室ID
 * @param {Object} params - { date, start_time, end_time }
 */
export function getSeats(roomId, params) {
  return get(`/api/v1/rooms/${roomId}/seats/`, params)
}
```

- [ ] **Step 2: Write bookings API**

```javascript
// br-app/src/api/bookings.js
import { get, post } from '@/utils/request'

/**
 * 创建预约
 */
export function createBooking(data) {
  return post('/api/v1/bookings/', data)
}

/**
 * 获取我的预约列表
 */
export function getBookings(params) {
  return get('/api/v1/bookings/', params)
}

/**
 * 获取预约详情
 */
export function getBooking(id) {
  return get(`/api/v1/bookings/${id}/`)
}

/**
 * 取消预约
 */
export function cancelBooking(id) {
  return post(`/api/v1/bookings/${id}/cancel/`)
}
```

- [ ] **Step 3: Commit**

```bash
git add br-app/src/api/seats.js br-app/src/api/bookings.js
git commit -m "feat: add frontend seats and bookings API modules"
```

---

### Task 13: Booking Tab Page (Main Booking UI)

**Files:**
- Rewrite: `br-app/src/pages/booking/index.vue`

This is the core interaction page. Refer to `prototype/booking.html` for exact layout. Key sections: date selector (horizontal scroll, 7 days), time slot grid (2-hour slots), zone filter tabs, seat map grid, bottom info bar with "立即预约" button.

- [ ] **Step 1: Rewrite booking/index.vue**

Implement the full page following prototype/booking.html pattern. Key implementation details:

- **Date selector**: Generate 7 days from today using `new Date()`, display as horizontal scroll with weekday + day number
- **Time slots**: Fixed 2-hour slots from business hours (08:00-22:00): `["08:00-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00", "16:00-18:00", "18:00-20:00", "20:00-22:00"]`
- **Zone filter**: Tabs for 全部/静音区/键盘区/VIP区
- **Seat map**: Grid layout using `row` and `col` from API, color-coded: green (available), blue (selected), gray (occupied/maintenance), orange (VIP)
- **Bottom bar**: Fixed at bottom, shows selected seat info (number, zone, position, time, price), "立即预约" button
- **API calls**: `getRooms()` on mount to get first room, `getSeats(roomId, {date, start_time, end_time})` when date/time changes
- **Navigation**: On "立即预约" tap → `uni.navigateTo({ url: '/pages/booking/confirm?seat_id=X&room_id=Y&date=Z&start_time=A&end_time=B' })`

The page uses Options API (matching existing pattern in index/index.vue), SCSS scoped styles with `$primary`, `$text-primary`, etc. variables.

- [ ] **Step 2: Test in browser**

Run `npm run dev:h5` in br-app directory, verify:
- Date selector renders 7 days
- Time slot grid renders 7 slots
- Seat map loads from API
- Selecting a seat updates bottom bar
- "立即预约" navigates to confirm page

- [ ] **Step 3: Commit**

```bash
git add br-app/src/pages/booking/index.vue
git commit -m "feat: implement booking tab page with date/time/seat selection"
```

---

### Task 14: Store Detail Page

**Files:**
- Create: `br-app/src/pages/booking/detail.vue`

Refer to `prototype/store-detail.html`. Key sections: cover image with gradient overlay, store info card (name, status, rating, address, hours, zone tags), environment photos carousel, seat stats (total/available/occupied/maintenance), bottom bar (favorite button + "立即预约").

- [ ] **Step 1: Create detail.vue**

Implementation notes:
- Receives `room_id` via page params (`onLoad(options)`)
- Calls `getRooms()` or a single-room endpoint to get room data (currently only list API exists, so fetch page 1 and filter, or add a single-room endpoint later)
- Seat stats: call `getSeats(room_id)` and compute: total = all.length, available = filtered by `is_available`, occupied = total - available, maintenance = filtered by `status === 'maintenance'`
- Bottom "立即预约" → `uni.navigateTo({ url: '/pages/booking/seat-select?room_id=X' })`
- Uses `uni.navigateTo` for back button via `uni.navigateBack()`
- Zone tags rendered as colored pills (静音区, 键盘区, VIP区, 免费WiFi, 充电插座)

- [ ] **Step 2: Register in pages.json**

Add to `pages` array in `br-app/src/pages.json`:

```json
{
  "path": "pages/booking/detail",
  "style": {
    "navigationBarTitleText": "门店详情",
    "navigationStyle": "custom"
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add br-app/src/pages/booking/detail.vue br-app/src/pages.json
git commit -m "feat: add store detail page with seat stats"
```

---

### Task 15: Seat Select Page

**Files:**
- Create: `br-app/src/pages/booking/seat-select.vue`

Refer to `prototype/seat-select.html`. Key sections: zone tabs (全部/静音区¥6/h/键盘区¥8/h/VIP区¥12/h), floor selector (3楼/4楼/5楼 — MVP: fixed 3楼, hide selector), seat map grouped by zone with desk rows, legend (可选/已选/已占/VIP), bottom bar (seat info + "确认选座").

- [ ] **Step 1: Create seat-select.vue**

Implementation notes:
- Receives `room_id` via page params
- Needs date and time — if coming from store detail (no date/time selected), show a date/time picker first, or redirect to booking tab. MVP: require date and time as query params, or add inline date/time picker
- Calls `getSeats(room_id, { date, start_time, end_time })` to load seat map
- Zone tabs filter the seat list by `zone` field
- Seat map grouped by zone with section headers (静音区 section, 键盘区 section, VIP区 section)
- Each seat rendered as a small square with seat_number text, color-coded
- VIP seats (`zone === 'vip'`) styled orange
- Selected seat highlighted blue
- Bottom bar shows: seat number, zone tag, position, time, calculated price
- "确认选座" → navigate to confirm page with all params

- [ ] **Step 2: Register in pages.json**

```json
{
  "path": "pages/booking/seat-select",
  "style": {
    "navigationBarTitleText": "选择座位"
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add br-app/src/pages/booking/seat-select.vue br-app/src/pages.json
git commit -m "feat: add seat selection page with zone-filtered seat map"
```

---

### Task 16: Order Confirm Page

**Files:**
- Create: `br-app/src/pages/booking/confirm.vue`

Refer to `prototype/order-confirm.html`. Key sections: store info card, seat info card, date/time display, price summary (seat fee, coupon placeholder, total), bottom bar (total + "立即支付" button), success modal with booking summary.

- [ ] **Step 1: Create confirm.vue**

Implementation notes:
- Receives query params: `room_id`, `seat_id`, `date`, `start_time`, `end_time`
- On mount, load seat and room info via API calls
- Display: store name, seat number + zone + position, date, time range, hours, price
- MVP: no real payment. "立即支付" calls `createBooking()` API
- On success (201): show success modal with booking info (order number, store, seat, time, amount), "完成" button → `uni.switchTab({ url: '/pages/orders/index' })`
- On conflict (409): `uni.showToast({ title: '该座位该时段已被预约', icon: 'none' })`
- On network error: `uni.showToast({ title: '预约失败，请重试', icon: 'none' })`
- Loading state: "立即支付" button shows spinner while submitting

- [ ] **Step 2: Register in pages.json**

```json
{
  "path": "pages/booking/confirm",
  "style": {
    "navigationBarTitleText": "确认订单"
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add br-app/src/pages/booking/confirm.vue br-app/src/pages.json
git commit -m "feat: add order confirmation page with booking submission"
```

---

### Task 17: Orders List Page

**Files:**
- Rewrite: `br-app/src/pages/orders/index.vue`

Refer to `prototype/orders.html`. Key sections: status filter tabs (全部/已确认/已取消/已完成), booking list cards (store name, seat number, date, time range, status badge), empty state with "去预约" button.

- [ ] **Step 1: Rewrite orders/index.vue**

Implementation notes:
- On `onShow()`: call `getBookings({ page: 1, page_size: 20, status: currentFilter })`
- Status tabs at top: 全部(null)/已确认(confirmed)/已取消(cancelled)/已完成(completed)
- Each card shows: store name (from `room.name`), seat number + zone (from `seat.seat_number`), date, time range, status badge
- Status badge colors: confirmed = green, cancelled = gray, completed = blue (using `$success`, `$text-muted`, `$primary`)
- Pull-down refresh and load-more pagination
- Empty state: icon + "暂无预约记录" + "去预约" button → `uni.switchTab({ url: '/pages/booking/index' })`

- [ ] **Step 2: Commit**

```bash
git add br-app/src/pages/orders/index.vue
git commit -m "feat: implement orders list page with status filtering"
```

---

### Task 18: Update Home Page Room Card Navigation

**Files:**
- Modify: `br-app/src/pages/index/index.vue`

- [ ] **Step 1: Update onTapRoom to navigate to booking detail**

In `br-app/src/pages/index/index.vue`, the existing `onTapRoom` method navigates to `/pages/room/detail?id=X`. Update it to use the new booking detail page:

```javascript
onTapRoom(room) {
  uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
},
```

- [ ] **Step 2: Commit**

```bash
git add br-app/src/pages/index/index.vue
git commit -m "feat: update home page room card to navigate to booking detail"
```

---

### Task 19: API Documentation Update

**Files:**
- Modify: `docs/api.md`

- [ ] **Step 1: Add seats and bookings API documentation**

Append to `docs/api.md`:

```
## Seats API

### GET /api/v1/rooms/{room_id}/seats/
List seats for a room.

Query Parameters:
- date (optional): YYYY-MM-DD format
- start_time (optional): HH:MM format
- end_time (optional): HH:MM format

## Bookings API

### POST /api/v1/bookings/
Create a booking. Requires authentication.

Request Body:
- seat_id (int, required)
- date (string, required, YYYY-MM-DD)
- start_time (string, required, HH:MM)
- end_time (string, required, HH:MM)

### GET /api/v1/bookings/
List current user's bookings. Requires authentication.

Query Parameters:
- page (int, default 1)
- page_size (int, default 10, max 50)
- status (string, optional): confirmed/cancelled/completed

### GET /api/v1/bookings/{booking_id}/
Get booking detail. Requires authentication.

### POST /api/v1/bookings/{booking_id}/cancel/
Cancel a booking. Requires authentication.
```

- [ ] **Step 2: Commit**

```bash
git add docs/api.md
git commit -m "docs: add seats and bookings API documentation"
```

---

### Task 20: Final Verification

- [ ] **Step 1: Run all backend tests**

```bash
cd br-server && python -m pytest tests/ -v --tb=short
```

- [ ] **Step 2: Verify frontend build**

```bash
cd br-app && npm run build:h5
```

- [ ] **Step 3: Manual smoke test in browser**

```bash
cd br-app && npm run dev:h5
```

Verify the full flow:
1. Booking tab → select date/time → seat appears → select seat → "立即预约" → confirm page
2. "立即支付" → success modal → redirects to orders tab
3. Orders tab shows the booking
4. Home page → click room card → detail page → "立即预约" → seat-select page

- [ ] **Step 4: Final commit if any fixes needed**
