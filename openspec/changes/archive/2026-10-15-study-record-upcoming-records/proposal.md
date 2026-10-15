# Proposal: study-record-upcoming-records

## Why

学习记录页当前只展示"已学习"记录（completed/in_progress 订单及已过日期的课程课时）。用户无法在日历和列表中看到"未开始"的安排：待开始/进行中订单中的自习室预约与课程课时。历史上该能力曾实现后于 edce77e 被简化移除，本次基于现行"单一口径"架构重新引入。

## What Changes

- 后端：记录收集扩展出 upcoming 集合——自习室 pending_start 订单（已支付）产生未开始记录；pending_start/in_progress 课程订单中未到日期的课时产生未开始记录。`GET /api/v1/study-records` 默认返回 已学习+未开始 合并列表（status 参数 completed/upcoming 可单选），summary 的 `calendar_mark.upcoming` 标记未开始日期。
- 前端：记录列表拆分为"学习记录"（已学习）与"学习计划"（未开始）两个 Tab，分别按 `status=completed/upcoming` 请求；日历为未开始日期显示橙色圆点（图例新增"未开始"）；课程记录图标已学习为绿色、未开始为橙色；状态标签"已学习"（绿）/"未开始"（橙）；点击日期过滤对未开始日期同样可用（取消未来日期不可点限制），并按日期是否晚于今日自动切换 Tab。

## Scope

- br-server：`app/services/study_record_service.py`（路由 `date/status` 参数已存在，无需改动）
- br-app：`src/pages-sub/study-record/index.vue`

## Out of Scope

- 顶部统计卡片口径不变（仍只统计已学习；monthly_upcoming_* 字段保持 0）
- 不改数据库 schema、不新增接口
