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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Aliyun SMS
    ALIYUN_SMS_ACCESS_KEY_ID: str = ""
    ALIYUN_SMS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = "\u53bbK\u4e66"
    ALIYUN_SMS_TEMPLATE_CODE: str = "SMS_504980114"
    ALIYUN_CAPTCHA_SCENE_ID: str = ""

    # Admin
    ADMIN_TOKEN: str = ""

    # Cookie
    COOKIE_SECURE: bool = False

    # Feature flags
    REGISTRATION_ENABLED: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
