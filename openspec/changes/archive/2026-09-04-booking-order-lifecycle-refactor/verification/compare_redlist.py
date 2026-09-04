#!/usr/bin/env python3
"""比对候选红名单与基线红名单，判定「集合恒等」。

内置唯一已知的挂钟敏感项规则：
tests/test_booking_verification_service.py::test_issue_verification_token_for_future_booking_returns_token
仅当采集时刻的本地时间 > 11:00 (Asia/Shanghai) 时通过。
见同目录 BASELINE.md。

用法: python3 compare_redlist.py <基线前缀> <候选前缀>
退出码: 0 = 恒等（含挂钟等价）; 1 = 不恒等或挂钟规则被违反
"""
from __future__ import annotations

import sys
from datetime import datetime

TIME_SENSITIVE = (
    "tests/test_booking_verification_service.py::"
    "test_issue_verification_token_for_future_booking_returns_token"
)
BOUNDARY_HOUR, BOUNDARY_MINUTE = 11, 0


def load_ids(prefix: str) -> set[str]:
    with open(f"{prefix}.txt", encoding="utf-8") as fh:
        return {line.strip() for line in fh if line.strip()}


def load_ts(prefix: str) -> datetime:
    with open(f"{prefix}.ts", encoding="utf-8") as fh:
        return datetime.fromisoformat(fh.read().strip())


def is_before_boundary(ts: datetime) -> bool:
    return (ts.hour, ts.minute) <= (BOUNDARY_HOUR, BOUNDARY_MINUTE)


def normalize(ids: set[str], ts: datetime, label: str) -> tuple[set[str], bool]:
    """扣除挂钟敏感项。返回 (归一化集合, 是否符合挂钟规则)。"""
    should_be_red = is_before_boundary(ts)
    actually_red = TIME_SENSITIVE in ids
    if should_be_red != actually_red:
        bucket = "11:00 前" if should_be_red else "11:00 后"
        print(
            f"  !! {label} 挂钟规则被违反: 采集于 {bucket}，"
            f"预期该项{'红' if should_be_red else '绿'}，实际{'红' if actually_red else '绿'}"
        )
        return ids, False
    return ids - {TIME_SENSITIVE}, True


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    base_prefix, cand_prefix = sys.argv[1], sys.argv[2]
    base_ids, cand_ids = load_ids(base_prefix), load_ids(cand_prefix)
    base_ts, cand_ts = load_ts(base_prefix), load_ts(cand_prefix)

    print(f"基线: {len(base_ids)} 项 @ {base_ts.isoformat()}")
    print(f"候选: {len(cand_ids)} 项 @ {cand_ts.isoformat()}")

    base_norm, base_ok = normalize(base_ids, base_ts, "基线")
    cand_norm, cand_ok = normalize(cand_ids, cand_ts, "候选")

    if not (base_ok and cand_ok):
        print("FAIL 挂钟敏感项行为与已知规则不符，需人工复核核销域改动")
        return 1

    missing = base_norm - cand_norm   # 基线红、候选绿 → 被意外修好
    added = cand_norm - base_norm     # 候选红、基线绿 → 新增回归

    if not missing and not added:
        print(f"PASS 红名单集合恒等（归一化后 {len(base_norm)} 项）")
        return 0

    print("FAIL 红名单集合不恒等")
    for item in sorted(missing):
        print(f"  [被意外修好] {item}")
    for item in sorted(added):
        print(f"  [新增回归]   {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
