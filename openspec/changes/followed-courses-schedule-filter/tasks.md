# Tasks

## 1. 后端

- [x] 1.1 `room_follow_service.list_followed_rooms` course 分支复用 `_has_in_progress_fixed_schedule()` 追加过滤（count 与列表同口径）
- [x] 1.2 修复既有关注课程测试 fixture（test_course_follow.py / test_room_follow_service.py / test_follow_city_filter.py 补 fixed+in_progress 排课）
- [x] 1.3 新增用例：无进行中排课被隐藏（无排课 / completed / pending_start），有排课正常返回，room/teacher 分支不受影响

## 2. 验证

- [ ] 2.1 pytest 关注相关全部测试 + 培训相关回归通过
- [ ] 2.2 br-app 构建通过（记录 comet check 证据并通过 build/verify 守卫）
