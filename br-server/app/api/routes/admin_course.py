"""Admin course management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin_course import (
    AdminCourseCreate,
    AdminCourseDetailResponse,
    AdminCourseListResponse,
    AdminCourseUpdate,
    AdminLessonCreate,
    AdminLessonItem,
    AdminLessonUpdate,
    CourseScheduleCreate,
    CourseScheduleResponse,
    CourseScheduleUpdate,
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


# ── 课时 CRUD ──────────────────────────────────────────────


@router.get("/{course_id}/lessons", response_model=list[AdminLessonItem])
async def list_lessons(course_id: int, db: AsyncSession = Depends(get_db)):
    """查询课程的课时列表。"""
    service = AdminCourseService()
    return await service.list_lessons(db, course_id)


@router.post(
    "/{course_id}/lessons",
    response_model=AdminLessonItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    course_id: int,
    data: AdminLessonCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建课时。"""
    service = AdminCourseService()
    try:
        lesson = await service.create_lesson(db, course_id, data)
        await db.commit()
        return lesson
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{course_id}/lessons/{lesson_id}", response_model=AdminLessonItem)
async def update_lesson(
    course_id: int,
    lesson_id: int,
    data: AdminLessonUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新课时。"""
    service = AdminCourseService()
    try:
        lesson = await service.update_lesson(db, lesson_id, data)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课时不存在")
        await db.commit()
        return lesson
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{course_id}/lessons/{lesson_id}")
async def delete_lesson(
    course_id: int,
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除课时。"""
    service = AdminCourseService()
    success = await service.delete_lesson(db, lesson_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课时不存在")
    await db.commit()
    return {"message": "删除成功"}


# ── 排课 CRUD ──────────────────────────────────────────────────


@router.get("/{course_id}/schedules", response_model=list[CourseScheduleResponse])
async def list_schedules(course_id: int, db: AsyncSession = Depends(get_db)):
    """查询课程的所有排课记录。"""
    service = AdminCourseService()
    return await service.list_schedules(db, course_id)


@router.post(
    "/{course_id}/schedules",
    response_model=CourseScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    course_id: int,
    data: CourseScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增排课记录。"""
    service = AdminCourseService()
    try:
        result = await service.create_schedule(db, course_id, data)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{course_id}/schedules/{schedule_id}", response_model=CourseScheduleResponse)
async def update_schedule(
    course_id: int,
    schedule_id: int,
    data: CourseScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新排课记录。"""
    service = AdminCourseService()
    try:
        result = await service.update_schedule(db, schedule_id, data)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="排课记录不存在")
        await db.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{course_id}/schedules/{schedule_id}")
async def delete_schedule(
    course_id: int,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除排课记录。"""
    service = AdminCourseService()
    success = await service.delete_schedule(db, schedule_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="排课记录不存在")
    await db.commit()
    return {"message": "删除成功"}


@router.post("/{course_id}/schedules/{schedule_id}/postpone-lesson", response_model=CourseScheduleResponse)
async def postpone_lesson(
    course_id: int,
    schedule_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """延期某一课时及其后续所有课时。"""
    lesson_id = data.get("lesson_id")
    if not lesson_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lesson_id is required")
    service = AdminCourseService()
    try:
        result = await service.postpone_lesson(db, schedule_id, lesson_id)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
