from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banner import Banner


async def list_active_banners(db: AsyncSession) -> list[Banner]:
    """Return all active banners ordered by sort_order ascending."""
    result = await db.execute(
        select(Banner)
        .where(Banner.is_active.is_(True))
        .order_by(Banner.sort_order.asc())
    )
    return list(result.scalars().all())
