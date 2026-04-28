from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.seat import SeatResponse, SeatWithAvailabilityResponse
from app.services import seat_service

router = APIRouter(prefix="/api/v1/rooms", tags=["seats"])


@router.get("/{room_id}/seats/", response_model=list[SeatResponse] | list[SeatWithAvailabilityResponse])
async def list_seats(
    room_id: int,
    target_date: date | None = Query(None, alias="date"),
    start_time: time | None = Query(None),
    end_time: time | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[SeatResponse] | list[SeatWithAvailabilityResponse]:
    try:
        return await seat_service.list_seats(db, room_id, target_date, start_time, end_time)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
