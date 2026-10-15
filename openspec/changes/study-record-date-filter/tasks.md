# Tasks: study-record-date-filter

## 1. 后端日期过滤

- [x] 1.1 `study_record_service.list_study_records` 新增 `record_date` 参数并按记录日期过滤
- [x] 1.2 `study_record.py` 路由新增 `date` 查询参数并透传

## 2. 前端日历点击过滤

- [x] 2.1 `index.vue` 新增 `selectedDate` 状态，日历日期绑定点击切换过滤/取消
- [x] 2.2 `fetchRecords` 附加 `date` 参数，切换月份清除选中；补选中高亮样式

## 3. 验证

- [x] 3.1 后端接口自测（date 参数过滤正确、参数缺省行为不变）
- [x] 3.2 br-app 构建通过（build:mp-weixin / H5）
