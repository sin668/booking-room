"""time_slots 数据契约层（Design Doc §3.1 / §3.2）。

标准格式: [{"weekday": int 1-7, "time_slot": "HH:MM-HH:MM"}]
兼容历史格式 A: ["HH:MM-HH:MM"]（纯字符串数组，weekday 缺省 None）
兼容历史格式 B: [{"weekday": N, "start": "HH:MM", "end": "HH:MM"}]（拆分）
解析失败静默容错返回空列表，由调用方回退展示。本模块只处理数据契约，
不产生任何展示文案（三端展示文案各自保留，见 §3.2）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TimeSlot:
    weekday: int | None
    start: str
    end: str


def _split_range(text: str) -> tuple[str, str] | None:
    if "-" not in text:
        return None
    start, _, end = text.partition("-")
    return start.strip(), end.strip()


def parse_time_slots(raw: str | None) -> list[TimeSlot]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    result: list[TimeSlot] = []
    for item in data:
        if isinstance(item, str):
            pair = _split_range(item)
            if pair:
                result.append(TimeSlot(weekday=None, start=pair[0], end=pair[1]))
        elif isinstance(item, dict):
            weekday = item.get("weekday")
            if "time_slot" in item:
                pair = _split_range(str(item["time_slot"]))
                if pair:
                    result.append(TimeSlot(weekday=weekday, start=pair[0], end=pair[1]))
            elif "start" in item and "end" in item:
                result.append(TimeSlot(weekday=weekday, start=str(item["start"]), end=str(item["end"])))
    return result


def build_time_slots_from_date(*, booking_date: date, time_slot: str) -> str:
    return json.dumps(
        [{"weekday": booking_date.isoweekday(), "time_slot": time_slot}],
        ensure_ascii=False,
    )


def rebuild_from_time_range(*, booking_date: date | None, start_time, end_time) -> str:
    weekday = booking_date.isoweekday() if booking_date is not None else None
    start = start_time.strftime("%H:%M") if hasattr(start_time, "strftime") else str(start_time)
    end = end_time.strftime("%H:%M") if hasattr(end_time, "strftime") else str(end_time)
    return json.dumps(
        [{"weekday": weekday, "time_slot": f"{start}-{end}"}],
        ensure_ascii=False,
    )
