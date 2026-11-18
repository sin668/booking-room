# 验证报告：user-source-user-type-rename

- 日期：2026-11-18
- 分支：main（isolation current，用户明确要求）
- 验证模式：full（8 tasks、1 delta spec、38 变更文件；scale 建议 full）
- base_ref：bf3526f8dbaa43364107d7c268fa8174467c728d

## 摘要

| 维度 | 结果 |
|------|------|
| 完整性 Completeness | 8/8 tasks 完成；2/2 delta 需求已实现 |
| 正确性 Correctness | 11/11 delta 场景覆盖（测试/API/浏览器）；全量测试零回归 |
| 一致性 Coherence | design.md 全部决策已遵循；无 spec 漂移 |

**结论：全部检查通过，可归档。无 CRITICAL / WARNING 问题。**

## 1. 完整性

- tasks.md 8/8 勾选（build 守卫已核验）。
- 改动范围与 tasks 一致：`git diff --stat bf3526f...HEAD` 38 文件，全部落在迁移/模型/schemas/服务/路由/种子/脚本/前端 5 文件/测试 11 文件/文档 2 文件/OpenSpec 产物内，无无关路径。
- delta 需求实现定位：
  - Create user API → br-server/app/schemas/admin_user_management.py（Literal 枚举校验）、app/services/admin_user_service.py:88-150（创建/强制 normal-user/自动角色）
  - Admin user type management → br-admin/src/views/system/user/{columns.ts,index.vue,edit.vue,CreateModal.vue}、admin_user_service.py:160（升级清空角色）

## 2. 正确性（场景覆盖）

| 场景 | 证据 | 结果 |
|------|------|------|
| Create app user | test_admin_user_management 创建用例 + API 冒烟（app 强制 normal-user，201） | PASS |
| Create admin user | test_user_type.py::test_create_admin_defaults_normal_user | PASS |
| Create super admin user | test_user_type.py::test_create_super_admin + CDP UI 创建 | PASS |
| Duplicate phone / username | test_admin_user_management 409 用例（全量通过） | PASS |
| User source and type columns | CDP：admin→后台创建/超级管理员，csagent→后台创建/普通用户，app→App注册/`-` | PASS |
| User type dropdown in form | CDP：新增/编辑页枚举下拉，payload 携带 user_type | PASS |
| Super admin skips role assignment | CDP：admin 行下拉仅[切换状态,删除]；csagent 行含分配角色 | PASS |
| Promote clears roles | test_update_to_super_clears_roles + API 冒烟（roles=[]） | PASS |
| List API exposes fields | API 冒烟：列表含 user_source/user_type，无 is_super_admin | PASS |

补充边界：非法枚举 422（test_create_invalid_user_type_rejected + API 冒烟）；降级保留角色（test_update_to_normal_keeps_roles）；CHECK 约束拒绝非法 user_source/user_type（test_unified_user_model）；user_source 筛选（API + CDP）。

## 3. 检查证据

| 检查 | 命令/方式 | 结果 |
|------|-----------|------|
| 迁移 | alembic --sql 预览后 upgrade；asyncpg 核对列/约束/数据映射 | PASS（1 super-admin / 1 normal admin / 2 app；VARCHAR(20)；双 CHECK） |
| 后端构建 | `.venv/bin/python -c "from app.main import app"` | PASS |
| 前端构建 | comet check run build --local -- pnpm run build（cwd br-admin） | PASS（exit=0，build 守卫 14/14） |
| 验证测试 | comet check run verify --local -- pytest 11 个涉及文件（log e915ec26） | **125 passed, 1 deselected** |
| 全量回归 | pytest 全量 | 19 failed / 1082 passed / 16 skipped；与基线（19/1078/16）失败集合一致，零回归 |
| 存量失败排除 | test_update_user_multiple_fields：KeyError 'mobile'，base_ref worktree 已证明存量，与本次无关 | 记录在案 |
| API 冒烟 | me/列表/筛选/创建/升级/降级/非法枚举/删除（127.0.0.1:8000） | PASS，测试数据已清理 |
| 浏览器验收 | 独立 CDP Chrome（9222）：列表/隐藏分配角色/新增/编辑回填/降级/筛选/删除 | PASS，临时用户已删除，截图 /tmp/rename-user-list.png |
| 安全检查 | 无硬编码密钥新增；枚举 Literal+CHECK 双层校验；登录逻辑未改动 | PASS |
| 残留清扫 | grep 全源码：is_super_admin 仅存 AdminContext 内部布尔（设计保留）；旧语义 user_type 引用为零 | PASS |

## 4. 一致性（design.md 决策核对）

- 两步迁移 + VARCHAR(20) + 双 CHECK + downgrade：已实现并验证 ✓
- AdminContext 保留内部布尔（由 user_type=='super-admin' 派生）：dependencies.py:98 ✓，7 个测试 fixture 未波及 ✓
- API 直接改名无双字段过渡（br-app 零引用）✓
- admin 登录不加 user_source 校验（行为不变）✓
- setattr 直写字段名与模型一致 ✓
- 种子幂等（seed_admin 重跑设 super-admin）✓
- delta spec 与 design.md 无矛盾；tweak 流程无 Superpowers Design Doc（以 change design.md 为准，检查项 3/7 按 tweak 预设跳过）

## 5. 集成代码审查

review_mode=off（tweak 预设默认）。跳过原因：本次为机械性字段重命名，权限语义与登录行为不变；以全量测试零回归、125 项定向测试、API 冒烟与浏览器端到端验收替代自动审查；残留引用清扫确认无遗漏。

## 6. 遗留说明

- 19 个存量 pytest 失败为基线问题（前次 change 已用 base_ref worktree 证明），不属本次范围。
- 旧版已部署 app 客户端若读取 /auth/me 的 user_type（旧语义 app/admin）将看到新枚举值；仓库内 br-app 零引用，用户已确认直接改名不做双字段过渡（proposal 范围）。