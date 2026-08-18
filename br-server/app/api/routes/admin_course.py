"""Admin course management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin_course import (
    AdminCourseCreate,
    AdminCourseDetailResponse,
    AdminCourseListResponse,
    AdminCourseUpdate,
)
from app.services.admin_course_service import AdminCourseService

router = APIRouter(prefix="/api/v1/admin/courses", tags=["admin-courses"])


@router.get("", response_model=AdminCourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    teacher_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """分页查询课程列表。"""
    service = AdminCourseService()
    return await service.list_courses(
        db, page=page, page_size=page_size,
        category=category, status=status, keyword=keyword, teacher_id=teacher_id,
    )


@router.get("/{course_id}", response_model=AdminCourseDetailResponse)
async def get_course_detail(course_id: int, db: AsyncSession = Depends(get_db)):
    """获取课程详情。"""
    service = AdminCourseService()
    result = await service.get_course_detail(db, course_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return result


@router.post("", response_model=AdminCourseDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_course(data: AdminCourseCreate, db: AsyncSession = Depends(get_db)):
    """创建新课程。"""
    service = AdminCourseService()
    try:
        course = await service.create_course(db, data)
        await db.commit()
        # 重新查询以返回完整详情
        result = await service.get_course_detail(db, course.id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="创建失败")
        return result
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{course_id}", response_model=AdminCourseDetailResponse)
async def update_course(course_id: int, data: AdminCourseUpdate, db: AsyncSession = Depends(get_db)):
    """更新课程信息。"""
    service = AdminCourseService()
    try:
        course = await service.update_course(db, course_id, data)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
        await db.commit()
        result = await service.get_course_detail(db, course_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="更新后查询失败")
        return result
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """删除课程。"""
    service = AdminCourseService()
    success = await service.delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    await db.commit()
    return {"message": "删除成功"}


@router.patch("/{course_id}/status")
async def toggle_course_status(
    course_id: int,
    status_param: str = Query(..., alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """切换课程状态。"""
    service = AdminCourseService()
    course = await service.toggle_course_status(db, course_id, status_param)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    await db.commit()
    return {"message": "状态更新成功", "status": status_param}
