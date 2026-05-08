## 1. Backend Auth

- [x] 1.1 在 `br-server/app/core/config.py` 中添加 `get_current_admin` 依赖，校验请求 Header `X-Admin-Token` 与环境变量 `ADMIN_TOKEN` 是否匹配
- [x] 1.2 在 `br-server/app/core/config.py` 中添加 `ADMIN_TOKEN` 配置项

## 2. Backend File Upload

- [x] 2.1 创建 `br-server/app/api/routes/upload.py`，实现 `POST /upload/` 接口：接收 multipart 文件，校验类型（仅图片）和大小（≤5MB），UUID 重命名，按年/月/日存储到 `uploads/` 目录
- [x] 2.2 在 `br-server/app/main.py` 中注册 upload 路由到 `/api/v1/admin/upload`，并挂载 `uploads/` 目录为静态文件服务

## 3. Backend Schemas

- [x] 3.1 在 `br-server/app/schemas/activity.py` 中添加 `ActivityCreate`、`ActivityUpdate`、`ActivityAdminResponse`、`ActivityListResponse`（含分页字段）、`ActivityStatusUpdate`、`UploadResponse` 等 Pydantic 模型

## 4. Backend Service

- [x] 4.1 在 `br-server/app/services/activity_service.py` 中添加管理端 CRUD 方法：`list_activities`（分页+搜索+筛选）、`get_activity_by_id`、`create_activity`、`update_activity`、`delete_activity`、`toggle_activity_status`

## 5. Backend API Routes

- [x] 5.1 创建 `br-server/app/api/routes/admin_activity.py`，实现管理端路由：`GET /`（分页列表）、`POST /`（创建）、`GET /{id}/`（详情）、`PUT /{id}/`（更新）、`DELETE /{id}/`（删除）、`PATCH /{id}/status/`（上下架），所有接口依赖 `get_current_admin`
- [x] 5.2 在 `br-server/app/main.py` 中注册 `admin_activity` 路由到 `/api/v1/admin/activities`

## 6. Backend Tests

- [x] 6.1 编写管理端 API 集成测试（`br-server/tests/test_api_admin_activity.py`），覆盖所有接口和异常场景（含无 Token、错误 Token、CRUD、分页、状态切换）
- [x] 6.2 编写文件上传接口测试（`br-server/tests/test_api_upload.py`），覆盖成功上传、非法类型、超大文件、缺失文件字段
- [x] 6.3 在 `br-server/tests/conftest.py` 中添加 `get_current_admin` 依赖覆盖，使测试绕过鉴权

## 7. Frontend API Layer

- [x] 7.1 创建 `br-admin/src/api/activity/index.ts`，导出以下内容：
  - 类型定义：`ActivityItem`、`ActivityListResult`、`ActivityFormParams`
  - API 函数：`getActivityList`、`createActivity`、`getActivityById`、`updateActivity`、`deleteActivity`、`toggleActivityStatus`
  - **注意**：当前 Alova 实例的 `beforeRequest` 拦截器仅注入 `token` 头，管理端 API 需要 `X-Admin-Token` 头。需要在每个请求中通过 `localConfig.headers` 显式传递 `X-Admin-Token`，或在 API 函数内部从 store/env 读取 token 后注入 header
  - **参考模式**：`br-admin/src/api/system/menu.ts` 使用 `Alova.Get<Type>('/path', { params })` 的写法

- [x] 7.2 在 `br-admin/src/api/activity/index.ts` 中同时导出 `uploadFile` 函数：
  - 使用 `FormData` 构建请求体
  - **注意**：Alova 的 `Post` 方法传递 `FormData` 时，不应手动设置 `Content-Type`，让浏览器自动添加 `multipart/form-data` 边界
  - 返回 `{ url: string }`

## 8. Frontend Activity List Page

- [x] 8.1 创建 `br-admin/src/views/activity/list/columns.ts`，定义表格列配置：
  - **参考**：`BasicColumn<T>` 类型来自 `@/components/Table`
  - 列定义：ID、标题（ellipsis+tooltip）、描述（ellipsis+tooltip）、封面图（`NImage` 缩略图 60x40）、参与人数、排序值、状态（`NTag` success/default）、创建时间
  - **导入**：`import { h } from 'vue'`、`import { NImage, NTag } from 'naive-ui'`、`import type { BasicColumn } from '@/components/Table'`

- [x] 8.2 创建 `br-admin/src/views/activity/list/index.vue`，实现活动列表页：
  - **参考模式**：`br-admin/src/views/list/basicList/index.vue`（搜索表单 + 表格 + 操作列）
  - 搜索表单使用 `BasicForm` + `useForm`（`@/components/Form`），定义 `FormSchema[]`：
    - `keyword` 字段 → `NInput`（placeholder: "搜索标题或描述"）
    - `is_active` 字段 → `NSelect`（选项：全部/已上架/已下架）
  - 表格使用 `BasicTable`（`@/components/Table`），`:request` 绑定 `loadDataTable` 异步函数
  - `loadDataTable` 合并表单值与表格分页参数，调用 `getActivityList`
  - **注意**：`is_active` 的 `NSelect` 返回字符串 `'true'/'false'`，需转换为布尔值传给 API
  - 操作列使用 `TableAction`（`@/components/Table`），包含编辑、删除按钮，下拉操作含上架/下架
  - 删除使用 `window['$dialog'].warning` 确认，成功后 `actionRef.reload()`
  - 新建按钮在 `#tableTitle` 插槽中，使用 `@vicons/antd` 的 `PlusOutlined` 图标
  - 点击新建/编辑时打开 `ActivityEditModal`，`editData` 为 null 表示新建

## 9. Frontend Activity Edit Modal

- [x] 9.1 创建 `br-admin/src/views/activity/list/ActivityEditModal.vue`，实现编辑弹窗：
  - **参考模式**：`br-admin/src/views/system/menu/CreateDrawer.vue`
  - 使用 `n-modal` + `preset="dialog"`，宽度 600px
  - Props：`show: boolean`、`editData: ActivityItem | null`；通过 `v-model:show` 双向绑定
  - 表单字段（`n-form` + `FormRules`）：
    - 标题（`n-input`，必填，maxlength=100，show-count）
    - 描述（`n-input type="textarea"`，可选，maxlength=500，show-count，rows=3）
    - 封面图（`n-upload` :max="1" accept="image/*" + `n-image` 预览），custom-request 调用 `uploadFile` 后回填 URL
    - 参与人数（`n-input-number` :min="0"）
    - 排序值（`n-input-number`）
    - 是否上架（`n-switch`）
  - `watch(show)` 时重置表单：编辑模式填充 `editData` 值，新建模式填充默认值
  - 提交时先 `formRef.validate()`，再调用 `createActivity` 或 `updateActivity`
  - 成功后 emit `success` 事件，父组件关闭弹窗并 reload 表格

## 10. Frontend Router & Menu

- [x] 10.1 创建 `br-admin/src/router/modules/activity.ts`：
  - **参考**：`br-admin/src/router/modules/system.ts`
  - 使用 `Layout`（`@/router/constant`）作为父组件
  - 图标使用 `@vicons/ionicons5` 的 `CalendarOutline`，通过 `renderIcon`（`@/utils/index`）包装
  - 路由路径：`/activity`，重定向到 `/activity/list`
  - 子路由：`activity_list`，懒加载 `@/views/activity/list/index.vue`
  - meta.title: '活动管理'，meta.sort: 2（排在系统设置之后）

- [x] 10.2 验证侧边栏菜单自动渲染（项目使用路由自动生成菜单，新模块注册后应自动显示）

## 11. 集成与收尾

- [x] 11.1 运行前端构建验证：`cd br-admin && pnpm run build`，修复 TypeScript 错误和导入问题
- [ ] 11.2 手动验证前端页面（启动 dev server，测试列表加载、搜索筛选、新建编辑、删除、上下架、图片上传）
- [x] 11.3 后端全量测试通过确认：`cd br-server && python -m pytest tests/ -v`
- [ ] 11.4 API 文档更新（docs/api.md 补充新增的相关接口）
- [ ] 11.5 代码审查与重构（确保 Clean Architecture 分层、消除重复代码）
- [ ] 11.6 全量测试通过（单元测试 + 集成测试，覆盖率 > 90%）
