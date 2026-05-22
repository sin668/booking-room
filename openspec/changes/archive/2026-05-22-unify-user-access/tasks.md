## 1. 数据一致性检查

- [x] 1.1 编写 SQL 查询检测 users 表中跨 user_type 的 phone 和 username 重复记录，确认是否存在数据冲突
- [ ] 1.2 如有冲突数据，手动合并或清理（保留较早创建的记录，更新关联表中的外键引用）

## 2. 登录 Schema 调整

- [x] 2.1 修改 `br-server/app/schemas/user.py:21-23`：`UserLogin.phone` 改为 `Optional[str]`，新增 `username: str | None = None`，添加 `model_validator` 确保 phone 和 username 至少提供一个
- [x] 2.2 修改 `br-server/app/schemas/admin_auth.py:8-10`：`AdminLoginRequest.username` 改为 `Optional[str]`，新增 `phone: str | None = Field(None, max_length=11)`，添加 `model_validator` 确保 phone 和 username 至少提供一个

## 3. 后端登录逻辑修改

- [x] 3.1 修改 `br-server/app/services/auth_service.py:71`：register 方法中移除 `User.user_type == 'app'` 过滤，改为全局手机号唯一性校验 `select(User).where(User.phone == data.phone)`
- [x] 3.2 修改 `br-server/app/services/auth_service.py:141-144`：login 方法根据 `data.phone` 或 `data.username` 构建 `or_` 查询条件，移除 `User.user_type == 'app'` 过滤
- [x] 3.3 修改 `br-server/app/services/admin_auth_service.py:81-85`：login 方法签名从 `(self, username, password)` 改为 `(self, phone, username, password)`，用 `or_` 条件查询，移除 `User.user_type == 'admin'` 过滤
- [x] 3.4 修改 `br-server/app/services/admin_auth_service.py:68-72`：get_admin_by_id 移除 `User.user_type == 'admin'` 过滤条件
- [x] 3.5 修改 `br-server/app/api/routes/admin_auth.py:27`：login 路由调用从 `.login(data.username, data.password)` 改为 `.login(data.phone, data.username, data.password)`

## 4. 用户管理接口调整

- [x] 4.1 修改 `br-server/app/services/admin_user_service.py:91-96`：create_user 中手机号唯一性校验移除 `User.user_type == 'app'`，改为 `select(User).where(User.phone == data.phone)`
- [x] 4.2 修改 `br-server/app/services/admin_user_service.py:97-102`：create_user 中用户名唯一性校验移除 `User.user_type == 'admin'`，改为 `select(User).where(User.username == data.username)`

## 5. 测试更新

- [x] 5.1 更新 `br-server/tests/test_unified_user_model.py:40-58`：phone_uniqueness_constraint 测试移除 user_type 区分，两条 User 均不再指定 user_type（验证全局唯一）
- [x] 5.2 更新 `br-server/tests/test_unified_user_model.py:61-80`：username_uniqueness_constraint 测试移除 user_type 区分，验证全局唯一
- [x] 5.3 新增集成测试：br-app (`POST /api/v1/auth/login`) 支持用户名登录 — 用 username+password 请求，验证返回 200 和 token
- [x] 5.4 新增集成测试：br-admin (`POST /api/v1/admin/auth/login`) 支持手机号登录 — 用 phone+password 请求，验证返回 200 和 token
- [x] 5.5 新增测试：phone 和 username 均为空时，两个登录接口均返回 422

## 6. 代码审查与文档

- [x] 6.1 全局搜索 `user_type` 确认无遗漏的过滤逻辑（重点关注 `WHERE` 和 `.where(` 子句）
- [x] 6.2 更新 `docs/api.md`：补充 `UserLogin` 和 `AdminLoginRequest` schema 变更，说明 phone/username 双字段登录语义
