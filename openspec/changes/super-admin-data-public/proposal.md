# Proposal: super-admin-data-public

## Why

现有数据权限规则（admin-data-scope）下，普通管理员只能看到「自己创建 + 创建人为空（存量）」的业务数据。超级管理员创建的课程、自习室、活动、优惠券、教师等业务数据，普通管理员即使拥有对应菜单权限也看不到，导致公共运营内容无法共享。用户要求：超级管理员创建的所有业务数据，对拥有对应菜单权限的所有用户公开可见。

## What Changes

- `br-server/app/services/data_scope.py` 的三个可见性条件函数（`scope_condition`、`booking_scope_condition`、`review_scope_condition`）在「自己创建 + 创建人为空」之外，新增「创建人当前为超级管理员（`user_type='super-admin'`）」的豁免分支。
- 座位随自习室、预约/评价随关联内容的归属规则同步豁免：关联内容创建人为超管时，对应座位/预约/评价对有权限用户可见。
- 菜单/按钮权限仍由现有 `require_admin_permission` 控制，不改动；前端无需改动（可见性由服务端过滤决定）。
- 补充 `tests/test_data_scope.py` 覆盖超管创建数据的公开可见场景。

## 范围

- 仅修改数据权限可见性过滤层（data_scope）与其测试；不改数据库 schema、不新增 API、不改前端。

## 非目标

- 不改变超管自身「查看全部数据」的行为。
- 不改变创建人记录（created_by）写入逻辑。
- 不涉及认证、钱包流水、教育 listing（本就不做数据过滤）。