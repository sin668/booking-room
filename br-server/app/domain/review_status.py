"""评价审核状态词表 —— 全仓唯一权威定义处。

契约：枚举成员值即写库/查询绑定的取值，统一走 .value；
本模块不依赖 models / schemas / services 三层，也不做时间处理。
"""
from __future__ import annotations

from enum import Enum


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# 管理员可流转到的目标状态：pending 是新建初值，不由审核接口写入
AUDIT_TARGET_STATUSES = (ReviewStatus.APPROVED, ReviewStatus.REJECTED)
