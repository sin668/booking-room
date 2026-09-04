from contextlib import asynccontextmanager
import asyncio
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import suppress
from typing import AsyncGenerator
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.activity import router as activity_router
from app.api.routes.admin_activity import router as admin_activity_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_booking import router as admin_booking_router
from app.api.routes.admin_course import router as admin_course_router
from app.api.routes.admin_teacher import router as admin_teacher_router
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
from app.api.routes.course_booking import router as course_booking_router
from app.api.routes.coupon import router as coupon_router
from app.api.routes.booking_verification import router as booking_verification_router
from app.api.routes.cities import router as cities_router
from app.api.routes.notification import router as notification_router
from app.api.routes.room_follow import router as room_follow_router
from app.api.routes.teacher import router as teacher_router
from app.api.routes.seat import router as seat_router
from app.api.routes.study_record import router as study_record_router
from app.api.routes.study_room import router as study_room_router
from app.api.routes.training import router as training_router
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

# 确保 app 命名空间的日志能输出到控制台（uvicorn 默认不配置 app logger）
_app_logger = logging.getLogger("app")
if not _app_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    _app_logger.addHandler(_handler)
    _app_logger.setLevel(logging.INFO)
    _app_logger.propagate = False


async def _payment_reconciliation_job() -> None:
    async with async_session() as session:
        try:
            wechat_client = (
                WechatPayClient(settings)
                if getattr(settings, "WECHAT_PAY_ENABLED", False)
                else None
            )
            if wechat_client is None:
                if settings.SCHEDULER_LOG_ENABLED:
                    logger.info("[微信支付对账定时任务] 已跳过: 微信支付未启用")
                return
            count = await BookingPaymentService(
                session,
                wechat_client=wechat_client,
                config=settings,
            ).reconcile_pending_payments()
            await session.commit()
            if settings.SCHEDULER_LOG_ENABLED:
                logger.info("[微信支付对账定时任务] 已检查 %d 个待支付订单", count)
        except Exception:
            await session.rollback()
            logger.exception("[微信支付对账定时任务] 执行失败")
            raise


async def _booking_payment_reconciliation_loop() -> None:
    """Fallback periodic runner for environments without APScheduler."""
    while True:
        await asyncio.sleep(settings.BOOKING_CLEANUP_INTERVAL_SECONDS)
        try:
            await _payment_reconciliation_job()
        except Exception:
            # The job logs failures. Keep the loop alive for later retries.
            pass


async def _order_status_check_job() -> None:
    """订单状态定时检查任务"""
    from app.services.order_status_scheduler import check_and_update_order_statuses
    try:
        stats = await check_and_update_order_statuses()
        if settings.SCHEDULER_LOG_ENABLED:
            total_changes = (
                stats["seat_started"] + stats["seat_completed"]
                + stats["course_started"] + stats["course_highlight_updated"] + stats["course_completed"]
            )
            logger.info(
                "[订单状态定时任务] 扫描 %d 个订单，变更 %d 个 | "
                "自习室: 开始 %d / 完成 %d | "
                "课程: 开始 %d / 高亮更新 %d / 完成 %d",
                stats["total_scanned"], total_changes,
                stats["seat_started"], stats["seat_completed"],
                stats["course_started"], stats["course_highlight_updated"], stats["course_completed"],
            )
    except Exception:
        logger.exception("Order status check job failed")
        raise


async def _order_status_check_loop() -> None:
    """Fallback periodic runner for order status check without APScheduler."""
    while True:
        await asyncio.sleep(settings.ORDER_STATUS_CHECK_INTERVAL_SECONDS)
        try:
            await _order_status_check_job()
        except Exception:
            pass


def _parse_schedule_status_check_time() -> tuple[int, int]:
    """解析排课状态检查每日运行时间（HH:MM），非法配置回退到 00:00。"""
    try:
        hour_str, minute_str = settings.SCHEDULE_STATUS_CHECK_TIME.split(":")
        hour, minute = int(hour_str), int(minute_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (ValueError, AttributeError):
        pass
    logger.warning(
        "Invalid SCHEDULE_STATUS_CHECK_TIME=%r, fallback to 00:00",
        getattr(settings, "SCHEDULE_STATUS_CHECK_TIME", None),
    )
    return 0, 0


async def _schedule_status_check_job() -> None:
    """排课状态定时检查任务：扫描待开始/进行中排课，今天 >= 开课日期 → 进行中，当前日期 > 结课日期 → 已完成"""
    from app.services.schedule_status_scheduler import check_and_update_schedule_statuses
    try:
        stats = await check_and_update_schedule_statuses()
        if settings.SCHEDULER_LOG_ENABLED:
            logger.info(
                "[排课状态定时任务] 扫描 %d 条待处理排课，转进行中 %d 条，标记完成 %d 条",
                stats["total_scanned"], stats["schedule_started"], stats["schedule_completed"],
            )
    except Exception:
        logger.exception("Schedule status check job failed")
        raise


async def _schedule_status_check_loop() -> None:
    """Fallback daily runner for schedule status check without APScheduler."""
    tz = ZoneInfo("Asia/Shanghai")
    hour, minute = _parse_schedule_status_check_time()
    while True:
        now = datetime.now(tz)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        try:
            await _schedule_status_check_job()
        except Exception:
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
            _payment_reconciliation_job,
            "interval",
            seconds=settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
        scheduler.add_job(
            _order_status_check_job,
            "interval",
            seconds=settings.ORDER_STATUS_CHECK_INTERVAL_SECONDS,
            id="order_status_check",
            replace_existing=True,
        )
        _hour, _minute = _parse_schedule_status_check_time()
        scheduler.add_job(
            _schedule_status_check_job,
            "cron",
            hour=_hour,
            minute=_minute,
            timezone=ZoneInfo("Asia/Shanghai"),
            id="schedule_status_check",
            replace_existing=True,
        )
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info(
            "Booking payment reconciliation scheduler started: interval=%s seconds",
            settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
        logger.info(
            "Order status check scheduler started: interval=%s seconds",
            settings.ORDER_STATUS_CHECK_INTERVAL_SECONDS,
        )
        logger.info(
            "Schedule status check scheduler started: daily at %02d:%02d (Asia/Shanghai)",
            _hour, _minute,
        )
    else:
        fallback_task = asyncio.create_task(_booking_payment_reconciliation_loop())
        app.state.booking_cleanup_fallback_task = fallback_task
        logger.warning(
            "Booking payment reconciliation using asyncio fallback: "
            "apscheduler is not installed; interval=%s seconds",
            settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
        order_status_fallback_task = asyncio.create_task(_order_status_check_loop())
        app.state.order_status_fallback_task = order_status_fallback_task
        logger.warning(
            "Order status check using asyncio fallback: "
            "apscheduler is not installed; interval=%s seconds",
            settings.ORDER_STATUS_CHECK_INTERVAL_SECONDS,
        )
        schedule_status_fallback_task = asyncio.create_task(_schedule_status_check_loop())
        app.state.schedule_status_fallback_task = schedule_status_fallback_task
        logger.warning(
            "Schedule status check using asyncio fallback: "
            "apscheduler is not installed; daily at %s (Asia/Shanghai)",
            settings.SCHEDULE_STATUS_CHECK_TIME,
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
    order_status_fallback_task = getattr(app.state, "order_status_fallback_task", None)
    if order_status_fallback_task is not None:
        order_status_fallback_task.cancel()
        with suppress(asyncio.CancelledError):
            await order_status_fallback_task
    schedule_status_fallback_task = getattr(app.state, "schedule_status_fallback_task", None)
    if schedule_status_fallback_task is not None:
        schedule_status_fallback_task.cancel()
        with suppress(asyncio.CancelledError):
            await schedule_status_fallback_task
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
app.include_router(admin_course_router)
app.include_router(admin_teacher_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(banner_router)
app.include_router(activity_router)
app.include_router(coupon_router)
app.include_router(cities_router)
app.include_router(seat_router)
app.include_router(study_room_router)
app.include_router(training_router)
app.include_router(study_record_router)
app.include_router(booking_router)
app.include_router(course_booking_router)
app.include_router(booking_verification_router)
app.include_router(wallet_router)
app.include_router(notification_router)
app.include_router(room_follow_router)
app.include_router(teacher_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
