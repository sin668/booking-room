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
    apply_msg_withdraw,
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


OSS_IMAGE_URL = "https://oss.example.com/chat/image/a.jpg"


def signed_query(token: str = "secret", sdk_appid: str = "123456") -> str:
    """按官方公式 Sign = sha256(Token + RequestTime) 生成回调 URL 参数。"""
    request_time = str(int(time.time() * 1000))
    sign = hashlib.sha256(f"{token}{request_time}".encode()).hexdigest()
    return f"SdkAppid={sdk_appid}&RequestTime={request_time}&Sign={sign}"


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

    def test_video_extracts_video_url(self):
        parsed = parse_message(
            [
                {
                    "MsgType": "TIMVideoFileElem",
                    "MsgContent": {
                        "VideoUrl": "https://im/video.mp4",
                        "ThumbUrl": "https://im/thumb.jpg",
                        "ThumbWidth": 128,
                        "ThumbHeight": 72,
                        "Second": 10,
                        "Size": 1024000,
                    },
                }
            ]
        )
        assert parsed.element_type == "video"
        assert parsed.media_url == "https://im/video.mp4"
        assert parsed.content == "10s"
        assert media_kind_for(ImMessage(element_type="video", media_url=parsed.media_url)) == "video"

    def test_legacy_video_elem_also_works(self):
        """兼容旧版 TIMVideoElem 类型"""
        parsed = parse_message(
            [{"MsgType": "TIMVideoElem", "MsgContent": {"VideoUrl": "https://im/old.mp4", "Second": 5}}]
        )
        assert parsed.element_type == "video"
        assert parsed.media_url == "https://im/old.mp4"

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

    async def test_cloud_custom_data_persisted(self, db_session: AsyncSession):
        """引用/回复消息的 CloudCustomData 要落库，历史重建时才能还原引用卡片。"""
        record = await save_send_msg_callback(
            db_session, send_payload("key-ccd", CloudCustomData='{"messageReply":{"messageId":"x"}}')
        )
        await db_session.commit()

        assert record.cloud_custom_data == '{"messageReply":{"messageId":"x"}}'

    async def test_missing_cloud_custom_data_stays_none(self, db_session: AsyncSession):
        record = await save_send_msg_callback(db_session, send_payload("key-ccd-empty"))
        await db_session.commit()

        assert record.cloud_custom_data is None


@pytest.mark.usefixtures("im_users")
class TestApplyMsgWithdraw:
    async def test_marks_by_msg_key(self, db_session: AsyncSession):
        await save_send_msg_callback(db_session, send_payload("key-w1"))
        await db_session.commit()

        updated = await apply_msg_withdraw(db_session, {"MsgKey": "key-w1", "EventTime": 1700000123456})
        await db_session.commit()
        assert updated == 1

        row = (await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-w1"))).scalar_one()
        assert row.is_revoked is True
        assert row.revoke_time == 1700000123456
        assert row.content == "你好"  # 只标记状态，不删内容

    async def test_repeat_delivery_is_idempotent(self, db_session: AsyncSession):
        await save_send_msg_callback(db_session, send_payload("key-w2"))
        await db_session.commit()

        assert await apply_msg_withdraw(db_session, {"MsgKey": "key-w2"}) == 1
        assert await apply_msg_withdraw(db_session, {"MsgKey": "key-w2"}) == 0

    async def test_missing_msg_key_and_unknown_key(self, db_session: AsyncSession):
        assert await apply_msg_withdraw(db_session, {"EventTime": 1}) == 0
        assert await apply_msg_withdraw(db_session, {"MsgKey": "never-saved"}) == 0


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
        assert _extension("video", "https://im/v.mp4") == ".mp4"
        assert _extension("video", "https://im/v.mov") == ".mov"
        assert _extension("video", "https://im/no-ext") == ".mp4"


class TestMediaDownloadLimit:
    async def test_aborts_when_body_exceeds_cap(self):
        import httpx

        from app.services.im_media_service import MAX_MEDIA_BYTES, MediaTooLarge, _download

        handler = httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"x" * (MAX_MEDIA_BYTES + 1))
        )
        with pytest.raises(MediaTooLarge):
            await _download("https://im/big.jpg", transport=handler)

    async def test_oversized_media_degrades_to_none(self, monkeypatch):
        """超限按转存失败降级：返回 None，不影响消息落库。"""
        import httpx

        from app.services import im_media_service

        handler = httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"x" * (im_media_service.MAX_MEDIA_BYTES + 1))
        )

        class _Client(httpx.AsyncClient):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, transport=handler)

        monkeypatch.setattr(im_media_service.httpx, "AsyncClient", _Client)
        assert await im_media_service.fetch_and_upload("image", "https://im/big.jpg") is None



class TestVerifyCallbackSign:
    def test_rejects_other_sdk_appid(self, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        assert verify_callback_sign("654321", "1700000000000", "x") is False

    def test_rejects_without_token_configured(self, monkeypatch):
        """SdkAppid 是 /chat/user-sig 下发的公开值，没配 Token 时不能只凭它放行。"""
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "")
        assert verify_callback_sign("123456", None, None) is False

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
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")
        # 后台任务默认连接真实库，这里改用测试会话
        monkeypatch.setattr(route, "async_session", lambda: _SessionScope(db_session))

        async def fake_transfer(kind: str, media_url: str) -> str | None:
            assert (kind, media_url) == ("image", "https://im/original.jpg")
            return OSS_IMAGE_URL

        monkeypatch.setattr(route, "fetch_and_upload", fake_transfer)

        payload = send_payload(
            "key-media",
            MsgBody=[
                {
                    "MsgType": "TIMImageElem",
                    "MsgContent": {"ImageInfoArray": [{"Type": 1, "URL": "https://im/original.jpg"}]},
                }
            ],
        )
        response = await client.post(
            f"/api/v1/im/callback?{signed_query()}&CallbackCommand=C2C.CallbackAfterSendMsg", json=payload
        )

        assert response.status_code == 200
        assert response.json() == {"ActionStatus": "OK", "ErrorInfo": "", "ErrorCode": 0}

        row = (await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-media"))).scalar_one()
        assert row.media_url == "https://im/original.jpg"
        assert row.oss_url == OSS_IMAGE_URL

    async def test_media_transfer_crash_keeps_message(
        self, client: AsyncClient, db_session: AsyncSession, im_users, monkeypatch
    ):
        """消息先提交：转存环节抛异常不能把已落库的消息一起回滚掉。"""
        from app.api.routes import im_callback as route

        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")
        monkeypatch.setattr(route, "async_session", lambda: _SessionScope(db_session))

        async def boom(kind: str, media_url: str) -> str | None:
            raise RuntimeError("unexpected media failure")

        monkeypatch.setattr(route, "fetch_and_upload", boom)

        payload = send_payload(
            "key-media-crash",
            MsgBody=[{"MsgType": "TIMSoundElem", "MsgContent": {"Url": "not a url", "Second": 3}}],
        )
        response = await client.post(
            f"/api/v1/im/callback?{signed_query()}&CallbackCommand=C2C.CallbackAfterSendMsg", json=payload
        )

        assert response.status_code == 200
        row = (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-media-crash"))
        ).scalar_one()
        assert row.element_type == "sound"
        assert row.media_url == "not a url"
        assert row.oss_url is None

    async def test_rejects_missing_callback_token(
        self, client: AsyncClient, db_session: AsyncSession, monkeypatch
    ):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "")

        response = await client.post(
            "/api/v1/im/callback?SdkAppid=123456&CallbackCommand=C2C.CallbackAfterSendMsg",
            json=send_payload("key-no-token"),
        )

        assert response.status_code == 200  # 仍返回 OK 不影响 IM，但不落库
        assert (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-no-token"))
        ).scalar_one_or_none() is None

    async def test_rejects_forged_sign(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")

        stale = str(int(time.time() * 1000) - 300_000)
        response = await client.post(
            "/api/v1/im/callback?SdkAppid=123456&RequestTime="
            f"{stale}&Sign=whatever&CallbackCommand=C2C.CallbackAfterSendMsg",
            json=send_payload("key-forged"),
        )

        assert response.status_code == 200
        assert (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-forged"))
        ).scalar_one_or_none() is None

    async def test_non_object_body_is_ignored(self, client: AsyncClient, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")

        response = await client.post(
            f"/api/v1/im/callback?{signed_query()}&CallbackCommand=C2C.CallbackAfterSendMsg", json=[1, 2]
        )

        assert response.status_code == 200
        assert response.json() == {"ActionStatus": "OK", "ErrorInfo": "", "ErrorCode": 0}

    async def test_rejects_wrong_sdk_appid(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")

        response = await client.post(
            f"/api/v1/im/callback?{signed_query(sdk_appid='999')}&CallbackCommand=C2C.CallbackAfterSendMsg",
            json=send_payload("key-bad"),
        )

        assert response.status_code == 200  # 不向 IM 暴露错误，但不落库
        assert (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-bad"))
        ).scalar_one_or_none() is None



@pytest.mark.usefixtures("im_users")
class TestCallbackWithdrawRoute:
    async def test_withdraw_callback_marks_revoked(
        self, client: AsyncClient, db_session: AsyncSession, monkeypatch
    ):
        from app.api.routes import im_callback as route

        monkeypatch.setattr(settings, "IM_SDK_APP_ID", 123456)
        monkeypatch.setattr(settings, "IM_CALLBACK_TOKEN", "secret")
        monkeypatch.setattr(route, "async_session", lambda: _SessionScope(db_session))

        await save_send_msg_callback(db_session, send_payload("key-w-route"))
        await db_session.commit()

        response = await client.post(
            f"/api/v1/im/callback?{signed_query()}",
            json={
                "CallbackCommand": "C2C.CallbackAfterMsgWithDraw",
                "From_Account": SELF_IM,
                "To_Account": PEER_IM,
                "MsgKey": "key-w-route",
                "EventTime": 1700000999000,
            },
        )

        assert response.json() == {"ActionStatus": "OK", "ErrorInfo": "", "ErrorCode": 0}
        row = (
            await db_session.execute(select(ImMessage).where(ImMessage.msg_key == "key-w-route"))
        ).scalar_one()
        assert row.is_revoked is True
        assert row.revoke_time == 1700000999000


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

    async def test_normalizes_peer_case_and_hyphens(self, auth_history_client: AsyncClient):
        """库里存的是 uuid.hex，入参带大写或连字符也应命中同一会话。"""
        response = await auth_history_client.get(f"/api/v1/chat/messages?peer={str(PEER_ID).upper()}")
        assert response.status_code == 200
        assert [m["msg_key"] for m in response.json()["messages"]] == ["h-1", "h-2"]

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

    async def test_returns_rebuild_fields(self, auth_history_client: AsyncClient):
        """历史重建需要的字段：MsgBody、CloudCustomData、撤回状态、IM 账号、已读。"""
        response = await auth_history_client.get(f"/api/v1/chat/messages?peer={PEER_IM}")
        h2 = next(m for m in response.json()["messages"] if m["msg_key"] == "h-2")
        assert h2["msg_seq"] == 7
        assert h2["im_from_account"] == PEER_IM
        assert h2["im_to_account"] == SELF_IM
        assert h2["elements"] == [
            {"MsgType": "TIMSoundElem", "MsgContent": {"Url": "https://im/a.mp3", "Second": 3}}
        ]
        assert h2["cloud_custom_data"] is None
        assert h2["is_revoked"] is False

    async def test_same_second_orders_by_msg_seq(self, db_session: AsyncSession, auth_history_client: AsyncClient):
        """同一秒内的多条消息按 MsgSeq 排，与 IM 单聊排序口径一致。"""
        db_session.add_all(
            [
                ImMessage(
                    msg_key="seq-5",
                    im_from_account=SELF_IM,
                    im_to_account=PEER_IM,
                    msg_time=200,
                    msg_seq=5,
                    element_type="text",
                    content="同秒更早",
                ),
                ImMessage(
                    msg_key="seq-9",
                    im_from_account=SELF_IM,
                    im_to_account=PEER_IM,
                    msg_time=200,
                    msg_seq=9,
                    element_type="text",
                    content="同秒更晚",
                ),
            ]
        )
        await db_session.commit()

        response = await auth_history_client.get(f"/api/v1/chat/messages?peer={PEER_IM}")
        assert [m["msg_key"] for m in response.json()["messages"]] == ["h-1", "seq-5", "h-2", "seq-9"]

    async def test_before_cursor_is_strict(self, db_session: AsyncSession, auth_history_client: AsyncClient):
        """游标取严格更早：边界秒的消息不重复出现在上一页/下一页。"""
        response = await auth_history_client.get(f"/api/v1/chat/messages?peer={PEER_IM}&before=200")
        assert [m["msg_key"] for m in response.json()["messages"]] == ["h-1"]


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
                msg_seq=3,
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
                msg_seq=7,
                element_type="sound",
                media_url="https://im/a.mp3",
                oss_url="https://oss.example.com/a.mp3",
                raw_payload={
                    "MsgBody": [{"MsgType": "TIMSoundElem", "MsgContent": {"Url": "https://im/a.mp3", "Second": 3}}]
                },
            ),
            ImMessage(
                msg_key="h-3",
                im_from_account=THIRD_IM,
                im_to_account=PEER_IM,
                from_user_id=THIRD_ID,
                to_user_id=PEER_ID,
                msg_time=150,
                msg_seq=4,
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
