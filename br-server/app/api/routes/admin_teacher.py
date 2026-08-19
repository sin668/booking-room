"""Admin teacher management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.admin_teacher import (
    AdminTeacherCreate,
    AdminTeacherDetail,
    AdminTeacherListResponse,
    AdminTeacherStatusUpdate,
    AdminTeacherUpdate,
)
from app.services import admin_teacher_service

router = APIRouter(prefix="/api/v1/admin/teachers", tags=["admin-teachers"])


@router.get("", response_model=AdminTeacherListResponse, dependencies=[Depends(require_admin_permission("teacher:view"))])
async def list_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str | None = None,
    status_filter: str | None = Query(None, alias="status", pattern="^(active|inactive)$"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询老师列表（兼容排课老师下拉）。"""
    return await admin_teacher_service.list_teachers(
        db, page=page, page_size=page_size, keyword=keyword, status=status_filter
    )


@router.get("/{teacher_id}", response_model=AdminTeacherDetail, dependencies=[Depends(require_admin_permission("teacher:view"))])
async def get_teacher_detail(teacher_id: int, db: AsyncSession = Depends(get_db)):
    """获取老师详情。"""
    result = await admin_teacher_service.get_teacher_detail(db, teacher_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="老师不存在")
    return result


@router.post("", response_model=AdminTeacherDetail, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_permission("teacher:create"))])
async def create_teacher(data: AdminTeacherCreate, db: AsyncSession = Depends(get_db)):
    """新增老师。"""
    try:
        teacher = await admin_teacher_service.create_teacher(db, data)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    result = await admin_teacher_service.get_teacher_detail(db, teacher.id)
    assert result is not None
    return result


@router.put("/{teacher_id}", response_model=AdminTeacherDetail, dependencies=[Depends(require_admin_permission("teacher:update"))])
async def update_teacher(teacher_id: int, data: AdminTeacherUpdate, db: AsyncSession = Depends(get_db)):
    """更新老师信息。"""
    try:
        teacher = await admin_teacher_service.update_teacher(db, teacher_id, data)
        if teacher is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="老师不存在")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    result = await admin_teacher_service.get_teacher_detail(db, teacher_id)
    assert result is not None
    return result


@router.delete("/{teacher_id}", dependencies=[Depends(require_admin_permission("teacher:delete"))])
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    """删除老师；存在关联排课时拒绝删除。"""
    result = await admin_teacher_service.delete_teacher(db, teacher_id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="老师不存在")
    if result == "has_schedules":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该老师存在关联排课，无法删除")
    await db.commit()
    return {"message": "删除成功"}


@router.patch("/{teacher_id}/status", response_model=AdminTeacherDetail, dependencies=[Depends(require_admin_permission("teacher:status"))])
async def toggle_teacher_status(
    teacher_id: int,
    data: AdminTeacherStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """停用/启用老师。"""
    teacher = await admin_teacher_service.toggle_status(db, teacher_id, data.status)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="老师不存在")
    await db.commit()
    result = await admin_teacher_service.get_teacher_detail(db, teacher_id)
    assert result is not None
    return result
