# arrival-reminder-notification 验证报告

- 日期：2026-11-25
- 流程：tweak（classic），verify_mode=full
- 验证语言：zh-CN

## 总结

| 维度 | 结果 |
|------|------|
| 完整性 | 14/14 任务完成；2 个 delta spec 能力（message-notification-api、message-notification-ui） |
| 正确性 | 所有需求在代码中均有实现；后端 17 个通知相关测试通过 |
| 一致性 | 实现符合 change design.md；与既有 2026-05-28 通知设计无矛盾 |
| 构建 | pytest + br-admin 构建 + br-app 距离单测 + mp-weixin/h5 构建全部通过 |

## 验证项

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | tasks.md 全部完成 | PASS | 14/14 勾选 |
| 2 | 实现符合 change design.md | PASS | 公共发送方法、默认目标、500 米门槛、24 小时去重、前端静默触发均按设计落地 |
| 3 | 实现符合 Design Doc | PASS | 既有 `docs/superpowers/specs/2026-05-28-message-notification-frontend-backend-design.md` 的跳转规则保持；本次为新增能力，由 change design.md 记录 |
| 4 | 能力规格场景通过 | PASS | 见下方场景映射 |
| 5 | proposal 目标满足 | PASS | 公共发送方法、到店提醒接口、详情页触发、消息跳转均已完成 |
| 6 | delta spec 与 design 无矛盾 | PASS | delta spec 在 open 阶段与 design.md 同步产出，Build 未增量修改 spec |
| 7 | 关联设计文档可定位 | PASS | 2026-05-28 通知前后端设计文档存在；change 级 design.md 存在 |

## 场景覆盖映射

message-notification-api：

- 默认 target_url 回填：`test_send_notification_fills_default_target`
- 偏好关闭不发送：`test_send_notification_skips_disabled_preference`、`test_arrival_reminder_respects_disabled_preference`
- 500 米内发送：`test_arrival_reminder_sends_when_within_500_meters`
- 超距不发送：`test_arrival_reminder_skips_when_too_far`
- 24 小时去重：`test_arrival_reminder_deduplicates_within_24_hours`
- 房间无坐标：`test_arrival_reminder_skips_room_without_coordinates`
- 鉴权与归属：`test_arrival_reminder_requires_authentication`
- 不支持的 type：`_validate_type` 拒绝（既有实现）

message-notification-ui：

- ≤500 米触发、>500 米不触发、无定位不触发、游客不触发、单次进入只触发一次：`br-app/src/pages/booking/detail.vue` 的 `loadRealDistance` / `maybeSendArrivalReminder` 与 `src/utils/notification.js` 的登录判断
- 非会话消息点击跳转：`src/pages-sub/notifications/index.vue` 的 `openNotification` → `navigateToTarget`（target_url 优先，类型默认目标兜底）
- 会话条目独立路由：`openConversation`

## 执行证据

- `comet check run arrival-reminder-notification verify --local -- sh -c "..."`：exit=0（pytest 3 个既有测试文件 + br-admin 构建 + br-app test:distance + mp-weixin/h5 构建）
- 通知专项测试：`pytest tests/test_notification_send.py tests/test_api_notifications.py -q` → 17 passed
- 变更范围：`git diff --stat d5f1a41...HEAD` → 16 个文件（9 个交付文件 + 7 个 change 产物）

## 未执行项说明

- 集成代码审查：`.comet.yaml` 的 `review_mode=off`（tweak 预设默认），按 Verify 规则跳过自动代码审查，改为人工核对最终 diff、tasks.md 与测试结果。
- 真机/小程序运行时验证：本环境无法启动微信开发者工具做真机定位与点击验证；已通过构建、单测与代码路径核对覆盖。后续可在真机确认定位授权后到店提醒的端到端表现。

## 问题

### CRITICAL

无。

### WARNING

无。

### SUGGESTION

1. 前端到店触发目前只有代码路径核对，没有自动化脚本；可在后续迭代补充基于 `verify-*.js` 风格的触发条件自检。
2. 不支持的 `type` 仅由既有 `_validate_type` 覆盖，没有专门用例；不影响本次行为。

## 结论

无 CRITICAL/WARNING。实现与 delta spec、design.md 一致，测试与构建全部通过，可以进入归档确认。
