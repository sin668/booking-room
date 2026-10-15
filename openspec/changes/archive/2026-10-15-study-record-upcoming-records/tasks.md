# Tasks: study-record-upcoming-records

## 1. 后端未开始记录收集

- [x] 1.1 `_collect_items` 返回 studied+upcoming 双集合（自习室 pending_start、课程未完成课时）
- [x] 1.2 summary 的 `calendar_mark.upcoming` 填充未开始日期；list 支持合并/按 status 过滤

## 2. 前端未开始展示与过滤

- [x] 2.1 日历橙点标记未开始日期 + 图例新增"未开始"
- [x] 2.2 记录列表拆分为"学习记录/学习计划"双 Tab（status=completed/upcoming）；状态标签与课程图标按状态配色（已学习绿/未开始橙）；点击日期过滤放开未来日期并按日期自动切换 Tab

## 3. 验证

- [x] 3.1 后端测试：新增未开始记录/日历标记/status 过滤用例，全量通过
- [x] 3.2 br-app 构建通过（build:mp-weixin）

## 4. 用户增量调整（2026-10-15）

- [x] 4.1 记录列表拆分为"学习记录/学习计划"双 Tab，按 status=completed/upcoming 请求
- [x] 4.2 未开始配色统一为橙色（日历点/图例/状态标签/课程图标），已学习课程图标改绿色
- [x] 4.3 点击日历日期自动切换 Tab（今日及未来→学习计划，过去→学习记录）
