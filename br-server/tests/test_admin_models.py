import pytest
from sqlalchemy.exc import IntegrityError

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.admin_setting import SystemSetting
from app.models.admin_user import AdminUser
from app.services.seed_admin import BUTTON_SEEDS, MENU_SEEDS


@pytest.mark.asyncio
async def test_admin_user_username_is_unique(db_session):
    db_session.add_all(
        [
            AdminUser(username="admin", password_hash="hash"),
            AdminUser(username="admin", password_hash="hash"),
        ]
    )

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_admin_role_menu_relationships_include_buttons(db_session):
    role = AdminRole(name="Operator", code="operator")
    parent = AdminMenu(type="directory", title="System", path="/system", name="System", component="LAYOUT")
    button = AdminMenu(
        type="button",
        title="Create role",
        permission_code="system:role:create",
        parent=parent,
    )
    role.menus.append(button)
    db_session.add(role)
    await db_session.commit()

    assert button.parent is parent
    assert role.menus == [button]


@pytest.mark.asyncio
async def test_system_setting_secret_flag_is_persisted(db_session):
    setting = SystemSetting(
        key="smtp_password",
        value="secret-value",
        group="email",
        is_secret=True,
    )
    db_session.add(setting)
    await db_session.commit()
    await db_session.refresh(setting)

    assert setting.is_secret is True


def test_admin_seed_permission_codes_are_unique():
    menu_codes = [seed.permission_code for seed in MENU_SEEDS if seed.permission_code]
    button_codes = [permission_code for _parent_key, permission_code, _title in BUTTON_SEEDS]
    codes = menu_codes + button_codes

    assert len(codes) == len(set(codes))
