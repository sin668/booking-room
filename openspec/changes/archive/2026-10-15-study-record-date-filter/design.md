# Design: study-record-date-filter

## 实现说明

后端：`list_study_records` 已在 Python 层按 `item.date` 做月份过滤（study_record_service.py:349-353），沿用同一模式新增 `record_date: date | None` 参数，过滤 `item.date == record_date`；路由新增 `date: date | None = Query(None)`（FastAPI 自动解析 YYYY-MM-DD），直接透传。

前端：新增 `selectedDate` ref（`YYYY-MM-DD` 字符串，null 表示不过滤）。日历 `day-inner` 绑定 `@tap`，点击非未来日期时切换选中（再次点击同一天置 null），`fetchRecords` 在选中时附加 `date` 参数并 reset 分页。选中日期加 `day-selected` 高亮样式，`prevMonth`/`nextMonth` 中清除 `selectedDate`。

复用既有分页、加载与空态逻辑，不新增组件与依赖。
