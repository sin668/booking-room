# Tasks: super-admin-data-public

## 1. 数据权限豁免实现

- [x] 1.1 `data_scope.py` 新增超管创建人子查询辅助，并扩展 `scope_condition`、`booking_scope_condition`、`review_scope_condition` 三个函数的非超管可见性条件

## 2. 测试

- [x] 2.1 `tests/test_data_scope.py` 新增超管创建数据公开可见场景（内容列表/详情、座位随教室、预约/评价随关联内容），并确认普通管理员互看仍被过滤
- [ ] 2.2 运行数据权限相关测试与全量回归，确认零回归（19 个存量失败基线不变）

## 3. 验收

- [ ] 3.1 API 冒烟验收：普通管理员（有菜单权限）可见超管创建的业务数据；无关脏数据清理