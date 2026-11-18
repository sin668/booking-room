# Design: super-admin-data-public

## 实现说明

可见性过滤集中在 `br-server/app/services/data_scope.py`，所有业务列表/详情服务均调用其三个条件函数，无需逐个服务修改：

1. 新增内部辅助 `_super_admin_creator_condition(column)`：返回 `column.in_(select(User.id).where(User.user_type == "super-admin"))` 子查询条件（`User` 延迟导入，避免循环依赖）。使用子查询而非 join，调用方 SQL 结构零改动。
2. `scope_condition(model, viewer)`：非超管条件由 `or_(created_by IS NULL, created_by == viewer)` 扩展为三分支 `or_(created_by IS NULL, created_by == viewer, _super_admin_creator_condition(model.created_by))`。
3. `booking_scope_condition` / `review_scope_condition`：课程分支与自习室分支内的 `or_(Course/StudyRoom.created_by IS NULL, == viewer)` 同样追加超管创建人子查询分支。
4. `_unrestricted`（超管/legacy/None 不过滤）与 `creator_id`（创建人记录）不变。

## 语义决策

- **按创建人当前类型判定**：豁免依据创建人当前 `user_type='super-admin'`。超管被降级为普通用户后，其创建的数据恢复按创建人归属过滤（与「用户类型为超级管理员的用户创建的数据」语义一致，且无需迁移或冗余字段）。
- **菜单权限不变**：能否进入某业务页面仍由 `require_admin_permission` 的权限码控制；本豁免只扩大可见数据范围，不授予任何新权限。
- **前端零改动**：可见性完全由服务端过滤决定。
- **无 schema 变更、无新 API**：仅查询条件扩展。

## 测试

`tests/test_data_scope.py` 扩展：种子数据加入超管创建的教室/课程（及关联座位/预约/评价），断言普通管理员列表/详情可见超管创建数据、座位随超管教室可见、预约/评价随超管关联内容可见；他人（普通管理员）创建数据仍 404。