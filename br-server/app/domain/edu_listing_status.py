from enum import Enum


class EduListingStatus(str, Enum):
    """教培供需信息审核状态。

    比 review 多一个 `offline`（已通过后被管理员下架），广场只展示 approved。
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    OFFLINE = "offline"


# 审核接口可写入的目标状态：通过 / 拒绝 / 下架。pending 不由审核接口写入。
AUDIT_TARGET_STATUSES = (
    EduListingStatus.APPROVED,
    EduListingStatus.REJECTED,
    EduListingStatus.OFFLINE,
)
