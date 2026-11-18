# 验证报告：super-admin-data-readonly

- 日期：2026-11-18
- 工作流：tweak（isolation=current，绑定分支 main，baseRef ad31119）
- 验证模式：full（含 1 个 delta spec：admin-data-scope）
- 产物语言：zh-CN
- 审查模式：off（tweak direct 默认；跳过自动代码审查，由本报告的场景映射与真实环境冒烟覆盖正确性/安全/边界）

## 摘要

| 维度 | 结论 |
| --- | --- |
| 完整性 Completeness | 6/6 任务完成；1 个需求、6 个场景全部有实现与验证证据 |
| 正确性 Correctness | 6/6 场景通过；后端写端点 403、readonly 标志、超管/本人/存量可写均经测试与冒烟确认 |
| 一致性 Coherence | 实现与 change design.md 一致；delta spec 与 design 无矛盾 |

最终结论：**全部检查通过，无 CRITICAL / IMPORTANT 问题，可归档。**

## 1. 任务完整性

tasks.md 6/6 全部 `[x]`：
1. 后端助手与单测（data_scope.py + test_data_scope.py）
2. 内容型五类接入（room/course/activity/coupon/teacher）
3. 随属记录接入（seat/booking/review）
4. 前端基础设施（rowClassName 透传 + 置灰样式 + 8 API 类型）
5. 前端 8 个列表页置灰与按钮禁用
6. 回归与验收（全量 pytest + pnpm build + 真实环境冒烟）

## 2. 规格场景覆盖（delta spec：admin-data-scope）

需求：Super-admin created content is read-only for non-super admins

| 场景 | 实现证据 | 验证证据 | 结论 |
| --- | --- | --- | --- |
| Non-super admin write rejected | 8 路由写端点调用 ensure_writable（room/activity/coupon/teacher/course 含课时排课） | test_super_content_write_endpoints_rejected：19 个写请求全 403，数据未改 | PASS |
| Sub-resource and record writes rejected | ensure_seat_writable / ensure_booking_writable / ensure_review_writable；course lessons/schedules 全守卫 | test_super_record_write_endpoints_rejected：座位嵌套/批量/扁平、预约 cancel/confirm、评价 status/reply 共 9 请求全 403 | PASS |
| List rows carry readonly flag | 8 schema 加 readonly；8 服务用 readonly_creators 批量判定（booking/review 随课程或自习室创建人） | test_readonly_flags_in_content_lists / test_readonly_flags_in_record_lists：超管行 true、本人/存量 false、详情一致 | PASS |
| Super admin unaffected | _unrestricted（超管/legacy/None）返回空集，ensure_* 直接放行 | 测试断言超管查看 all readonly=false；超管本人写 200；UI 冒烟超管 0 置灰行、按钮全可用 | PASS |
| Frontend grays readonly rows | 8 列表页 row-class-name + 修改类动作 disabled + 全局 .readonly-row 样式；查看入口保留 | CDP 冒烟：只读行 td 色 rgb(191,191,191)，编辑/删除禁用，下拉「下架」n-dropdown-option-body--disabled，管理座位/查看保留 | PASS |
| Own and legacy content stays writable | ensure_writable 对 created_by 为空/普通用户不拦截；降级后恢复归属 | test_own_and_legacy_content_writable / test_own_records_writable / test_ensure_writable_after_demotion | PASS |

## 3. 设计一致性

- data_scope.py 助手（readonly_creators / ensure_writable / ensure_seat_writable / ensure_booking_writable / ensure_review_writable）与 design.md「唯一判定来源」一致；判定按创建人**当前** user_type，与可见性口径一致。
- 路由接入表（design.md）与实现逐端点核对一致：study_room PUT/DELETE/status；course PUT/DELETE/status + lessons POST/PUT/DELETE + schedules POST/PUT/DELETE/postpone-lesson；activity PUT/DELETE/status；coupon PUT/status/DELETE；teacher PUT/DELETE/status/available-time-slots；seat 嵌套 POST/批量 POST + 扁平 PUT/DELETE/status；booking cancel/confirm；review status/reply。
- readonly 字段批量计算（列表一次 SELECT），避免逐行查询，与 design 一致。
- 前端 rowClassName 经 NDataTable.props 既有声明透传（无需改 props.ts），全局置灰样式 + 8 页 disabled，与 design 一致。
- delta spec 与 design.md 无矛盾。tweak 无 Superpowers Design Doc，以 change design.md 为准（检查项 3/7 按 tweak 规则跳过）。

## 4. 回归与构建证据

- 全量 pytest（br-server，.venv/bin/python -m pytest -q）：**19 failed / 1095 passed / 16 skipped**（74.72s）。19 个失败恰为存量基线（test_models_import 3、test_coupon_service 8、test_im_callback_sync 5、test_admin_user_management 1、test_activity_coupon_campaign 2），**零回归**。
  - 说明：test_api_booking.py 的 cancel 退款分层用例存在**时间依赖缺陷**（end_time 由 start_at+2h 取 .time()，运行时刻靠近午夜时跨日回绕导致 should_mark_booking_completed 误判 completed → cancel 400）。本次运行未触发（19 失败）；先前 11:35 运行曾触发（20 失败）。该用例属 C 端取消路径，本 change 未触碰，记为间歇性存量缺陷，非回归。
- 定向回归 test_data_scope.py：**23 passed**（build/verify 守卫检查命令）。
- br-admin pnpm build：**通过**（built in 7.69s，零错误）。

## 5. 真实环境冒烟（CDP 独立 Chrome，端口 9222）

临时数据：超管创建教室 id14；临时普通管理员 smoke_ro_tmp（仅教室菜单/按钮权限）；临时角色 id7。

- 后端：普通管理员列表 readonly=true；PUT/DELETE 教室返回 403（detail「超级管理员创建的数据仅可查看，不能修改」）；超管 GET readonly=false。
- 前端（普通管理员）：教室列表 2 行、只读行 1；只读行整行置灰（td rgb(191,191,191)）；编辑/删除按钮 disabled=true；「更多」下拉「下架」项 disabled（n-dropdown-option-body--disabled）；管理座位查看入口保留可用。
- 前端（超管）：教室列表 8 行、只读行 0；编辑/删除/管理座位/更多按钮全部可用，超管不受影响。
- 截图：/tmp/smoke-readonly-normal.png、/tmp/smoke-readonly-super.png。
- 清理：冒烟后已删除教室 14、用户 04a79c85、角色 7（均 204；复核 room/user 404、role 列表无 id7），无残留。

## 6. 安全检查

- 无硬编码密钥；写保护在后端强制执行（ensure_* 抛 403），不依赖前端隐藏，符合项目 RBAC 后端强制规则。
- readonly 判定与可见性同源（创建人当前 user_type），超管降级后数据恢复归属过滤，本人可写，无权限提升路径。
- 前端 disabled 仅为体验层，直达编辑 URL 的写提交由后端 403 兜底。

## 7. 问题清单

- CRITICAL：无
- IMPORTANT：无
- WARNING：无
- SUGGESTION：READONLY_DETAIL 文案（「超级管理员创建的数据仅可查看，不能修改」）较 design.md 近似引用更完整，非矛盾，无需处理。

## 结论

全部检查通过，6/6 场景验证通过，零回归，构建通过，真实环境冒烟通过，无 CRITICAL/IMPORTANT 问题。可进入归档。