from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 图片是上传接口回传的 URL（object key 上限 512），标签取自前端固定标签池
MAX_IMAGE_URL_LENGTH = 512
MAX_TAG_LENGTH = 20


class ReviewCreate(BaseModel):
    """发表评价请求。"""

    booking_id: int
    rating: int = Field(..., ge=1, le=5)
    content: str = Field(..., min_length=1, max_length=500)
    images: list[str] = Field(default_factory=list, max_length=9)
    tags: list[str] = Field(default_factory=list, max_length=5)
    is_anonymous: bool = False

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        # min_length 拦不住纯空白串，spec 要求空白内容返回 422
        stripped = v.strip()
        if not stripped:
            raise ValueError("评价内容不能为空")
        return stripped

    @field_validator("images", "tags")
    @classmethod
    def bound_item_length(cls, v: list[str], info) -> list[str]:
        limit = MAX_IMAGE_URL_LENGTH if info.field_name == "images" else MAX_TAG_LENGTH
        if any(len(item) > limit for item in v):
            raise ValueError("单项长度超出限制")
        return [item.strip() for item in v if item.strip()]


class ReviewItem(BaseModel):
    """评价条目。

    昵称/头像/课程名/老师名不在 Review 模型上，由 service 批量查询后显式构造。
    """

    id: int
    booking_id: int
    user_nickname: str | None = None
    user_avatar: str | None = None
    rating: int
    content: str
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_anonymous: bool
    course_id: int | None = None
    course_name: str | None = None
    teacher_id: int | None = None
    teacher_name: str | None = None
    reply_content: str | None = None
    reply_at: datetime | None = None
    status: str
    reject_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("images", "tags", mode="before")
    @classmethod
    def none_to_empty_list(cls, v):
        # 数据库列可空，契约要求序列化为 [] 而非 null
        return v or []


class ReviewListResponse(BaseModel):
    items: list[ReviewItem]
    total: int
    page: int
    page_size: int


class ReviewSummary(BaseModel):
    """评价概览。无已通过评价时全部为 0，不返回 404。"""

    average: float = 0.0
    count: int = 0
    positive_rate: int = 0
    # 键为星级 "5".."1"，值为该星级的已通过评价数
    distribution: dict[str, int] = Field(default_factory=dict)
