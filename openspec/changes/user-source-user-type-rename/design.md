# Design: user-source-user-type-rename

## 数据库迁移（两步、单个 Alembic revision）

基线 head：`l7m3n9p5q1r6`。新 revision 内按顺序执行：

1. **旧列改名**：`ALTER TABLE users RENAME COLUMN user_type TO user_source`；删除旧 CHECK 约束 `ck_users_user_type`，新建 `ck_users_user_source` CHECK (`user_source` IN ('app','admin'))。类型保持 String(10)，默认 'app'，非空。
2. **布尔转枚举**：新增 `user_type` VARCHAR(20) 列（先可空），`UPDATE users SET user_type = CASE WHEN is_super_admin THEN 'super-admin' ELSE 'normal-user' END`，再设非空 + 默认 'normal-user'，删除 `is_super_admin` 列，新建 CHECK `ck_users_user_type` (`user_type` IN ('super-admin','normal-user'))。

关键约束：'super-admin'/'normal-user' 长 11 字符，新列必须 VARCHAR(20)（旧 String(10) 不够）。

downgrade：反向重建 `is_super_admin` 布尔（`user_type='super-admin'` → true），删除新 CHECK 与新列，`user_source` 改回 `user_type` 并恢复旧 CHECK。

## 模型（app/models/user.py）

- `user_source`: String(10)，default='app'，nullable=False，CheckConstraint `ck_users_user_source`
- `user_type`: String(20)，default='normal-user'，nullable=False，CheckConstraint `ck_users_user_type`
- 删除 `is_super_admin` 列

## 内部权限表示（决策：保留布尔派生）

`AdminContext.is_super_admin`（frozen dataclass）保留布尔字段，由 `admin.user_type == 'super-admin'` 派生（dependencies.py）。`data_scope._unrestricted`、`require_admin_permission`、菜单服务、`permissions_for` 等内部布尔判定不动，7 个测试文件的 AdminContext fixture 不受影响。legacy X-Admin-Token 仍 `is_super_admin=True`，合成 User 改为 `user_source='admin', user_type='super-admin'`。

## API 字段（直接改名，无双字段过渡）

- admin 用户管理 schemas（admin_user_management.py）：`user_type`('app'/'admin') → `user_source`；`is_super_admin`(bool) → `user_type`(str 枚举)。Create 校验：`user_source='app'` 时强制 `user_type='normal-user'`；仅 admin 可为 'super-admin'。
- AdminCurrentResponse（admin_auth.py schemas）：`is_super_admin` → `user_type` 字符串；`admin_profile_from_model` 同步。
- app 端 UserResponse / UserProfileResponse（schemas/user.py）：`user_type` → `user_source`；`is_super_admin` → `user_type`。br-app 全仓零引用（含 camelCase），直接改名。
- admin 登录逻辑不变：仍只校验用户名/手机号+密码+状态，不加 `user_source` 校验。

## 服务层要点

- `admin_user_service.py` setattr 直写模型：schema 字段名必须与模型列名一致（`user_source`/`user_type`）。
- 创建交叉点：`user_type = data.user_type if data.user_source=='admin' else 'normal-user'`。
- 升级清空角色条件：`update_data.get('user_type') == 'super-admin'`。
- `wechat_auth_service.py`：合并校验 `target_user.user_source != 'app'`；注册创建 `user_source='app'`。
- `seed_admin.py` 幂等重跑：设 `user_type='super-admin'`；`seed_data.py` 改 `user_source='app'`。
- `scripts/check_user_uniqueness.sql` 列名同步。

## 前端（br-admin）

- `api/system/user.ts` 类型：`user_source: 'app'|'admin'`、`user_type: 'super-admin'|'normal-user'`
- `columns.ts`：「用户来源」key `user_source`；「用户类型」key `user_type`（admin 显示中文映射，app 显示 `-`）
- `index.vue`：隐藏「分配角色」条件 `record.user_source==='admin' && record.user_type==='super-admin'`
- `edit.vue`：下拉 options 值改字符串枚举；回填/payload 用 `user_type`
- `CreateModal.vue`：app/admin 单选字段名改 `user_source`

## 测试与文档

- 11 个测试文件 32 处 `user_type=` kwargs 按语义分别改为 `user_source=` 或新枚举；`test_user_type.py` 按枚举语义重写；CHECK 约束测试覆盖新枚举。
- `br-server/docs/api.md` 与根 `docs/api.md` 字段说明同步。
- 基线：19 个存量 pytest 失败（已用 base_ref worktree 证明），非本次回归。