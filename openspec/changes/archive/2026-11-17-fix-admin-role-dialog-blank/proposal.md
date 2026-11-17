# 修复 br-admin 角色管理弹窗内容空白

## 动机

br-admin `/system/role` 角色权限管理页点击「新增角色」「编辑」按钮后，弹窗只有标题和取消/保存按钮，表单内容区一片空白，无法新增或编辑角色。浏览器复现确认弹窗内容区渲染为未解析的 `<basicform></basicform>` 未知元素。

## 根因

`CreateModal.vue` / `EditModal.vue` 使用 `<script setup>`，模板中的 `<BasicForm>` 需要显式导入才能解析。这两个文件只导入了 `useForm` / `FormSchema`，未导入 `BasicForm` 组件；`src/plugins/customComponents.ts` 的全局注册是空 stub，因此 Vue 将 `BasicForm` 当作未知自定义元素渲染，表单不显示。

受影响文件（实际在用的全部调用方）：

- `br-admin/src/views/system/role/CreateModal.vue`
- `br-admin/src/views/system/role/EditModal.vue`

排查中发现 `views/system/user/CreateModal.vue`、`EditModal.vue` 存在同样缺陷，但已无任何引用（用户管理改为路由页面表单 `edit.vue`，列表页仅引用 `RoleModal.vue`），属死代码，不在本次修复范围。

## 目标

- 角色新增/编辑弹窗正常渲染表单（名称、编码、说明、状态），可提交保存。
- 不改变弹窗交互、字段与 API 行为。

## 范围

仅补齐 role 两个弹窗文件的 `BasicForm` 组件导入（沿用项目其他视图的显式导入惯例），不做全局注册、不重构 Modal/Form 组件、不清理死代码。