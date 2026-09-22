# Verification Report: followed-rooms-city-filter

- 日期：2026-09-21
- workflow：tweak / verify_mode：full
- 分支：main（bound_branch=main）

## Summary

| Dimension    | Status |
|--------------|--------|
| Completeness | 8/8 tasks 完成；3 条 ADDED requirements 全部有实现与测试映射 |
| Correctness  | 3/3 requirements 覆盖；后端 6 个新测试全部通过；首页为代码走查验证（uni-app 无自动化测试基建） |
| Coherence    | 实现与 design.md D1–D5 一致；delta spec 与 design 无矛盾 |

## 检查项

1. **tasks.md**：1.1–1.3、2.1–2.3、3.1–3.2 全部 `[x]`。
2. **实现 ↔ design**：
   - D1 服务端过滤：`room_follow_service.list_followed_rooms(city_id=...)` 三分支均实现；首页改为传 `cityId` 并删除前端自习室过滤（`br-app/src/pages/index/index.vue:357`）。
   - D2 `or_(StudyRoom.city_id == city_id, is_(None))`：`_city_or_null_condition` 统一实现。
   - D3 teacher EXISTS：`has_city_room`/`has_any_room` 均显式 `TeacherRoom.teacher_id == Teacher.id` 关联主表，谓词 `or_(has_city_room, ~has_any_room)` 同时用于 count 与列表。
   - D4 course count JOIN：city 过滤时 count/列表同步 `join(StudyRoom, Course.room_id == StudyRoom.id)`，无笛卡尔积风险（测试断言 `total == len(items)`）。
   - D5 参数可选：`getFollowedRooms(followType, cityId=null)`、`getAllFollowedCategories(cityId=null)`；favorites 页与其他调用方（booking/detail、course-detail、teacher-profile、followedCourses/Teachers）未改动，不传参行为不变。
3. **Design Doc（docs/superpowers/specs）**：tweak 档位无深度设计文档（design_doc: null），以 change design.md 为准。
4. **Spec scenario 覆盖**（`tests/test_follow_city_filter.py`，6 passed）：
   - 房间按城市过滤 / 无城市房间豁免 → `test_room_follows_filtered_by_city`
   - 不传 city_id 行为不变 → `test_room_follows_without_city_id_returns_all`、`test_teacher_follows_without_city_id_returns_all`
   - 课程按所属房间城市过滤 → `test_course_follows_filtered_by_room_city`
   - 教师匹配/不匹配/无房间关联三情形 → `test_teacher_follows_filtered_by_city`
   - 非法 city_id → `test_invalid_city_id_rejected`（422）
   - 首页城市联动 / 未选城市不过滤 → 代码走查：`loadFollowedRooms` 传 `currentCityId`（null 时不拼参数）。
5. **proposal 目标**：四个关注板块统一服务端城市过滤，已满足。
6. **回归**：`tests/test_api_room_follows.py`、`tests/test_teacher_follow.py` 全部通过；`npm run build:mp-weixin` exit 0。
7. **安全**：city_id 经 FastAPI Query(ge=1) 校验后以绑定参数进入 SQL；无新增注入面。

## Issues

- **WARNING（既有，非本次引入）**：`tests/test_course_follow.py`、`tests/test_room_follow_service.py` 共 10 个用例在干净 HEAD（git stash 后验证）即因陈旧 fixture 向 `Course(...)` 传已在排课重构中移除的 `price=` 而在 setup 阶段 ERROR。与 training 系列陈旧测试同类，超出本 change 范围，建议后续单独修复。
- SUGGESTION：课程/教师关注响应仍返回 `city_id=None`；因过滤已移至服务端且首页不消费该字段，按 ponytail 原则本次不扩展。

## 结论

PASS。无 CRITICAL / IMPORTANT 问题，允许进入归档。
