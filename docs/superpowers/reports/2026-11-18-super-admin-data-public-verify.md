# 验证报告：super-admin-data-public

- 日期：2026-11-18
- 模式：full（规模评估：4 任务 / 1 delta spec 能力 / 8 变更文件，建议 full；已选 full）
- 分支：main（isolation current）
- 基线：ce5d4f8 之前两个 tweak 提交（33debc8 实现+测试+产物、ce5d4f8 任务勾选）

## 摘要

| 维度 | 结果 |
| --- | --- |
| 完整性 | 4/4 任务完成；2/2 MODIFIED 需求已实现 |
| 正确性 | 8/8 规格场景全部有实现与测试覆盖 |
| 一致性 | 实现与 design.md 决策一致；delta spec 与 design.md 无矛盾 |

## 1. 任务完成度

tasks.md 4/4 全部 `[x]`（1.1 豁免实现、2.1 测试、2.2 回归、3.1 冒烟验收）。

## 2. 需求实现映射

| 需求 | 实现位置 | 结论 |
| --- | --- | --- |
| Data scope for non-super admins | br-server/app/services/data_scope.py `scope_condition` + `_visible_creator_condition`（超管创建人子查询 `select(User.id).where(User.user_type=='super-admin')`） | PASS |
| Record data follows associated content | 同文件 `booking_scope_condition` / `review_scope_condition` 课程/自习室两分支均改用 `_visible_creator_condition` | PASS |

菜单/按钮权限仍由 `require_admin_permission` 强制（未改动）；`_unrestricted`、`creator_id` 未改动；前端零改动；无 schema 变更、无新 API。

## 3. 场景覆盖（8/8）

| 场景 | 覆盖证据 | 结果 |
| --- | --- | --- |
| Normal admin lists own and legacy content | tests/test_data_scope.py::test_course_list_scope（A 见 X+Z 不见 Y） | PASS |
| Super admin sees all | test_course_list_scope / test_booking_follows_associated_content（super_admin=True 全量） | PASS |
| Detail respects scope | test_course_detail_scope + test_super_admin_content_public_to_normal_admin（普通管理员 B 的教室仍 404） | PASS |
| Seats follow room ownership | test_seat_follows_room + test_super_admin_seats_bookings_reviews_public（超管教室座位可见） | PASS |
| Super-admin created content is public | test_super_admin_content_public_to_normal_admin（列表+详情 200）；活动/优惠券/教师与课程/教室共用同一 `scope_condition`，豁免等价生效 | PASS |
| Creator demoted loses public visibility | test_demoted_super_admin_content_not_public（降级后列表不含、详情 404） | PASS |
| Booking visibility by associated content | test_booking_follows_associated_content + test_super_admin_seats_bookings_reviews_public（超管课程订单/座位订单可见） | PASS |
| Review visibility by associated content | test_review_follows_associated_content + test_super_admin_seats_bookings_reviews_public（超管关联评价可见） | PASS |

## 4. 检查证据

- **verify 检查（Runtime）**：`comet check run super-admin-data-public verify --local -- .venv/bin/python -m pytest tests/test_data_scope.py -q`，cwd=br-server，exit=0，日志 `openspec/changes/super-admin-data-public/.comet/checks/72ebc41d-59cf-472f-b062-e8fa0f83d61f.log`：**13 passed**（10 存量 + 3 新增）。
- **build 检查（Runtime）**：同命令，日志 `c05ca478-e442-4ba4-a16d-3d972248afef.log`，exit=0；build 守卫 14/14 PASS。
- **全量回归**：`.venv/bin/python -m pytest -q`（br-server）：**19 failed / 1085 passed / 16 skipped**（90.70s）。19 个失败与已证明的存量基线完全一致（test_models_import 3、test_coupon_service 8、test_im_callback_sync 5、test_activity_coupon_campaign 2、test_admin_user_management::test_update_user_multiple_fields 1），**零回归**；passed 由 1082 增至 1085 为本次新增 3 个测试。
- **API 冒烟验收**（真实 dev 环境，脚本 /tmp/smoke_public.py）：
  - 超管 admin 创建教室「超管公开验收教室」；
  - 临时普通管理员 smoke_public_admin（临时角色仅含教室相关菜单权限 room:manage/room:view/room:create/room:delete/seat:view）登录后列表可见该教室、详情 200；
  - 超管可见全部教室（含普通管理员自建）；
  - 验收数据全部清理（2 教室、临时账号、临时角色均删除，断言 204/200）。
- **安全检查**：diff 无硬编码密钥、无新增 unsafe 操作；子查询经 SQLAlchemy 参数化；权限码校验未放宽；普通管理员互看仍 404（测试断言）。
- **残留检查**：`git diff --stat` 交付文件仅 data_scope.py 与 test_data_scope.py，与 tasks 描述一致。

## 5. 一致性（design.md）

- 子查询辅助 + 三函数扩展、User 延迟导入：与实现一致 ✓
- 按创建人**当前** user_type 判定（降级恢复过滤）：design/spec/测试三者一致 ✓
- 菜单权限不变、前端零改动、无 schema/新 API：与实现一致 ✓
- tweak 无 Superpowers Design Doc，以 change design.md 为准；delta spec 与 design.md 无矛盾（Build 阶段未增量修改 spec）。

## 6. 集成代码审查

review_mode=off（tweak 预设默认，策略非 autonomous）：跳过自动代码审查。原因：改动集中于单一过滤模块（+24/-8 行）与测试，已由 13 个定向测试、全量零回归与真实环境冒烟覆盖正确性与授权边界。构建、测试、安全检查未跳过。

## 7. 工作区核对

未提交改动仅：本 change 的 .comet/check-policy.json 与状态元数据（.comet.yaml），以及已知无关文件（.graphify/*、.mcp.json、br-admin/pnpm-lock.yaml、其他 change 元数据、br-app 资产、html/ 等），均不属本次实现，未混入提交。

## 结论

**全部检查通过，无 CRITICAL / WARNING / SUGGESTION 问题，可归档。**