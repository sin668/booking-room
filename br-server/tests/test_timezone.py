from datetime import datetime, timezone

from app.utils.timezone import CHINA_TIMEZONE, booking_now, ensure_booking_timezone


def test_china_timezone_is_shanghai():
    assert str(CHINA_TIMEZONE) == "Asia/Shanghai"


def test_booking_now_returns_naive():
    assert booking_now().tzinfo is None


def test_booking_now_matches_shanghai_wall_clock():
    now = booking_now()
    aware = datetime.now(CHINA_TIMEZONE).replace(tzinfo=None)
    assert abs((aware - now).total_seconds()) < 2


def test_booking_now_explicit_timezone_param():
    utc_now = booking_now("UTC")
    assert utc_now.tzinfo is None
    assert abs((booking_now() - utc_now).total_seconds() - 8 * 3600) < 2


def test_ensure_booking_timezone_naive_input():
    result = ensure_booking_timezone(datetime(2026, 9, 3, 10, 0, 0))
    assert result.tzinfo == CHINA_TIMEZONE and result.hour == 10


def test_ensure_booking_timezone_aware_input_converts():
    result = ensure_booking_timezone(datetime(2026, 9, 3, 2, 0, 0, tzinfo=timezone.utc))
    assert result.tzinfo == CHINA_TIMEZONE and result.hour == 10  # UTC 02:00 -> 沪 10:00
