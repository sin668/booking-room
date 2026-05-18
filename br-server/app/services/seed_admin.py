from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole, admin_role_menus, admin_user_roles
from app.models.admin_user import AdminUser
from app.models.admin_setting import SystemSetting
from app.services.admin_auth_service import AdminAuthService


@dataclass(frozen=True)
class MenuSeed:
    key: str
    type: str
    title: str
    permission_code: str | None = None
    path: str | None = None
    name: str | None = None
    component: str | None = None
    redirect: str | None = None
    icon: str | None = None
    sort: int = 0
    hidden: bool = False
    keep_alive: bool = False
    enabled: bool = True
    parent: str | None = None


MENU_SEEDS = [
    MenuSeed("dashboard", "directory", "控制台", "dashboard:view", "dashboard", "Dashboard", "LAYOUT", "/dashboard/console", "HomeOutlined", 10),
    MenuSeed("dashboard.console", "menu", "工作台", "dashboard:console:view", "console", "DashboardConsole", "/dashboard/console/console", None, "DashboardOutlined", 11, parent="dashboard"),
    MenuSeed("system", "directory", "系统设置", "system:view", "system", "System", "LAYOUT", "/system/menu", "SettingOutlined", 20),
    MenuSeed("system.menu", "menu", "菜单设置", "system:menu:view", "menu", "SystemMenu", "/system/menu/menu", None, "MenuOutlined", 21, parent="system"),
    MenuSeed("system.role", "menu", "角色权限", "system:role:view", "role", "SystemRole", "/system/role/role", None, "TeamOutlined", 22, parent="system"),
    MenuSeed("setting", "directory", "设置页面", "setting:view", "setting", "Setting", "LAYOUT", "/setting/account", "ToolOutlined", 30),
    MenuSeed("setting.account", "menu", "个人设置", "admin:profile:view", "account", "AccountSetting", "/setting/account/account", None, "UserOutlined", 31, parent="setting"),
    MenuSeed("setting.system", "menu", "系统设置", "system:settings:view", "system", "SystemSetting", "/setting/system/system", None, "SettingOutlined", 32, parent="setting"),
    MenuSeed("room", "directory", "房间管理", "room:manage", "room", "Room", "LAYOUT", "/room/list", "HomeOutlined", 40),
    MenuSeed("room.list", "menu", "自习室管理", "room:view", "list", "RoomList", "/room/list/index", None, "HomeOutlined", 41, parent="room"),
    MenuSeed("room.seats", "menu", "座位管理", "seat:view", "seats", "RoomSeats", "/room/seats/index", None, "AppsOutlined", 42, parent="room"),
    MenuSeed("activity", "directory", "活动管理", "activity:manage", "activity", "Activity", "LAYOUT", "/activity/list", "GiftOutlined", 50),
    MenuSeed("activity.list", "menu", "活动列表", "activity:view", "list", "ActivityList", "/activity/list/index", None, "GiftOutlined", 51, parent="activity"),
    MenuSeed("booking", "directory", "预约管理", "booking:manage", "booking", "Booking", "LAYOUT", "/booking/list", "CalendarOutlined", 60),
    MenuSeed("booking.list", "menu", "预约列表", "booking:view", "list", "BookingList", "/booking/list/index", None, "CalendarOutlined", 61, parent="booking"),
]

BUTTON_SEEDS = [
    ("system.menu", "system:menu:create", "菜单设置-新增"),
    ("system.menu", "system:menu:update", "菜单设置-编辑"),
    ("system.menu", "system:menu:delete", "菜单设置-删除"),
    ("system.role", "system:role:create", "角色权限-新增"),
    ("system.role", "system:role:update", "角色权限-编辑"),
    ("system.role", "system:role:delete", "角色权限-删除"),
    ("system.role", "system:role:assign", "角色权限-授权"),
    ("setting.system", "system:settings:update", "系统设置-更新"),
    ("setting.system", "system:settings:email", "系统设置-邮件测试"),
    ("setting.account", "admin:profile:update", "个人设置-更新资料"),
    ("setting.account", "admin:profile:password", "个人设置-修改密码"),
    ("room.list", "room:create", "自习室-新增"),
    ("room.list", "room:update", "自习室-编辑"),
    ("room.list", "room:delete", "自习室-删除"),
    ("room.list", "room:status", "自习室-状态"),
    ("room.seats", "seat:create", "座位-新增"),
    ("room.seats", "seat:bulk_create", "座位-批量新增"),
    ("room.seats", "seat:update", "座位-编辑"),
    ("room.seats", "seat:delete", "座位-删除"),
    ("room.seats", "seat:status", "座位-状态"),
    ("activity.list", "activity:create", "活动-新增"),
    ("activity.list", "activity:update", "活动-编辑"),
    ("activity.list", "activity:delete", "活动-删除"),
    ("activity.list", "activity:status", "活动-状态"),
    ("booking.list", "booking:cancel", "预约-取消"),
    ("booking.list", "upload:create", "文件-上传"),
]

BASIC_SETTING_DEFAULTS = {
    "site_name": "Booking Room",
    "icp_code": "",
    "contact_phone": "",
    "contact_address": "",
    "login_captcha": "false",
    "system_open": "true",
    "close_text": "",
    "login_desc": "欢迎使用自习室预约管理后台",
}

EMAIL_SETTING_DEFAULTS = {
    "smtp_host": "",
    "smtp_port": "",
    "smtp_username": "",
    "smtp_sender": "",
    "smtp_tls": "true",
}


async def seed_admin() -> dict[str, Any]:
    password = settings.ADMIN_DEFAULT_PASSWORD
    if not password:
        if settings.ENVIRONMENT.lower() in {"production", "prod"}:
            raise RuntimeError("ADMIN_DEFAULT_PASSWORD must be set in production")
        password = "123456"

    async with async_session() as session:
        role = await _get_or_create_role(session)
        admin = await _get_or_create_admin(session, password)
        await _ensure_user_role(session, admin.id, role.id)

        menu_by_key = await _seed_menus(session)
        await _seed_buttons(session, menu_by_key)
        await session.flush()

        all_menus = list((await session.execute(select(AdminMenu))).scalars().all())
        await _ensure_role_menus(session, role.id, [menu.id for menu in all_menus])
        await _seed_settings(session)
        await session.commit()

        return {
            "admin_username": admin.username,
            "role_code": role.code,
            "menu_count": len(all_menus),
        }


async def _get_or_create_role(session) -> AdminRole:
    role = (await session.execute(select(AdminRole).where(AdminRole.code == "super_admin"))).scalar_one_or_none()
    if role is None:
        role = AdminRole(
            name="超级管理员",
            code="super_admin",
            description="拥有全部后台权限",
            status="active",
            is_default=True,
        )
        session.add(role)
        await session.flush()
    else:
        role.name = "超级管理员"
        role.status = "active"
        role.is_default = True
    return role


async def _get_or_create_admin(session, password: str) -> AdminUser:
    username = settings.ADMIN_DEFAULT_USERNAME or "admin"
    admin = (await session.execute(select(AdminUser).where(AdminUser.username == username))).scalar_one_or_none()
    if admin is None:
        admin = AdminUser(
            username=username,
            password_hash=AdminAuthService.hash_password(password),
            nickname="超级管理员",
            email=settings.ADMIN_DEFAULT_EMAIL or None,
            status="active",
            is_super_admin=True,
        )
        session.add(admin)
        await session.flush()
    else:
        admin.status = "active"
        admin.is_super_admin = True
        if settings.ADMIN_DEFAULT_EMAIL:
            admin.email = settings.ADMIN_DEFAULT_EMAIL
    return admin


async def _ensure_user_role(session, admin_user_id, admin_role_id: int) -> None:
    exists = await session.scalar(
        select(admin_user_roles.c.admin_user_id).where(
            admin_user_roles.c.admin_user_id == admin_user_id,
            admin_user_roles.c.admin_role_id == admin_role_id,
        )
    )
    if exists is None:
        await session.execute(
            admin_user_roles.insert().values(
                admin_user_id=admin_user_id,
                admin_role_id=admin_role_id,
            )
        )


async def _ensure_role_menus(session, admin_role_id: int, admin_menu_ids: list[int]) -> None:
    existing_ids = set(
        (
            await session.execute(
                select(admin_role_menus.c.admin_menu_id).where(
                    admin_role_menus.c.admin_role_id == admin_role_id
                )
            )
        ).scalars()
    )
    for menu_id in admin_menu_ids:
        if menu_id not in existing_ids:
            await session.execute(
                admin_role_menus.insert().values(
                    admin_role_id=admin_role_id,
                    admin_menu_id=menu_id,
                )
            )


async def _seed_menus(session) -> dict[str, AdminMenu]:
    menu_by_key: dict[str, AdminMenu] = {}
    for seed in MENU_SEEDS:
        parent_id = menu_by_key[seed.parent].id if seed.parent else None
        menu = await _get_or_create_menu(session, seed.permission_code, seed.title)
        _apply_menu_seed(menu, seed, parent_id)
        menu_by_key[seed.key] = menu
        await session.flush()
    return menu_by_key


async def _seed_buttons(session, menu_by_key: dict[str, AdminMenu]) -> None:
    sort = 1000
    for parent_key, permission_code, title in BUTTON_SEEDS:
        parent = menu_by_key[parent_key]
        menu = await _get_or_create_menu(session, permission_code, title)
        menu.type = "button"
        menu.title = title
        menu.permission_code = permission_code
        menu.parent_id = parent.id
        menu.path = None
        menu.name = None
        menu.component = None
        menu.redirect = None
        menu.icon = None
        menu.sort = sort
        menu.hidden = False
        menu.keep_alive = False
        menu.enabled = True
        sort += 1


async def _get_or_create_menu(session, permission_code: str | None, title: str) -> AdminMenu:
    menu = None
    if permission_code:
        menu = (await session.execute(select(AdminMenu).where(AdminMenu.permission_code == permission_code))).scalar_one_or_none()
    if menu is None:
        menu = AdminMenu(type="button", title=title, permission_code=permission_code)
        session.add(menu)
    return menu


def _apply_menu_seed(menu: AdminMenu, seed: MenuSeed, parent_id: int | None) -> None:
    menu.type = seed.type
    menu.title = seed.title
    menu.permission_code = seed.permission_code
    menu.parent_id = parent_id
    menu.path = seed.path
    menu.name = seed.name
    menu.component = seed.component
    menu.redirect = seed.redirect
    menu.icon = seed.icon
    menu.sort = seed.sort
    menu.hidden = seed.hidden
    menu.keep_alive = seed.keep_alive
    menu.enabled = seed.enabled


async def _seed_settings(session) -> None:
    for key, value in BASIC_SETTING_DEFAULTS.items():
        await _upsert_setting(session, key, value, "basic", False)
    for key, value in EMAIL_SETTING_DEFAULTS.items():
        await _upsert_setting(session, key, value, "email", False)


async def _upsert_setting(session, key: str, value: str, group: str, is_secret: bool) -> None:
    setting = await session.get(SystemSetting, key)
    if setting is None:
        session.add(SystemSetting(key=key, value=value, group=group, is_secret=is_secret))
    else:
        setting.group = group
        setting.is_secret = is_secret
        if setting.value in {None, ""}:
            setting.value = value


def main() -> None:
    result = asyncio.run(seed_admin())
    print(
        "Seeded admin RBAC: "
        f"admin={result['admin_username']} role={result['role_code']} menus={result['menu_count']}"
    )


if __name__ == "__main__":
    main()
