import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity


async def list_active_activities(db: AsyncSession) -> list[Activity]:
    """Return all active activities ordered by sort_order ascending."""
    result = await db.execute(
        select(Activity)
        .where(Activity.is_active.is_(True))
        .order_by(Activity.sort_order.asc())
    )
    return list(result.scalars().all())


async def list_activities(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """Return paginated activity list with optional keyword search and status filter."""
    query = select(Activity)
    count_query = select(func.count(Activity.id))

    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )
        count_query = count_query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )

    if is_active is not None:
        query = query.where(Activity.is_active.is_(is_active))
        count_query = count_query.where(Activity.is_active.is_(is_active))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    if offset > total and total > 0:
        offset = (total_pages - 1) * page_size

    query = query.order_by(Activity.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def get_activity_by_id(db: AsyncSession, activity_id: int) -> Activity | None:
    """Return a single activity by ID, or None if not found."""
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    return result.scalar_one_or_none()


async def create_activity(db: AsyncSession, data: dict) -> Activity:
    """Create a new activity."""
    activity = Activity(**data)
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


async def update_activity(db: AsyncSession, activity: Activity, data: dict) -> Activity:
    """Update an existing activity with the given fields."""
    for key, value in data.items():
        if value is not None:
            setattr(activity, key, value)
    await db.flush()
    await db.refresh(activity)
    return activity


async def delete_activity(db: AsyncSession, activity: Activity) -> None:
    """Delete an activity."""
    await db.delete(activity)
    await db.flush()


async def toggle_activity_status(db: AsyncSession, activity: Activity, is_active: bool) -> Activity:
    """Toggle activity active status."""
    activity.is_active = is_active
    await db.flush()
    await db.refresh(activity)
    return activity
