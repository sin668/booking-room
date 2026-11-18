# 验证报告：role-page-user-type-data-scope

- 日期：2026-11-17
- 流程：Comet Classic tweak（用户授权继续轻量流程，见 change `.comet/rulings.md`）
- 验证模式：full（8 任务 / 3 delta spec 能力 / 46 变更文件，`comet state scale` 建议 full）
- 分支：main（isolation current，base_ref `c9c691bac8f48896d9c7c3320fa2e9fd04cbfa1c`）
- 实现提交：`a3e9de2`（用户类型后端+角色详情）、`1669504`（数据权限）、`f54fc4a`（前端）、`a88b0ec`（OpenSpec 产物）

## 总结

| 维度 | 结果 |
| --- | --- |
| 完整性 Completeness | 8/8 任务完成；3 个 delta spec 共 10 个 Requirement 场景组全部有实现 |
| 正确性 Correctness | 17/17 场景均有测试或浏览器验收证据覆盖 |
| 一致性 Coherence | 实现遵循 design.md 全部决策；无 spec 漂移 |

**最终结论：全部检查通过，无 CRITICAL / WARNING 问题，可进入归档。**

## 完整验证检查项（comet-verify 2b）

| # | 检查项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | tasks.md 全部任务 `[x]` | PASS | 8/8（OpenSpec apply 进度 all_done） |
| 2 | 实现符合 change design.md 高层决策 | PASS | 见下方「设计一致性」 |
| 3 | 实现符合 Design Doc（docs/superpowers/specs/） | 跳过 | tweak 流程无完整 Design Doc，以 change design.md 为准（流程允许） |
| 4 | 能力规格场景全部通过 | PASS | 见下方「场景覆盖」 |
| 5 | proposal.md 目标已满足 | PASS | 角色页跳转编辑、用户类型列/下拉、完整数据权限均已交付并验收 |
| 6 | delta spec 与 design doc 无矛盾 | PASS | design.md 覆盖全部 delta 内容（含归属规则、NULL 可见性、写操作边界），Build 期间无未记录的 spec 增量修改 |
| 7 | 关联设计文档可定位 | 跳过 | 同第 3 项，tweak 无 docs/superpowers/specs/ 产物；change design.md 存在且相关 |

## 场景覆盖

### admin-rbac-ui（4 场景，CDP 浏览器验收）

| 场景 | 证据 |
| --- | --- |
| Load role list（无「菜单权限」按钮） | CDP：/system/role 按钮仅 [新增角色, 编辑, 删除]，表格真实数据 |
| Create role via page navigation | CDP：点击新增跳转 /system/role/edit，基本信息+菜单树（22 节点）；填写并勾选后保存，列表出现新角色（POST roles + PUT menus） |
| Edit role via page navigation | CDP：/system/role/edit/5 名称/编码回填、编码禁用、4 个菜单勾选回显（GET roles/5 + GET roles/5/menus）；改名保存后列表更新 |
| Assign directory/menu/button permissions | CDP：n-tree cascade 勾选（父节点联动 4 节点选中），保存走 PUT menus；树含 directory/menu/button 节点（getMenuList 全量树） |

### admin-user-management（10 场景）

| 场景 | 证据 |
| --- | --- |
| Create app user / Create admin user | 既有 test_admin_user_management.py 创建用例（基线通过）；CDP 新增 admin 用户 201 |
| Create super admin user | test_user_type.py：创建超管 201、is_super_admin=true、无角色 |
| Duplicate phone / Duplicate username | 既有 test_admin_user_management.py 409 用例（基线通过） |
| User type column in list | CDP：表头「用户类型」位于「状态」前；admin 行显示超级管理员/普通用户，app 行显示 `-` |
| User type dropdown in form | CDP：编辑页字段顺序 …用户类型、状态；下拉选项 [超级管理员, 普通用户]；新增页同样显示；payload 携带 is_super_admin（api/system/user.ts） |
| Super admin skips role assignment | CDP：超管行「更多」=[切换状态, 删除]；普通管理员行含「分配角色」 |
| Promote to super admin clears roles | test_user_type.py：设超管后 admin_user_roles 清空、响应 roles=[] |
| List API exposes is_super_admin | test_user_type.py：列表项含 is_super_admin |

### admin-data-scope（7 场景）

| 场景 | 证据 |
| --- | --- |
| Admin creates content | test_data_scope.py（课程/自习室创建人记录）；API 验收：admin/cdp_normal 各创建自习室 201，created_by 落各自 id |
| Legacy admin creates content | test_data_scope.py：legacy X-Admin-Token 创建 created_by 为 NULL |
| Normal admin lists own and legacy content | test_data_scope.py（课程/自习室/优惠券/教师）；API+CDP：cdp_normal 见 8 条（7 存量+自建），不见 admin 创建的自习室 |
| Super admin sees all | test_data_scope.py；API+CDP：admin 见全部 9 条 |
| Detail respects scope | test_data_scope.py；API：cdp_normal 访问他人自习室详情 404、自建 200 |
| Seats follow room ownership | test_data_scope.py；API：cdp_normal 对他人教室座位 404、自建/存量教室 200 |
| Booking / Review visibility by associated content | test_data_scope.py：课程订单随课程、座位订单随自习室、评价随关联内容，存量关联全员可见 |

## 构建与测试证据（Runtime）

- Build：`comet check run … build --local --cwd br-admin -- pnpm run build`，exit=0，日志 `openspec/changes/role-page-user-type-data-scope/.comet/checks/2b385910-958a-40eb-8b32-7f38d1ac39c6.log`；build 守卫 14/14 PASS（2026-11-17T10:08Z）
- Verify：`comet check run … verify --local --cwd br-server -- .venv/bin/python -m pytest tests/test_data_scope.py tests/test_user_type.py tests/test_admin_role_api.py -q`，**16 passed**，日志 `.comet/checks/ec6c96fc-a473-4222-8a04-dfd170c17971.log`
- 前端业务测试：`pnpm test:business-refactor` 通过（Build 阶段执行并记录）
- 全量后端套件：**19 failed / 1078 passed / 16 skipped**。19 个失败为存量基线问题：在 base_ref `c9c691b` 的临时 worktree（复制 .env 后运行）得到**完全相同的 19 个失败**（基线 19 failed / 1064 passed），本 change 净增 14 个测试全部通过，**零回归**。失败集中在 test_models_import（历史列断言过期）、test_admin_user_management 部分 update 用例（'mobile' 键过期）、test_coupon_service、test_im_callback_sync、test_activity_coupon_campaign，均与本 change 无关，不在本次范围内修复。
- 数据库迁移：`l7m3n9p5q1r6_add_created_by_to_content_tables` 已应用于开发库（alembic upgrade head），5 列可空、无 FK、带索引，不回填。

## 设计一致性

- 路由/页面结构、保存时序（先角色后菜单）、废弃弹窗删除：与 design.md 一致（CDP 验收佐证）。
- 用户类型语义映射 is_super_admin、仅 admin 类型适用、设超管清空角色：与 design.md 一致（测试佐证）。
- 数据权限：created_by 可空 UUID 无 FK（沿用 reviewed_by 先例）、NULL 全员可见、超管判定用 is_super_admin、legacy UUID(int=0) 落 NULL、座位随教室、预约/评价 outerjoin 关联过滤、认证/钱包/教育 listing 不过滤、写操作仍由权限码控制：全部按 design.md 实现。
- admin_course.py 补齐 get_current_admin 参数依赖：已实现。

## 安全与审查

- 无硬编码密钥、无新增 unsafe 操作；数据权限过滤在 service 层统一构造（data_scope.py），详情越权返回 404；写操作权限码控制未放宽。
- 集成代码审查：`review_mode: off`（tweak 预设，用户确认的轻量流程），跳过自动代码审查；构建、测试、安全检查与浏览器验收未跳过。
- 已知边界（design.md 已记录，非偏差）：数据权限只约束查看；更新/删除仍由功能权限码控制。

## 验收环境

- br-server uvicorn 127.0.0.1:8000 + 开发 PostgreSQL；br-admin dev http://localhost:8002；独立 CDP Chrome（--remote-debugging-port=9222）
- 验收创建的测试数据（CDP测试角色、cdp_normal 账号、2 个 CDP 自习室）已全部清理（DELETE 204）。