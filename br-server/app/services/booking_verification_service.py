import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.booking_status import BookingStatus, PaymentStatus
from app.domain.verification_rules import (
    COMPACT_TOKEN_VERSION,
    TOKEN_TTL_SECONDS,
    ExpiredVerificationToken,
    InvalidVerificationToken,
    create_compact_verification_token,
    decode_compact_verification_token,
    is_verifiable,
    resolve_verification_status,
)
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.booking_verification import (
    BookingVerificationBookingSummary,
    BookingVerificationConfirmResponse,
    BookingVerificationDetailResponse,
    BookingVerificationTokenResponse,
    VerifiableBookingListResponse,
)

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
    return settings.JWT_SECRET_KEY


def _create_verification_token(booking_id: int, user_id: str, now: datetime) -> tuple[str, datetime]:
    return create_compact_verification_token(
        booking_id=booking_id,
        secret=_get_signing_secret(),
        now=now,
        nonce=secrets.token_urlsafe(3),
    )


def _decode_compact_verification_token(token: str, now: datetime) -> VerificationTokenPayload:
    try:
        payload = decode_compact_verification_token(
            token=token,
            secret=_get_signing_secret(),
            now=now,
        )
    except ExpiredVerificationToken as exc:
        raise ExpiredVerificationTokenError("核销码已过期") from exc
    except InvalidVerificationToken as exc:
        raise InvalidVerificationTokenError("无效的核销码") from exc

    return VerificationTokenPayload(
        booking_id=payload.booking_id,
        user_id="",
        iat=payload.issued_at,
        nonce=payload.nonce,
    )


def _create_legacy_jwt_verification_token(booking_id: int, user_id: str, now: datetime) -> tuple[str, datetime]:
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
    if token.startswith(f"{COMPACT_TOKEN_VERSION}."):
        return _decode_compact_verification_token(token, now)

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
        can_verify=is_verifiable(
            status=booking.status, payment_status=booking.payment_status
        ),
    )


async def issue_verification_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    booking_id: int | None = None,
) -> BookingVerificationTokenResponse:
    now = _booking_now()
    rows = await _load_verifiable_booking_rows(db, user_id)
    row = _select_booking(rows, now, booking_id)
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


async def list_verifiable_bookings(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> VerifiableBookingListResponse:
    rows = await _load_verifiable_booking_rows(db, user_id)
    if not rows:
        raise NoVerifiableBookingError("暂无可核销预约")

    user = await _load_user(db, str(user_id))
    return VerifiableBookingListResponse(
        items=[
            _build_booking_summary(booking, seat, room, user)
            for booking, seat, room in rows
        ]
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

    if booking.status == BookingStatus.COMPLETED:
        raise BookingAlreadyVerifiedError("预约已核销")
    if not is_verifiable(status=booking.status, payment_status=booking.payment_status):
        raise BookingNotVerifiableError("预约状态不可核销")

    now = _booking_now()
    end_at = datetime.combine(
        booking.date, booking.end_time, tzinfo=_booking_timezone()
    )
    new_status = resolve_verification_status(
        now=now.replace(tzinfo=None), end_at=end_at.replace(tzinfo=None)
    )

    # 幂等保护：已核销的 confirmed 预约不可重复核销
    if booking.status == BookingStatus.IN_PROGRESS and new_status == BookingStatus.IN_PROGRESS:
        raise BookingAlreadyVerifiedError("预约已核销")

    update_result = await db.execute(
        update(Booking)
        .where(
            Booking.id == payload.booking_id,
            Booking.user_id == booking.user_id,
            or_(
                Booking.status == BookingStatus.IN_PROGRESS.value,
                and_(
                    Booking.status == BookingStatus.PENDING_START.value,
                    Booking.payment_status == PaymentStatus.PAID.value,
                ),
            ),
        )
        .values(status=new_status.value)
    )
    if update_result.rowcount != 1:
        refreshed = await _load_booking_for_status(db, payload)
        if refreshed.status == BookingStatus.COMPLETED:
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
        .where(Booking.id == payload.booking_id)
    )
    row = result.first()
    if row is None:
        raise NoVerifiableBookingError("暂无可核销预约")
    booking, seat, room = row
    if payload.user_id and booking.user_id != payload.user_id:
        raise NoVerifiableBookingError("暂无可核销预约")
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
            select(Booking).where(Booking.id == payload.booking_id)
        )
    ).scalar_one_or_none()
    if booking is None or (payload.user_id and booking.user_id != payload.user_id):
        raise NoVerifiableBookingError("暂无可核销预约")
    return booking


async def _load_verifiable_booking_rows(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[tuple[Booking, Seat, StudyRoom]]:
    result = await db.execute(
        select(Booking, Seat, StudyRoom)
        .join(Seat, Seat.id == Booking.seat_id)
        .join(StudyRoom, StudyRoom.id == Booking.room_id)
        .where(
            Booking.user_id == str(user_id),
            or_(
                Booking.status == BookingStatus.IN_PROGRESS.value,
                and_(
                    Booking.status == BookingStatus.PENDING_START.value,
                    Booking.payment_status == PaymentStatus.PAID.value,
                ),
            ),
        )
        .order_by(Booking.date.asc(), Booking.start_time.asc(), Booking.id.asc())
    )
    return list(result.all())


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


def _select_nearest_booking(
    rows: list[tuple[Booking, Seat, StudyRoom]],
    now: datetime,
) -> tuple[Booking, Seat, StudyRoom] | None:
    if not rows:
        return None

    now = _ensure_booking_timezone(now)

    def sort_key(row: tuple[Booking, Seat, StudyRoom]) -> tuple[int, float, int]:
        booking = row[0]
        start_at = datetime.combine(
            booking.date,
            booking.start_time,
            tzinfo=_booking_timezone(),
        )
        verification_start_at = start_at - timedelta(
            minutes=VERIFICATION_EARLY_ARRIVAL_MINUTES,
        )
        end_at = datetime.combine(
            booking.date,
            booking.end_time,
            tzinfo=_booking_timezone(),
        )
        if verification_start_at <= now <= end_at:
            return 0, verification_start_at.timestamp(), booking.id
        if now < verification_start_at:
            return 1, verification_start_at.timestamp(), booking.id
        return 2, -end_at.timestamp(), booking.id

    return min(rows, key=sort_key)


def _select_booking(
    rows: list[tuple[Booking, Seat, StudyRoom]],
    now: datetime,
    booking_id: int | None,
) -> tuple[Booking, Seat, StudyRoom] | None:
    if booking_id is None:
        return _select_nearest_booking(rows, now)
    for row in rows:
        if row[0].id == booking_id:
            return row
    return None


def _build_verify_url(token: str) -> str:
    path = f"{VERIFY_HASH_PATH}?token={token}"
    if not settings.FRONTEND_BASE_URL:
        return path
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
