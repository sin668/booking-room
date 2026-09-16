from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.edu_listing_status import AUDIT_TARGET_STATUSES, EduListingStatus
from app.schemas.edu_listing import EduListingItem


class AdminEduListingItem(EduListingItem):
    """后台供需信息条目：额外携带审核元数据。"""

    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None


class AdminEduListingListResponse(BaseModel):
    items: list[AdminEduListingItem]
    total: int
    page: int
    page_size: int


class EduListingStatusUpdate(BaseModel):
    """审核请求。目标状态限定 approved / rejected / offline，pending 不由审核接口写入。"""

    status: EduListingStatus
    reject_reason: str | None = Field(None, max_length=200)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status")
    @classmethod
    def must_be_audit_target(cls, v: EduListingStatus) -> EduListingStatus:
        if v not in AUDIT_TARGET_STATUSES:
            raise ValueError("审核状态只能是 approved、rejected 或 offline")
        return v

    @field_validator("reject_reason")
    @classmethod
    def strip_reject_reason(cls, v: str | None) -> str | None:
        # 是否"理由非空"由 service 结合目标状态判断，此处只做归一
        return v.strip() if v else None
