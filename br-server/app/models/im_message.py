from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImMessage(Base):
    """腾讯云 IM 单聊消息镜像，由服务端第三方回调写入。

    IM 侧账号是 users.id 派生的 UserID（见 app.core.im.to_im_user_id），
    因此收发用户 ID 可反查；反查不到（非本系统账号）时保留 IM 账号、用户 ID 为空。
    媒体只存地址：media_url 为 IM/COS 原始地址，oss_url 为服务端转存后的 OSS 地址。
    本模型不声明 relationship，避免 async 序列化触发 MissingGreenlet。
    """

    __tablename__ = "im_messages"
    __table_args__ = (
        Index("ix_im_messages_pair_time", "im_from_account", "im_to_account", "msg_time"),
        Index("ix_im_messages_read_state", "im_to_account", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msg_key: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="腾讯云 IM MsgKey，消息唯一标识"
    )
    im_from_account: Mapped[str] = mapped_column(String(64), nullable=False)
    im_to_account: Mapped[str] = mapped_column(String(64), nullable=False)
    from_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    msg_seq: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    msg_time: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="消息发送时间戳（秒，取 IM MsgTime）"
    )
    element_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="text / image / sound / custom / other"
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文本内容或媒体描述摘要")
    media_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="IM/COS 原始媒体地址"
    )
    oss_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="服务端转存后的 OSS 地址"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="回调原始 MsgBody")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
