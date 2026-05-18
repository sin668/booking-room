import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_setting import SystemSetting
from app.schemas.admin_setting import BasicSettings, EmailSettings, EmailSettingsUpdate, SettingsResponse

BASIC_DEFAULTS = BasicSettings().model_dump()
EMAIL_DEFAULTS = {
    "smtp_host": "",
    "smtp_port": "",
    "smtp_username": "",
    "smtp_sender": "",
    "smtp_tls": "true",
}


class AdminSettingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def read(self) -> SettingsResponse:
        settings = await self._settings_map()
        return SettingsResponse(
            basic=BasicSettings(**{key: self._decode_value(settings.get(key), default) for key, default in BASIC_DEFAULTS.items()}),
            email=self._email_response(settings),
        )

    async def update_basic(self, data: BasicSettings) -> BasicSettings:
        for key, value in data.model_dump().items():
            await self._upsert(key, str(value), "basic", is_secret=False)
        await self._db.flush()
        return (await self.read()).basic

    async def update_email(self, data: EmailSettingsUpdate) -> EmailSettings:
        values = data.model_dump(exclude_unset=True)
        password = values.pop("smtp_password", None)
        for key, value in values.items():
            await self._upsert(key, "" if value is None else str(value), "email", is_secret=False)
        if password:
            await self._upsert("smtp_password", password, "email", is_secret=True)
        await self._db.flush()
        return (await self.read()).email

    async def send_test_email(self, to_email: str) -> None:
        response = await self.read()
        settings = await self._settings_map()
        password = settings.get("smtp_password").value if settings.get("smtp_password") else ""
        email = response.email
        if not email.smtp_host or not email.smtp_port or not email.smtp_sender or not to_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件配置不完整")

        message = EmailMessage()
        message["Subject"] = "Booking Room test email"
        message["From"] = email.smtp_sender
        message["To"] = to_email
        message.set_content("This is a test email from Booking Room.")
        try:
            with smtplib.SMTP(email.smtp_host, email.smtp_port, timeout=10) as client:
                if email.smtp_tls:
                    client.starttls()
                if email.smtp_username and password:
                    client.login(email.smtp_username, password)
                client.send_message(message)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="测试邮件发送失败") from exc

    async def _settings_map(self) -> dict[str, SystemSetting]:
        rows = list((await self._db.execute(select(SystemSetting))).scalars().all())
        return {row.key: row for row in rows}

    async def _upsert(self, key: str, value: str, group: str, is_secret: bool) -> None:
        setting = await self._db.get(SystemSetting, key)
        if setting is None:
            setting = SystemSetting(key=key, value=value, group=group, is_secret=is_secret)
            self._db.add(setting)
        else:
            setting.value = value
            setting.group = group
            setting.is_secret = is_secret

    def _email_response(self, settings: dict[str, SystemSetting]) -> EmailSettings:
        port_value = self._decode_value(settings.get("smtp_port"), EMAIL_DEFAULTS["smtp_port"])
        return EmailSettings(
            smtp_host=self._decode_value(settings.get("smtp_host"), EMAIL_DEFAULTS["smtp_host"]),
            smtp_port=int(port_value) if port_value else None,
            smtp_username=self._decode_value(settings.get("smtp_username"), EMAIL_DEFAULTS["smtp_username"]),
            smtp_sender=self._decode_value(settings.get("smtp_sender"), EMAIL_DEFAULTS["smtp_sender"]),
            smtp_tls=self._as_bool(self._decode_value(settings.get("smtp_tls"), EMAIL_DEFAULTS["smtp_tls"])),
            smtp_password_set=bool(settings.get("smtp_password") and settings["smtp_password"].value),
        )

    def _decode_value(self, setting: SystemSetting | None, default):
        if setting is None:
            return default
        if isinstance(default, bool):
            return self._as_bool(setting.value)
        return setting.value or default

    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}
