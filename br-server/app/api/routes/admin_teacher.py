"""Admin teacher management API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.teacher import Teacher

router = APIRouter(prefix="/api/v1/admin/teachers", tags=["admin-teachers"])


@router.get("")
async def list_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取教师列表（用于下拉选择）。"""
    query = select(Teacher).order_by(Teacher.id.asc())
    if keyword:
        query = query.where(Teacher.name.ilike(f"%{keyword}%"))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    teachers = list(result.scalars().all())
    items = [
        {
            "id": t.id,
            "name": t.name,
            "avatar": t.avatar,
            "title": t.title,
        }
        for t in teachers
    ]
    return {"items": items, "total": len(items)}
