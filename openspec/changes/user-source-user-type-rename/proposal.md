# Proposal: user-source-user-type-rename

## 动机

users 表当前用 `user_type`（'app'/'admin'）表示用户来源、用 `is_super_admin` 布尔表示管理员级别，语义命名不直观。需要：

- `user_type` 改名为 `user_source`，语义为「用户来源」（'app'/'admin'）
- `is_super_admin` 改为 `user_type`，语义为「用户类型」，枚举字符串 `super-admin`（超级管理员）/ `normal-user`（普通用户）

## 目标

1. 数据库两步迁移：先重命名旧 `user_type` → `user_source`，再将 `is_super_admin` 布尔转换为新 `user_type` 枚举列（String(20)，含 CHECK 约束与可用 downgrade）
2. br-server 模型、schemas、服务、路由、种子脚本、SQL 脚本全链路同步改名
3. br-admin 用户管理页（列表「用户来源」「用户类型」列、编辑页下拉、新增弹窗）与 API 类型同步
4. app 端响应字段同步改名（br-app 代码零引用，直接改，不做双字段过渡）
5. 测试与 API 文档同步；admin 登录行为不变（不新增 user_source 校验）

## 范围

- br-server：模型/迁移/schemas/服务/依赖/种子/脚本/测试/文档
- br-admin：types、columns、index、edit、CreateModal
- br-app：零改动（已确认无字段引用）
- 内部 AdminContext 保留布尔 `is_super_admin`（由 `user_type == 'super-admin'` 派生），减少内部权限判定与测试 fixture 波及

## 非目标

- 不改变任何权限语义：超级管理员仍是全菜单+全数据，普通用户仍按角色+创建人归属
- 不给 admin 登录增加来源校验（docs/api.md 明文禁止）