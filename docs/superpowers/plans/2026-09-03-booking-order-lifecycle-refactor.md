---
change: booking-order-lifecycle-refactor
design-doc: docs/superpowers/specs/2026-09-03-booking-order-lifecycle-refactor-design.md
base-ref: 6582eb0268f658b75bcd2030e959d709a21e712d
---

# 订单生命周期重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把分散在 br-server 7 处判定点、br-app 4 份派生实现中的订单状态逻辑收敛为单一领域词表 + 纯函数，并把状态取值从旧词表（`pending`/`confirmed`）切换到语义自明的新词表（`pending_start`/`in_progress`），全程保持用户可见行为零变更。

**Architecture:** 分 6 个 Phase 递进，每个 Phase 结束时全量测试的**红名单集合恒等**。关键设计是把「结构重构」与「取值变更」分离：Phase 2 先建领域层并让服务层改调纯函数，此时**枚举成员的值仍是旧字面量**（`PENDING_START = "pending"`），因此行为完全不变；Phase 4 才翻转枚举值并同步三端，此时所有改动点都已收敛到单一事实源，翻转是一次性的。时区统一（Phase 3）夹在中间，因为领域纯函数要求 `now`/`today` 参数为 naive 本地时间，而现状存在 aware 孤岛。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2 async / Alembic / pytest 9（asyncio_mode=auto，SQLite in-memory）；br-admin Vue 3 + Naive UI + Vite + pnpm；br-app uni-app（Vue 3 选项式 API）+ npm。

## Global Constraints

以下约束适用于**每一个** Task，各 Task 的 Requirements 隐式包含本节。

**环境与命令**

- 工作区：`/Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor`，分支 `feature/20260902/booking-order-lifecycle-refactor`，起点 commit `6582eb0`。所有相对路径以该 worktree 根为基准。
- Python 解释器**必须**用 `/opt/miniconda3/envs/booking-room/bin/python`（conda env `booking-room`，Python 3.12.11，pytest 9.0.3）。系统 `python3` 无 pytest。
- 全量测试命令（在 `br-server/` 下执行）：
  `/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/ -q --tb=no -p no:cacheprovider`
  耗时约 126s，退出码非 0 属**预期**（存在既有红灯）。
- `comet` / `openspec` CLI 不在非登录 shell 的 PATH 中，需用 `zsh -lic '<命令>'` 调用。
- br-admin 构建：`cd br-admin && pnpm run build`；br-app 构建：`cd br-app && npm run build:h5`。两端 `node_modules` 均已存在。

**架构与代码形态**

- 枚举一律沿用既有 `(str, Enum)` 形态（与 `models/booking.py`、`domain/booking_rules.py` 一致）。**不得**引入 `StrEnum`，那会造成第三种形态。
- `app/domain/` 下任何模块**不得** import `app.models` / `app.schemas` / `app.services`。现状 `domain/booking_rules.py` 只依赖标准库，新增文件必须同样满足。
- 所有领域纯函数的 `now` / `today` / `current_time` 参数一律为 **naive 的 `settings.BOOKING_TIMEZONE`（Asia/Shanghai）本地时间**。时区转换只在服务层入口做一次，领域层不做 `tzinfo` 处理。
- 领域函数必须是**无副作用纯函数**，不接收 `AsyncSession`，可脱离数据库单测。

**行为零变更红线（Q5）**

- `None` 兜底**必须**原样保留为 `IN_PROGRESS`（4 处：`booking_payment_service.py:289,299`、`course_booking_service.py:436`、`booking_service.py:1243-1244` 的 `booking.date or today`）。**不得**"顺手改成更安全的 `PENDING_START`"——那是行为变更。
- 边界运算符**必须**逐一保持：课程 `first_lesson_date <= today` → `IN_PROGRESS`；课程完成 `today > last_lesson_date`（**严格大于**，`today == last_lesson_date` 时不完成）；座位 `now >= booking_start` → `IN_PROGRESS`；座位 `now >= booking_end` → `COMPLETED`；核销 `now <= end_at` → `IN_PROGRESS`。
- `order_status_scheduler.py` 的 `stats` 六个键名（`total_scanned` / `seat_started` / `seat_completed` / `course_started` / `course_highlight_updated` / `course_completed`）**保持不变**，否则 `main.py` 日志与既有断言连带破裂。
- `main.py:113-122` 的日志格式串「课程: 开始 %d / 高亮更新 %d / 完成 %d」**不动**。
- `BOOKING_CLEANUP_INTERVAL_SECONDS` **保留原名**（已部署环境的环境变量兼容性），只在文档注明它实际控制支付对账频率。
- `ACCESS_TOKEN_EXPIRE_MINUTES: int = 15` **保持不变**（C 端 br-app 与 `jwt_service` 零影响）。管理端有效期走新增的 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS`。
- 管理端 `admin_list_bookings`（`booking_service.py:843-858`）保持**纯列匹配**，不引入 C 端的派生口径。跨端同名参数语义不一致（F11）是**已知遗留缺陷**，本次只记录不修复。
- `time_slots` 的**展示文案层三端各自保留现状**：br-admin `builders.ts:formatTimeSlots`（顿号分隔完整时段）、br-app `formatters.js:formatCourseSchedule`（口语化、只取 start、含 5 天同时段合并特例）。只统一**数据契约层**。

**跨域同名陷阱（6 类，一律不得被重命名波及）**

| # | 陷阱 | 位置 | 语义 |
|---|---|---|---|
| 1 | `payment_status = 'pending'` | `booking_service.py:305,644,744`、`booking_payment_service.py:160,188`、`course_booking_service.py:517,632,647`、`schemas/booking.py:16`、前端按钮判定 | 待支付 |
| 2 | `lesson_schedules.schedule_status = 'in_progress'` | `booking_service.py:531` | 课时进行中（排课域） |
| 3 | `course_schedules.schedule_status = 'in_progress'` | `booking_service.py:1303`、`schedule_status_scheduler.py` | 排课进行中（排课域） |
| 4 | `WALLET_STATUS_TAGS.pending` | `br-admin/src/views/business/shared/options.ts:86` | 钱包交易待处理 |
| 5 | `status === 'pending'` | `br-app/src/utils/accountSecurity.js:7` | 管理员审核中 |
| 6 | `status` / `pending` | `br-app/src/pages/wallet/transactions.vue:279,290,333` | 钱包交易域 |

后端**非订单域字面量不改清单**（15 处，实测）：`wallet_service.py:105,241,246,267,333,409`、`user_security_service.py:236,248,252`、`models/wallet.py:52,87`、`api/routes/admin_wallet.py:30,165`、`domain/wallet_rules.py:18`、`schemas/booking.py:16`。

**订单域字面量判定规则**：仅当字面量出现在 `Booking.status` 的读/写/比较，或作为订单状态的返回值/初始值时才改。出现在 `payment_status`、`WalletTransaction.status`、`schedule_status`、`User.status` 或钱包/审核/优惠券状态映射时**一律不改**。

> **对 Design Doc 的精度修正**：tasks.md 5.2 与 Design Doc §9.1 写「替换 74 处字面量」。74 是 `grep` 原始命中数，其中含上述 15 处非订单域命中、`booking_payment_service.py:279-283` 的 4 处 docstring 文本，以及 Phase 1 已删除的 `booking_cleanup_service.py` 2 处。**实际需改的订单域代码字面量约 55 处**，以本节判定规则 + Phase 4 的 grep 守卫为准，不以「74」这个数字为准。

**测试与验收**

- **不治理**既有红灯（Q1 用户决策）。既有红灯根因是 `Course` 模型历史重构与优惠券服务签名重构后测试侧未同步，与本 change 无关。
- **覆盖率不设门槛**（Q2 用户显式撤回 >80% 指标）。73% 仅作参考数据。
- 每个 Phase 结束的验收判据是**红名单集合恒等**，而非「失败数不增」。只看数量会漏掉「修好一个又弄坏一个」的抵消。
- 新增测试**不得**引入新依赖（`dev` extras 里没有 freezegun/faketime，不要添加）。

**挂钟敏感性（build 阶段实测新发现，Design Doc §11.1 未记录）**

- `tests/test_booking_verification_service.py::test_issue_verification_token_for_future_booking_returns_token` 是**挂钟敏感**测试：仅当本地时间 **> 11:00**（Asia/Shanghai）时通过。
- 机制：fixture `verification_data` 的 `pending_paid` 固定为「今天 09:00-11:00 / `status="pending"` / `payment_status="paid"`」，按 F22 属可核销；测试把 `confirmed` 改到明天后，`_select_nearest_booking`（`booking_verification_service.py:383-413`）的三档排序在 `now <= 11:00` 时选中 `pending_paid`（档 0/1），在 `now > 11:00` 时 `pending_paid` 落档 2、`confirmed` 落档 1 而胜出。
- 探针实测边界：`now=11:00` → FAIL，`now=11:01` → PASS（`VERIFICATION_EARLY_ARRIVAL_MINUTES = 30`）。
- 后果：红名单基线在 11:00 前是 **96 项**、11:00 后是 **95 项**。Design Doc §11.1 记录的「95 项」采集于 2026-09-02 的 11:00 之后。
- 该项落在核销域（Q12 本次重构范围内），**不得**当作「与订单生命周期无关」忽略。Phase 0 的比对脚本已内置该规则。
- 详见 `openspec/changes/booking-order-lifecycle-refactor/verification/BASELINE.md`。

## 文件结构

**br-server 新建（5 个）**

| 文件 | 职责 |
|---|---|
| `app/utils/__init__.py` | 新建 utils 包（`app/utils/` 当前不存在，F4） |
| `app/utils/timezone.py` | 时区单一事实源：`CHINA_TIMEZONE` 常量、`booking_now()`、`ensure_booking_timezone()` |
| `app/utils/time_slots.py` | `time_slots` **数据契约层**：解析 3 种历史格式、按日期构造、从时段重建 |
| `app/domain/booking_status.py` | 订单状态词表（`BookingStatus`/`PaymentStatus`/`PaymentMethod`）+ 8 个领域纯函数 + `build_status_filter_conditions` |
| `alembic/versions/2026_09_03_*-<rev>_rename_booking_status_values.py` | 数据迁移：`bookings.status` 旧值 → 新值，含成对 `downgrade()` |

**br-server 新建测试（3 个）**

| 文件 | 覆盖 |
|---|---|
| `tests/test_booking_status.py` | 8 个领域纯函数全部分支 + `None` 兜底 + 边界运算符 + 筛选条件派生口径 |
| `tests/test_time_slots.py` | 3 种历史格式、解析失败静默容错、重建分支 |
| `tests/test_timezone.py` | `booking_now()` 返 naive 且为 Asia/Shanghai 本地时间、显式传参生效、`ensure_booking_timezone()` 归一化 |

**br-server 删除（4 个 + 1 空目录）**

`app/services/booking_cleanup_service.py`、`tests/test_booking_cleanup.py`、`app/application/booking_use_cases.py`、`tests/test_booking_use_cases.py`、`app/application/`（含 `__init__.py`）。

**br-server 修改（14 个）**

`app/models/booking.py`（枚举改 re-export + `:32` default）、`app/schemas/booking.py`（枚举改别名 re-export）、`app/domain/booking_rules.py`（`:40,51` 改枚举引用）、`app/domain/verification_rules.py`（新增 2 个核销领域函数）、`app/services/booking_service.py`、`app/services/booking_payment_service.py`、`app/services/course_booking_service.py`、`app/services/order_status_scheduler.py`、`app/services/booking_verification_service.py`、`app/services/booking_cancellation_policy.py`（`booking_now` 改 re-export）、`app/main.py`（重命名 job 与 scheduler state）、`app/api/routes/booking.py`（`_BOOKING_STATUS` Literal）、`app/core/config.py`（新增 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS`）、`app/services/admin_auth_service.py` + `app/api/routes/admin_auth.py`（管理端令牌有效期）。

另：`app/services/study_record_service.py:54,168`、`app/services/user_security_service.py:224`、`app/services/study_room_service.py:204`、`app/services/seat_service.py:262`、`app/services/coupon_service.py:172` 只在 Phase 4 做字面量 → 枚举引用替换（订单域命中）；`wallet_service.py:119`、`course_booking_service.py:26`、`coupon_service.py:42`、`admin_coupon_service.py:13`、`activity_service.py:25`、`seed_data.py:26` 的 `CHINA_TIMEZONE` 只在 Phase 3 改导入源、不改返回语义。

**br-admin 修改（3 个）**：`src/views/business/shared/options.ts`（4 处）、`src/views/booking/list/index.vue`（2 处）、`src/store/modules/user.ts`（2 处）。

**br-app 修改（5 个）**：`src/constants/booking.js`、`src/pages/orders/index.vue`、`src/pages/verify-booking/index.vue`、`src/utils/formatters.js`（仅随键集变化，不改逻辑）、`src/pages/course-booking/*.vue` 与 `src/pages/booking/seat-select.vue`（字面量替换）。

**文档修改（5 个）**：`docs/booking-rules.md`、`docs/api.md`、`bug-fixed.md`、`br-server/.env.example`、`openspec/changes/booking-order-lifecycle-refactor/`（tasks.md 勾选 + design.md/Design Doc 的基线精度修正）。

**验证工件（Phase 0 新建）**：`openspec/changes/booking-order-lifecycle-refactor/verification/` 下的 `redlist.sh`、`compare_redlist.py`、`redlist-baseline.txt`、`redlist-baseline.ts`。该目录随 change 一起归档，保留验收证据。

---

## Phase 0：建立可复现的红名单验收基线

本 Phase 是**所有后续 Phase 的验收前提**。红名单集合恒等是本 change 唯一的验收判据，而基线本身依赖挂钟时间（见 Global Constraints），因此必须先把采集与比对固化成脚本。

### Task 0.1: 红名单采集与比对脚本

**Files:**
- Create: `openspec/changes/booking-order-lifecycle-refactor/verification/redlist.sh`
- Create: `openspec/changes/booking-order-lifecycle-refactor/verification/compare_redlist.py`
- Create: `openspec/changes/booking-order-lifecycle-refactor/verification/redlist-baseline.txt`（脚本生成）
- Create: `openspec/changes/booking-order-lifecycle-refactor/verification/redlist-baseline.ts`（脚本生成）

**Interfaces:**
- Consumes: 无（起点任务）
- Produces:
  - `bash <verification>/redlist.sh <输出前缀>` → 生成 `<输出前缀>.txt`（每行一个测试 ID，已排序去重）与 `<输出前缀>.ts`（ISO 格式的 Asia/Shanghai 采集时刻）；stdout 打印 pytest 汇总行、采集时刻、条目数。退出码 0 表示采集成功（**与测试是否全绿无关**）。
  - `python3 <verification>/compare_redlist.py <基线前缀> <候选前缀>` → 退出码 0 = 集合恒等（含挂钟等价），1 = 不恒等；stdout 打印 `PASS`/`FAIL` 与逐项差集。

- [x] **Step 1: 写采集脚本**

创建 `openspec/changes/booking-order-lifecycle-refactor/verification/redlist.sh`：

```bash
#!/usr/bin/env bash
# 采集 br-server 全量测试的红名单（FAILED + ERROR 测试 ID 集合）。
# 用法: bash redlist.sh <输出前缀>   例: bash redlist.sh redlist-baseline
# 退出码 0 表示采集成功；pytest 本身退出码非 0 属预期（存在既有红灯）。
set -uo pipefail

PREFIX="${1:?用法: redlist.sh <输出前缀>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../../.." && pwd)"
# 输出前缀解析为绝对路径（相对调用时 CWD），避免随后 cd 到 br-server 后写错位置
case "$PREFIX" in
  /*) OUT="$PREFIX" ;;
  *)  OUT="$(pwd)/$PREFIX" ;;
esac
PY=/opt/miniconda3/envs/booking-room/bin/python
LOG="$(mktemp -t redlog.XXXXXX)"

cd "$REPO_ROOT/br-server" || exit 2
"$PY" -m pytest tests/ -q --tb=no -p no:cacheprovider > "$LOG" 2>&1

grep -E '^(FAILED|ERROR) ' "$LOG" \
  | sed -E 's/^(FAILED|ERROR) //; s/ - .*$//' \
  | sort -u > "$OUT.txt"

# 采集时刻（Asia/Shanghai），供比对脚本判定挂钟桶
TZ=Asia/Shanghai date '+%Y-%m-%dT%H:%M:%S%z' > "$OUT.ts"

echo "--- pytest 汇总 ---"
tail -1 "$LOG"
echo "--- 采集时刻 ---"
cat "$OUT.ts"
echo "--- 红名单条目数 ---"
wc -l < "$OUT.txt"
rm -f "$LOG"
```

- [x] **Step 2: 写比对脚本**

创建 `openspec/changes/booking-order-lifecycle-refactor/verification/compare_redlist.py`：

```python
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
```

- [x] **Step 3: 采集基线并验证脚本可用**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/openspec/changes/booking-order-lifecycle-refactor/verification
bash redlist.sh redlist-baseline
```
Expected: 汇总行为 `15 failed, 750 passed, 16 skipped, ... errors`（11:00 前）或 `14 failed, 751 passed, ...`（11:00 后）；`redlist-baseline.txt` 相应为 **96** 或 **95** 行；`redlist-baseline.ts` 为当前 Asia/Shanghai 时刻。

- [x] **Step 4: 自比对，验证比对脚本判 PASS**

Run:
```bash
python3 compare_redlist.py redlist-baseline redlist-baseline
echo "EXIT=$?"
```
Expected: `PASS 红名单集合恒等（归一化后 95 项）`，`EXIT=0`。归一化后恒为 95 项——这正是 Design Doc §11.1 记录的基线规模。

- [x] **Step 5: 负向验证比对脚本能抓到回归**

Run:
```bash
cp redlist-baseline.txt /tmp/neg.txt && cp redlist-baseline.ts /tmp/neg.ts
echo "tests/test_fake.py::test_injected_regression" >> /tmp/neg.txt
sort -u /tmp/neg.txt -o /tmp/neg.txt
python3 compare_redlist.py redlist-baseline /tmp/neg; echo "EXIT=$?"
```
Expected: `FAIL 红名单集合不恒等` + `[新增回归]   tests/test_fake.py::test_injected_regression`，`EXIT=1`。确认后删除临时文件：`rm -f /tmp/neg.txt /tmp/neg.ts`。

> 这一步是必要的：未经验证的比对脚本会让后续 5 个 Phase 的验收全部失效。

- [x] **Step 6: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add openspec/changes/booking-order-lifecycle-refactor/verification/
git commit -m "test: 建立订单生命周期重构的红名单验收基线与比对脚本

基线 95 项（归一化后）。比对脚本内置唯一挂钟敏感项规则：
test_issue_verification_token_for_future_booking_returns_token
仅当本地时间 > 11:00 通过，故红名单原始条数在 95/96 间浮动。"
```

---

## Phase 1：死代码清理与误导命名重命名

对应 Design Doc §6、tasks.md §4 的 4.1/4.2/4.3/4.4/4.6/4.11 与 §3 的 3.5。**Phase 结束验收：红名单集合恒等。**

### Task 1.1: 删除 booking_cleanup_service（明确不引入 15 分钟自动取消）

**Files:**
- Delete: `br-server/app/services/booking_cleanup_service.py`
- Delete: `br-server/tests/test_booking_cleanup.py`

**Interfaces:**
- Consumes: Task 0.1 的 `redlist.sh` / `compare_redlist.py`
- Produces: 无对外接口。删除后仓库内**不存在**任何「未支付订单超时自动取消」实现——这是**行为决策**，不是纯清理。

**为什么可以删（实测依据）**：`cleanup_unpaid_bookings` 生产代码零引用，唯一引用是 `tests/test_booking_cleanup.py:14` 的 `from app.services.booking_cleanup_service import cleanup_unpaid_bookings`。该服务实现「15 分钟未支付自动取消 + 恢复优惠券」，删除意味着**明确不引入**该行为；未支付订单的收敛由既有 `BookingPaymentService.reconcile_pending_payments()`（微信支付对账）承担。用户已在 Q4 确认「无消费方的一律删除」。

- [x] **Step 1: 复核零生产引用**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn "booking_cleanup_service\|cleanup_unpaid_bookings\|BookingCleanupService" app/ --include='*.py'
grep -rn "booking_cleanup_service\|cleanup_unpaid_bookings" tests/ --include='*.py'
```
Expected: 第一条**无输出**（`app/` 内零引用）；第二条只输出 `tests/test_booking_cleanup.py:14` 一处。若有其它输出，**停止**并重新评估。

- [x] **Step 2: 删除两个文件**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
git rm app/services/booking_cleanup_service.py tests/test_booking_cleanup.py
```
Expected: `rm 'app/services/booking_cleanup_service.py'` 与 `rm 'tests/test_booking_cleanup.py'` 两行。

- [x] **Step 3: 验证无悬空引用且测试可收集**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn "booking_cleanup_service\|cleanup_unpaid_bookings" app/ tests/ --include='*.py'
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/ -q --collect-only -p no:cacheprovider 2>&1 | tail -3
```
Expected: grep 无输出；collect-only 末尾无 `error`， collected 数比删除前少 4（`test_booking_cleanup.py` 有 4 个测试）。

- [x] **Step 4: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git commit -m "refactor: 删除零引用的 booking_cleanup_service，明确不引入未支付订单超时自动取消

生产代码零引用，仅 tests/test_booking_cleanup.py 消费。未支付订单收敛
由既有 reconcile_pending_payments（微信支付对账）承担。"
```

### Task 1.2: 删除 app/application 透传层

**Files:**
- Delete: `br-server/app/application/booking_use_cases.py`
- Delete: `br-server/app/application/__init__.py`
- Delete: `br-server/tests/test_booking_use_cases.py`

**Interfaces:**
- Consumes: Task 0.1 的脚本
- Produces: 无。`app/application/` 目录整体消失，仓库分层为 `api/ → services/ → domain/ + models/ + schemas/`。

**为什么可以删（实测依据）**：`BookingUseCases` 是 7 行、4 个 `staticmethod` 透传别名（`create_booking` / `list_bookings` / `get_booking` / `cancel_booking` → `app.services.booking_service` 同名函数）。生产零引用；唯一引用 `tests/test_booking_use_cases.py:1,4` 且只断言 `callable()`，不验证任何行为。

- [x] **Step 1: 复核零生产引用**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn "booking_use_cases\|BookingUseCases\|app\.application\|from app import application" app/ tests/ --include='*.py'
```
Expected: 只输出 `app/application/booking_use_cases.py` 自身定义行与 `tests/test_booking_use_cases.py:1,4`。`app/` 内除定义文件外**无其它命中**。

- [x] **Step 2: 删除文件与目录**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
git rm app/application/booking_use_cases.py app/application/__init__.py tests/test_booking_use_cases.py
rm -rf app/application/__pycache__ && rmdir app/application 2>/dev/null; ls -d app/application 2>&1
```
Expected: 三条 `rm '...'`；最后 `ls` 输出 `ls: app/application: No such file or directory`。

- [x] **Step 3: 验证应用仍可导入**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -c "from app.main import app; print('app import OK', len(app.routes))"
```
Expected: `app import OK <路由数>`，无 `ModuleNotFoundError`。

- [x] **Step 4: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git commit -m "refactor: 删除 app/application 透传层（4 个 staticmethod 别名，生产零引用）"
```

### Task 1.3: 重命名误导的定时任务标识符

**Files:**
- Modify: `br-server/app/main.py:69`（函数定义）、`:100`（fallback loop 内调用）、`:195`（`add_job` 注册）、`:217`（`app.state` 赋值）

**Interfaces:**
- Consumes: 无
- Produces:
  - `async def _payment_reconciliation_job() -> None`（原 `_cleanup_unpaid_bookings_job`，签名与实现不变）
  - `app.state.scheduler`（原 `app.state.booking_cleanup_scheduler`，仍承载全部 3 个 job）
  - `app.state.booking_cleanup_fallback_task` **保留原名不动**（`:232` 赋值、`:256` 读取，属 fallback 分支且不在 tasks.md 范围）

**为什么改名（实测依据 F10）**：`main.py:69` 的 `_cleanup_unpaid_bookings_job` 实际调用的是 `BookingPaymentService.reconcile_pending_payments()`，日志写「[微信支付对账定时任务]」，与函数名完全不符。`app.state.booking_cleanup_scheduler` 承载的是全部 3 个 job（支付对账 + 订单状态推进 + 排课状态推进），非仅 cleanup。

- [x] **Step 1: 确认改动点只有 4 处**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn "_cleanup_unpaid_bookings_job\|booking_cleanup_scheduler" app/ tests/ --include='*.py'
```
Expected: 恰好 4 行，全在 `app/main.py`：`:69`、`:100`、`:195`、`:217`。`tests/` 内**无命中**（改名不会破坏测试）。

- [x] **Step 2: 改函数名（3 处）**

在 `br-server/app/main.py` 中：

`:69` 定义处：
```python
async def _payment_reconciliation_job() -> None:
```

`:100` `_booking_payment_reconciliation_loop` 内调用处：
```python
            await _payment_reconciliation_job()
```

`:195` `lifespan` 内 `scheduler.add_job` 第一参数：
```python
        scheduler.add_job(
            _payment_reconciliation_job,
            "interval",
            seconds=settings.BOOKING_CLEANUP_INTERVAL_SECONDS,
        )
```

> `seconds=settings.BOOKING_CLEANUP_INTERVAL_SECONDS` **保持不变**——环境变量名保留（Global Constraints）。

- [x] **Step 3: 改 app.state 名（1 处）**

`:217`：
```python
        app.state.scheduler = scheduler
```

> `:254-255` 的 shutdown 用的是局部变量 `scheduler`（`if scheduler is not None: scheduler.shutdown(wait=False)`），**不读 `app.state`**，因此无需同步改动。已实测确认。

- [x] **Step 4: 验证无残留 + 应用可导入**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn "_cleanup_unpaid_bookings_job\|booking_cleanup_scheduler" app/ tests/ --include='*.py'; echo "残留检查退出码=$?"
grep -n "_payment_reconciliation_job\|app.state.scheduler" app/main.py
/opt/miniconda3/envs/booking-room/bin/python -c "
from app.main import app, _payment_reconciliation_job
print('rename OK', callable(_payment_reconciliation_job))"
```
Expected: 第一条 grep **无输出**（退出码 1）；第二条输出 4 行（`:69`、`:100`、`:195`、`:217`）；python 输出 `rename OK True`。

- [x] **Step 5: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git commit -m "refactor: 重命名误导的定时任务标识符

_cleanup_unpaid_bookings_job -> _payment_reconciliation_job（实际做微信支付对账）
app.state.booking_cleanup_scheduler -> app.state.scheduler（承载全部 3 个 job）
BOOKING_CLEANUP_INTERVAL_SECONDS 环境变量名保留不变。"
```

### Task 1.4: `import json` 提到模块顶部

**Files:**
- Modify: `br-server/app/services/course_booking_service.py`（顶部 import 区 + `:481` 函数内 import）

**Interfaces:**
- Consumes: 无
- Produces: `course_booking_service` 模块顶部有 `import json`；`_create_booking_record` 内不再有函数级 import。

- [x] **Step 1: 确认函数内 import 只有 1 处**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -n "^import json\|^ *import json" app/services/course_booking_service.py
sed -n '1,20p' app/services/course_booking_service.py
```
Expected: 只有 `:481` 一处缩进形式的 `import json`；顶部 import 区无 `import json`。

- [x] **Step 2: 顶部加 import，删除函数内 import**

在 `br-server/app/services/course_booking_service.py` 顶部 import 区（`:1` 起，与其它标准库 import 同组，按字母序放在最前）加入：
```python
import json
```

删除 `:481` 的函数内 `import json` 一行，使 `:478-486` 变为：
```python
            if data.time_slot:
                # 与课程排课 time_slots 格式一致：[{"weekday": N, "time_slot": "HH:MM-HH:MM"}]
                # weekday 从用户选择的开课日期推算（isoweekday: 1=周一, 7=周日）
                weekday = booking_date.isoweekday()
                booking_time_slots = json.dumps(
                    [{"weekday": weekday, "time_slot": data.time_slot}],
                    ensure_ascii=False,
                )
```

> 本 Task 只提 import，**不改** `json.dumps` 的构造逻辑。Phase 2 的 Task 2.5 会把整块替换为 `build_time_slots_from_date()`。

- [x] **Step 3: 验证**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -c "^ *import json" app/services/course_booking_service.py
/opt/miniconda3/envs/booking-room/bin/python -c "
from app.services import course_booking_service as m
print('json at module level:', hasattr(m, 'json'))"
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_course_booking_service.py -q --tb=short -p no:cacheprovider 2>&1 | tail -3
```
Expected: `grep -c` 输出 `0`（无缩进形式的 import）；python 输出 `json at module level: True`；pytest 汇总行的 passed 数与本 Task 前一致（无新增失败）。

- [x] **Step 4: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git commit -m "refactor: course_booking_service 的 import json 提到模块顶部"
```

### Task 1.5: 删除 br-app 订单页 3 个零消费方常量

**Files:**
- Modify: `br-app/src/pages/orders/index.vue:267-285`（删除 `TABS` / `STATUS_MAP` / `ZONE_MAP` 三个 `const`）

**Interfaces:**
- Consumes: 无
- Produces: `orders/index.vue` 的 `<script>` 顶部只保留 `PAGE_SIZE` 与 `SCHEDULE_TRUNCATE_THRESHOLD` 两个模块级常量；tab 数据来自导入的 `BOOKING_TABS`，座位区文案来自导入的 `SEAT_ZONE_LABELS`。

**为什么可以删（实测依据 F24）**：三个常量各自只有定义处 1 次 grep 命中，零消费方。页面 `:293` 实际用 `tabs: BOOKING_TABS`（导入自 `@/constants/booking`），`:494` 用 `SEAT_ZONE_LABELS[seat.zone]`。附带消灭 `STATUS_MAP.pending = '待确认'` 与 `BOOKING_STATUS_LABELS.pending = '待支付'` 的**互相矛盾文案**。

- [x] **Step 1: 逐个实测零消费方**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-app
for name in TABS STATUS_MAP ZONE_MAP; do
  echo "--- $name ---"
  grep -rn "\b$name\b" src/ --include='*.vue' --include='*.js' | grep -v node_modules
done
```
Expected: `TABS` 只有 `src/pages/orders/index.vue:267`（定义处）1 行——注意 `BOOKING_TABS` 因 `\b` 词边界不会误命中；`STATUS_MAP` 只有 `:274`；`ZONE_MAP` 只有 `:281`。若任一常量出现第 2 处命中，**停止**并重新评估。

- [x] **Step 2: 删除三个常量**

在 `br-app/src/pages/orders/index.vue` 中删除 `:267-285` 整块，使 `:265` 的 import 之后直接接 `PAGE_SIZE`：

```javascript
import { formatBookingStatus, formatCourseEndDate, formatCourseSchedule, formatCourseStartDate, formatHourCount, formatMoney } from '@/utils/formatters'

const PAGE_SIZE = 20
const SCHEDULE_TRUNCATE_THRESHOLD = 12
```

> `import { BOOKING_TABS, SEAT_ZONE_LABELS } from '@/constants/booking'`（`:264`）**保留**，它们才是真实消费的对象。

- [x] **Step 3: 验证已删且构建通过**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-app
grep -n "const TABS\|STATUS_MAP\|ZONE_MAP" src/pages/orders/index.vue; echo "残留退出码=$?"
grep -n "BOOKING_TABS\|SEAT_ZONE_LABELS" src/pages/orders/index.vue
npm run build:h5 2>&1 | tail -8
```
Expected: 第一条 grep **无输出**（退出码 1）；第二条输出 `:264` import、`tabs: BOOKING_TABS`、`SEAT_ZONE_LABELS[seat.zone]` 等命中；构建**成功**（末尾无 `ERROR`/`Build failed`，输出产物体积汇总）。

- [x] **Step 4: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-app/src/pages/orders/index.vue
git commit -m "refactor: 删除 br-app 订单页 3 个零消费方常量 TABS/STATUS_MAP/ZONE_MAP

附带消灭 STATUS_MAP.pending='待确认' 与 BOOKING_STATUS_LABELS.pending='待支付'
的互相矛盾文案。页面实际消费导入的 BOOKING_TABS 与 SEAT_ZONE_LABELS。"
```

### Task 1.6: Phase 1 验收（红名单集合恒等）

**Files:**
- Create: `openspec/changes/booking-order-lifecycle-refactor/verification/redlist-phase1.txt` / `.ts`（脚本生成，不提交）

**Interfaces:**
- Consumes: Task 0.1 的 `redlist.sh` / `compare_redlist.py`、`redlist-baseline.*`
- Produces: Phase 1 的验收结论（记录在提交信息与后续验证报告中）

- [x] **Step 1: 采集 Phase 1 红名单**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/openspec/changes/booking-order-lifecycle-refactor/verification
bash redlist.sh redlist-phase1
```
Expected: 汇总行 passed 数 = 基线 passed 数 **减 5**（Task 1.1 删 4 个测试 + Task 1.2 删 1 个测试）；红名单条目数 = 基线条目数 **减 0**（被删的 5 个测试原本都是绿的，不在红名单里）。

- [x] **Step 2: 比对**

Run:
```bash
python3 compare_redlist.py redlist-baseline redlist-phase1; echo "EXIT=$?"
```
Expected: `PASS 红名单集合恒等（归一化后 95 项）`，`EXIT=0`。

若 `FAIL`：逐项读差集。`[新增回归]` 说明 Phase 1 引入了破坏（最可能是 Task 1.3 改名漏了引用），回到对应 Task 修复后重跑本 Task。`[被意外修好]` 同样要查——删除死代码不该修好任何既有红灯。

- [x] **Step 3: grep 守卫（已删标识符无残留）**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
grep -rn "booking_cleanup_service\|cleanup_unpaid_bookings\|BookingUseCases\|booking_use_cases\|_cleanup_unpaid_bookings_job\|booking_cleanup_scheduler" br-server/app br-server/tests --include='*.py'
grep -n "const TABS\|STATUS_MAP\|ZONE_MAP" br-app/src/pages/orders/index.vue
echo "全部守卫退出码应为 1（无命中）"
```
Expected: 两条 grep 均**无输出**。

- [x] **Step 4: 清理临时红名单文件（不提交）**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/openspec/changes/booking-order-lifecycle-refactor/verification
rm -f redlist-phase1.txt redlist-phase1.ts && git status --short .
```
Expected: `git status` 对该目录无输出（基线文件已在 Task 0.1 提交，Phase 红名单是临时工件）。

> Phase 1 的 5 个 Task 各自已提交，本 Task 只做验收，**不产生新提交**。若验收 FAIL 需修复，修复提交归入对应 Task。

---

## Phase 2：领域层与 utils（枚举值仍为旧字面量）

对应 Design Doc §13 Step 2、§2、§3.1、§4.1（#1-5、#7）、tasks.md §2/§3.1/§3.4/§6.1/§6.2/§6.3。**本 Phase 是纯结构重构：枚举成员名是新的（`PENDING_START`/`IN_PROGRESS`），但成员的值仍是旧字面量（`PENDING_START = "pending"`、`IN_PROGRESS = "confirmed"`），因此落库值与 API 响应逐字节不变。Phase 结束验收：红名单集合恒等。**

> **关键不变量（贯穿 Phase 2-3）**：所有新增测试断言**枚举成员**（`BookingStatus.IN_PROGRESS`）而非字符串字面量，因此同一份测试在 Phase 4 翻转枚举值后**无需修改**仍通过。`(str, Enum)` 成员与裸字符串比较对称相等（`BookingStatus.IN_PROGRESS == "confirmed"` 为真），且作为 `String(20)` 列值绑定时写入其 `.value`——这与仓库既有 `PaymentStatus(str, Enum)` 的用法完全一致，绑定行为已被现网验证。

### Task 2.1: 新建 utils 包 + timezone.py + time_slots.py

**Files:**
- Create: `br-server/app/utils/__init__.py`
- Create: `br-server/app/utils/timezone.py`
- Create: `br-server/app/utils/time_slots.py`
- Test: `br-server/tests/test_timezone.py`
- Test: `br-server/tests/test_time_slots.py`

**Interfaces:**
- Consumes: 无（Phase 2 起点）
- Produces:
  - `app.utils.timezone.CHINA_TIMEZONE: ZoneInfo`（`ZoneInfo("Asia/Shanghai")`，全仓单一事实源）
  - `app.utils.timezone.booking_now(timezone: str | None = None) -> datetime`（返 **naive** 本地时间）
  - `app.utils.timezone.ensure_booking_timezone(value: datetime) -> datetime`（naive 补 Asia/Shanghai、aware 转换到 Asia/Shanghai）
  - `app.utils.time_slots.TimeSlot`（frozen dataclass：`weekday: int | None`、`start: str`、`end: str`）
  - `app.utils.time_slots.parse_time_slots(raw: str | None) -> list[TimeSlot]`
  - `app.utils.time_slots.build_time_slots_from_date(*, booking_date: date, time_slot: str) -> str`
  - `app.utils.time_slots.rebuild_from_time_range(*, booking_date: date | None, start_time, end_time) -> str`

**为什么（实测依据 §2.3 / §3.1 / F4 / F19 / F21）**：`app/utils/` 当前不存在（F4，已实测确认）。订单链路内有 3 个同语义「当前业务本地时间」实现（`booking_cancellation_policy.booking_now` 返 naive、`course_booking_service._now_naive` 返 naive、`booking_verification_service._booking_now` 返 aware），全仓 `CHINA_TIMEZONE` 有 6 处重复定义 + 1 处等价变体。领域纯函数要求 `now`/`today` 为 naive，故必须先建唯一时区源，否则 aware 孤岛与 naive 调用点共用纯函数会抛 `TypeError: can't compare offset-naive and offset-aware datetimes`。

- [x] **Step 1: 写 test_timezone.py 失败测试**

创建 `br-server/tests/test_timezone.py`：

```python
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
```

- [x] **Step 2: 运行确认失败**

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && /opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_timezone.py -q --tb=line -p no:cacheprovider 2>&1 | tail -5`
Expected: 收集错误，`ModuleNotFoundError: No module named 'app.utils'`。

- [x] **Step 3: 建 utils 包与 timezone.py**

先读现状确认 `ensure_booking_timezone` 语义与之逐条一致（该模块覆盖率 100%，任何偏差立刻红灯）：

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && sed -n '445,460p' app/services/booking_verification_service.py`

创建空文件 `br-server/app/utils/__init__.py`。创建 `br-server/app/utils/timezone.py`：

```python
"""业务时区单一事实源（Design Doc §2.3）。

契约：所有领域纯函数的 now/today/current_time 参数一律为 naive 的
settings.BOOKING_TIMEZONE（Asia/Shanghai）本地时间；时区转换只在服务层入口做一次。
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


def booking_now(timezone: str | None = None) -> datetime:
    """返回 naive 的业务本地时间（默认 settings.BOOKING_TIMEZONE）。"""
    return datetime.now(ZoneInfo(timezone or settings.BOOKING_TIMEZONE)).replace(tzinfo=None)


def ensure_booking_timezone(value: datetime) -> datetime:
    """naive 补 Asia/Shanghai；aware 转换到 Asia/Shanghai。

    从 booking_verification_service 的 _ensure_booking_timezone 提升，语义须逐条一致。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=CHINA_TIMEZONE)
    return value.astimezone(CHINA_TIMEZONE)
```

> 若 Step 3 读到的 `_ensure_booking_timezone` 现状与上述实现不一致（例如对 aware 输入不做 `astimezone` 而是直接 `replace`），**以现状为准**改写 `ensure_booking_timezone` 并同步调整 `test_ensure_booking_timezone_aware_input_converts` 的断言——本 Task 是提升既有实现，不是重新设计。

- [x] **Step 4: 写 test_time_slots.py 失败测试**

创建 `br-server/tests/test_time_slots.py`：

```python
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
```

> `build_from_date` / `rebuild` 的期望 weekday 由 `d.isoweekday()` 派生，不硬编码具体星期，避免计划书写时的星期口算错误。

- [x] **Step 5: 建 time_slots.py**

先读现状两处重复实现，`rebuild_from_time_range` 的输出格式必须与 `booking_service.py:1270-1291` 现状逐字节一致：

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && sed -n '1268,1292p' app/services/booking_service.py`

创建 `br-server/app/utils/time_slots.py`：

```python
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
```

> 若 Step 5 读到的 `booking_service.py:1270-1291` 重建分支输出的键名/结构与上述不同（例如用 `start`/`end` 拆分键而非 `time_slot`），**以现状为准**改写 `rebuild_from_time_range` 并同步 `test_rebuild_from_time_range_roundtrip`——重构必须保持输出契约不变。

- [x] **Step 6: 运行新测试全绿**

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && /opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_timezone.py tests/test_time_slots.py -q --tb=short -p no:cacheprovider 2>&1 | tail -6`
Expected: 全部 PASS，0 failed / 0 error。

- [x] **Step 7: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/utils/ br-server/tests/test_timezone.py br-server/tests/test_time_slots.py
git commit -m "feat: 新建 app/utils 时区与 time_slots 数据契约单一事实源

booking_now() 返 naive 本地时间，CHINA_TIMEZONE 常量单一源；
time_slots 兼容 3 种历史格式、解析失败静默容错。仅新增，未接线，行为零变更。"
```

> 本 Task 只新建文件，**不改任何现有服务**，因此不跑全量红名单（无行为面变化）；红名单验收在 Task 2.7 统一做。

### Task 2.2: 新建 domain/booking_status.py 词表 + 8 个领域纯函数（枚举值仍为旧字面量）

**Files:**
- Create: `br-server/app/domain/booking_status.py`
- Modify: `br-server/app/models/booking.py:11-19`（`PaymentMethod`/`PaymentStatus` 改 re-export）
- Modify: `br-server/app/schemas/booking.py:10-18`（`PaymentMethodEnum`/`PaymentStatusEnum` 改别名 re-export）
- Test: `br-server/tests/test_booking_status.py`

**Interfaces:**
- Consumes: 无（纯领域模块，不 import models/schemas/services）
- Produces:
  - `BookingStatus`（`PENDING_CONFIRM="pending_confirm"`、`PENDING_START="pending"`、`IN_PROGRESS="confirmed"`、`COMPLETED="completed"`、`CANCELLED="cancelled"`）——**Phase 2 值仍旧字面量，Phase 4 Task 4.1 翻转**
  - `PaymentStatus`（`PENDING/PAID/FAILED`）、`PaymentMethod`（`BALANCE/WECHAT`）
  - `SeatTransition(new_status: BookingStatus | None, stat_key: str | None)`、`CourseTransition(new_status, stat_key, highlight_only: bool)`（均 frozen dataclass）
  - 8 个纯函数：`resolve_seat_status`、`resolve_course_status`、`resolve_seat_transition`、`resolve_course_transition`、`is_cancellable`、`is_unpaid_cancellable`、`is_payable`、`is_full_refund_cancellation`
  - `build_status_filter_conditions(status_column, payment_status_column, status: str | None) -> list`

**为什么（实测依据 §2.1 / §2.2 / §2.4.1 / §2.5 / §2.6 / Q9）**：`models/booking.py:11-19` 与 `schemas/booking.py:10-18` 是**完全相同的两份** `PaymentMethod`/`PaymentStatus` 定义，收敛为单一事实源 + re-export，保留既有导入路径不断链（Q9）。8 个纯函数的真值表已逐处实测（见下方各函数 docstring 引用的行号），抽取是**等价替换**而非行为变更（§2.5）。

- [x] **Step 1: 写 test_booking_status.py 失败测试**

创建 `br-server/tests/test_booking_status.py`：

```python
from datetime import date, datetime, time

from app.domain.booking_status import (
    BookingStatus,
    CourseTransition,
    PaymentStatus,
    SeatTransition,
    build_status_filter_conditions,
    is_cancellable,
    is_full_refund_cancellation,
    is_payable,
    is_unpaid_cancellable,
    resolve_course_status,
    resolve_course_transition,
    resolve_seat_status,
    resolve_seat_transition,
)
from app.models.booking import Booking


# resolve_seat_status: now < start -> PENDING_START; now >= start -> IN_PROGRESS; None -> IN_PROGRESS
def test_seat_before_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.PENDING_START
def test_seat_at_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 10, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_after_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 11, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_none_date_fallback_in_progress():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=None, start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_string_start_time():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time="10:00") == BookingStatus.PENDING_START


# resolve_course_status: first <= today -> IN_PROGRESS; first > today -> PENDING_START; None -> IN_PROGRESS
def test_course_first_before_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 1)) == BookingStatus.IN_PROGRESS
def test_course_first_equals_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 3)) == BookingStatus.IN_PROGRESS
def test_course_first_after_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 10)) == BookingStatus.PENDING_START
def test_course_none_first_fallback_in_progress():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=None) == BookingStatus.IN_PROGRESS


# resolve_seat_transition（order_status_scheduler.py:89-99）
def test_seat_transition_start():
    assert resolve_seat_transition(status=BookingStatus.PENDING_START, now=datetime(2026, 9, 3, 10, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(BookingStatus.IN_PROGRESS, "seat_started")
def test_seat_transition_complete():
    assert resolve_seat_transition(status=BookingStatus.IN_PROGRESS, now=datetime(2026, 9, 3, 12, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(BookingStatus.COMPLETED, "seat_completed")
def test_seat_transition_pending_before_start_noop():
    assert resolve_seat_transition(status=BookingStatus.PENDING_START, now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(None, None)
def test_seat_transition_in_progress_before_end_noop():
    assert resolve_seat_transition(status=BookingStatus.IN_PROGRESS, now=datetime(2026, 9, 3, 11, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(None, None)


# resolve_course_transition（order_status_scheduler.py:164-184；完成为 today > last 严格大于）
def test_course_transition_start():
    assert resolve_course_transition(status=BookingStatus.PENDING_START, today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 3), last_lesson_date=date(2026, 9, 10)) == CourseTransition(BookingStatus.IN_PROGRESS, "course_started", False)
def test_course_transition_complete_strictly_greater():
    assert resolve_course_transition(status=BookingStatus.IN_PROGRESS, today=date(2026, 9, 11), first_lesson_date=date(2026, 9, 1), last_lesson_date=date(2026, 9, 10)) == CourseTransition(BookingStatus.COMPLETED, "course_completed", False)
def test_course_transition_today_equals_last_not_completed():
    assert resolve_course_transition(status=BookingStatus.IN_PROGRESS, today=date(2026, 9, 10), first_lesson_date=date(2026, 9, 1), last_lesson_date=date(2026, 9, 10)) == CourseTransition(None, None, True)
def test_course_transition_pending_before_first_noop():
    assert resolve_course_transition(status=BookingStatus.PENDING_START, today=date(2026, 9, 2), first_lesson_date=date(2026, 9, 3), last_lesson_date=date(2026, 9, 10)) == CourseTransition(None, None, False)


# is_cancellable（booking_service.py:654+657 / booking_rules.py:40 前置部分）
def test_cancellable_in_progress_paid():
    assert is_cancellable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PAID) is True
def test_cancellable_pending_start_paid():
    assert is_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is True
def test_cancellable_completed_paid_false():
    assert is_cancellable(status=BookingStatus.COMPLETED, payment_status=PaymentStatus.PAID) is False
def test_cancellable_in_progress_unpaid_false():
    assert is_cancellable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PENDING) is False


# is_unpaid_cancellable / is_payable：均为「双 pending」（status=PENDING_START 且 payment=PENDING）
def test_unpaid_cancellable_double_pending():
    assert is_unpaid_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PENDING) is True
def test_unpaid_cancellable_paid_false():
    assert is_unpaid_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is False
def test_payable_double_pending():
    assert is_payable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PENDING) is True
def test_payable_paid_false():
    assert is_payable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is False


# is_full_refund_cancellation（booking_service.py:1158-1161）
def test_full_refund_course_pending_start():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.PENDING_START) is True
def test_full_refund_course_pending_confirm():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.PENDING_CONFIRM) is True
def test_full_refund_seat_false():
    assert is_full_refund_cancellation(booking_type="seat", status=BookingStatus.PENDING_START) is False
def test_full_refund_course_in_progress_false():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.IN_PROGRESS) is False


# build_status_filter_conditions：派生口径分支形状（§2.6；行为等价由红名单恒等 + 既有 API 测试保证）
def test_filter_none_empty():
    assert build_status_filter_conditions(Booking.status, Booking.payment_status, None) == []
def test_filter_in_progress_two_conditions():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "in_progress")) == 2
def test_filter_pending_start_two_conditions():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "pending_start")) == 2
def test_filter_other_one_condition():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "completed")) == 1
```

- [x] **Step 2: 运行确认失败**

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && /opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_status.py -q --tb=line -p no:cacheprovider 2>&1 | tail -4`
Expected: 收集错误，`ModuleNotFoundError: No module named 'app.domain.booking_status'`。

- [x] **Step 3: 建 domain/booking_status.py**

创建 `br-server/app/domain/booking_status.py`：

```python
"""订单状态词表 —— 全仓唯一权威定义处（Design Doc §2）。

契约：本模块所有纯函数的 now/today 参数一律为 naive 的 Asia/Shanghai 本地时间；
本模块不 import app.models / app.schemas / app.services，不做 tzinfo 处理。
Phase 2 期间枚举成员值仍为旧字面量，Phase 4 Task 4.1 统一翻转。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class BookingStatus(str, Enum):
    PENDING_CONFIRM = "pending_confirm"
    PENDING_START = "pending"      # Phase 4 翻转为 "pending_start"
    IN_PROGRESS = "confirmed"      # Phase 4 翻转为 "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    BALANCE = "balance"
    WECHAT = "wechat"


@dataclass(frozen=True, slots=True)
class SeatTransition:
    new_status: BookingStatus | None
    stat_key: str | None


@dataclass(frozen=True, slots=True)
class CourseTransition:
    new_status: BookingStatus | None
    stat_key: str | None
    highlight_only: bool


def _parse_time(value):
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    return value


def resolve_seat_status(*, now: datetime, booking_date: date | None, start_time) -> BookingStatus:
    """booking_service.py:286-288 / :762-764、booking_payment_service.py:292-299。"""
    if booking_date is None or start_time is None:
        return BookingStatus.IN_PROGRESS
    booking_start = datetime.combine(booking_date, _parse_time(start_time))
    return BookingStatus.IN_PROGRESS if now >= booking_start else BookingStatus.PENDING_START


def resolve_course_status(*, today: date, first_lesson_date: date | None) -> BookingStatus:
    """booking_payment_service.py:288-290、course_booking_service.py:433、booking_service.py:1244。"""
    if first_lesson_date is None:
        return BookingStatus.IN_PROGRESS
    return BookingStatus.IN_PROGRESS if first_lesson_date <= today else BookingStatus.PENDING_START


def resolve_seat_transition(*, status, now, booking_date, start_time, end_time) -> SeatTransition:
    """order_status_scheduler.py:89-99。"""
    if status == BookingStatus.PENDING_START:
        if now >= datetime.combine(booking_date, _parse_time(start_time)):
            return SeatTransition(BookingStatus.IN_PROGRESS, "seat_started")
    elif status == BookingStatus.IN_PROGRESS:
        if now >= datetime.combine(booking_date, _parse_time(end_time)):
            return SeatTransition(BookingStatus.COMPLETED, "seat_completed")
    return SeatTransition(None, None)


def resolve_course_transition(*, status, today, first_lesson_date, last_lesson_date) -> CourseTransition:
    """order_status_scheduler.py:164-184。完成条件 today > last_lesson_date 为严格大于。"""
    if status == BookingStatus.PENDING_START:
        if first_lesson_date is not None and today >= first_lesson_date:
            return CourseTransition(BookingStatus.IN_PROGRESS, "course_started", False)
    elif status == BookingStatus.IN_PROGRESS:
        if last_lesson_date is not None and today > last_lesson_date:
            return CourseTransition(BookingStatus.COMPLETED, "course_completed", False)
        return CourseTransition(None, None, True)
    return CourseTransition(None, None, False)


def is_cancellable(*, status, payment_status) -> bool:
    """booking_service.py:654+657 / booking_rules.py:40 的状态+支付前置部分（不含时间判定）。"""
    return (
        status in (BookingStatus.IN_PROGRESS, BookingStatus.PENDING_START)
        and payment_status == PaymentStatus.PAID
    )


def is_unpaid_cancellable(*, status, payment_status) -> bool:
    """booking_service.py:644 的「双 pending」：未支付待开始可直接取消（无退款逻辑）。"""
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PENDING


def is_payable(*, status, payment_status) -> bool:
    """booking_service.py:744 的「双 pending」：仅待开始且待支付可发起支付。"""
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PENDING


def is_full_refund_cancellation(*, booking_type, status) -> bool:
    """booking_service.py:1158-1161 的 is_course_pending_start。"""
    return booking_type == "course" and status in (
        BookingStatus.PENDING_START,
        BookingStatus.PENDING_CONFIRM,
    )


def build_status_filter_conditions(status_column, payment_status_column, status: str | None) -> list:
    """C 端 list_bookings 派生口径（§2.6，Q5 行为零变更）。

    status 是 C 端 API 的「虚拟状态」查询参数，取值 "in_progress"/"pending_start" 是稳定的
    API 契约，与枚举成员的值无关（Phase 2 枚举值仍旧字面量，Phase 4 翻转后二者恰好重合）。
    """
    if status is None:
        return []
    if status == "in_progress":
        return [status_column == BookingStatus.IN_PROGRESS, payment_status_column == PaymentStatus.PAID]
    if status == "pending_start":
        return [
            status_column.in_([BookingStatus.PENDING_START, BookingStatus.PENDING_CONFIRM]),
            payment_status_column == PaymentStatus.PAID,
        ]
    return [status_column == status]
```

- [x] **Step 4: models/schemas 枚举改 re-export（收敛双份定义，Q9）**

`br-server/app/models/booking.py:11-19`：删除本地 `PaymentMethod`/`PaymentStatus` 两份 `class` 定义，改为一行 re-export（保留 `from app.models.booking import PaymentStatus` 等既有导入路径不断链）：
```python
from app.domain.booking_status import PaymentMethod, PaymentStatus  # noqa: F401
```

`br-server/app/schemas/booking.py:10-18`：删除本地 `PaymentMethodEnum`/`PaymentStatusEnum` 定义，改为别名 re-export：
```python
from app.domain.booking_status import PaymentMethod as PaymentMethodEnum  # noqa: F401
from app.domain.booking_status import PaymentStatus as PaymentStatusEnum  # noqa: F401
```

> `models/booking.py:32` 的 `default="confirmed"` **本 Task 不动**（留到 Phase 4 Task 4.1 随枚举值翻转一起改为 `BookingStatus.PENDING_START`），以保证 Phase 2「零行为面变化」。`schemas/booking.py:16` 的 `payment_status='pending'`（trap #1）是**支付域默认值，不改**。

- [x] **Step 5: 运行新测试 + 依赖方向校验**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_status.py -q --tb=short -p no:cacheprovider 2>&1 | tail -6
grep -n "import" app/domain/booking_status.py | grep -E "app.models|app.schemas|app.services"; echo "领域依赖方向违规退出码应为 1（无命中）"
/opt/miniconda3/envs/booking-room/bin/python -c "from app.models.booking import PaymentStatus; from app.schemas.booking import PaymentStatusEnum; print('re-export OK', PaymentStatus.PAID.value, PaymentStatusEnum.PAID.value)"
```
Expected: 新测试全 PASS；grep 无命中（领域层不依赖 models/schemas/services）；python 输出 `re-export OK paid paid`。

- [x] **Step 6: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/domain/booking_status.py br-server/app/models/booking.py br-server/app/schemas/booking.py br-server/tests/test_booking_status.py
git commit -m "feat: 新建 domain/booking_status 词表与 8 个领域纯函数，收敛双份支付枚举

枚举成员值仍为旧字面量（PENDING_START=pending / IN_PROGRESS=confirmed），
models/schemas 改 re-export 保留导入路径不断链。纯结构重构，行为零变更。"
```

> 本 Task 新建领域模块并接线 models/schemas 的定义源，但**服务层尚未改调纯函数**（Task 2.4-2.6 做），故落库/响应仍走旧内联判定，红名单不变；统一验收在 Task 2.7。

### Task 2.3: domain/verification_rules.py 新增 is_verifiable + resolve_verification_status（核销域，Q12）

**Files:**
- Modify: `br-server/app/domain/verification_rules.py`（新增 2 个纯函数 + import `BookingStatus`/`PaymentStatus`）
- Test: `br-server/tests/test_booking_status.py`（追加核销域分支，tasks 8.2「含核销域」）

**Interfaces:**
- Consumes: Task 2.2 的 `BookingStatus`/`PaymentStatus`
- Produces:
  - `is_verifiable(*, status, payment_status) -> bool`（`IN_PROGRESS` 恒可核销；`PENDING_START` 仅当 `PAID`）
  - `resolve_verification_status(*, now: datetime, end_at: datetime) -> BookingStatus`（`now <= end_at` → `IN_PROGRESS`，否则 `COMPLETED`）

**为什么（实测依据 §2.4.2 / §4.1 #7 / Q12）**：核销是订单生命周期终点，其状态判定重复 4 处（`booking_verification_service.py:189-192,255-258,275-281,353-356`）+ 窗口内/外状态判定 1 处（`:264`）。`verification_rules.py` 已承载 token 签发/解码且覆盖率 100%，**复用该既有领域模块，不新建文件**。`is_verifiable` 的真实语义**不是**「仅 `in_progress` 可核销」，而是含「`pending_start` 且已支付」分支（F22）。

- [x] **Step 1: 追加核销域失败测试**

在 `br-server/tests/test_booking_status.py` **末尾追加**（import 区补 `from app.domain.verification_rules import is_verifiable, resolve_verification_status`）：

```python
# is_verifiable（booking_verification_service.py:189-192 复合判定）
def test_verifiable_in_progress_unpaid_true():
    assert is_verifiable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PENDING) is True
def test_verifiable_in_progress_paid_true():
    assert is_verifiable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PAID) is True
def test_verifiable_pending_start_paid_true():
    assert is_verifiable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is True
def test_verifiable_pending_start_unpaid_false():
    assert is_verifiable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PENDING) is False
def test_verifiable_completed_false():
    assert is_verifiable(status=BookingStatus.COMPLETED, payment_status=PaymentStatus.PAID) is False


# resolve_verification_status（booking_verification_service.py:264；now <= end_at 含等号）
def test_verification_status_before_end_in_progress():
    assert resolve_verification_status(now=datetime(2026, 9, 3, 10, 0), end_at=datetime(2026, 9, 3, 12, 0)) == BookingStatus.IN_PROGRESS
def test_verification_status_at_end_in_progress():
    assert resolve_verification_status(now=datetime(2026, 9, 3, 12, 0), end_at=datetime(2026, 9, 3, 12, 0)) == BookingStatus.IN_PROGRESS
def test_verification_status_after_end_completed():
    assert resolve_verification_status(now=datetime(2026, 9, 3, 13, 0), end_at=datetime(2026, 9, 3, 12, 0)) == BookingStatus.COMPLETED
```

- [x] **Step 2: 运行确认失败**

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && /opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_status.py -q --tb=line -p no:cacheprovider 2>&1 | tail -4`
Expected: FAIL，`ImportError: cannot import name 'is_verifiable'`。

- [x] **Step 3: 在 verification_rules.py 新增 2 个纯函数**

先读现状确认导入区与既有函数风格：`sed -n '1,20p' app/domain/verification_rules.py`。在 `br-server/app/domain/verification_rules.py` 顶部 import 区加入 `from app.domain.booking_status import BookingStatus, PaymentStatus`（若尚未导入 `datetime` 一并补上），并追加：

```python
def is_verifiable(*, status, payment_status) -> bool:
    """核销可核销复合判定（booking_verification_service.py:189-192 等 4 处）。

    实测语义：IN_PROGRESS 恒可核销；PENDING_START 仅当已支付（F22）。
    """
    if status == BookingStatus.IN_PROGRESS:
        return True
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PAID


def resolve_verification_status(*, now, end_at) -> BookingStatus:
    """窗口内/外状态判定（booking_verification_service.py:264）。now <= end_at 含等号。"""
    return BookingStatus.IN_PROGRESS if now <= end_at else BookingStatus.COMPLETED
```

> 依赖方向：`verification_rules` 与 `booking_status` 同属 `domain/`，同层 import 合法；仍**不得** import models/schemas/services。

- [x] **Step 4: 运行新测试全绿 + 既有核销测试不回归**

Run: `cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server && /opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_status.py tests/test_booking_verification_service.py -q --tb=short -p no:cacheprovider 2>&1 | tail -6`
Expected: `test_booking_status.py` 全 PASS；`test_booking_verification_service.py` 的通过/失败构成与本 Task 前**一致**（本 Task 只新增领域函数，未接线服务，核销服务测试结果不应变化）。

- [x] **Step 5: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/domain/verification_rules.py br-server/tests/test_booking_status.py
git commit -m "feat: verification_rules 新增 is_verifiable/resolve_verification_status 核销领域函数

复用既有 domain/verification_rules.py，覆盖核销域第 7 处判定点。仅新增，未接线。"
```

### Task 2.4: booking_verification_service 改调核销领域函数（aware 孤岛只在边界降级）

**Files:**
- Modify: `br-server/app/services/booking_verification_service.py`（`:189-192,255-258,275-281,353-356` → `is_verifiable()`；`:264` → `resolve_verification_status()`；`:449` `_booking_now` → import `app.utils.timezone.booking_now`）

**Interfaces:**
- Consumes: Task 2.3 的 `is_verifiable`/`resolve_verification_status`、Task 2.1 的 `booking_now`
- Produces: 核销服务对外行为**完全不变**（含幂等保护、并发 UPDATE 命中 0 行分支、`_select_nearest_booking` 三档排序）

**为什么（实测依据 §4.1 #7 / §2.3 / §14 / Q11）**：本服务是全仓唯一 aware 孤岛，已有 `_ensure_booking_timezone()` 归一化工具。重构只在**调用领域函数的边界**用 `.replace(tzinfo=None)` 降级一次，**内部 aware 比较与 `_ensure_booking_timezone` 用法保持不变**（Q11：孤岛只在边界降级）。

> **红线（挂钟敏感项就在这里）**：`_select_nearest_booking`（`:383-413`）的三档排序逻辑**绝对不动**——`test_issue_verification_token_for_future_booking_returns_token` 的挂钟敏感性正源于此。`:267` 的幂等保护（窗口内已核销 → 抛「预约已核销」）语义**原样保留**（§2.4.2）。本 Task 只替换状态判定表达式，不改任何查询/排序/分支结构。

- [x] **Step 1: 定位全部改动点**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -n '"confirmed"\|"pending"\|"completed"\|_booking_now\|can_verify\|new_status =' app/services/booking_verification_service.py
```
Expected: 命中集中在 `:189-192`（`can_verify` 复合判定）、`:255-258`（拒绝判定）、`:264`（`new_status = "confirmed" if now <= end_at else "completed"`）、`:275-281`（条件 UPDATE）、`:353-356`（第二处查询）、`:449`（`_booking_now` 定义）。逐处阅读上下文后再改。

- [x] **Step 2: 复合判定改调 is_verifiable**

把 `:189-192,255-258,275-281,353-356` 四处的「`status`/`payment_status` 复合布尔判定」替换为 `is_verifiable(status=booking.status, payment_status=booking.payment_status)`（各处按现状变量名传参）。**保留**每处原有的分支后果（返回 token / 抛特定错误 / 条件 UPDATE 的 WHERE），只把布尔表达式换成函数调用。示例（`:189-192` 的 `can_verify`）：
```python
from app.domain.verification_rules import is_verifiable, resolve_verification_status
# ...
can_verify = is_verifiable(status=booking.status, payment_status=booking.payment_status)
```

- [x] **Step 3: 窗口状态判定改调 resolve_verification_status（边界降级）**

`:264` 的 `new_status = "confirmed" if now <= end_at else "completed"` 改为：
```python
new_status = resolve_verification_status(
    now=now.replace(tzinfo=None), end_at=end_at.replace(tzinfo=None)
)
```
> `now` 与 `end_at` **必须成对降级**（同为 naive），否则领域函数内 `now <= end_at` 抛 `TypeError`。若二者本就同为 aware 且同时区，直接传入亦可比较；本计划统一按 §2.3 在边界降级为 naive，与全局契约一致。`new_status` 随后写入 `booking.status` 时，其值为枚举成员 `.value`（Phase 2 仍是旧字面量 `"confirmed"`/`"completed"`），落库不变。

- [x] **Step 4: _booking_now 改为 import（内部 aware 用法保留）**

`:449` 的 `_booking_now()` 定义删除，模块顶部改 `from app.utils.timezone import booking_now`。原 `_booking_now()` 的 2 处调用点（`:201,260`）改为 `booking_now(settings.BOOKING_TIMEZONE)`——但注意原 `_booking_now` 返 **aware**，而 `utils.booking_now` 返 **naive**。因此这 2 处若下游需要 aware，必须包一层 `ensure_booking_timezone(booking_now(settings.BOOKING_TIMEZONE))` 保持 aware 语义。

> **先读后改**：`sed -n '195,265p' app/services/booking_verification_service.py` 确认 `:201,260` 两处 `_booking_now()` 的下游是否需要 aware。本服务内部一律 aware，故这 2 处应保持 aware：用 `ensure_booking_timezone(booking_now(settings.BOOKING_TIMEZONE))`，或保留模块内一个薄封装 `_booking_now = lambda: ensure_booking_timezone(booking_now(settings.BOOKING_TIMEZONE))`。目标是**消除重复的时区定义**，但**不改变本服务的 aware 内部语义**。

- [x] **Step 5: 验证核销服务测试构成不变（挂钟感知）**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
TZ=Asia/Shanghai date '+现在沪时=%H:%M（<=11:00 则敏感项应红，>11:00 应绿）'
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_verification_service.py -q --tb=short -p no:cacheprovider 2>&1 | tail -8
```
Expected: 除挂钟敏感项 `test_issue_verification_token_for_future_booking_returns_token` 按当前时刻应有的红/绿外，其余核销测试**全绿且构成与本 Task 前一致**。若出现**新的**核销失败，说明边界降级或 is_verifiable 接线有误，**停止**并按 systematic-debugging 排查（不得改 `_select_nearest_booking`）。

- [x] **Step 6: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/services/booking_verification_service.py
git commit -m "refactor: 核销服务改调 is_verifiable/resolve_verification_status，时区定义收敛

aware 孤岛只在调用领域函数的边界 .replace(tzinfo=None) 降级；内部 aware 比较与
_ensure_booking_timezone 用法不变；_select_nearest_booking 三档排序与幂等保护原样保留。"
```

### Task 2.5: booking_service.py 改调座位/课程状态纯函数（判定点 #1/#2/#3 + 取消/支付/筛选）

**Files:**
- Modify: `br-server/app/services/booking_service.py`
  - `:284-290` 座位下单 `initial_status`（判定点 #1，§4.1）
  - `:350-365` 虚拟状态筛选（§2.6）
  - `:644` 双 `pending` 未支付直接取消
  - `:654-658` 取消前置判定（**两段式错误消息陷阱**）
  - `:744` 支付前置判定
  - `:760-764` 余额支付座位状态（判定点 #2）
  - `:1158-1162` `is_course_pending_start`
  - `:1230-1244` `admin_confirm_booking` 定制订单确认（判定点 #3）

**Interfaces:**
- Consumes: Task 2.2 的 `BookingStatus` / `resolve_seat_status` / `resolve_course_status` / `is_cancellable` / `is_unpaid_cancellable` / `is_payable` / `is_full_refund_cancellation` / `build_status_filter_conditions`；既有 `booking_now`（从 `booking_cancellation_policy` 导入，Task 2.6 后为 re-export，同一函数）
- Produces: `booking_service` 对外行为**完全不变**——含两段式取消错误消息、双 `pending` 直接取消、虚拟筛选派生口径、`admin_confirm_booking` 落库值

> **全局规则（Phase 2 关键不变量，Task 2.5/2.6 通用，务必遵守）**
> 1. **写库与查询绑定一律用 `.value`**：`booking.status = resolve_seat_status(...).value`、`status_column == BookingStatus.IN_PROGRESS.value`。理由：① 与既有约定一致（`:304 payment_method=data.payment_method.value`）；② 规避 `(str, Enum)` 成员在不同 DBAPI / Python 版本下 `str()` / `format()` 结果差异（可能得到 `"BookingStatus.IN_PROGRESS"` 而非 `"in_progress"`）。
> 2. **纯函数内部与布尔比较用枚举成员**：`booking.status == BookingStatus.IN_PROGRESS`（`(str, Enum)` 成员与等值 `str` 相等成立，DB 读回的 `str` 可直接比较）。
> 3. Phase 2 枚举 `.value` 仍是旧字面量（`PENDING_START.value == "pending"`、`IN_PROGRESS.value == "confirmed"`），故所有 `.value` 写库/查询结果与现状**逐字节相同**；Phase 4 翻转 `.value` 后，这些写点与查询点**自动跟随新词表**，无需再改调用点——这正是「结构重构与取值变更分离」的落地机制。
> 4. **座位纯函数需 naive `now`**：调用 `resolve_seat_status` 前用 `booking_now(settings.BOOKING_TIMEZONE)`（返 naive）取当前时间，替换原 `datetime.now(ZoneInfo("Asia/Shanghai"))`（aware）。课程纯函数只需 `today`（date），沿用既有 `datetime.now(ZoneInfo("Asia/Shanghai")).date()` 即可，其 `CHINA_TIMEZONE` 常量收敛留待 Phase 3。

> **红线（§10 陷阱 #2/#3，绝对不动）**：`:531` 的 `lesson_schedules.schedule_status`、`:1303` 的 `course_schedules.schedule_status` 属**排课域**，其 `"in_progress"` 与订单状态无关，本 Task 与 Phase 4 均**不得触碰**（grep 守卫 #2/#3 保护）。

- [x] **Step 1: 追加领域函数导入**

在 `booking_service.py` 顶部导入区追加（`booking_now` 已在 `:48` 从 `booking_cancellation_policy` 导入，勿重复）：
```python
from app.domain.booking_status import (
    BookingStatus,
    build_status_filter_conditions,
    is_cancellable,
    is_full_refund_cancellation,
    is_payable,
    is_unpaid_cancellable,
    resolve_course_status,
    resolve_seat_status,
)
```
Run 确认导入可解析：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -c "import app.services.booking_service" && echo IMPORT_OK
```
Expected: 打印 `IMPORT_OK`，无 `ImportError`。

- [x] **Step 2: 座位下单 initial_status 改调 resolve_seat_status（判定点 #1，:284-290）**

把：
```python
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    if balance_payment:
        booking_start = datetime.combine(data.date, data.start_time)
        booking_start = booking_start.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        initial_status = "pending" if now < booking_start else "confirmed"
    else:
        initial_status = "pending"
```
改为：
```python
    if balance_payment:
        initial_status = resolve_seat_status(
            now=booking_now(settings.BOOKING_TIMEZONE),
            booking_date=data.date,
            start_time=data.start_time,
        ).value
    else:
        initial_status = BookingStatus.PENDING_START.value
```
**等价性**：`resolve_seat_status` 为 `now >= combine(date,start) → IN_PROGRESS("confirmed")`，否则 `PENDING_START("pending")`，与旧 `now < booking_start → "pending" else "confirmed"` 逐值一致；微信分支旧代码无条件 `"pending"`，即 `PENDING_START.value`（§14「微信支付创建座位预约 → 无条件 PENDING_START」）。`:299 status=initial_status` 不变（仍是 str）。

- [x] **Step 3: 虚拟状态筛选改调 build_status_filter_conditions（:350-365）**

把：
```python
    is_in_progress_filter = status == "in_progress"
    is_pending_start_filter = status == "pending_start"
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    conditions = [Booking.user_id == str(user_id)]
    if status is not None and not is_in_progress_filter and not is_pending_start_filter:
        conditions.append(Booking.status == status)
    elif is_in_progress_filter:
        conditions.append(Booking.status == "confirmed")
        conditions.append(Booking.payment_status == "paid")
    elif is_pending_start_filter:
        conditions.append(Booking.status.in_(["pending", "pending_confirm"]))
        conditions.append(Booking.payment_status == "paid")
```
改为：
```python
    is_in_progress_filter = status == "in_progress"
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    conditions = [Booking.user_id == str(user_id)]
    conditions.extend(
        build_status_filter_conditions(Booking.status, Booking.payment_status, status)
    )
```
**保留 `is_in_progress_filter`**：`:371 if is_in_progress_filter:` 的课程后置过滤仍需用它。**删除 `is_pending_start_filter`**：仅在被替换的 conditions 块用到（先 `grep -n is_pending_start_filter app/services/booking_service.py` 确认只剩本块 2 处命中再删）。`build_status_filter_conditions` 展开与旧三分支逐条一致（§2.6）：`None→[]`、`"in_progress"→[status==IN_PROGRESS.value, payment==PAID.value]`、`"pending_start"→[status.in_([PENDING_START.value, PENDING_CONFIRM.value]), payment==PAID.value]`、其它→`[status==status]`。

- [x] **Step 4: 双 pending 未支付取消改调 is_unpaid_cancellable（:644）**

把 `if booking.payment_status == "pending" and booking.status == "pending":` 改为：
```python
    if is_unpaid_cancellable(status=booking.status, payment_status=booking.payment_status):
```
**等价性**：`is_unpaid_cancellable` = `status == PENDING_START and payment_status == PENDING`，Phase 2 展开即双 `"pending"`，与旧判定同形（分支体 `:645-652` 不变）。

- [x] **Step 5: 取消前置判定改调 is_cancellable（:654-658，保留两段式错误消息）**

把：
```python
    if booking.status not in ("confirmed", "pending"):
        raise BookingCancellationNotAllowedError("该预约不可取消")

    if booking.payment_status != "paid":
        raise BookingCancellationNotAllowedError("未支付预约不可取消")
```
改为：
```python
    if not is_cancellable(status=booking.status, payment_status=booking.payment_status):
        # 保留两段式错误消息与判定顺序：状态非法优先于未支付（行为零变更）
        if booking.status not in (BookingStatus.IN_PROGRESS, BookingStatus.PENDING_START):
            raise BookingCancellationNotAllowedError("该预约不可取消")
        raise BookingCancellationNotAllowedError("未支付预约不可取消")
```
> **陷阱说明（务必按此写，不得简化为单一 raise）**：旧代码是**两段独立 raise**，消息不同（「该预约不可取消」/「未支付预约不可取消」），且**状态检查在前**。若直接 `if not is_cancellable(...): raise BookingCancellationNotAllowedError("该预约不可取消")` 会**丢失「未支付预约不可取消」消息**并在「状态非法且未支付」时改变抛出的消息 → 用户可见行为变更。上面的写法用 `is_cancellable` 消除与 `booking_rules.py:40` 的重复布尔（§4.1 line 275 意图），同时在分支内**先判状态、再判支付**，逐一复刻旧的两段消息与优先级。

- [x] **Step 6: 支付前置判定改调 is_payable（:744）**

把 `if booking.status != "pending" or booking.payment_status != "pending":` 改为：
```python
    if not is_payable(status=booking.status, payment_status=booking.payment_status):
```
**等价性**：`is_payable` = `status == PENDING_START and payment_status == PENDING`；`not is_payable` = `status != "pending" or payment != "pending"`（Phase 2），与旧判定德摩根等价（分支体 `:745 raise` 不变）。

- [x] **Step 7: 余额支付座位状态改调 resolve_seat_status（判定点 #2，:760-764）**

把：
```python
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        booking_start = datetime.combine(booking.date, booking.start_time)
        booking_start = booking_start.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        booking.status = "pending" if now < booking_start else "confirmed"
```
改为：
```python
        booking.status = resolve_seat_status(
            now=booking_now(settings.BOOKING_TIMEZONE),
            booking_date=booking.date,
            start_time=booking.start_time,
        ).value
```
**等价性**：同 Step 2。`:765 booking.payment_status = "paid"` 等后续赋值不变。

- [x] **Step 8: is_course_pending_start 改调 is_full_refund_cancellation（:1158-1162）**

把：
```python
    is_course_pending_start = booking.booking_type == "course" and booking.status in (
        "pending",
        "pending_confirm",
    )
    if booking.status == "pending_confirm" or is_course_pending_start:
```
改为：
```python
    is_course_pending_start = is_full_refund_cancellation(
        booking_type=booking.booking_type, status=booking.status
    )
    if booking.status == BookingStatus.PENDING_CONFIRM.value or is_course_pending_start:
```
**等价性**：`is_full_refund_cancellation` = `booking_type == "course" and status in (PENDING_START, PENDING_CONFIRM)`，Phase 2 展开即 `("pending", "pending_confirm")`。该判定与 br-admin `views/booking/list/index.vue:72,139` 是同一规则的前后端两份实现（§4.1 line 277），语义契约在 Phase 6 写入 `docs/booking-rules.md`。

- [x] **Step 9: admin_confirm_booking 定制订单确认改调 resolve_course_status（判定点 #3，:1230-1244）**

把 `:1230` 的 guard 与 `:1244` 的状态解析改为：
```python
    if booking.status != BookingStatus.PENDING_CONFIRM.value:
        raise BookingError("该预约不是待确认状态")

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    # ...（:1235-1243 定制排课创建与 booking_date 兜底逻辑不变）...
    booking_date = booking.date or today
    booking.status = resolve_course_status(today=today, first_lesson_date=booking_date).value
```
**等价性**：`resolve_course_status` 为 `first_lesson_date <= today → IN_PROGRESS("confirmed")`，否则 `PENDING_START("pending")`，与旧 `"confirmed" if booking_date <= today else "pending"` 一致；`booking_date` 已在 `:1243` 用 `or today` 兜底故非 `None`（不触发 `None→IN_PROGRESS` 兜底分支，但即便触发也与旧 `booking.date or today` 语义殊途同归）。`:1235-1238` 的 `_create_custom_schedule_on_confirm` 调用、`:1246 flush`、`:1249` 重查均不变。

- [x] **Step 10: 运行 booking 相关测试，核对红名单恒等**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_service.py tests/test_booking_payment_service.py tests/test_course_booking_service.py -q --tb=short -p no:cacheprovider 2>&1 | tail -15
```
Expected: 通过/失败构成与本 Task 前**一致**（既有红灯仍是 `teacher_id`/`price`/coupon 签名那批，与本改动无关）。随后跑 Phase 0 的红名单比对：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
bash openspec/changes/booking-order-lifecycle-refactor/verification/redlist.sh > /tmp/redlist_after_2_5.txt 2>&1
/opt/miniconda3/envs/booking-room/bin/python openspec/changes/booking-order-lifecycle-refactor/verification/compare_redlist.py \
  openspec/changes/booking-order-lifecycle-refactor/verification/redlist-baseline.txt /tmp/redlist_after_2_5.txt
```
Expected: `REDLIST IDENTICAL`（挂钟敏感项按当前时刻规则豁免）。若出现新增/消失项，**停止**并按 systematic-debugging 定位是哪个判定点接线有误。

- [x] **Step 11: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/services/booking_service.py
git commit -m "refactor: booking_service 改调座位/课程状态纯函数（判定点 #1/#2/#3）

座位下单/余额支付 → resolve_seat_status；admin 确认 → resolve_course_status；
双 pending 取消 → is_unpaid_cancellable；支付前置 → is_payable；
取消前置 → is_cancellable（保留两段式错误消息与状态优先顺序）；
is_course_pending_start → is_full_refund_cancellation；虚拟筛选 → build_status_filter_conditions。
写库/查询一律 .value，Phase 2 值仍为旧字面量，行为零变更。"
```

### Task 2.6: booking_payment_service + course_booking_service 改调纯函数 + booking_cancellation_policy.booking_now 改 re-export

**Files:**
- Modify: `br-server/app/services/booking_payment_service.py`（`:275-299` `_determine_course_booking_status` → 分派 `resolve_course_status` / `resolve_seat_status`，判定点 #4）
- Modify: `br-server/app/services/course_booking_service.py`（`:420-436` 固定班课下单三分支 → `resolve_course_status`，`custom` 分支保留 `PENDING_CONFIRM`，判定点 #5）
- Modify: `br-server/app/services/booking_cancellation_policy.py`（`:25-26` `booking_now` 改为 re-export `app.utils.timezone.booking_now`，保留导入路径不断链）

**Interfaces:**
- Consumes: Task 2.2 的 `BookingStatus` / `resolve_course_status` / `resolve_seat_status`；Task 2.1 的 `app.utils.timezone.booking_now`
- Produces: `_determine_course_booking_status` 返回值与课程/座位分支行为**逐值不变**（含 `None` 兑底落 `IN_PROGRESS`、`start_time` 为 `str` 的 `strptime` 兼容）；`booking_cancellation_policy.booking_now` 与 `course_booking_service._now_naive` 导入路径均可用

> **本 Task 不碰时区常量**：`booking_payment_service` 内的 `ZoneInfo("Asia/Shanghai")` 内联与 `course_booking_service:26 CHINA_TIMEZONE` / `:49 _now_naive` 的**常量收敛留到 Phase 3**（line 110）。本 Task 只在座位分支需要 naive `now` 时调 `booking_now`，其余时区写法不动。

- [x] **Step 1: booking_payment_service 追加导入并确认 settings**

Run 确认 `settings` 是否已导入：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -n 'from app.core.config import\|import settings' app/services/booking_payment_service.py
```
在导入区追加（若上步未命中 `settings`，一并加 `from app.core.config import settings`）：
```python
from app.core.config import settings
from app.domain.booking_status import BookingStatus, resolve_course_status, resolve_seat_status
from app.utils.timezone import booking_now
```

- [x] **Step 2: _determine_course_booking_status 改为分派领域函数（:275-299）**

把整个方法体改为：
```python
    async def _determine_course_booking_status(self, booking: Booking) -> str:
        """课程预约按开课日期、座位预约按时段开始时间返回状态（分派领域纯函数）。

        课程（开课日期取第一课时，下单时已回写至 booking.date）:
          first_lesson_date <= today → IN_PROGRESS("confirmed")；> today → PENDING_START("pending")；None → IN_PROGRESS
        座位:
          now >= date+start_time → IN_PROGRESS；< → PENDING_START；date/start_time 为 None → IN_PROGRESS
        """
        if booking.course_id:
            return resolve_course_status(
                today=booking_now(settings.BOOKING_TIMEZONE).date(),
                first_lesson_date=booking.date,
            ).value
        return resolve_seat_status(
            now=booking_now(settings.BOOKING_TIMEZONE),
            booking_date=booking.date,
            start_time=booking.start_time,
        ).value
```
**等价性（逐项实测）**：
- 课程分支：旧 `if booking.date is None: return "confirmed"` + `"confirmed" if booking.date <= today else "pending"` ⇔ `resolve_course_status`（`None→IN_PROGRESS("confirmed")`、`first<=today→IN_PROGRESS`、`>today→PENDING_START`）。
- 座位分支：旧 `if booking.date and booking.start_time:` 内处理 `str` 型 `start_time`（`strptime("%H:%M")`）+ `"confirmed" if now >= booking_start else "pending"`，否则 `return "confirmed"` ⇔ `resolve_seat_status`（`None→IN_PROGRESS("confirmed")`、`now>=combine→IN_PROGRESS`、`<→PENDING_START`、`start_time` 为 `str` 时内部 `strptime`）。两边 `now` 同为上海本地时间（旧 aware / 新 naive，但 `combine` 同步 naive，比较结果一致）。
- 调用点 `:169` `paid_status = await self._determine_course_booking_status(booking)` 与 `:316` 不变（仍得到 `str`）。`:166-168` 的 `pending_confirm` 直通分支属字面量，留 Phase 4。

- [x] **Step 3: course_booking_service 追加导入**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -n 'from app.domain.booking_status\|from app.core.config import' app/services/course_booking_service.py
```
在导入区追加：
```python
from app.domain.booking_status import BookingStatus, resolve_course_status
```
（`today` 仍用既有 `datetime.now(CHINA_TIMEZONE).date()`，不引入 `booking_now`，避免提前碰时区常量。）

- [x] **Step 4: 固定班课下单三分支改调 resolve_course_status（:430-436）**

把：
```python
        if data.booking_type == "custom":
            initial_status = "pending_confirm"
        else:
            if first_lesson_date is not None and first_lesson_date > today:
                initial_status = "pending"
            else:
                initial_status = "confirmed"
```
改为：
```python
        if data.booking_type == "custom":
            initial_status = BookingStatus.PENDING_CONFIRM.value
        else:
            initial_status = resolve_course_status(
                today=today, first_lesson_date=first_lesson_date
            ).value
```
**等价性**：旧 `else` 为 `first_lesson_date > today → "pending"`，否则（`<= today` 或 `None`）`"confirmed"` ⇔ `resolve_course_status`（`None→IN_PROGRESS("confirmed")`、`first<=today→IN_PROGRESS("confirmed")`、`first>today→PENDING_START("pending")`）。`custom → PENDING_CONFIRM.value("pending_confirm")`。`:420-428` 的 `today` / `first_lesson_date` 推导、`:511 status=initial_status` 均不变。

- [x] **Step 5: booking_cancellation_policy.booking_now 改 re-export（:25-26）**

先确认现状与消费方：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
grep -rn 'from app.services.booking_cancellation_policy import\|booking_cancellation_policy.booking_now' app tests | head
grep -n 'ZoneInfo\|DEFAULT_BOOKING_TIMEZONE' app/services/booking_cancellation_policy.py
```
把 `:25-26` 的 `def booking_now(...)` 删除，在文件顶部导入区改为 re-export（保留 `from app.services.booking_cancellation_policy import booking_now` 不断链，供 `booking_service.py:48` 消费）：
```python
from app.utils.timezone import booking_now  # noqa: F401  # re-export：booking_now 单一事实源已迁至 app.utils.timezone
```
- `calculate_cancellation_policy:36` 的 `now or booking_now()` 不变——现在解析到 `app.utils.timezone.booking_now()`（默认 Asia/Shanghai、返 naive），与旧 `booking_now()` 逐值相同。
- 若上步 grep 确认 `ZoneInfo` 在本文件**仅剩导入行**一处命中，则删除 `:6 from zoneinfo import ZoneInfo`（避免未用导入）；`DEFAULT_BOOKING_TIMEZONE`（`:10`）若仍被其它文件引用则保留，否则可保留为无害常量。
- 无循环导入：`app.utils.timezone` 不反导入 `booking_cancellation_policy`。

- [x] **Step 6: 运行支付/课程/取消策略测试 + 红名单比对**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -c "import app.services.booking_payment_service, app.services.course_booking_service, app.services.booking_cancellation_policy, app.services.booking_service" && echo IMPORT_OK
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_payment_service.py tests/test_course_booking_service.py tests/test_booking_cancellation_policy.py -q --tb=short -p no:cacheprovider 2>&1 | tail -15
```
Expected: `IMPORT_OK` 且测试构成与本 Task 前一致。再跑全量红名单比对：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
bash openspec/changes/booking-order-lifecycle-refactor/verification/redlist.sh > /tmp/redlist_after_2_6.txt 2>&1
/opt/miniconda3/envs/booking-room/bin/python openspec/changes/booking-order-lifecycle-refactor/verification/compare_redlist.py \
  openspec/changes/booking-order-lifecycle-refactor/verification/redlist-baseline.txt /tmp/redlist_after_2_6.txt
```
Expected: `REDLIST IDENTICAL`。若 `test_booking_cancellation_policy.py` 新红，优先怀疑 re-export 后 `booking_now()` 默认时区或签名不一致。

- [x] **Step 7: 提交**

```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
git add br-server/app/services/booking_payment_service.py br-server/app/services/course_booking_service.py br-server/app/services/booking_cancellation_policy.py
git commit -m "refactor: 支付回调与课程下单改调状态纯函数，booking_now 收敛为 re-export

_determine_course_booking_status → 分派 resolve_course_status/resolve_seat_status（判定点 #4）；
固定班课下单三分支 → resolve_course_status，custom 保留 PENDING_CONFIRM（判定点 #5）；
booking_cancellation_policy.booking_now → re-export app.utils.timezone.booking_now（导入路径不断链）。
本 Task 不碰时区常量（CHINA_TIMEZONE/_now_naive 收敛留 Phase 3）。"
```

### Task 2.7: Phase 2 红名单验收（结构重构零行为变更）

**Files:**
- 无代码改动（纯验收）；如需补测试只动 `br-server/tests/test_booking_status.py`

**Interfaces:**
- Consumes: Task 2.1–2.6 全部产物
- Produces: Phase 2 完成判定——全量红名单与基线集合恒等，且枚举值仍为旧字面量

- [x] **Step 1: 确认枚举值仍为旧字面量（Phase 2 不变量）**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -c "from app.domain.booking_status import BookingStatus as B; print(B.PENDING_START.value, B.IN_PROGRESS.value, B.PENDING_CONFIRM.value, B.COMPLETED.value, B.CANCELLED.value)"
```
Expected: 输出 `pending confirmed pending_confirm completed cancelled`——确认 Phase 2 枚举值**仍为旧字面量**（`PENDING_START="pending"`、`IN_PROGRESS="confirmed"`）。若输出新词表，说明误提前做了 Phase 4，**停止**回滚。

- [x] **Step 2: 全量测试 + 红名单集合恒等比对**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
bash openspec/changes/booking-order-lifecycle-refactor/verification/redlist.sh > /tmp/redlist_phase2.txt 2>&1
/opt/miniconda3/envs/booking-room/bin/python openspec/changes/booking-order-lifecycle-refactor/verification/compare_redlist.py \
  openspec/changes/booking-order-lifecycle-refactor/verification/redlist-baseline.txt /tmp/redlist_phase2.txt
```
Expected: `REDLIST IDENTICAL`。这是 Phase 2（§13 Step 2）的核心验收判据：结构重构零行为变更。

- [x] **Step 3: 新增领域测试全绿**

Run:
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor/br-server
/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_booking_status.py tests/test_timezone.py tests/test_time_slots.py -q -p no:cacheprovider 2>&1 | tail -8
```
Expected: Task 2.1–2.3 新增的领域/工具测试**全绿**（它们不在基线红名单内，属新增绿灯，不破坏集合恒等）。

- [x] **Step 4: 标记 Phase 2 完成（无代码提交）**

Phase 2 验收通过后，无需额外提交（前 6 个 Task 已各自提交）。在本计划文件将 Phase 2 各 Task 的 `- [ ]` 勾选为 `- [x]`，并记录红名单比对输出截图/文本至 change 目录：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/.worktrees/booking-order-lifecycle-refactor
cp /tmp/redlist_phase2.txt openspec/changes/booking-order-lifecycle-refactor/verification/redlist-after-phase2.txt
git add openspec/changes/booking-order-lifecycle-refactor/verification/redlist-after-phase2.txt
git commit -m "chore: 归档 Phase 2 红名单比对证据（结构重构零行为变更）"
```

---

## Phase 3: 定时任务重构 + 时区收敛 + time_slots 接线（§13 Step 3）

> **本 Phase 不变量**：① 枚举值**仍为旧字面量**（Phase 4 才翻转）；② 验收 = 全量红名单集合恒等 **+** §11.2 新增断言通过；③ **代码级细节以 Design Doc 为事实源**（§5.1–§5.5 scheduler、§3.1 time_slots、§2.3 时区），本 Phase 只锁定任务边界、关键陷阱与验收命令，不重复展开已有伪代码。

### Task 3.1: order_status_scheduler 重构（§5.1–§5.5 + Q6 course_started 修正）

**Files:**
- Modify: `br-server/app/services/order_status_scheduler.py`（`:28-30` 时区入口、`:58` seat 调用签名、`:70-101` `_process_seat_booking`、`:164-184` `_process_course_booking`、`:187-211` `_update_highlight`、`:168` 注释）
- Test: `br-server/tests/test_order_status_scheduler_course.py`（5 处 `{}` stats → `_empty_stats()`；test #3 补 `course_started` 断言）

**Interfaces:**
- Consumes: Task 2.2 的 `resolve_seat_transition` / `resolve_course_transition` / `BookingStatus`；Task 2.1 的 `booking_now`
- Produces: `check_and_update_order_statuses` 返回的 `stats` 6 键名不变；`course_started` 由恒 0 变为真实计数（Q6 修正）；`_process_seat_booking` 签名由 `(session, booking, today, current_time, stats)` 改为 `(session, booking, now, stats)`

**关键陷阱（本 Task 的价值所在，务必遵守）：**
- **5 处 `{}` stats 测试必须与重构同一提交原子修复**：§5.2 修正后 `_process_course_booking` 在 `PENDING_START→IN_PROGRESS` 时执行 `stats["course_started"] += 1`、`_update_highlight` 无条件执行 `stats["course_highlight_updated"] += 1`；若测试仍传 `{}` 会 `KeyError` → 新增红灯 → 违反集合恒等。实测：**无任何测试断言 stats 计数值**，故把 `{}` 换成真实 6 键 dict 后，4 个测试仍全绿。
- **`elif` 单次转移语义保留**：`resolve_seat_transition` / `resolve_course_transition` 每次只返回一个转移（座位 `pending→confirmed` 不越级 `completed`；课程同理），与旧 `if/elif` 一致。
- **§5.4 `:119-145` 课时查询双路径逐字保留**（`schedule_id` 精确命中 + 旧订单 `course_id+lesson_ids+schedule_type` 回退）——这是刻意保留，**不是**可消除的重复代码。
- **§5.3 只改注释不改实现**：`:168` 注释「第一个 `lesson_date >= today`」与实现矛盾，实现正确口径是「最后一个 `lesson_date <= today`」，改注释/docstring 对齐实现。
- **§5.5 时区入口统一**：`:28-30` 改 `now = booking_now(settings.BOOKING_TIMEZONE)`（naive）、`today = now.date()`，删除 `current_time`；`_process_seat_booking` 内 `:79` 的 `datetime.combine(today, current_time)` 降级拼装删除，直接用传入的 naive `now`。
- **`main.py:113-122` 日志格式串不动**（§5.2）。

**Steps（精简）：**
- [x] **Step 1**：按 **Design §5.2 伪代码逐字采用**，把 `_process_seat_booking:89-101` 改为 `resolve_seat_transition` 驱动、`_process_course_booking:164-184` 改为 `resolve_course_transition` 驱动（`new_status is not None` 时写 `booking.status = transition.new_status.value` + `stats[transition.stat_key] += 1`；`COMPLETED` 时清 `highlighted_lesson_id`；`IN_PROGRESS or highlight_only` 时调 `_update_highlight`）。
- [x] **Step 2**：简化 `_update_highlight`——删除 `is_new_start` 参数与死分支 `elif is_new_start: stats["course_started"] += 1`（F5），保留 target_lesson 查找与 `highlighted_lesson_id != target` 时的 `course_highlight_updated += 1`；docstring 改为正确口径。
- [x] **Step 3**：`:168` 注释对齐实现；`:28-30` 时区入口改 `booking_now`，`:58` 调用改传 `now`，`_process_seat_booking` 签名与 `:79` 同步调整。
- [x] **Step 4**：`test_order_status_scheduler_course.py` 顶部加 `_empty_stats()` helper（返回 6 键全 0 dict），把 `:89,104,117,136,139` 的 5 处 `{}` 换成 `_empty_stats()`；test #3（`converts_on_start_date`）用命名 `stats` 变量并补 `assert stats["course_started"] == 1`（§11.2 Q6 回归断言，Phase 3 枚举值仍旧字面量故断 `booking.status == "confirmed"`）。
```python
def _empty_stats() -> dict:
    return {"total_scanned": 0, "seat_started": 0, "seat_completed": 0,
            "course_started": 0, "course_highlight_updated": 0, "course_completed": 0}
```
- [x] **Step 5**：验证——`pytest tests/test_order_status_scheduler_course.py -q` 全绿（含新增 `course_started` 断言）；再跑全量红名单比对（`redlist.sh` + `compare_redlist.py`），期望 `REDLIST IDENTICAL`。
- [x] **Step 6**：提交 `refactor: scheduler 改调 transition 纯函数 + course_started 计数修正（§5.2/Q6）`，正文说明 5 处 `{}` 测试原子修复、双路径保留、日志格式串不动。

### Task 3.2: 全仓时区实现收敛（§2.3 / line 110 / §10 guard #7）

**Files:** Modify 6 处 `CHINA_TIMEZONE` 定义改为 `from app.utils.timezone import CHINA_TIMEZONE`：`wallet_service.py:119`、`course_booking_service.py:26`、`coupon_service.py:42`、`admin_coupon_service.py:13`、`activity_service.py:25`、`seed_data.py:26`；`course_booking_service.py:49 _now_naive` → `booking_now`

**Interfaces:** Consumes Task 2.1 的 `app.utils.timezone.CHINA_TIMEZONE` / `booking_now`；Produces 链路内时区实现单一事实源。

**关键陷阱：**
- **只改导入源、不改返回语义**（line 110）——各处 `CHINA_TIMEZONE` 值恒等，仅去重。
- `seed_data.py:26` 是 `timezone(timedelta(hours=8))` **等价变体**（§12.2）：中国 1991 年后无 DST，与 `ZoneInfo("Asia/Shanghai")` 对所有业务日期等价，收敛前 `grep` 确认 seed_data 未涉及历史日期运算。
- `_booking_now`（Task 2.4）、`booking_cancellation_policy.booking_now`（Task 2.6）已在前序收敛，本 Task 只剩 `_now_naive` 与 6 处常量。
- `wallet/coupon/activity` 属订单链路外域，改动仅为常量导入替换；红名单比对兜底任何意外。

**Steps（精简）：**
- [x] **Step 1**：逐个把 6 处 `CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")` 替换为导入；`_now_naive()` 定义删除、调用点改 `booking_now(settings.BOOKING_TIMEZONE)`（先 `grep _now_naive` 确认调用点）。
- [x] **Step 2**：验证 §10 **guard #7**——`grep -rn 'def booking_now\|def _booking_now\|def _now_naive' br-server/app --include='*.py'` **只剩 `app/utils/timezone.py` 一处**；`grep -rn 'CHINA_TIMEZONE = ZoneInfo' br-server/app` 只剩 `app/utils/timezone.py`。
- [x] **Step 3**：全量红名单比对 `REDLIST IDENTICAL`；提交 `refactor: 时区实现收敛至 app.utils.timezone 单一事实源（§2.3）`。

### Task 3.3: time_slots 公用方法接线（§3.1）

**Files:** Modify `course_booking_service.py:478-486`（→ `build_time_slots_from_date`，连带消除 `:481` 函数内 `import json`）；`booking_service.py:1267-1291`（→ `parse_time_slots` + `rebuild_from_time_range`）

**Interfaces:**
- Consumes: Task 2.1 的 `parse_time_slots(raw: str | None) -> list[TimeSlot]`、`build_time_slots_from_date(*, booking_date: date, time_slot: str) -> str`、`rebuild_from_time_range(*, booking_date: date | None, start_time, end_time) -> str`、`TimeSlot(weekday: int, start: str, end: str)`
- Produces: 三处 time_slots JSON 构造/解析收敛为公用方法，输出 JSON 字符串**逐字节不变**

**关键陷阱：**
- **`booking_service:1284-1285` 的 weekday 注入必须在调用方保留**：`parse_time_slots` 对纯字符串数组历史格式返回 `weekday=None`（§14），而现逻辑给 str 项补 `lesson_date.isoweekday()`。接线时调用方需对 `weekday is None` 的项 backfill `lesson_date.isoweekday()` 再 dump，**否则下游 lesson 创建行为变更**。
- `:1288-1291` 空回退分支 → `rebuild_from_time_range(booking_date=lesson_date, start_time=booking.start_time, end_time=booking.end_time)`，输出与旧 `[{"weekday": isoweekday, "time_slot": "HH:MM-HH:MM"}]` 一致。
- **不迁移**（§3.1 Non-Goals）：`admin_course_service._find_next_slot_after`、老师排课域的 time_slots 处理。

**Steps（精简）：**
- [x] **Step 1**：`course_booking_service:478-486` 改 `booking_time_slots = build_time_slots_from_date(booking_date=booking_date, time_slot=data.time_slot)`，删 `:481 import json`。
- [x] **Step 2**：`booking_service:1267-1291` 改为 `parse_time_slots` + weekday backfill + 空则 `rebuild_from_time_range`，保持 dump 输出不变。
- [x] **Step 3**：验证——`pytest tests/test_time_slots.py tests/test_course_booking_service.py -q` + 定制订单确认相关测试全绿；全量红名单比对 `REDLIST IDENTICAL`；提交 `refactor: time_slots 构造/解析收敛至 app.utils.time_slots（§3.1）`。

### Task 3.4: Phase 3 验收

- [x] **Step 1**：确认枚举值仍旧字面量（`python -c "...BookingStatus.PENDING_START.value..."` 输出 `pending`）。
- [x] **Step 2**：全量 `pytest` + 红名单集合恒等比对；确认 §11.2 新增断言（`course_started` 自增、双路径各一例）通过。
- [x] **Step 3**：归档证据 `redlist-after-phase3.txt` 并提交 `chore: 归档 Phase 3 红名单比对证据`。

---

## Phase 4: 枚举值切换新词表 + 三端同步（§13 Step 4，BREAKING）

> **本 Phase 是唯一改变「取值」的 Phase**（前三 Phase 只动结构）。不变量/红线：
> 1. **原子性**：枚举值翻转 + 全部后端残留字面量 + **24 个测试文件 151 处**状态字面量必须**单一提交**；任何部分翻转的中间态都会大面积红。
> 2. **`.value` 不变量兑现**：因 Phase 2 所有写库/查询都走 `.value`，翻转 `booking_status.py` 枚举值后，服务层写点/筛选点**自动跟随新词表**，无需再改调用点。
> 3. **数据迁移是 Phase 5，本 Phase 只翻代码**。测试用 fresh SQLite（`create_all`），行以新字面量创建 → 自洽，红名单比对有效；生产按 §8.2 停服→迁移→部署。
> 4. **§10 六类跨域同名值不得波及**：`payment_status='pending'`（待支付）、`schedule_status='in_progress'`（排课域，`booking_service:531,1303`）、`WALLET_STATUS_TAGS.pending`（钱包域）、br-app 审核域 `accountSecurity.js:7` 与钱包域 `transactions.vue`。**7 条 grep 守卫全绿是硬验收**。
> 5. 代码级逐行改动以 **Design §9.1/§9.2/§9.3** 表为准，本 Phase 只列任务划分、原子边界与陷阱。

### Task 4.1: 后端枚举值翻转 + 残留字面量→枚举 + 24 测试文件原子更新

**Files:**
- Modify: `br-server/app/domain/booking_status.py`（`PENDING_START` 值 `"pending"`→`"pending_start"`；`IN_PROGRESS` 值 `"confirmed"`→`"in_progress"`；其余三个不变）
- Modify: `booking_rules.py:40,51`、`models/booking.py:32` default、`schemas/booking.py`、`api/routes/booking.py` `_BOOKING_STATUS` Literal、以及 §9.1 列出的 5 服务 + `study_record_service.py:54,168`、`user_security_service.py:224`、`study_room_service.py:204`、`seat_service.py:262`、`coupon_service.py:172` 的**订单域**裸字面量
- Modify: 24 个测试文件共 151 处状态字面量（§11.2）

**Interfaces:** Produces `BookingStatus.PENDING_START.value == "pending_start"`、`BookingStatus.IN_PROGRESS.value == "in_progress"`（COMPLETED/CANCELLED/PENDING_CONFIRM 值不变）。

**关键陷阱：**
- **原子提交**：枚举翻转、后端字面量、151 测试字面量缺一不可，必须同一 `git commit`（否则红名单大面积变动）。
- **§10 跨域同名值不动**：尤其 `booking_service:531,1303` 的 `schedule_status='in_progress'`（排课域）、各处 `payment_status='pending'`（待支付域）——guard #1/#2 验证未被误改。
- **虚拟状态是稳定 API 契约**（§2.6）：`?status=in_progress` / `?status=pending_start` 查询参数串**不变**；翻转后 DB 真实状态与虚拟状态同形，`build_status_filter_conditions` 的分派逻辑已在 Phase 2 写好，无需改。`_BOOKING_STATUS` Literal 需含新值。
- **None 兜底与边界运算符（`<=`/`>=`）已在 Phase 2 固化到纯函数**，翻转值不影响判定逻辑。

**Steps（精简）：**
- [x] **Step 1**：翻转 `booking_status.py` 中 `PENDING_START` / `IN_PROGRESS` 两个枚举值（仅此两行）。
- [x] **Step 2**：后端残留裸字面量→枚举引用：`grep -rn '"pending"\|"confirmed"' br-server/app --include='*.py'` 逐处判定**订单域 vs 跨域**（订单域→枚举；`payment_status`/`schedule_status`/alembic→不动），覆盖 `booking_rules:40,51`、`models:32`、`schemas`、`routes` Literal、各服务比较点（§9.1 表）。
- [x] **Step 3**：24 测试文件 151 处状态字面量→新词表（`grep -rln '"pending"\|"confirmed"' br-server/tests` 驱动，逐文件排除 `payment_status`/`schedule_status` 断言）。
- [x] **Step 4**：验证——§10 **guard #1/#2/#4** 全绿；全量 `pytest` + 红名单集合恒等（`REDLIST IDENTICAL`）；`python -c "...PENDING_START.value..."` 输出 `pending_start`。
- [x] **Step 5**：**单一原子提交**（`feat!: 订单状态词表切换 pending→pending_start、confirmed→in_progress（BREAKING）`），正文标注枚举+后端字面量+151 测试字面量同提交、跨域值未动。

### Task 4.2: br-admin 6 处 3 文件（§9.3）

**Files:** Modify `br-admin/src/views/business/shared/options.ts:41,42,55,56`（`value:'pending'`→`'pending_start'`、`value:'confirmed'`→`'in_progress'`、`BOOKING_STATUS_TAGS` 键同步）；`views/booking/list/index.vue:72,139`（`isCoursePendingStart` 与取消按钮判定）

**关键陷阱：**`options.ts:86 WALLET_STATUS_TAGS.pending`（label「待处理」）**不在重命名范围**（guard #3）；`views/booking/list/builders.ts:formatTimeSlots` 保留（§3.2）。

**Steps（精简）：**
- [x] **Step 1**：按 §9.3 表改 6 处；guard #3 `grep -n 'pending' options.ts` 确认 `WALLET_STATUS_TAGS.pending` 未变。
- [x] **Step 2**：`cd br-admin && pnpm install && pnpm run build`（§11.3：worktree 中 node_modules 缺失）构建通过；提交 `refactor(br-admin): 订单状态词表同步 pending_start/in_progress（§9.3）`。

### Task 4.3: br-app 订单域 12 处 4 文件（§9.2）

**Files:** Modify `br-app/src/constants/booking.js`（`BOOKING_STATUS_LABELS` 删 `pending:'待支付'`+`confirmed:'已预约'` 旧键，**新增 `PAYMENT_STATUS_LABELS`**）；`pages/orders/index.vue`（删 `displayStatus()`、`statusLabel()` 去 `confirmed` 特例+**Q13 前置分支**、`isOrderStarted`/`isOrderPendingStart` 收敛、删 `TABS`/`STATUS_MAP`/`ZONE_MAP` 死代码、取消按钮 `v-if :209,216,223` 改 `order.status`）；`pages/verify-booking/index.vue:150-164`（`statusText`）；`utils/formatters.js`、`course-booking/*.vue`、`booking/seat-select.vue`、`study-record/index.vue` 字面量

**关键陷阱：**
- **Q13 顺序不可颠倒**：**先**给 `statusLabel()` 加 `order.payment_status === 'pending'` → `PAYMENT_STATUS_LABELS.pending`（「待支付」）**前置分支**，**再**删 `BOOKING_STATUS_LABELS.pending` 键；否则未支付订单标签从「待支付」退化为「待开始」（用户可见语义倒退，F23）。
- **`displayStatus ≡ status` 恒等**（§2.7 逐分支已证）→ 删除，模板/按钮直接消费 `order.status`；`isOrderStarted` 收敛为 `order.status === 'in_progress'`（`started===true` 分支对座位永不成立，§14）；`isOrderPendingStart` 收敛为对 `order.status` 直接判定，SHALL NOT 保留旧词表比较。
- **域外 7 处不改**：`accountSecurity.js:7`（审核域 guard #5）、`wallet/transactions.vue:279,290,333`（钱包域）。
- **`:223`** 改 `!(isCourseBooking(order) && order.status === 'pending_start')`，与长期记忆「仅管理端可取消课程待开始订单」一致（§9.2）。

**Steps（精简）：**
- [x] **Step 1**：`constants/booking.js` 新增 `PAYMENT_STATUS_LABELS`；`orders/index.vue` 按 §9.2 表删 `displayStatus`、加 Q13 前置分支、收敛 `isOrderStarted`/`isOrderPendingStart`、删 3 死代码常量、改取消按钮 `v-if`；`verify-booking` `statusText` 字面量改新词表（内联时间窗口判定与后端 `resolve_verification_status` 同口径）。
- [x] **Step 2**：guard #5（`accountSecurity.js:7 'pending'` 未动）、guard #6（`orders/index.vue` 不再含 `displayStatus`/`TABS`/`STATUS_MAP`/`ZONE_MAP`）全绿。
- [x] **Step 3**：`cd br-app && npm run build:h5` 构建通过；提交 `refactor(br-app): 订单状态词表同步 + 删 displayStatus 死代码 + Q13 待支付前置分支（§9.2）`。

### Task 4.4: Phase 4 验收（§10 7 守卫全绿 + 红名单恒等）

- [x] **Step 1**：逐条跑 **Design §10 的 7 条 grep 守卫**，全绿（#1 payment_status 未波及、#2 schedule_status in_progress 未动、#3 WALLET_STATUS_TAGS.pending 未动、#4 br-server app/ 无裸订单状态字面量、#5 br-app 审核/钱包域未动、#6 orders 无 4 死标识符、#7 时区实现已收敛）。
- [x] **Step 2**：全量 `pytest` + 红名单集合恒等（`REDLIST IDENTICAL`）；br-admin `pnpm run build` + br-app `npm run build:h5` 两端构建通过。
- [x] **Step 3**：归档证据 `redlist-after-phase4.txt` + grep 守卫输出，提交 `chore: 归档 Phase 4 验收证据（grep 守卫全绿 + 红名单恒等）`。

---

## Phase 5: alembic 数据迁移 + 管理端会话有效期 + 前端 expires_in（§13 Step 5）

> **本 Phase 与红名单恒等解耦**：前四 Phase 是代码重构（跑 pytest 验收），本 Phase 是**数据迁移 + 会话配置**——验收口径改为「离线渲染 SQL 核对 + 两端构建」（§13 Step 5），因测试用 `create_all` 不跑 alembic（§8.4），迁移**零自动化覆盖**，必须人工离线核对。
> 顺序不可提前：数据迁移必须在 Phase 4 代码词表翻转**之后**（否则新旧值混存）。生产发布按 §8.2「停服优先于迁移」6 步（`ORDER_STATUS_CHECK_INTERVAL_SECONDS=300` 事故教训，F17）。

### Task 5.1: alembic 迁移脚本（§8.1）

**Files:**
- Create: `br-server/alembic/versions/<YYYY_MM_DD_HHMM>-<new>_rename_booking_status.py`（沿用既有文件名约定，当前 head `f6a7b8c9d0e1`，共 46 迁移）

**Interfaces:** `revision='<new>'`、`down_revision='f6a7b8c9d0e1'`；`upgrade()` 两条 UPDATE（`status='pending'→'pending_start'`、`status='confirmed'→'in_progress'`），`downgrade()` 反向。

**关键陷阱（§8.1）：**
- **只触 `status` 列，绝不碰 `payment_status`**（其 `pending` 语义为「待支付」，跨域同名值）。
- **幂等**：WHERE 只命中旧值，重跑无副作用（支持新旧混存后收敛）。**方言中立**：纯 SQL UPDATE 在 PostgreSQL（生产）与 SQLite（测试）均可执行。**零 DDL**：`status` 为裸 `String(20)`，无 enum/CHECK，新值最长 13 字符（F7）。

**Steps（精简）：**
- [x] **Step 1**：`cd br-server && alembic revision -m "rename booking status"` 生成骨架，填 `down_revision='f6a7b8c9d0e1'`，按 §8.1 写 `upgrade`/`downgrade`（各 2 条 `op.execute` UPDATE，显式限定 `status` 列）。
- [x] **Step 2**：离线渲染核对（§8.4）——`alembic upgrade f6a7b8c9d0e1:<new> --sql` 与 `alembic downgrade <new>:f6a7b8c9d0e1 --sql`，核对生成 SQL **只 UPDATE `status` 列**、不含 `payment_status`；`alembic heads` 确认单一 head。
- [x] **Step 3**：提交 `feat(alembic): 订单状态数据迁移 pending→pending_start、confirmed→in_progress（§8.1）`，正文标注幂等/方言中立/零 DDL/不碰 payment_status。

### Task 5.2: 管理端会话有效期后端（§7.2 项 1/2/3/5）

**Files:**
- Modify: `br-server/app/core/config.py`（新增 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS: int = 7`）
- Modify: `br-server/app/services/admin_auth_service.py:41`（`exp` 改 `timedelta(days=settings.ADMIN_ACCESS_TOKEN_EXPIRE_DAYS)`）
- Modify: `br-server/app/api/routes/admin_auth.py:30`（`expires_in = settings.ADMIN_ACCESS_TOKEN_EXPIRE_DAYS * 86400`）
- Modify: `br-server/.env.example`（补新配置项说明）

**关键陷阱（§7.1/§7.2）：**
- **`ACCESS_TOKEN_EXPIRE_MINUTES=15` 保持不变**——它被 C 端与管理端**共用 4 处**（`admin_auth.py:30`、`admin_auth_service.py:41`、`auth_service.py:45,227`、`jwt_service.py:30`）；直接调大会把 C 端 br-app 令牌一并拉长到 7 天，放大设备丢失风险。故**新增独立 `ADMIN_` 配置**，只改管理端 2 处。
- `ADMIN_` 前缀与既有 `ADMIN_TOKEN`/`ADMIN_DEFAULT_USERNAME` 等命名约定一致；JWT `exp` 用 UTC（`datetime.now(UTC)`）不变，与业务时区 Asia/Shanghai 解耦。
- **取 7 天**：满足用户「至少三天以上」，与前端现状 `7*24*60*60` 对齐；管理端无 refresh 链路，不存在 access>refresh 倒挂。

**Steps（精简）：**
- [x] **Step 1**：按 §7.2 表改 4 处（config 新增键、`admin_auth_service.py:41` exp、`admin_auth.py:30` expires_in、`.env.example`）。
- [x] **Step 2**：验证——管理端登录响应 `expires_in == 604800`；`grep -rn 'ACCESS_TOKEN_EXPIRE_MINUTES' br-server/app` 确认 C 端 4 处引用未动；全量 `pytest` 红名单恒等。
- [x] **Step 3**：提交 `feat(admin-auth): 管理端会话有效期 15 分钟→7 天（ADMIN_ACCESS_TOKEN_EXPIRE_DAYS，§7.2）`。

### Task 5.3: br-admin 前端 expires_in 读取（§7.2 项 4）

**Files:** Modify `br-admin/src/store/modules/user.ts:69,95`（硬编码 `7 * 24 * 60 * 60` 改读后端 `result.expires_in`，带兜底）

**关键陷阱（§7.1）：** 前端**非瓶颈**（`user.ts:69` 已存 7 天、`Storage.ts:32,49` 证实 7 天内不丢弃，`expires_in=900` 前端根本没读）；本项是需求②「单一事实源」在会话有效期上的应用——有效期由后端单点定义，前端不再持有第二份常量。兜底防 `expires_in` 缺失时退回默认值。

**Steps（精简）：**
- [x] **Step 1**：`user.ts:69,95` 改读 `result.expires_in`（`?? 7*24*60*60` 兜底）。
- [x] **Step 2**：`cd br-admin && pnpm install && pnpm run build`（§11.3：worktree node_modules 缺失需先 install）构建通过；提交 `refactor(br-admin): 会话有效期改读后端 expires_in（单一事实源，§7.2）`。

### Task 5.4: Phase 5 验收 + 发布顺序固化

- [x] **Step 1**：alembic 双向离线渲染 SQL 核对（只触 `status` 列）+ `alembic heads` 单一 head（§8.4）。
- [x] **Step 2**：br-admin `pnpm run build` + br-app `npm run build:h5` 两端构建通过；全量 `pytest` 红名单集合恒等（迁移不影响 fresh SQLite 测试）。
- [x] **Step 3**：将 §8.2「停服优先」发布 6 步（备份→**停全部后端进程**→`alembic upgrade head`→启新后端核对单进程→发布两端→验证 `SELECT DISTINCT status` 无旧值）与 §8.3 回滚序写入交付说明；提交 `chore: 归档 Phase 5 验收证据（迁移离线渲染 + 两端构建 + 发布顺序）`。

---

## Phase 6: 文档与 delta spec 同步 + 执行交接（§13 Step 6）

> 收尾 Phase：**无代码逻辑改动**，验收口径为「文档与实现一致」（§13 Step 6）。四块：项目文档更新 + delta spec 回写 + tasks.md 基线数修正 + 长期记忆更新。

### Task 6.1: 项目文档更新

**Files:**
- Modify: `docs/booking-rules.md`（**注意在 repo 根 `docs/`，非 `br-server/docs/`**）——状态词表更新为 `pending_start`/`in_progress` 新语义，取消/完成/核销判定口径对齐领域纯函数
- Modify: `docs/api.md`——订单状态字段枚举值、`?status=in_progress`/`?status=pending_start` 虚拟状态查询契约**不变**说明、管理端登录 `expires_in=604800`
- Modify: `bug-fixed.md`——按既有格式追加本次修复的缺陷条目（Q6 `course_started` 死分支自增、Q13 待支付标签退化 F23、时区 aware/naive 收敛 F19/F21 等）

**关键陷阱：**`api.md` 须明确「DB 真实状态词表翻转，但 `?status=` API 契约稳定」（§2.6 虚拟状态是稳定契约）；`booking-rules.md` 路径易错（`docs/` 根）。

**Steps（精简）：**
- [x] **Step 1**：更新 3 文档（booking-rules 词表+判定口径、api 枚举值+虚拟状态契约+expires_in、bug-fixed 追加缺陷条目）。
- [x] **Step 2**：交叉核对文档与 Design §2/§4/§7 一致；提交 `docs: 同步订单状态词表与生命周期规则（booking-rules/api/bug-fixed）`。

### Task 6.2: delta spec 回写 + tasks.md 基线数修正

**Files:**
- Verify/Modify: 9 个 delta spec `openspec/changes/booking-order-lifecycle-refactor/specs/*/spec.md`（admin-auth-api、booking-admin-api、booking-admin-ui、booking-status-domain、booking-verification-api、course-booking-api、course-booking-ui、study-room-booking-api、study-room-booking-ui）
- Modify: `openspec/changes/booking-order-lifecycle-refactor/tasks.md:12,78`（「95 项」→「96 项」）

**关键陷阱：**
- **95→96 必须同改两处**（§1.5 line 12 与 §8.7 line 78）。依据 `BASELINE.md`：Design 记 `14 failed + 81 errors = 95`，实测红名单基线 **96 项**，差的 1 项为**挂钟敏感核销域项**（Q12 在本次重构范围内，不得当作无关忽略）。
- delta spec 重点核对：`booking-status-domain`（词表值 `pending_start`/`in_progress`）、`admin-auth-api`（`expires_in=604800`）、`booking-verification-api`（Q12 核销域）。

**Steps（精简）：**
- [x] **Step 1**：核对 9 delta spec 与实现一致（重点上列 3 个），不一致处回写。
- [x] **Step 2**：tasks.md line 12 与 line 78 的「95」→「96」，并注明挂钟敏感项按 BASELINE.md 边界规则复核。
- [x] **Step 3**：提交 `docs(openspec): delta spec 回写 + tasks 基线数 95→96 修正（对齐 BASELINE.md）`。

### Task 6.3: 长期记忆更新（§15，实现落地后执行）

> 记忆更新必须在词表翻转落地**后**执行，否则记忆与实际不符。

**Steps（精简）：**
- [x] **Step 1**：更新记忆「订单虚拟状态 pending_start 的过滤模式与实现规范」（§15.1）——`in_progress` 实测为 `status='in_progress'`（新词表）`AND payment_status='paid'` + 课程附加 `CourseSchedule.start_date <= today`、座位**不做**二次过滤（原记忆误记 `started=true` / `now >= date+end_time`）。
- [x] **Step 2**：修正记忆「Admin 预约列表时段列格式化规范」第 3 种格式（§15.2）——实测兼容 `["HH:MM-HH:MM"]` 纯字符串数组与 `{weekday,start,end}` 拆分格式（原记忆误记 `[{start,end}]` 无星期）。
- [x] **Step 3**：§15.3（F11 跨端同名参数语义不一致）、§15.4（95 项既有红灯为独立测试债务）确认为已知遗留、不在本 change 范围（已记录于 Design/tasks，无需新增记忆）。

### Task 6.4: 全量收尾验收 + comet verify 交接

- [x] **Step 1**：全量 `pytest tests/ -q --tb=no` + 红名单集合恒等（**96 项**，挂钟敏感项按 BASELINE.md 边界规则复核）。
- [x] **Step 2**：§10 7 守卫全绿复跑；br-admin `pnpm run build` + br-app `npm run build:h5` 两端构建通过。
- [x] **Step 3**：确认 tasks.md 全部 checkbox 完成、9 delta spec 与实现一致、3 文档同步；本 change 6 Phase 全部完成 → 交接 **comet-verify** 阶段。

---

## Execution Handoff

计划已完成并保存至 `docs/superpowers/plans/2026-09-03-booking-order-lifecycle-refactor.md`（Phase 0–6）。

> **comet-build 上下文：**本计划通过 `comet state set booking-order-lifecycle-refactor plan <path>` 注册后，由 **comet-build Step 2 联合决策**（继续/暂停 + isolation + build_mode + tdd_mode + review_mode + 分支名）驱动执行，**不**直接走 writing-plans 默认的 subagent/inline 二选一。执行阶段 REQUIRED SUB-SKILL：subagent-driven-development（推荐）或 executing-plans，由 Step 2 的 build_mode 决定。

**阶段依赖链（不可乱序）：**Phase 0（基线）→ Phase 1（死代码/命名）→ Phase 2（领域层+utils，枚举值旧字面量）→ Phase 3（定时任务+时区+接线）→ Phase 4（枚举值翻转+三端，BREAKING）→ Phase 5（迁移+会话有效期）→ Phase 6（文档+spec+记忆）。每 Phase 末尾以红名单集合恒等（Phase 5 除外，走离线渲染+构建）闸门。
