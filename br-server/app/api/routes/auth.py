import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.user import (
    RefreshRequest,
    SendCodeRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.jwt_service import JWTService
from app.services.sms_service import SMSService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
REFRESH_TOKEN_COOKIE_KEY = "refresh_token"
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _issue_cookie_token(jwt_svc: JWTService, access_token: str) -> str:
    """Create a refresh token for the cookie from an access token."""
    from jose import jwt as jose_jwt

    payload = jose_jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    user_id = uuid.UUID(payload["sub"])
    refresh_token = jwt_svc.create_refresh_token(user_id)
    rt_payload = jose_jwt.decode(
        refresh_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    jwt_svc.store_refresh_token(user_id, rt_payload["jti"])
    return refresh_token


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly cookie."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=refresh_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )


@router.post("/send-code")
async def send_code(
    body: SendCodeRequest,
    redis=Depends(get_redis),
) -> dict:
    """Send an SMS verification code to the given phone number."""
    sms_service = SMSService(redis=redis, config=settings)
    try:
        await sms_service.send_code(phone=body.phone, captcha_token=body.captcha_token)
    except HTTPException:
        raise

    return {"message": "验证码发送成功"}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TokenResponse:
    """Register a new user with phone number and SMS verification."""
    if not body.agree_terms:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="必须同意用户协议",
        )

    auth_service = AuthService(db=db, redis=redis, config=settings)
    jwt_svc = JWTService(config=settings, redis=redis)

    token_response = await auth_service.register(body)
    refresh_token = _issue_cookie_token(jwt_svc, token_response.access_token)
    _set_refresh_token_cookie(response, refresh_token)

    return token_response


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TokenResponse:
    """Authenticate user with phone and password."""
    auth_service = AuthService(db=db, redis=redis, config=settings)
    jwt_svc = JWTService(config=settings, redis=redis)

    token_response = await auth_service.login(body)
    refresh_token = _issue_cookie_token(jwt_svc, token_response.access_token)
    _set_refresh_token_cookie(response, refresh_token)

    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TokenResponse:
    """Refresh access and refresh tokens.

    Accepts the refresh token from the HttpOnly cookie or the request body.
    """
    refresh_token_str = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)
    if not refresh_token_str and body is not None:
        refresh_token_str = body.refresh_token

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供Refresh Token",
        )

    auth_service = AuthService(db=db, redis=redis, config=settings)
    jwt_svc = JWTService(config=settings, redis=redis)

    result = await auth_service.refresh_token(refresh_token_str)

    if result is None:
        response.delete_cookie(REFRESH_TOKEN_COOKIE_KEY)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        )

    refresh_token = _issue_cookie_token(jwt_svc, result.access_token)
    _set_refresh_token_cookie(response, refresh_token)

    return result


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> dict:
    """Logout the current user.

    Blacklists the access token and revokes all refresh tokens.
    """
    auth_header = request.headers.get("authorization", "")
    access_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    jwt_svc = JWTService(config=settings, redis=redis)
    payload = jwt_svc.verify_token(access_token)

    auth_service = AuthService(db=db, redis=redis, config=settings)
    await auth_service.logout(token=access_token, payload=payload)

    response.delete_cookie(REFRESH_TOKEN_COOKIE_KEY)

    return {"message": "退出成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get the current authenticated user's info."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return UserResponse.model_validate(user)
