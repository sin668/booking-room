# 红名单基线（build 阶段实测）

- 采集时间：2026-09-03 09:15 (Asia/Shanghai) —— **11:00 之前**的挂钟桶
- 采集命令：`pytest tests/ -q --tb=no -p no:cacheprovider`
- 结果：**15 failed / 750 passed / 16 skipped / 81 errors**（126.14s）
- 红名单条目数：**96**（见 `redlist-baseline.txt`）

## 与 Design Doc §11.1 记录的差异

Design Doc 记录 `14 failed / 751 passed / 16 skipped / 81 errors`（114.44s）= **95 项**，
采集于 2026-09-02 **11:00 之后**。差异的 1 项是：

```
tests/test_booking_verification_service.py::test_issue_verification_token_for_future_booking_returns_token
```

## 该项为挂钟敏感（确定性探针实测）

`_select_nearest_booking`（`booking_verification_service.py:383-413`）按三档排序：
档 0 = 在核销窗口内、档 1 = 未来、档 2 = 已过。fixture `verification_data` 中
`pending_paid` 固定为「今天 09:00-11:00 / status=pending / payment_status=paid」，
按 F22 属**可核销**；测试把 `confirmed` 改到明天 00:00-23:59 后：

| 本地时间 | pending_paid 档位 | confirmed 档位 | 选中 | 结果 |
|---|---|---|---|---|
| ≤ 11:00 | 0 或 1（均优于 confirmed） | 1 | id=4 | **FAIL** |
| > 11:00 | 2（已过） | 1 | id=1 | PASS |

探针实测边界：`now=11:00` → FAIL，`now=11:01` → PASS（`VERIFICATION_EARLY_ARRIVAL_MINUTES = 30`）。

## 对验收判据的影响

「红名单集合恒等」**不能**跨挂钟桶直接比对。执行期必须：
1. 在同一个挂钟桶内成对采集「基线」与「候选」红名单；或
2. 若两次采集跨越本地 11:00 边界，且差集恰为上述单项，则按边界规则复核后判定为等价。

该项落在核销域（Q12 本次重构范围内），因此**不得**当作「与订单生命周期无关」忽略。
