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
    BOOKING_CLEANUP_INTERVAL_SECONDS: int = 300

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
    WECHAT_PAY_BOOKING_NOTIFY_URL: str = ""
    WECHAT_PAY_API_BASE_URL: str = "https://api.mch.weixin.qq.com"

    # WeChat mini program login
    WECHAT_MINI_LOGIN_ENABLED: bool = False
    WECHAT_MINI_APPID: str = ""
    WECHAT_MINI_SECRET: str = ""
    WECHAT_MINI_API_BASE_URL: str = "https://api.weixin.qq.com"
    WECHAT_MINI_REQUEST_TIMEOUT_SECONDS: float = 5.0

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

    @property
    def wechat_mini_missing_settings(self) -> list[str]:
        """Return missing mini program login settings without exposing values."""
        if not self.WECHAT_MINI_LOGIN_ENABLED:
            return []

        required = {
            "WECHAT_MINI_APPID": self.WECHAT_MINI_APPID,
            "WECHAT_MINI_SECRET": self.WECHAT_MINI_SECRET,
            "WECHAT_MINI_API_BASE_URL": self.WECHAT_MINI_API_BASE_URL,
        }
        return [name for name, value in required.items() if not value]

    @property
    def is_wechat_mini_login_usable(self) -> bool:
        """Whether WeChat mini program login is enabled and configured."""
        return (
            self.WECHAT_MINI_LOGIN_ENABLED
            and not self.wechat_mini_missing_settings
            and self.WECHAT_MINI_REQUEST_TIMEOUT_SECONDS > 0
        )

    def require_wechat_mini_login_usable(self) -> None:
        """Raise a sanitized error if WeChat mini program login cannot be used."""
        if not self.WECHAT_MINI_LOGIN_ENABLED:
            raise ValueError("WeChat mini program login is disabled")
        missing = self.wechat_mini_missing_settings
        if missing:
            raise ValueError(
                "Missing WeChat mini program login configuration: "
                + ", ".join(sorted(missing))
            )
        if self.WECHAT_MINI_REQUEST_TIMEOUT_SECONDS <= 0:
            raise ValueError(
                "Invalid WeChat mini program login configuration: "
                "WECHAT_MINI_REQUEST_TIMEOUT_SECONDS"
            )


settings = Settings()
