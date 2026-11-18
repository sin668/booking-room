# Tasks: user-source-user-type-rename

## 1. 数据库与模型

- [x] 1.1 新增 Alembic 迁移（两步：user_type→user_source 改名+CHECK 重建；is_super_admin→user_type VARCHAR(20) 枚举+数据映射+CHECK，含 downgrade），模型 user.py 同步（user_source/user_type 列、约束、默认值，删除 is_super_admin），对开发库执行 upgrade 并验证

## 2. br-server 后端

- [x] 2.1 schemas 改名：admin_user_management.py（user_source/user_type 枚举+校验）、admin_auth.py（AdminCurrentResponse.user_type、admin_profile_from_model）、user.py（UserResponse/UserProfileResponse）
- [x] 2.2 服务与依赖：admin_user_service.py（列表过滤/创建/更新/清空角色/setattr）、dependencies.py（AdminContext 派生布尔）、admin_auth_service.py、admin_menu_service.py、wechat_auth_service.py、admin_auth.py 路由 legacy 合成 User、admin_user.py 路由参数
- [x] 2.3 种子与脚本：seed_admin.py（幂等设 super-admin）、seed_data.py（user_source='app'）、scripts/check_user_uniqueness.sql

## 3. br-admin 前端

- [x] 3.1 api/system/user.ts 类型、columns.ts 两列、index.vue 分配角色隐藏条件、edit.vue 枚举下拉与回填/payload、CreateModal.vue user_source 单选；pnpm build 通过

## 4. 测试与文档

- [x] 4.1 测试同步：11 个文件 kwargs 按语义改名、test_user_type.py 枚举语义重写、CHECK 约束测试更新；相关测试通过且相对基线（19 存量失败）零回归
- [ ] 4.2 文档同步：br-server/docs/api.md、根 docs/api.md 字段说明改名

## 5. 验收

- [ ] 5.1 CDP 浏览器验收：用户列表「用户来源」「用户类型」列显示正确、编辑页枚举下拉回填与保存、新增用户、超管隐藏分配角色；API 冒烟（列表/详情/创建/更新/me）