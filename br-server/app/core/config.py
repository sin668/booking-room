from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Database
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = ""

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3

    # Aliyun SMS
    ALIYUN_SMS_ACCESS_KEY_ID: str = ""
    ALIYUN_SMS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = "\u53bbK\u4e66"
    ALIYUN_SMS_TEMPLATE_CODE: str = "SMS_504980114"
    ALIYUN_CAPTCHA_SCENE_ID: str = ""

    # Admin
    ADMIN_TOKEN: str = ""
    ADMIN_DEFAULT_USERNAME: str = "admin"
    ADMIN_DEFAULT_PASSWORD: str = ""
    ADMIN_DEFAULT_EMAIL: str = ""
    ENVIRONMENT: str = "development"

    # Booking verification
    FRONTEND_BASE_URL: str = ""
    BOOKING_TIMEZONE: str = "Asia/Shanghai"

    # WeChat Pay
    WECHAT_PAY_ENABLED: bool = False
    WECHAT_PAY_APPID: str = ""
    WECHAT_PAY_MCHID: str = ""
    WECHAT_PAY_API_V3_KEY: str = ""
    WECHAT_PAY_PRIVATE_KEY_PATH: str = ""
    WECHAT_PAY_CERT_SERIAL_NO: str = ""
    WECHAT_PAY_PLATFORM_CERT_SERIAL_NO: str = ""
    WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH: str = ""
    WECHAT_PAY_NOTIFY_URL: str = ""
    WECHAT_PAY_API_BASE_URL: str = "https://api.mch.weixin.qq.com"

    # Cookie
    COOKIE_SECURE: bool = False

    # Feature flags
    REGISTRATION_ENABLED: bool = True
    WALLET_SIMULATED_CONFIRM_ENABLED: bool = False

    model_config = {"env_file": ".env"}

    @property
    def wechat_pay_missing_settings(self) -> list[str]:
        """Return missing setting names without exposing configured values."""
        if not self.WECHAT_PAY_ENABLED:
            return []

        required = {
            "WECHAT_PAY_APPID": self.WECHAT_PAY_APPID,
            "WECHAT_PAY_MCHID": self.WECHAT_PAY_MCHID,
            "WECHAT_PAY_API_V3_KEY": self.WECHAT_PAY_API_V3_KEY,
            "WECHAT_PAY_PRIVATE_KEY_PATH": self.WECHAT_PAY_PRIVATE_KEY_PATH,
            "WECHAT_PAY_CERT_SERIAL_NO": self.WECHAT_PAY_CERT_SERIAL_NO,
            "WECHAT_PAY_PLATFORM_CERT_SERIAL_NO": self.WECHAT_PAY_PLATFORM_CERT_SERIAL_NO,
            "WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH": self.WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH,
            "WECHAT_PAY_NOTIFY_URL": self.WECHAT_PAY_NOTIFY_URL,
        }
        return [name for name, value in required.items() if not value]

    @property
    def is_wechat_pay_usable(self) -> bool:
        """Whether WeChat Pay is enabled and has all required configuration."""
        return self.WECHAT_PAY_ENABLED and not self.wechat_pay_missing_settings

    def require_wechat_pay_usable(self) -> None:
        """Raise a sanitized error if WeChat Pay cannot be used."""
        if not self.WECHAT_PAY_ENABLED:
            raise ValueError("WeChat Pay is disabled")
        missing = self.wechat_pay_missing_settings
        if missing:
            raise ValueError(
                "Missing WeChat Pay configuration: " + ", ".join(sorted(missing))
            )
        if len(self.WECHAT_PAY_API_V3_KEY.encode("utf-8")) != 32:
            raise ValueError("Invalid WeChat Pay configuration: WECHAT_PAY_API_V3_KEY")


settings = Settings()
