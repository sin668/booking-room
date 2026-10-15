# Proposal: study-record-date-filter

## Why

学习记录页（br-app `/pages-sub/study-record/index`）的日历仅做展示：已学习日期有绿点标记，但点击日期无任何交互，用户无法快速查看某一天的学习记录，只能在整月列表里翻找。

## What Changes

- 后端 `GET /api/v1/study-records` 新增可选 `date` 查询参数（格式 YYYY-MM-DD），返回该日期的学习记录，与现有 `month` 过滤同为 Python 层按记录实际日期过滤。
- 前端日历日期可点击：点击某天即过滤显示当天学习记录并高亮选中日期；再次点击同一天取消过滤，恢复整月列表；切换月份时清除选中状态。

## Scope

- br-server：`app/api/routes/study_record.py`、`app/services/study_record_service.py`
- br-app：`src/pages-sub/study-record/index.vue`

## Out of Scope

- 不改动月度统计 summary 接口与统计口径
- 不改动日历标记（绿点/今日）既有展示逻辑
