from sqlalchemy import select
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
