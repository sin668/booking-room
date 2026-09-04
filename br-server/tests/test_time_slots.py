import json
from datetime import date, time

from app.utils.time_slots import (
    TimeSlot,
    build_time_slots_from_date,
    parse_time_slots,
    rebuild_from_time_range,
)


def test_parse_standard_format():
    raw = json.dumps([{"weekday": 3, "time_slot": "10:00-12:00"}])
    assert parse_time_slots(raw) == [TimeSlot(weekday=3, start="10:00", end="12:00")]


def test_parse_pure_string_array_format():
    raw = json.dumps(["14:00-16:00"])
    assert parse_time_slots(raw) == [TimeSlot(weekday=None, start="14:00", end="16:00")]


def test_parse_split_object_format():
    raw = json.dumps([{"weekday": 6, "start": "12:00", "end": "14:00"}])
    assert parse_time_slots(raw) == [TimeSlot(weekday=6, start="12:00", end="14:00")]


def test_parse_none_returns_empty():
    assert parse_time_slots(None) == []


def test_parse_empty_string_returns_empty():
    assert parse_time_slots("") == []


def test_parse_invalid_json_returns_empty():
    assert parse_time_slots("not-json") == []


def test_build_from_date_uses_isoweekday():
    d = date(2026, 9, 2)
    result = build_time_slots_from_date(booking_date=d, time_slot="10:00-12:00")
    assert json.loads(result) == [{"weekday": d.isoweekday(), "time_slot": "10:00-12:00"}]


def test_rebuild_from_time_range_roundtrip():
    d = date(2026, 9, 2)
    result = rebuild_from_time_range(booking_date=d, start_time=time(10, 0), end_time=time(12, 0))
    assert parse_time_slots(result) == [TimeSlot(weekday=d.isoweekday(), start="10:00", end="12:00")]
