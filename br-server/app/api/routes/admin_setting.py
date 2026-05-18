from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.admin_setting import (
    BasicSettings,
    EmailSettings,
    EmailSettingsUpdate,
    EmailTestRequest,
    EmailTestResponse,
    SettingsResponse,
)
from app.services.admin_setting_service import AdminSettingService

router = APIRouter(prefix="/api/v1/admin/settings", tags=["admin-settings"])


@router.get("", response_model=SettingsResponse, dependencies=[Depends(require_admin_permission("system:settings:view"))])
async def read_settings(db: AsyncSession = Depends(get_db)) -> SettingsResponse:
    return await AdminSettingService(db).read()


@router.put(
    "/basic",
    response_model=BasicSettings,
    dependencies=[Depends(require_admin_permission("system:settings:update"))],
)
async def update_basic(data: BasicSettings, db: AsyncSession = Depends(get_db)) -> BasicSettings:
    return await AdminSettingService(db).update_basic(data)


@router.put(
    "/email",
    response_model=EmailSettings,
    dependencies=[Depends(require_admin_permission("system:settings:update"))],
)
async def update_email(data: EmailSettingsUpdate, db: AsyncSession = Depends(get_db)) -> EmailSettings:
    return await AdminSettingService(db).update_email(data)


@router.post(
    "/email/test",
    response_model=EmailTestResponse,
    dependencies=[Depends(require_admin_permission("system:settings:email"))],
)
async def test_email(data: EmailTestRequest, db: AsyncSession = Depends(get_db)) -> EmailTestResponse:
    await AdminSettingService(db).send_test_email(str(data.to_email))
    return EmailTestResponse(message="测试邮件已发送")
