# Proposal: study-record-in-progress-plan

## Why

现行口径把「进行中」（in_progress）自习室订单整体视为已学习：记录显示在「学习记录」Tab 并计入顶部统计；进行中课程订单的未完成课时也标为橙色「未开始」。用户确认的新口径：进行中的安排属于"学习计划"而非已完成学习——进行中自习室订单应移入「学习计划」Tab 且不计入顶部统计；进行中订单产生的计划记录右上角显示绿色「进行中」标签（区别于橙色「未开始」）。

## What Changes

- 后端 `study_record_service`：进行中自习室订单从 studied 集合移入 upcoming 集合，记录 status 取 `in_progress`（顶部统计随之不再计入进行中的自习室时段）；进行中课程订单的未完成课时记录 status 由 `upcoming` 改为 `in_progress`（已完成课时仍计入学习记录与统计，不变）；`status=upcoming` 过滤返回全部计划记录（未开始+进行中）。
- 前端学习记录页：「学习计划」Tab 对 `record.status === 'in_progress'` 显示绿色「进行中」标签（课程图标绿色），未开始保持橙色；Tab 请求参数与日历橙点口径不变（进行中日期本就来自 upcoming 集合）。

## Scope

- br-server：`app/services/study_record_service.py` + 相关测试（路由与 schema 无需改动）
- br-app：`src/pages-sub/study-record/index.vue`

## Out of Scope

- 已完成课程订单的历史课时统计口径不变
- 不改数据库 schema、不新增接口、不改 status 查询参数取值
