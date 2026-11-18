# Proposal: app-cs-edu-follow

## 动机

br-app 各详情页缺少统一的客服触达入口：用户在学习室/课程/老师/教培供需详情页遇到问题时，无法快速发起 IM 会话。同时「我的关注」只覆盖自习室/培训室/课程/教师，教培供需信息无法关注与回看。培训室详情页的「返回课程」跳出本页，用户想看的其实是本页的「本培训室课程」列表。

## 目标

1. **客服按钮**：自习室/培训室详情页（`pages/booking/detail.vue`）与课程详情页（`pages/training/course-detail.vue`）底部关注按钮旁新增戴耳机客服图标按钮（🎧，与 ♥ 同一圆形按钮样式），点击打开与该学习室创建人的 IM 单聊（课程页取课程所在学习室创建人）。创建人为空（存量）或为当前用户自己时，回退打开平台客服会话。
2. **老师详情页底部**（`pages-sub/teacher/profile.vue`）：调整为 关注 + 客服 + 返回培训室 三个按钮；客服打开平台客服会话（老师档案未绑定用户账号）。
3. **培训室「查看课程」**：培训室详情页底部「返回课程」改为「查看课程」，点击滚动定位到本页「本培训室课程」列表，不再跳出页面。
4. **教培供需详情底部**（`pages-sub/edu-market/detail.vue`）：「咨询」替换为 关注 + 客服 两个图标按钮；客服打开平台客服（用户 id `bd7f84cc-3d8b-480f-9327-30ee827cf386`）会话；关注复用 room-follows 接口新增 `follow_type=listing`，保留「立即联系/编辑」主按钮。
5. **我的关注新增「关注供需」TAB**（`pages-sub/favorites/index.vue`）：展示已关注的教培供需信息列表，点击跳转供需详情。

平台客服 IM 用户名 = 用户 UUID 的 hex（`to_im_user_id` 规则）：`bd7f84cc3d8b480f932730ee827cf386`。

## 范围

- br-server：
  - `schemas/study_room.py` + `study_room_service.get_study_room`：C 端房间详情新增 `creator_username`（创建人 IM 用户名，可空）。
  - `schemas/course.py` + `training_service.get_course_detail`：课程详情新增 `creator_username`（课程所在学习室创建人 IM 用户名，可空）。
  - `room_follow.py` 路由：三个端点 `follow_type` pattern 扩展 `listing`。
  - `room_follow_service.py`：`follow_room`/`list_followed_rooms` 新增 listing 分支（仅 approved 供需可关注/出现在列表，映射 FollowedRoomResponse，room_type='listing'）。
  - 测试：creator_username 字段、listing 关注/取消/列表、非 approved 拒绝。
- br-app：
  - 新增 `utils/customerService.js`：平台客服常量 + `openCSChat(creatorUsername)`（ensureLogin + ensureIM + TUIChat C2C 跳转，空/自己回退平台客服）。
  - `pages/booking/detail.vue`：客服按钮；培训室「查看课程」定位本培训室课程列表。
  - `pages/training/course-detail.vue`：客服按钮。
  - `pages-sub/teacher/profile.vue`：底部 关注+客服+返回培训室。
  - `pages-sub/edu-market/detail.vue`：底部 关注+客服（平台客服）+ 立即联系/编辑。
  - `services/followedRooms.js`：`getAllFollowedCategories` 增加 listing 分类。
  - `pages-sub/favorites/index.vue`：「关注供需」TAB 与列表渲染。
- 不改数据库 schema（room_follows.room_id 无外键、follow_type 为 String(20)，listing 直接复用）、不改权限码、不改管理端。

## 用户已确认决策

- 课程详情页客服对象 = 课程所在学习室创建人。
- 老师详情页客服对象 = 平台客服。
- 创建人为空或为当前用户自己时，客服回退打开平台客服会话。
- main 分支直接修复验证并提交 github（isolation=current）。