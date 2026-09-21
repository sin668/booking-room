# Design

## 1. 后端：课程列表 city_id 过滤

`list_courses` 主查询已 `JOIN StudyRoom ON Course.room_id == StudyRoom.id`，因此可直接在主查询过滤 `StudyRoom.city_id`。难点在 count 查询：当前为 `select(func.count()).select_from(Course).where(*filters)`，未 JOIN `StudyRoom`；若把引用 `StudyRoom.city_id` 的条件放入共享 `filters`，count 查询会把 `StudyRoom` 隐式加入 FROM 形成笛卡尔积，导致 total 被放大。

**方案**：`city_id` 存在时，count 查询显式 `JOIN StudyRoom`，与主查询保持一致；`city_id` 为空时 count 查询保持原样（零行为变化）。过滤口径复用培训室列表的 `or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None))`——未设置城市的培训室下的课程对任意城市可见。

```python
if city_id is not None:
    filters.append(or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None)))

count_stmt = select(func.count()).select_from(Course)
if city_id is not None:
    count_stmt = count_stmt.join(StudyRoom, Course.room_id == StudyRoom.id)
total = (await db.execute(count_stmt.where(*filters))).scalar_one()
```

> 注：`keyword` 过滤引用 `Teacher.name` 而 count 查询未 JOIN Teacher 属于既有行为，不在本次范围内改动。

路由 `list_training_courses` 新增 `city_id: int | None = Query(None, ge=1)` 并透传给 service。

## 2. 前端：课程卡片角标

课程卡片 `.course-cover-wrap`（`position: relative`）内新增两个元素，直接复用培训室卡片已有的 scoped 样式类，无需新增 CSS：

```html
<view class="cover-status open">
  <text class="cover-status-text">可预约</text>
</view>
<view class="cover-chip">
  <text class="cover-chip-text">课程</text>
</view>
```

课程列表仅展示有进行中固定班课排课的课程（即可预约），故「可预约」为静态标签，与培训室展开区热门课程的 `hot-course-status` 口径一致。右上角既有的 `.course-badge`（热销/新课/名师/推荐）保留不变，三个角标位置互不冲突（左上/右上/右下）。

## 3. 前端：城市联动

- `fetchCourses` 在 `currentCityId.value` 存在时加入 `params.city_id`，与 `fetchTrainingRooms` 一致。
- `onShow` 检测城市变化后，按 `activeTab` 分支刷新：`all` 刷新培训室，否则刷新课程。修复此前城市切换只刷新培训室、课程 TAB 不联动的问题。

## 4. 数据流

```
城市选择(cityStore) ──> currentCityId
        │
        ├─ activeTab=all  ──> fetchTrainingRooms(city_id) ──> GET /training/rooms?city_id=
        └─ activeTab=分类 ──> fetchCourses(city_id)      ──> GET /training/courses?city_id=&category=
                                                              │
                                          list_courses: JOIN StudyRoom + or_(city_id==X, city_id IS NULL)
```
