from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user_identity_verification import UserIdentityVerification
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/user-identity-verifications", tags=["certification"])


class RealNameCertificationRequest(BaseModel):
    real_name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    id_card: str = Field(..., min_length=18, max_length=18, description="身份证号")


class EducationCertificationRequest(BaseModel):
    school: str = Field(..., min_length=2, max_length=100, description="学校名称")
    education_level: str = Field(..., description="学历：本科/硕士/博士")
    major: Optional[str] = Field(None, max_length=100, description="专业")
    graduation_year: Optional[int] = Field(None, ge=1950, le=2030, description="毕业年份")
    diploma_image_url: Optional[str] = Field(None, max_length=512, description="学历证书图片URL")


class TeacherCertificationRequest(BaseModel):
    teacher_certificate_number: str = Field(..., min_length=10, max_length=50, description="教师资格证号")
    teaching_subject: Optional[str] = Field(None, max_length=50, description="任教科目")
    certificate_image_url: Optional[str] = Field(None, max_length=512, description="教师资格证书图片URL")


class CertificationResponse(BaseModel):
    id: uuid.UUID
    verification_type: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Real name fields
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
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[CertificationResponse])
async def get_user_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有认证记录"""
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id
    ).order_by(UserIdentityVerification.created_at.desc())
    
    result = await db.execute(stmt)
    certifications = result.scalars().all()
    
    return certifications


@router.post("/real-name", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_real_name_certification(
    data: RealNameCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交实名认证"""
    import hashlib
    
    # 检查是否已有实名认证
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "real_name"
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing and existing.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成实名认证，无需重复提交"
        )
    
    # 对身份证号进行哈希处理（保护隐私）
    id_card_hash = hashlib.sha256(data.id_card.encode()).hexdigest()
    id_card_masked = f"{data.id_card[:6]}********{data.id_card[-4:]}"
    
    if existing:
        # 更新现有记录
        existing.real_name = data.real_name
        existing.id_card_hash = id_card_hash
        existing.id_card_masked = id_card_masked
        existing.status = "pending"
        existing.submitted_at = datetime.utcnow()
        existing.rejection_reason = None
        certification = existing
    else:
        # 创建新记录
        certification = UserIdentityVerification(
            user_id=current_user.id,
            verification_type="real_name",
            real_name=data.real_name,
            id_card_hash=id_card_hash,
            id_card_masked=id_card_masked,
            status="pending",
        )
        db.add(certification)
    
    await db.commit()
    await db.refresh(certification)
    
    return certification


@router.post("/education", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_education_certification(
    data: EducationCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交学历认证"""
    # 检查是否已完成实名认证
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "real_name",
        UserIdentityVerification.status == "approved"
    )
    result = await db.execute(stmt)
    real_name_cert = result.scalar_one_or_none()
    
    if not real_name_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成实名认证"
        )
    
    # 检查是否已有学历认证
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "education"
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing and existing.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成学历认证，无需重复提交"
        )
    
    if existing:
        # 更新现有记录
        existing.school = data.school
        existing.education_level = data.education_level
        existing.major = data.major
        existing.graduation_year = data.graduation_year
        existing.diploma_image_url = data.diploma_image_url
        existing.status = "pending"
        existing.submitted_at = datetime.utcnow()
        existing.rejection_reason = None
        certification = existing
    else:
        # 创建新记录
        certification = UserIdentityVerification(
            user_id=current_user.id,
            verification_type="education",
            school=data.school,
            education_level=data.education_level,
            major=data.major,
            graduation_year=data.graduation_year,
            diploma_image_url=data.diploma_image_url,
            status="pending",
        )
        db.add(certification)
    
    await db.commit()
    await db.refresh(certification)
    
    return certification


@router.post("/teacher", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_teacher_certification(
    data: TeacherCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交教师资格认证"""
    # 检查是否已完成实名认证
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "real_name",
        UserIdentityVerification.status == "approved"
    )
    result = await db.execute(stmt)
    real_name_cert = result.scalar_one_or_none()
    
    if not real_name_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成实名认证"
        )
    
    # 检查是否已完成学历认证（如果未完成，同时提交学历和教师认证）
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "education",
        UserIdentityVerification.status == "approved"
    )
    result = await db.execute(stmt)
    education_cert = result.scalar_one_or_none()
    
    # 如果没有学历认证，提示需要先完成
    if not education_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成学历认证，或同时提交学历认证和教师资格认证"
        )
    
    # 检查是否已有教师资格认证
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.verification_type == "teacher"
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing and existing.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成教师资格认证，无需重复提交"
        )
    
    if existing:
        # 更新现有记录
        existing.teacher_certificate_number = data.teacher_certificate_number
        existing.teaching_subject = data.teaching_subject
        existing.certificate_image_url = data.certificate_image_url
        existing.status = "pending"
        existing.submitted_at = datetime.utcnow()
        existing.rejection_reason = None
        certification = existing
    else:
        # 创建新记录
        certification = UserIdentityVerification(
            user_id=current_user.id,
            verification_type="teacher",
            teacher_certificate_number=data.teacher_certificate_number,
            teaching_subject=data.teaching_subject,
            certificate_image_url=data.certificate_image_url,
            status="pending",
        )
        db.add(certification)
    
    await db.commit()
    await db.refresh(certification)
    
    return certification
