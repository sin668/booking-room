## Why

br-app 培训课程页 `/pages/training/index` 的「培训室」TAB 中，培训室封面图已有两个角标：左上角「可预约」状态标签、右下角「培训」类型标签。但切换到分类课程 TAB（小学辅导/中学辅导/公考备考/技能提升）后，课程卡片封面图缺少这两个角标，视觉上与培训室卡片不一致。

同时，培训室列表已支持按当前所选城市（`city_id`）过滤，而课程列表接口 `GET /api/v1/training/courses` 没有 `city_id` 过滤：课程隶属于培训室、培训室隶属于城市，切换城市后课程 TAB 仍返回全部城市的课程，与培训室 TAB 的城市口径不一致。

## What Changes

- **前端（br-app）**：分类课程 TAB 的课程卡片封面图增加两个角标——左上角「可预约」状态标签、右下角「课程」类型标签，复用培训室卡片已有的 `.cover-status` / `.cover-chip` 样式，保持视觉一致。
- **前端（br-app）**：`fetchCourses` 携带当前城市 `city_id`；城市切换后（`onShow`）按当前激活 TAB 刷新对应列表（课程 TAB 刷新课程，培训室 TAB 刷新培训室）。
- **后端（br-server）**：`GET /api/v1/training/courses` 新增可选查询参数 `city_id`，按课程所属培训室的城市过滤；口径与培训室列表一致——培训室 `city_id` 等于指定值**或**培训室未设置城市（`city_id` 为 null）的课程都返回。

## Capabilities

### Modified Capabilities
- `training-course-list-api`: 课程列表接口新增 `city_id` 过滤参数。
- `training-course-list-ui`: 课程卡片封面新增「可预约」/「课程」角标，并随城市切换刷新课程列表。

## Impact

- **br-server**: 改 `app/api/routes/training.py`（`list_training_courses` 新增 `city_id` Query 参数并透传）、`app/services/training_service.py`（`list_courses` 新增 `city_id` 形参，count 查询在 `city_id` 存在时 JOIN `StudyRoom` 以避免笛卡尔积，过滤条件 `or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None))`）；新增测试 `tests/test_training_course_city_filter.py`。
- **br-app**: 改 `src/pages/training/index.vue`（课程卡片模板增加角标、`fetchCourses` 传 `city_id`、`onShow` 按 TAB 刷新）；可选更新 `src/api/training.js` 的 JSDoc。
- **数据库**: 无 schema 变更（`courses.room_id → study_rooms.id`、`study_rooms.city_id` 均已存在）。
- **回滚方案**: 后端移除 `city_id` Query 参数与 `list_courses` 的 `city_id` 形参及对应过滤/JOIN，删除新增测试文件；前端移除课程卡片角标元素、`fetchCourses` 的 `city_id` 传参与 `onShow` 的 TAB 分支刷新。改动均为向后兼容的可选参数与纯展示元素，移除即恢复原状。
