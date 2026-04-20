from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_room import StudyRoom
from app.schemas.study_room import StudyRoomListResponse, StudyRoomResponse

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


async def list_study_rooms(
    db: AsyncSession, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
) -> StudyRoomListResponse:
    """Return paginated list of open study rooms."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(StudyRoom).where(StudyRoom.status == "open")
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(StudyRoom)
        .where(StudyRoom.status == "open")
        .order_by(StudyRoom.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    items = [StudyRoomResponse.model_validate(room) for room in result.scalars().all()]

    return StudyRoomListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
