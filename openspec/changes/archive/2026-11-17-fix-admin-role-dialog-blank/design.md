# 实现说明

## 方案

在 2 个受影响弹窗文件的现有 Form 导入行中补上 `BasicForm`：

```ts
import { BasicForm, FormSchema, useForm } from '@/components/Form';
```

`@/components/Form/index.ts` 已导出 `BasicForm`，无需新增导出或全局注册。

## 取舍

- 不采用 `app.component('BasicForm', ...)` 全局注册：项目惯例是各视图显式导入（如 `views/room/seats/index.vue`），全局注册会引入隐式依赖且超出本次修复范围。
- 不改动 `basicModal` / `useModal` / `BasicForm` 组件本身：注册机制（`@register` + `onMounted` emit）工作正常，问题仅在组件解析。
- `views/system/user/CreateModal.vue`、`EditModal.vue` 有同样缺陷但无引用（死代码），不修改、不删除，避免扩大范围。
- 验证期间发现项目测试入口 `test:business-refactor` 基线失败：两处断言过期（868a0e2 词表 confirmed→in_progress；7721d2b 自习室搜索项 2→4）。仅更新测试断言对齐有意变更，不改源码行为。

## 验证

- 独立 Chrome（CDP 9222）+ 本地 br-server(8000)/br-admin(8002) 实测：角色新增弹窗表单渲染、创建提交、编辑回填与保存、删除清理；用户管理页（页面式表单与 RoleModal）回归。
- `pnpm build` 确认构建无回归。