# 发布与回滚说明（booking-order-lifecycle-refactor）

> 本 change 是 **BREAKING 取值变更**：订单状态词表 `pending→pending_start`、`confirmed→in_progress` 三端同步翻转，并含一条 `bookings.status` 数据迁移（`a33171f2c2fb`）。
> **迁移零自动化覆盖**：测试用 `create_all` 建表、不跑 alembic（`tests/conftest.py`），故迁移仅靠离线渲染 SQL 人工核对（见文末验收证据）。生产发布务必按本说明执行。

## 一、发布顺序：停服优先于迁移（不可调换）

**根因（F17，真实事故教训）**：`bug-fixed.md` 记录「数据还原后约一个调度周期（5 分钟内）订单即被旧进程再次改写为 `confirmed`」，与 `ORDER_STATUS_CHECK_INTERVAL_SECONDS` 默认 **300 秒** 完全吻合。若先迁移再停旧进程，旧后端会在迁移后继续按旧词表写入 `pending`/`confirmed`，制造新旧值混存。

1. **备份** `bookings`（至少含 `id, status, payment_status, booking_type, schedule_id, highlighted_lesson_id` 快照）。
2. **停止全部后端进程**，`ps` 核对确认无残留（含定时任务进程）。
3. `alembic upgrade head`（推进到 `a33171f2c2fb`）。
4. **启动新后端**，再次 `ps` 核对**只有一个进程**在跑。
5. **发布两端**：br-admin（`pnpm run build`）、br-app（`npm run build:h5`）。
6. **验证**：新建座位/课程订单、管理员确认定制订单、等一个调度周期看定时推进、取消退款各走一遍；抽查 `SELECT DISTINCT status FROM bookings` **无 `pending`/`confirmed` 旧值残留**。

## 二、回滚顺序

1. **三端代码** `git revert`；分支 `feature/20260902/booking-order-lifecycle-refactor` 未合并则直接不合并。
2. **数据** `alembic downgrade -1`（`a33171f2c2fb→f6a7b8c9d0e1`，反向 UPDATE，仅触 `status` 列）。
3. **管理端会话有效期** 是独立配置（`ADMIN_ACCESS_TOKEN_EXPIRE_DAYS`），改回配置值即可，**无数据影响**。
4. 回滚后运行订单生命周期测试，并用 `alembic downgrade --sql` 离线渲染确认脚本可执行。

## 三、迁移脚本安全属性（§8.1）

- **只触 `status` 列，绝不碰 `payment_status`**（其 `pending` 语义为「待支付」，跨域同名值）。
- **幂等**：`WHERE` 只命中旧值，重跑无副作用，可在新旧值混存后重跑收敛。
- **方言中立**：纯 SQL `UPDATE` 在 PostgreSQL（生产）与 SQLite（测试）均可执行。
- **零 DDL**：`status` 为裸 `String(20)`，无 enum/CHECK 约束，新值最长 13 字符。

## 四、Phase 5 验收证据

- **迁移双向离线渲染**（`verification/` 外的 §8.4 核对）：`alembic upgrade f6a7b8c9d0e1:a33171f2c2fb --sql` 与 `alembic downgrade a33171f2c2fb:f6a7b8c9d0e1 --sql` 生成 SQL **仅 UPDATE `status` 列**、不含 `payment_status`；`alembic heads` 单一 head `a33171f2c2fb`。
- **后端红名单集合恒等**：`verification/redlist-after-phase5.txt`（95 项 @17:17）vs `redlist-baseline.txt`（96 项，挂钟敏感项归一化扣除）→ `compare_redlist.py` **PASS**（管理端会话有效期改动无测试断言 expires_in，行为对测试零影响）。
- **两端构建**：br-admin `pnpm run build`（vite，23.70s）、br-app `npm run build:h5`（uni build）均通过。
- **提交链**：`1b03133`（迁移）→ `71cc543`（管理端会话后端）→ `694f733`（br-admin expires_in）→ 本说明归档提交。
