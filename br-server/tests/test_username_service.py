import pytest
from fastapi import HTTPException

from app.models.user import User
from app.services.username_service import UsernameService


@pytest.mark.asyncio
async def test_generate_unique_username_matches_default_format(db_session):
    service = UsernameService(db_session)

    username = await service.generate_unique_username()

    assert username[:-5].isalpha()
    assert username[-5:].isdigit()
    assert len(username[-5:]) == 5


def test_validate_editable_username_accepts_allowed_values():
    UsernameService.validate_editable_username("Luna_01")
    UsernameService.validate_editable_username("User123456")


@pytest.mark.parametrize("username", ["abc", "中文用户123", "name with spaces", "toolong_" + "a" * 40])
def test_validate_editable_username_rejects_invalid_values(username):
    with pytest.raises(HTTPException) as exc_info:
        UsernameService.validate_editable_username(username)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_generate_unique_username_retries_collisions(db_session, monkeypatch):
    existing = User(
        phone="13800138000",
        username="Luna10000",
        nickname="existing",
        password_hash="hashed",
    )
    db_session.add(existing)
    await db_session.flush()

    candidates = iter(["Luna10000", "Mia10001"])
    monkeypatch.setattr(UsernameService, "generate_candidate", staticmethod(lambda: next(candidates)))

    username = await UsernameService(db_session).generate_unique_username()

    assert username == "Mia10001"


@pytest.mark.asyncio
async def test_generate_unique_username_raises_after_retry_exhaustion(db_session, monkeypatch):
    monkeypatch.setattr(UsernameService, "generate_candidate", staticmethod(lambda: "Luna10000"))
    db_session.add(
        User(
            phone="13800138000",
            username="Luna10000",
            nickname="existing",
            password_hash="hashed",
        )
    )
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await UsernameService(db_session, max_attempts=2).generate_unique_username()

    assert exc_info.value.status_code == 503
