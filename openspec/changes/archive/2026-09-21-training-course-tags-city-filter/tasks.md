# Tasks

## 1. br-server 后端：课程列表 city_id 过滤

- [x] 1.1 `app/api/routes/training.py`：`list_training_courses` 新增 `city_id: int | None = Query(None, ge=1)`，透传给 `training_service.list_courses`
- [x] 1.2 `app/services/training_service.py`：`list_courses` 新增 `city_id: int | None = None` 形参；`city_id` 存在时向 `filters` 追加 `or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None))`，并让 count 查询显式 `JOIN StudyRoom`（仅当 `city_id` 存在），主查询保持既有 JOIN
- [x] 1.3 新增 `tests/test_training_course_city_filter.py`：自包含 fixture（两个城市 + 各自培训室 + 课程 + in_progress fixed 排课），验证 `city_id` 过滤只返回对应城市课程、未设城市的培训室课程始终可见、不传 `city_id` 返回全部

## 2. br-app 前端：课程卡片角标 + 城市联动

- [x] 2.1 `src/pages/training/index.vue`：课程卡片 `.course-cover-wrap` 内新增左上角「可预约」（`cover-status open`）与右下角「课程」（`cover-chip`）角标，复用既有样式类
- [x] 2.2 `src/pages/training/index.vue`：`fetchCourses` 在 `currentCityId.value` 存在时加入 `params.city_id`
- [x] 2.3 `src/pages/training/index.vue`：`onShow` 城市变化时按 `activeTab` 分支刷新（all→培训室，否则→课程）
- [x] 2.4 `src/api/training.js`：更新 `getTrainingCourses` 的 JSDoc，补充 `city_id` 参数说明

## 3. 验证

- [x] 3.1 运行 `pytest tests/test_training_course_city_filter.py` 通过
- [x] 3.2 运行 `npm run build:mp-weixin`（br-app）构建通过
