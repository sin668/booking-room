from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin
from app.core.database import get_db
from app.models.user_identity_verification import UserIdentityVerification
from app.models.user import User

router = APIRouter(prefix="/api/v1/admin/certifications", tags=["admin-certification"])


class AdminCertificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    verification_type: str
    real_name: Optional[str] = None
    id_card_masked: Optional[str] = None
    
    # Education fields
    school: Optional[str] = None
    education_level: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    diploma_image_url: Optional[str] = None
    
    # Teacher fields
    teacher_certificate_number: Optional[str] = None
    teaching_subject: Optional[str] = None
    certificate_image_url: Optional[str] = None
    
    status: str
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    
    # User info
    user_nickname: Optional[str] = None
    user_phone: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=dict)
async def list_certifications(
    status_filter: Optional[str] = Query(None, description="状态过滤：pending/approved/rejected"),
    type_filter: Optional[str] = Query(None, description="类型过滤：real_name/education/teacher"),
    keyword: Optional[str] = Query(None, max_length=100, description="按昵称/手机号/学校模糊匹配"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: AdminContext = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取认证列表（管理员）"""
    conditions = []
    
    if status_filter:
        conditions.append(UserIdentityVerification.status == status_filter)
    if type_filter:
        conditions.append(UserIdentityVerification.verification_type == type_filter)

    trimmed = (keyword or "").strip()
    if trimmed:
        from sqlalchemy import or_
        pattern = f"%{trimmed}%"
        conditions.append(
            or_(
                User.nickname.ilike(pattern),
                User.phone.ilike(pattern),
                UserIdentityVerification.school.ilike(pattern),
            )
        )

    # keyword 命中 User 字段时，count 查询同样需要 join users
    needs_user_join = bool(trimmed)

    # Count query
    count_stmt = select(func.count(UserIdentityVerification.id))
    if needs_user_join:
        count_stmt = count_stmt.join(User, UserIdentityVerification.user_id == User.id)
    if conditions:
        from sqlalchemy import and_
        count_stmt = count_stmt.where(and_(*conditions))
    
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Data query with user info
    stmt = (
        select(UserIdentityVerification, User.nickname, User.phone)
        .join(User, UserIdentityVerification.user_id == User.id)
    )
    
    if conditions:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*conditions))
    
    stmt = stmt.order_by(UserIdentityVerification.submitted_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    items = []
    for cert, nickname, phone in rows:
        item = {
            "id": cert.id,
            "user_id": cert.user_id,
            "verification_type": cert.verification_type,
            "real_name": cert.real_name,
            "id_card_masked": cert.id_card_masked,
            "school": cert.school,
            "education_level": cert.education_level,
            "major": cert.major,
            "graduation_year": cert.graduation_year,
            "diploma_image_url": cert.diploma_image_url,
            "teacher_certificate_number": cert.teacher_certificate_number,
            "teaching_subject": cert.teaching_subject,
            "certificate_image_url": cert.certificate_image_url,
            "status": cert.status,
            "rejection_reason": cert.rejection_reason,
            "submitted_at": cert.submitted_at,
            "reviewed_at": cert.reviewed_at,
            "user_nickname": nickname,
            "user_phone": phone,
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


class ApproveCertificationRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


@router.patch("/{cert_id}/review")
async def review_certification(
    cert_id: uuid.UUID,
    data: ApproveCertificationRequest,
    context: AdminContext = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """审核认证（通过或拒绝）"""
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.id == cert_id
    )
    result = await db.execute(stmt)
    certification = result.scalar_one_or_none()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="认证记录不存在"
        )
    
    if certification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该认证已审核"
        )
    
    if data.approved:
        certification.status = "approved"
        certification.rejection_reason = None
    else:
        if not data.rejection_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="拒绝时必须提供原因"
            )
        certification.status = "rejected"
        certification.rejection_reason = data.rejection_reason
    
    certification.reviewed_at = datetime.utcnow()
    certification.reviewer_id = context.admin_id
    
    await db.commit()
    await db.refresh(certification)
    
    return {"message": "审核成功", "status": certification.status}
