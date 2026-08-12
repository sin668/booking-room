from contextlib import asynccontextmanager
import asyncio
import logging
import re
from pathlib import Path
from contextlib import suppress
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.activity import router as activity_router
from app.api.routes.admin_activity import router as admin_activity_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_booking import router as admin_booking_router
from app.api.routes.admin_coupon import router as admin_coupon_router
from app.api.routes.admin_user import router as admin_user_router
from app.api.routes.admin_wallet import router as admin_wallet_router
from app.api.routes.admin_menu import router as admin_menu_router
from app.api.routes.admin_role import router as admin_role_router
from app.api.routes.admin_seat import flat_seats_router as admin_flat_seats_router
from app.api.routes.admin_seat import room_seats_router as admin_room_seats_router
from app.api.routes.admin_setting import router as admin_setting_router
from app.api.routes.admin_study_room import router as admin_study_room_router
from app.api.routes.auth import router as auth_router
from app.api.routes.banner import router as banner_router
from app.api.routes.booking import router as booking_router
from app.api.routes.coupon import router as coupon_router
from app.api.routes.booking_verification import router as booking_verification_router
from app.api.routes.cities import router as cities_router
from app.api.routes.notification import router as notification_router
from app.api.routes.room_follow import router as room_follow_router
from app.api.routes.seat import router as seat_router
from app.api.routes.study_record import router as study_record_router
from app.api.routes.study_room import router as study_room_router
from app.api.routes.upload import router as upload_router
from app.api.routes.user import router as user_router
from app.api.routes.wallet import router as wallet_router
from app.core.config import settings
from app.core.database import async_session
from app.core.redis import close_redis, init_redis
from app.services.booking_payment_service import BookingPaymentService
from app.services.wechat_pay_client import WechatPayClient

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    AsyncIOScheduler = None

logger = logging.getLogger(__name__)


async def _cleanup_unpaid_bookings_job() -> None:
    async with async_session() as session:
        try:
            wechat_client = (
                WechatPayClient(settings)
                if getattr(settings, "WECHAT_PAY_ENABLED", False)
                else None
            )
            if wechat_client is None:
                logger.info("Booking payment reconciliation skipped: WeChat Pay disabled")
                return
            count = await BookingPaymentService(
                session,
                wechat_client=wechat_client,
                config=settings,
            ).reconcile_pending_payments()
            await session.commit()
            logger.info("Booking payment reconciliation processed %s booking(s)", count)
        except Exception:
            await session.rollback()
            logger.exception("Booking payment reconciliation failed")
            raise


async def _booking_payment_reconciliation_loop() -> None:
    """Fallback periodic runner for environments without APScheduler."""
    while True:
        await asyncio.sleep(settings.BOOKING_CLEANUP_INTERVAL_SECONDS)
        try:
            await _cleanup_unpaid_bookings_job()
        except Exception:
            # The job logs failures. Keep the loop alive for later retries.
            pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    await init_redis()
    scheduler = None
    if AsyncIOScheduler is not None:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _cleanup_unpaid_bookings_job,
            "interval",
            seconds=settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
        scheduler.start()
        app.state.booking_cleanup_scheduler = scheduler
        logger.info(
            "Booking payment reconciliation scheduler started: interval=%s seconds",
            settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
    else:
        fallback_task = asyncio.create_task(_booking_payment_reconciliation_loop())
        app.state.booking_cleanup_fallback_task = fallback_task
        logger.warning(
            "Booking payment reconciliation using asyncio fallback: "
            "apscheduler is not installed; interval=%s seconds",
            settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
    yield
    # Shutdown
    if scheduler is not None:
        scheduler.shutdown(wait=False)
    fallback_task = getattr(app.state, "booking_cleanup_fallback_task", None)
    if fallback_task is not None:
        fallback_task.cancel()
        with suppress(asyncio.CancelledError):
            await fallback_task
    await close_redis()


app = FastAPI(
    title="Booking Room API",
    description="Backend service for Booking Room application",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)


# Combined ASGI middleware: CORS + trailing-slash normalisation.
# Handles preflight OPTIONS directly and injects CORS headers on all responses.
_CORS_ALLOWED_RE = re.compile(
    r"^https?://(localhost|127\.0\.0\.1|\d+\.\d+\.\d+\.\d+|.*\.?yichengpai\.cn)(:\d+)?$"
)


class AppMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # --- Strip trailing slash from path ---
        path = scope["path"]
        if path != "/" and path.endswith("/"):
            scope["path"] = path.rstrip("/")

        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return

        # --- CORS: read Origin header ---
        origin = None
        for name, value in scope.get("headers", []):
            if name == b"origin":
                origin = value.decode("latin-1")
                break

        if not origin or not _CORS_ALLOWED_RE.match(origin):
            # Not a CORS request — pass through
            await self.app(scope, receive, send)
            return

        cors_headers = [
            (b"access-control-allow-origin", origin.encode()),
            (b"access-control-allow-credentials", b"true"),
            (b"access-control-allow-methods", b"*"),
            (b"access-control-allow-headers", b"*"),
        ]

        # Preflight: respond immediately
        if scope["method"] == "OPTIONS":
            headers = cors_headers + [
                (b"access-control-max-age", b"86400"),
                (b"content-type", b"text/plain"),
                (b"content-length", b"0"),
            ]
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": headers,
            })
            await send({"type": "http.response.body", "body": b""})
            return

        # Normal request: wrap send() to inject CORS headers
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # Strip any CORS headers set by inner layers
                headers = [
                    (k, v) for k, v in headers
                    if not k.startswith(b"access-control-")
                ]
                headers.extend(cors_headers)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_cors)


app.add_middleware(AppMiddleware)

# Static files for uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(upload_router)
app.include_router(admin_auth_router)
app.include_router(admin_user_router)
app.include_router(admin_wallet_router)
app.include_router(admin_menu_router)
app.include_router(admin_role_router)
app.include_router(admin_setting_router)
app.include_router(admin_activity_router)
app.include_router(admin_booking_router)
app.include_router(admin_coupon_router)
app.include_router(admin_study_room_router)
app.include_router(admin_room_seats_router)
app.include_router(admin_flat_seats_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(banner_router)
app.include_router(activity_router)
app.include_router(coupon_router)
app.include_router(cities_router)
app.include_router(seat_router)
app.include_router(study_room_router)
app.include_router(study_record_router)
app.include_router(booking_router)
app.include_router(booking_verification_router)
app.include_router(wallet_router)
app.include_router(notification_router)
app.include_router(room_follow_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
