from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City


async def get_active_cities(db: AsyncSession) -> list[City]:
    """Return active cities ordered by sort_order ascending."""
    result = await db.execute(
        select(City).where(City.status == "active").order_by(City.sort_order.asc())
    )
    return list(result.scalars().all())
