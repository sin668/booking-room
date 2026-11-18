# Proposal: super-admin-data-readonly

## 动机

`super-admin-data-public` 已让超管创建的业务数据对拥有对应菜单权限的所有管理员公开可见。但当前非超管看到这些数据后仍可编辑、删除、切换状态——后端写端点没有归属校验，前端也没有任何只读提示。用户要求：非超管查看超管创建的数据时，列表中整行置灰、只能查看，不能进行任何修改类操作。

## 目标

1. 后端强制：非超管对「创建人当前为超管」的内容及其随属记录（座位、课时/排课、预约、评价）的写操作一律返回 403。
2. 列表/详情 API 返回 `readonly` 标志，供前端渲染只读态（超管查看恒为 false）。
3. br-admin 业务列表页对 `readonly` 行整行置灰，禁用编辑/删除/状态切换等修改类按钮；纯查看入口（查看详情、管理座位页浏览）保留。

## 范围

- br-server：`data_scope.py` 写保护与 readonly 计算助手；8 个 admin 路由文件的写端点接入；响应 schema 与列表/详情服务补 `readonly` 字段；测试。
- br-admin：`BasicTable` 透传 `rowClassName`；全局置灰样式；8 个 API 类型补 `readonly`；8 个列表页置灰与按钮禁用。
- 不改数据库 schema、不改可见性过滤规则、不改权限码体系。

## 授权

跨模块 + 文件数超阈值已由用户明确选择「继续 tweak」，见 `.comet/rulings.md`。