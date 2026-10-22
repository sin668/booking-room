"""腾讯云 IM 单聊回调落库、媒体转存与历史查询测试。"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.im import from_im_user_id, to_im_user_id, verify_callback_sign
from app.models.im_message import ImMessage
from app.models.user import User
from app.services.im_callback_service import (
    apply_msg_report,
    media_kind_for,
    parse_message,
    save_send_msg_callback,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PEER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
THIRD_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
SELF_IM = to_im_user_id(USER_ID)
PEER_IM = to_im_user_id(PEER_ID)
THIRD_IM = to_im_user_id(THIRD_ID)


def send_payload(msg_key: str, msg_time: int = 1_700_000_000, **body: Any) -> dict[str, Any]:
    payload = {
        "CallbackCommand": "C2C.CallbackAfterSendMsg",
        "From_Account": SELF_IM,
        "To_Account": PEER_IM,
        "MsgKey": msg_key,
        "MsgTime": msg_time,
        "MsgSeq": 1001,
        "MsgBody": [{"MsgType": "TIMTextElem", "MsgContent": {"Text": "你好"}}],
    }
    payload.update(body)
    return payload


@pytest.fixture
async def im_users(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            User(id=USER_ID, phone="13900139001", nickname="我", password_hash="h", username="im_self"),
            User(id=PEER_ID, phone="13900139002", nickname="对方", password_hash="h", username="im_peer"),
            User(id=THIRD_ID, phone="13900139003", nickname="无关", password_hash="h", username="im_third"),
        ]
    )
    await db_session.flush()


class TestParseMessage:
    def test_text(self):
        parsed = parse_message([{"MsgType": "TIMTextElem", "MsgContent": {"Text": "hi"}}])
        assert (parsed.element_type, parsed.content, parsed.media_url) == ("text", "hi", None)

    def test_image_prefers_original(self):
        parsed = parse_message(
            [
                {
                    "MsgType": "TIMImageElem",
                    "MsgContent": {
                        "ImageInfoArray": [
                            {"Type": 2, "URL": "https://im/big.jpg"},
                            {"Type": 1, "URL": "https://im/original.jpg"},
                            {"Type": 3, "URL": "https://im/thumb.jpg"},
                        ]
                    },
                }
            ]
        )
        assert parsed.element_type == "image"
        assert parsed.media_url == "https://im/original.jpg"
        assert media_kind_for(ImMessage(element_type="image", media_url=parsed.media_url)) == "image"

    def test_sound_uses_lowercase_url_field(self):
        parsed = parse_message(
            [{"MsgType": "TIMSoundElem", "MsgContent": {"Url": "https://im/a.mp3", "Second": 3}}]
        )
        assert (parsed.element_type, parsed.media_url, parsed.content) == ("sound", "https://im/a.mp3", "3")

    def test_unknown_type_is_other(self):
        assert parse_message([{"MsgType": "TIMGroupTipElem", "MsgContent": {}}]).element_type == "other"


@pytest.mark.usefixtures("im_users")
class TestSaveSendMsg:
    async def test_text_persisted_with_resolved_user_ids(self, db_session: AsyncSession):
        record = await save_send_msg_callback(db_session, send_payload("key-1"))
        await db_session.commit()

        assert record is not None
        assert record.from_user_id == USER_ID
        assert record.to_user_id == PEER_ID
        assert record.element_type == "text"
        assert record.content == "你好"

    async def test_duplicate_msg_key_is_idempotent(self, db_session: AsyncSession):
        await save_send_msg_callback(db_session, send_payload("key-dup"))
        await save_send_msg_callback(db_session, send_payload("key-dup"))
        await db_session.commit()

        rows = (await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-dup"))).scalars().all()
        assert len(rows) == 1

    async def test_failed_send_is_skipped(self, db_session: AsyncSession):
        assert await save_send_msg_callback(db_session, send_payload("key-fail", SendMsgResult=30001)) is None

    async def test_foreign_account_keeps_im_id_only(self, db_session: AsyncSession):
        record = await save_send_msg_callback(db_session, send_payload("key-ext", From_Account="external_user"))
        await db_session.commit()

        assert record is not None
        assert record.from_user_id is None


class TestApplyMsgReport:
    async def test_marks_peer_messages_read(self, db_session: AsyncSession, im_users):
        await save_send_msg_callback(db_session, send_payload("key-r1", msg_time=100))
        await db_session.commit()

        updated = await apply_msg_report(
            db_session,
            {"Report_Account": SELF_IM, "Peer_Account": PEER_IM, "LastReadTime": 200},
        )
        await db_session.commit()
        assert updated == 0  # key-r1 是我发给对方的，不该被我的已读上报影响

        inbound = send_payload("key-r2", msg_time=150, From_Account=PEER_IM, To_Account=SELF_IM)
        await save_send_msg_callback(db_session, inbound)
        await db_session.commit()

        updated = await apply_msg_report(
            db_session,
            {"Report_Account": SELF_IM, "Peer_Account": PEER_IM, "LastReadTime": 160},
        )
        await db_session.commit()
        assert updated == 1

        row = (await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-r2"))).scalar_one()
        assert row.is_read is True
        assert row.read_at is not None

        # 重复上报幂等
        assert await apply_msg_report(
            db_session,
            {"Report_Account": SELF_IM, "Peer_Account": PEER_IM, "LastReadTime": 160},
        ) == 0


class TestMediaKey:
    def test_extension_falls_back_per_kind(self):
        from app.services.im_media_service import _extension

        assert _extension("image", "https://im/a.png?sign=1") == ".png"
        assert _extension("image", "https://im/no-extension") == ".jpg"
        assert _extension("audio", "https://im/x.silk") == ".mp3"
        assert _extension("audio", "https://im/x.m4a") == ".m4a"


class TestVerifyCallbackSign:
    def test_rejects_other_sdk_appid(self, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        assert verify_callback_sign("654321", "1700000000000", "x") is False

    def test_accepts_without_token_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "")
        assert verify_callback_sign("123456", None, None) is True

    def test_valid_sign(self, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")
        request_time = str(int(time.time() * 1000))
        sign = hashlib.sha256(f"secret{request_time}".encode()).hexdigest()
        assert verify_callback_sign("123456", request_time, sign) is True

    def test_rejects_expired_timestamp_and_bad_sign(self, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")
        stale = str(int(time.time() * 1000) - 120_000)
        assert verify_callback_sign("123456", stale, hashlib.sha256(f"secret{stale}".encode()).hexdigest()) is False
        fresh = str(int(time.time() * 1000))
        assert verify_callback_sign("123456", fresh, "not-the-sign") is False


class TestCallbackRoute:
    async def test_sends_msg_callback_persists_and_transfers_media(
        self, client: AsyncClient, db_session: AsyncSession, im_users, monkeypatch
    ):
        from app.api.routes import im_callback as route

        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "")
        # 后台任务默认连接真实库，这里改用测试会话
        monkeypatch.setattr(route, "async_session", lambda: _SessionScope(db_session))

        async def fake_transfer(kind: str, media_url: str) -> str | None:
            assert (kind, media_url) == ("image", "https://im/original.jpg")
            return "https://oss.example.com/chat/image/2026/10/22/a.jpg"

        monkeypatch.setattr(route, "fetch_and_upload", fake_transfer)

        payload = send_payload(
            "key-media",
            MsgBody=[
                {"MsgType": "TIMImageElem", "MsgContent": {"ImageInfoArray": [{"Type": 1, "URL": "https://im/original.jpg"}]}}
            ],
        )
        response = await client.post("/api/v1/im/callback?SdkAppid=123456&CallbackCommand=C2C.CallbackAfterSendMsg", json=payload)

        assert response.status_code == 200
        assert response.json() == {"ActionStatus": "OK", "ErrorInfo": "", "ErrorCode": 0}

        row = (await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-media"))).scalar_one()
        assert row.media_url == "https://im/original.jpg"
        assert row.oss_url == "https://oss.example.com/chat/image/2026/10/22/a.jpg"

    async def test_rejects_wrong_sdk_appid(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "")

        response = await client.post("/api/v1/im/callback?SdkAppid=999", json=send_payload("key-bad"))

        assert response.status_code == 200  # 不向 IM 暴露错误，但不落库
        assert (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-bad"))
        ).scalar_one_or_none() is None


class _SessionScope:
    """复用测试会话的 async_session() 替身（不进不出真实连接）。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc: object) -> bool:
        return False


@pytest.mark.usefixtures("im_users")
class TestChatHistoryAPI:
    async def test_returns_only_own_conversation(self, auth_history_client: AsyncClient):
        response = await auth_history_client.get(f"/api/v1/chat/messages?peer={PEER_IM}")
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert [m["msg_key"] for m in messages] == ["h-1", "h-2"]
        assert [m["direction"] for m in messages] == ["send", "receive"]
        assert messages[1]["oss_url"] == "https://oss.example.com/a.mp3"

    async def test_rejects_invalid_peer(self, auth_history_client: AsyncClient):
        response = await auth_history_client.get("/api/v1/chat/messages?peer=not-a-hex-id")
        assert response.status_code == 400

    async def test_requires_login(self, client: AsyncClient):
        response = await client.get(f"/api/v1/chat/messages?peer={PEER_IM}")
        assert response.status_code == 401

    async def test_other_pair_returns_empty(self, other_history_client: AsyncClient):
        response = await other_history_client.get(f"/api/v1/chat/messages?peer={PEER_IM}")
        assert response.status_code == 200
        # 无关用户只能看到自己参与的 h-3，看不到 h-1/h-2
        assert [m["msg_key"] for m in response.json()["messages"]] == ["h-3"]


@pytest.fixture
async def history_rows(db_session: AsyncSession, im_users):
    db_session.add_all(
        [
            ImMessage(
                msg_key="h-1",
                im_from_account=SELF_IM,
                im_to_account=PEER_IM,
                from_user_id=USER_ID,
                to_user_id=PEER_ID,
                msg_time=100,
                element_type="text",
                content="早",
            ),
            ImMessage(
                msg_key="h-2",
                im_from_account=PEER_IM,
                im_to_account=SELF_IM,
                from_user_id=PEER_ID,
                to_user_id=USER_ID,
                msg_time=200,
                element_type="sound",
                media_url="https://im/a.mp3",
                oss_url="https://oss.example.com/a.mp3",
            ),
            ImMessage(
                msg_key="h-3",
                im_from_account=THIRD_IM,
                im_to_account=PEER_IM,
                from_user_id=THIRD_ID,
                to_user_id=PEER_ID,
                msg_time=150,
                element_type="text",
                content="无关会话",
            ),
        ]
    )
    await db_session.commit()


@pytest.fixture
async def auth_history_client(client: AsyncClient, history_rows):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def other_history_client(client: AsyncClient, history_rows):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: THIRD_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)
