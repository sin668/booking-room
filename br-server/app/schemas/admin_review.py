from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.review_status import AUDIT_TARGET_STATUSES, ReviewStatus
from app.schemas.review import ReviewItem


class AdminReviewItem(ReviewItem):
    """后台评价条目：永不脱敏，额外携带审核元数据。"""

    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None


class AdminReviewListResponse(BaseModel):
    items: list[AdminReviewItem]
    total: int
    page: int
    page_size: int


class ReviewStatusUpdate(BaseModel):
    """审核请求。目标状态限定 approved / rejected，pending 不由审核接口写入。"""

    status: ReviewStatus
    reject_reason: str | None = Field(None, max_length=200)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status")
    @classmethod
    def must_be_audit_target(cls, v: ReviewStatus) -> ReviewStatus:
        if v not in AUDIT_TARGET_STATUSES:
            raise ValueError("审核状态只能是 approved 或 rejected")
        return v

    @field_validator("reject_reason")
    @classmethod
    def strip_reject_reason(cls, v: str | None) -> str | None:
        # 是否"理由非空"由 service 结合目标状态判断，此处只做归一
        return v.strip() if v else None


class ReviewReplyUpdate(BaseModel):
    """机构回复请求。空白内容表示清空回复。"""

    reply_content: str = Field(..., max_length=500)
