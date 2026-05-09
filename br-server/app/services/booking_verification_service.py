import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.booking_verification import (
    BookingVerificationBookingSummary,
    BookingVerificationConfirmResponse,
    BookingVerificationDetailResponse,
    BookingVerificationTokenResponse,
)

TOKEN_TTL_SECONDS = 5 * 60
VERIFICATION_TOKEN_PURPOSE = "booking_verification"
VERIFICATION_AUDIENCE = "booking-verification"
VERIFICATION_EARLY_ARRIVAL_MINUTES = 30
VERIFY_HASH_PATH = "/#/pages/verify-booking/index"


class BookingVerificationError(ValueError):
    """Base exception for booking verification operations."""


class NoVerifiableBookingError(BookingVerificationError):
    pass


class InvalidVerificationTokenError(BookingVerificationError):
    pass


class ExpiredVerificationTokenError(BookingVerificationError):
    pass


class BookingAlreadyVerifiedError(BookingVerificationError):
    pass


class BookingNotVerifiableError(BookingVerificationError):
    pass


class VerificationTokenConfigurationError(BookingVerificationError):
    pass


@dataclass(frozen=True)
class VerificationTokenPayload:
    booking_id: int
    user_id: str
    iat: datetime
    nonce: str


def _get_signing_secret() -> str:
    if not settings.JWT_SECRET_KEY:
        raise VerificationTokenConfigurationError("JWT signing secret is not configured")
    return settings.JWT_SECRET_KEY


def _create_verification_token(booking_id: int, user_id: str, now: datetime) -> tuple[str, datetime]:
    now = _ensure_utc(now)
    expires_at = now + timedelta(seconds=TOKEN_TTL_SECONDS)
    payload = {
        "booking_id": booking_id,
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "nonce": str(uuid.uuid4()),
        "purpose": VERIFICATION_TOKEN_PURPOSE,
        "aud": VERIFICATION_AUDIENCE,
    }
    token = jwt.encode(payload, _get_signing_secret(), algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def _decode_verification_token(token: str, now: datetime) -> VerificationTokenPayload:
    try:
        payload = jwt.decode(
            token,
            _get_signing_secret(),
            algorithms=[settings.JWT_ALGORITHM],
            audience=VERIFICATION_AUDIENCE,
            options={"require_aud": True},
        )
    except ExpiredSignatureError as exc:
        raise ExpiredVerificationTokenError("核销码已过期") from exc
    except JWTError as exc:
        raise InvalidVerificationTokenError("无效的核销码") from exc

    try:
        booking_id = int(payload["booking_id"])
        user_id = str(payload["user_id"])
        issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=UTC)
        nonce = str(payload["nonce"])
        purpose = str(payload["purpose"])
        audience = str(payload["aud"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidVerificationTokenError("无效的核销码") from exc

    if (
        not user_id
        or not nonce
        or purpose != VERIFICATION_TOKEN_PURPOSE
        or audience != VERIFICATION_AUDIENCE
    ):
        raise InvalidVerificationTokenError("无效的核销码")

    return VerificationTokenPayload(
        booking_id=booking_id,
        user_id=user_id,
        iat=issued_at,
        nonce=nonce,
    )


def _build_booking_summary(
    booking: Booking,
    seat: Seat,
    room: StudyRoom,
    user: User,
) -> BookingVerificationBookingSummary:
    return BookingVerificationBookingSummary(
        id=booking.id,
        user_id=booking.user_id,
        user_nickname=user.nickname,
        user_phone=user.phone,
        room_id=room.id,
        room_name=room.name,
        room_address=room.address,
        seat_id=seat.id,
        seat_number=seat.seat_number,
        seat_zone=seat.zone,
        seat_position=seat.position,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_price=booking.total_price,
        status=booking.status,
        can_verify=booking.status == "confirmed",
    )


async def issue_verification_token(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> BookingVerificationTokenResponse:
    now = _booking_now()
    result = await db.execute(
        select(Booking, Seat, StudyRoom)
        .join(Seat, Seat.id == Booking.seat_id)
        .join(StudyRoom, StudyRoom.id == Booking.room_id)
        .where(
            Booking.user_id == str(user_id),
            Booking.status == "confirmed",
        )
        .order_by(Booking.date.asc(), Booking.start_time.asc(), Booking.id.asc())
    )
    row = next(
        (
            candidate
            for candidate in result.all()
            if _is_booking_in_verification_window(candidate[0], now)
        ),
        None,
    )
    if row is None:
        raise NoVerifiableBookingError("暂无可核销预约")

    booking, seat, room = row
    user = await _load_user(db, booking.user_id)
    token, expires_at = _create_verification_token(booking.id, booking.user_id, now)
    return BookingVerificationTokenResponse(
        token=token,
        expires_at=expires_at,
        verify_url=_build_verify_url(token),
        booking=_build_booking_summary(booking, seat, room, user),
    )


async def inspect_verification_token(
    db: AsyncSession,
    token: str,
) -> BookingVerificationDetailResponse:
    payload = _decode_verification_token(token, datetime.now(UTC))
    booking, seat, room, user = await _load_payload_booking(db, payload)
    return BookingVerificationDetailResponse(
        booking=_build_booking_summary(booking, seat, room, user),
    )


async def confirm_verification(
    db: AsyncSession,
    token: str,
) -> BookingVerificationConfirmResponse:
    payload = _decode_verification_token(token, datetime.now(UTC))
    booking, seat, room, user = await _load_payload_booking(db, payload)

    if booking.status == "completed":
        raise BookingAlreadyVerifiedError("预约已核销")
    if booking.status != "confirmed":
        raise BookingNotVerifiableError("预约状态不可核销")
    if not _is_booking_in_verification_window(booking, datetime.now(UTC)):
        raise BookingNotVerifiableError("预约状态不可核销")

    update_result = await db.execute(
        update(Booking)
        .where(
            Booking.id == payload.booking_id,
            Booking.user_id == payload.user_id,
            Booking.status == "confirmed",
        )
        .values(status="completed")
    )
    if update_result.rowcount != 1:
        refreshed = await _load_booking_for_status(db, payload)
        if refreshed.status == "completed":
            raise BookingAlreadyVerifiedError("预约已核销")
        raise BookingNotVerifiableError("预约状态不可核销")

    await db.flush()
    booking, seat, room, user = await _load_payload_booking(db, payload)

    return BookingVerificationConfirmResponse(
        booking=_build_booking_summary(booking, seat, room, user),
    )


async def _load_payload_booking(
    db: AsyncSession,
    payload: VerificationTokenPayload,
) -> tuple[Booking, Seat, StudyRoom, User]:
    result = await db.execute(
        select(Booking, Seat, StudyRoom)
        .join(Seat, Seat.id == Booking.seat_id)
        .join(StudyRoom, StudyRoom.id == Booking.room_id)
        .where(
            Booking.id == payload.booking_id,
            Booking.user_id == payload.user_id,
        )
    )
    row = result.first()
    if row is None:
        raise NoVerifiableBookingError("暂无可核销预约")
    booking, seat, room = row
    user = await _load_user(db, booking.user_id)
    return booking, seat, room, user


async def _load_user(db: AsyncSession, user_id: str) -> User:
    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise InvalidVerificationTokenError("无效的核销码") from exc

    user = (await db.execute(select(User).where(User.id == parsed_user_id))).scalar_one_or_none()
    if user is None:
        raise NoVerifiableBookingError("暂无可核销预约")
    return user


async def _load_booking_for_status(db: AsyncSession, payload: VerificationTokenPayload) -> Booking:
    booking = (
        await db.execute(
            select(Booking).where(
                Booking.id == payload.booking_id,
                Booking.user_id == payload.user_id,
            )
        )
    ).scalar_one_or_none()
    if booking is None:
        raise NoVerifiableBookingError("暂无可核销预约")
    return booking


def _is_booking_in_verification_window(booking: Booking, now: datetime) -> bool:
    now = _ensure_booking_timezone(now)
    if booking.date != now.date():
        return False

    start_at = datetime.combine(
        booking.date,
        booking.start_time,
        tzinfo=_booking_timezone(),
    ) - timedelta(minutes=VERIFICATION_EARLY_ARRIVAL_MINUTES)
    end_at = datetime.combine(
        booking.date,
        booking.end_time,
        tzinfo=_booking_timezone(),
    )
    return start_at <= now <= end_at


def _build_verify_url(token: str) -> str:
    if not settings.FRONTEND_BASE_URL:
        raise VerificationTokenConfigurationError("Frontend base URL is not configured")
    path = f"{VERIFY_HASH_PATH}?token={token}"
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}{path}"


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _booking_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.BOOKING_TIMEZONE)
    except ZoneInfoNotFoundError as exc:
        raise VerificationTokenConfigurationError("Booking timezone is not configured") from exc


def _booking_now() -> datetime:
    return datetime.now(_booking_timezone())


def _ensure_booking_timezone(value: datetime) -> datetime:
    timezone = _booking_timezone()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone)
    return value.astimezone(timezone)
