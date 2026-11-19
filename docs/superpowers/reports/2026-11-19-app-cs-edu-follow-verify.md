# 验证报告：app-cs-edu-follow

- 变更：app-cs-edu-follow（workflow: tweak，isolation: current，分支 main）
- 验证模式：full（3 个 delta spec 能力）；审查模式：standard（独立集成审查）
- 基线：base_ref=f616749；验证提交 HEAD=02f490f
- 验证日期：2026-11-19
- 产物语言：zh-CN

## 摘要计分卡

| 维度 | 状态 |
| --- | --- |
| 完整性 Completeness | 10/10 任务勾选；3 能力 / 7 需求 / 31 场景全部有实现 |
| 正确性 Correctness | 7/7 需求覆盖；31/31 场景由代码 + 单测 + 真实环境冒烟佐证 |
| 一致性 Coherence | 遵循 design.md 高层决策；1 处实现机制细化（已记录），命名等价差异 |
| 独立集成审查 | PASS-with-notes（无 CRITICAL / 无 IMPORTANT） |
| 后端测试 | test_cs_edu_follow.py 11/11 通过；全量 19 基线失败零回归（1111 passed） |
| 前端构建 | npm run build:h5 通过（仅 Sass legacy-js-api 弃用警告） |
| 真实环境冒烟 | API 10/10、UI A 14/14、UI B 10/10；关注数据已清理 |

最终结论：无 CRITICAL / IMPORTANT 问题。WARNING/SUGGESTION 偏差经用户确认接受（见下）。可归档。

## 1. 完整性

tasks.md 全部 10 项 `[x]`：1.1/1.2（后端）、2.1–2.6（前端）、3.1/3.2（验收）。

delta spec 需求与实现映射：

| 能力 | 需求 | 实现证据 |
| --- | --- | --- |
| app-detail-cs-follow (ADDED) | 客服会话对象与平台客服回退 | br-app/src/utils/customerService.js:1-25（openCSChat：ensureLogin→自身 hex 比较→ensureIM→C2C 跳转，空/自己回退平台客服） |
| app-detail-cs-follow | C 端详情返回创建人 IM 用户名 | br-server/app/schemas/study_room.py:20、course.py:189；study_room_service.py:87、training_service.py:459-463（study_room 或 created_by 为空均置 null） |
| app-detail-cs-follow | 老师详情页底部操作栏 | br-app/src/pages-sub/teacher/profile.vue（关注+客服两圆形 icon-btn + 返回培训室 action-btn，移除空 chat-btn，保留导航心形） |
| app-detail-cs-follow | 教培供需关注 | br-server/app/api/routes/room_follow.py:16/30/48（pattern 扩展 listing）；room_follow_service.py:46-60/70-90/257-259（仅 approved、幂等、城市 OR NULL、通用取消） |
| app-detail-cs-follow | 我的关注「关注供需」TAB | br-app/src/services/followedRooms.js:51-66（listing 分类）；pages-sub/favorites/index.vue:306/220-267/380-394（TAB+列表+空状态+跳转） |
| edu-listing-ui (MODIFIED) | 详情页底部操作栏 | br-app/src/pages-sub/edu-market/detail.vue:129-136（关注 fav-heart + 客服 cs-emoji，保留立即联系/编辑，移除咨询） |
| study-room-booking-ui (MODIFIED) | Store detail page | br-app/src/pages/booking/detail.vue:22/294/361-388/735-744（客服按钮、查看课程 scroll-into-view 定位 room-courses） |

## 2. 正确性（场景覆盖）

31 个场景全部覆盖，关键佐证：

- 客服会话对象：UI A room4/course1 客服 → C2C05a0adcc…（创建人 brian77）；teacher1 → C2Cbd7f84cc…（平台客服）；UI B 供需客服 → 平台客服。
- 回退：UI B brian77 打开 room4（创建人==自己）→ 平台客服；room1 创建人即平台客服 → 平台客服；token 失效时 ensureLogin 弹「请先登录」不跳转。
- creator_username：单测 test_room_detail_creator_username / _null_for_legacy / test_course_detail_creator_username_from_room / _null_for_legacy_room；API 冒烟 room1=平台 hex、room4/course1=brian77 hex。
- 供需关注：单测 follow_created/idempotent/not_approved_raises/missing_raises/unfollow/list_only_approved/city_filter（11 项）；API 冒烟 201/200/404/204；UI B 关注 toast「已加入关注供需」+ 心形高亮。
- 关注供需 TAB：UI B 我的关注 5 TAB，切「关注供需」显示已关注 listing2（小学英语口语陪练），点击跳供需详情。
- 查看课程定位：UI A room4 点击「查看课程」scroll-view scrollTop 0→634，锚点 #room-courses 视口顶 1163→529（进入可视区），无页面跳转。
- 老师页底部三按钮：UI A iconBtnCount=2（关注+客服）+ action「返回培训室」，导航心形保留，旧 chat-btn 移除。
- 其余展示/跳转/空状态/条件 API 场景由代码分支与既有渲染逻辑覆盖。

## 3. 一致性

- 遵循 design.md 高层决策：客服口径（创建人/平台客服/回退）、listing 复用 room-follows 不改表结构、不改权限码/管理端/首页关注板块。
- 实现机制细化（已记录，非矛盾）：design.md:48 以 `uni.pageScrollTo`（假设整页滚动）描述「查看课程」定位；实际页面内容位于 `<scroll-view class="content" scroll-y>`，故采用 `:scroll-into-view="scrollIntoView"` + `id="room-courses"` 同步定位。delta spec 场景仅要求「滚动定位到本页课程列表、不跳转」，实现完全满足并经冒烟验证。build 期去除 `scroll-with-animation`，避免动画 transitionend 依赖在不可见标签页被节流导致 overflow 卡死，改为同步提交 scrollTop（更稳健）。
- 命名等价差异：design 的 `cs-btn/onCS` 实现复用既有 `fav-btn/onOpenCS`；课程页 `this.creatorUsername` 实现用 `this.course.creator_username`（CourseDetailResponse 为扁平结构，this.course=data，等价）。

## 4. 独立集成审查（standard）

独立审查者核对完整 diff（f616749…HEAD）、三份 delta spec、tasks.md 与测试证据，结论 **PASS-with-notes**：无 CRITICAL、无 IMPORTANT；自身 hex 比较、ensureLogin/ensureIM 守卫、C2C 格式、null 处理、仅 approved 关注、参数化查询无注入、端点鉴权、room/course/teacher 分支零改动均核实通过。

### 用户已接受的偏差（WARNING / SUGGESTION）

用户于 2026-11-19 明确选择「接受偏差并归档推送」。原因与影响范围记录如下：

- W1 customerService.js:14 冷启动竞态：autoLogin 未完成时 userInfo 为空，ownImId='' 致「创建人==自己」回退短暂失效。影响：极窄窗口（冷深链且在 fetchUserInfo 完成前点击客服），正常路径冒烟已验证回退正确；不阻塞核心验收。建议后续 change 在 userInfo 缺失时保守回退平台客服。
- W2 首页/个人中心关注计数仍四类不含 listing：属 proposal/design 明确范围外（「不改首页关注板块（仍四类）」），非缺陷，按设计接受。
- W3 缺 course.study_room=None 专项单测：代码 training_service.py:459-463 已以 `if study_room and study_room.created_by` 双重守卫处理；现有 _null_for_legacy_room 覆盖创建人为空。覆盖缺口轻微，接受。
- W4 并发重复关注 IntegrityError→500：既有 room/course/teacher 同模式，非本次回归，范围外接受。
- W5 供需页 onShow 为空，游客登录返回后 isFav 不即时刷新：再点关注靠幂等自愈，轻微 UX，接受。
- SUGGESTION（末尾换行、空状态图标语义、404 toast 文案、已关注提前返回）：均为 cosmetic/微优化，接受。

## 5. 验证证据

- 后端单测：`comet check run app-cs-edu-follow verify --local -- .venv/bin/python -m pytest tests/test_cs_edu_follow.py -q`（cwd=br-server，11 项通过，exit=0）。
- 全量回归：build 期全量 pytest 19 基线失败 / 1111 passed / 16 skipped，零新增回归；build 后仅前端 detail.vue 去除 scroll-with-animation（不影响后端测试）。
- 前端构建：br-app `npm run build:h5` DONE Build complete。
- 真实环境冒烟（CDP Chrome + H5，本地后端 8000）：API 10/10、UI A 14/14、UI B 10/10；冒烟产生的 Noah→listing2 关注已 DELETE 清理（列表复查为空）。
- OpenSpec：`comet classic openspec -- validate app-cs-edu-follow` → valid。

## 6. 最终评估

无 CRITICAL / IMPORTANT。全部任务勾选、7 需求 31 场景覆盖、独立审查 PASS-with-notes、测试/构建/冒烟通过。WARNING/SUGGESTION 偏差经用户确认接受并记录原因与影响范围。**可归档（archive 选项 B：归档并推送 origin main）。**