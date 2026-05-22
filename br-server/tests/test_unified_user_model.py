import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.admin_role import AdminRole


@pytest.mark.asyncio
async def test_app_user_defaults_user_type_to_app(db_session):
    """Test creating app user defaults user_type to 'app'"""
    user = User(
        phone="1234567890",
        nickname="Test User",
        password_hash="hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.user_type == "app"


@pytest.mark.asyncio
async def test_admin_user_sets_user_type_admin(db_session):
    """Test creating admin user sets user_type='admin'"""
    user = User(
        user_type="admin",
        phone="1234567890",
        nickname="Admin User",
        password_hash="hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.user_type == "admin"


@pytest.mark.asyncio
async def test_phone_uniqueness_constraint(db_session):
    """Test same phone can't create two users"""
    db_session.add_all([
        User(
            phone="1234567890",
            nickname="User 1",
            password_hash="hash"
        ),
        User(
            phone="1234567890",
            nickname="User 2",
            password_hash="hash"
        )
    ])

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_username_uniqueness_constraint(db_session):
    """Test same username can't create two users"""
    db_session.add_all([
        User(
            username="admin_user",
            phone="1234567890",
            password_hash="hash"
        ),
        User(
            username="admin_user",
            phone="0987654321",
            password_hash="hash"
        )
    ])

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_check_constraint_rejects_invalid_user_type(db_session):
    """Test CHECK constraint rejects invalid user_type"""
    user = User(
        user_type="invalid",
        phone="1234567890",
        nickname="Test User",
        password_hash="hash"
    )
    db_session.add(user)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_roles_relationship_returns_associated_admin_role(db_session):
    """Test User.roles relationship returns associated AdminRole"""
    # Create admin role
    role = AdminRole(name="Operator", code="operator")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    # Create admin user with the role
    user = User(
        user_type="admin",
        username="admin_user",
        phone="1234567890",
        nickname="Admin User",
        password_hash="hash"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Verify the relationship
    assert len(user.roles) == 1
    assert user.roles[0] == role
    assert role in user.roles

    # Verify back-populates relationship
    assert user in role.users