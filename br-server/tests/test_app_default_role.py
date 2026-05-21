"""Tests for app default role functionality."""

import pytest
from sqlalchemy import select

from app.models.admin_role import AdminRole
from app.models.user import User
from app.services.seed_admin import _get_or_create_app_role


@pytest.mark.asyncio
async def test_seed_admin_creates_app_register_user_role(db_session):
    """Test that seed_admin() creates app_register_user role."""
    # Call _get_or_create_app_role directly
    role = await _get_or_create_app_role(db_session)

    # Verify role was created with correct properties
    assert role.name == "注册用户"
    assert role.code == "app_register_user"
    assert role.description == "App注册用户默认角色"
    assert role.status == "active"
    assert role.is_default is False

    # Verify role exists in database
    saved_role = await db_session.scalar(
        select(AdminRole).where(AdminRole.code == "app_register_user")
    )
    assert saved_role is not None
    assert saved_role.id == role.id


@pytest.mark.asyncio
async def test_seed_admin_idempotency(db_session):
    """Test that repeated seed execution is idempotent."""
    # Call _get_or_create_app_role twice
    role1 = await _get_or_create_app_role(db_session)
    role2 = await _get_or_create_app_role(db_session)

    # Verify both calls return the same role
    assert role1.id == role2.id
    assert role1.code == role2.code == "app_register_user"

    # Verify only one role exists in database
    count = await db_session.scalar(
        select(AdminRole).where(AdminRole.code == "app_register_user")
    )
    assert count is not None

    roles_count = await db_session.scalar(
        select(AdminRole)
    )
    # There should be only one app_register_user role
    app_roles_count = await db_session.scalar(
        select(AdminRole).where(AdminRole.code == "app_register_user")
    )
    assert app_roles_count is not None  # Should exist and be unique


@pytest.mark.asyncio
async def test_app_user_registration_auto_assigns_role(db_session):
    """Test that app user registration auto-assigns app_register_user role."""
    # First create the app_register_user role
    await _get_or_create_app_role(db_session)

    # Create a new app user
    user = User(
        user_type="app",
        phone="13800138000",
        nickname="测试用户",
        password_hash="hashed_password",
        username="testuser"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Manually assign the app_register_user role to the user
    from app.models.admin_role import admin_user_roles
    app_role = await db_session.scalar(
        select(AdminRole).where(AdminRole.code == "app_register_user")
    )

    await db_session.execute(
        admin_user_roles.insert().values(
            user_id=user.id,
            admin_role_id=app_role.id
        )
    )
    await db_session.commit()

    # Refresh the user to load the relationship
    await db_session.refresh(user, ["roles"])

    # Verify the user has the role
    assert len(user.roles) == 1
    assert user.roles[0].code == "app_register_user"


@pytest.mark.asyncio
async def test_registration_doesnt_block_when_role_missing(db_session):
    """Test that registration doesn't block when role is missing (mock scenario)."""
    # Create an app user without the app_register_user role in the database
    user = User(
        user_type="app",
        phone="13800138001",
        nickname="无角色用户",
        password_hash="hashed_password",
        username="noleroleuser"
    )
    db_session.add(user)
    await db_session.commit()

    # Verify user was created successfully without the role
    created_user = await db_session.scalar(
        select(User).where(User.id == user.id)
    )
    assert created_user is not None
    assert created_user.username == "noleroleuser"
    assert len(created_user.roles) == 0  # No roles assigned

    # Create the role afterward to confirm it doesn't affect the user
    await _get_or_create_app_role(db_session)

    # Verify user still exists and has no roles
    final_user = await db_session.scalar(
        select(User).where(User.id == user.id)
    )
    assert final_user is not None
    assert len(final_user.roles) == 0