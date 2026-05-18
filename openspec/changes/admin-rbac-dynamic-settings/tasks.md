## 1. 后端数据模型与迁移

- [x] 1.1 创建管理员用户模型 `AdminUser`
  - 文件：`br-server/app/models/admin_user.py`
  - 使用 SQLAlchemy 2.0 `Mapped` 风格，主键使用 UUID
  - 字段覆盖：`id`、`username`、`password_hash`、`nickname`、`email`、`mobile`、`avatar`、`status`、`is_super_admin`、`created_at`、`updated_at`
  - 约束覆盖：`username` 唯一并索引，`status` 限定 `active/disabled`

- [x] 1.2 创建角色模型 `AdminRole`
  - 文件：`br-server/app/models/admin_role.py`
  - 字段覆盖：`id`、`name`、`code`、`description`、`status`、`is_default`、`created_at`、`updated_at`
  - 约束覆盖：`code` 唯一并索引，`status` 限定 `active/disabled`

- [x] 1.3 创建菜单权限模型 `AdminMenu`
  - 文件：`br-server/app/models/admin_menu.py`
  - 字段覆盖：`id`、`parent_id`、`type`、`title`、`permission_code`、`path`、`name`、`component`、`redirect`、`icon`、`sort`、`hidden`、`keep_alive`、`enabled`、`created_at`、`updated_at`
  - 约束覆盖：自关联 `parent_id`，`type` 限定 `directory/menu/button`，`permission_code` 唯一可空
  - 行为边界：`button` 作为权限节点，不作为动态路由节点

- [x] 1.4 创建关联表模型
  - 文件：`br-server/app/models/admin_role.py` 或独立关系模型文件
  - 表：`admin_user_roles`，字段 `admin_user_id`、`admin_role_id`
  - 表：`admin_role_menus`，字段 `admin_role_id`、`admin_menu_id`
  - 约束覆盖：联合唯一约束，外键删除策略明确，避免重复授权

- [x] 1.5 创建系统设置模型 `SystemSetting`
  - 文件：`br-server/app/models/admin_setting.py`
  - 字段覆盖：`key`、`value`、`group`、`is_secret`、`created_at`、`updated_at`
  - 约束覆盖：`key` 唯一，`group` 限定 `basic/email`
  - 安全边界：`is_secret=true` 的值不得在读取 API 中明文返回

- [x] 1.6 更新模型导出
  - 文件：`br-server/app/models/__init__.py`
  - 导入 `AdminUser`、`AdminRole`、`AdminMenu`、关联表、`SystemSetting`
  - 验证 Alembic autogenerate 能识别新增表

- [x] 1.7 创建 Alembic 迁移
  - 目录：`br-server/alembic/versions/`
  - 迁移只创建表、索引、约束，不插入默认管理员、默认菜单或系统设置
  - 覆盖 upgrade 和 downgrade
  - 验证命令：在 `br-server` 执行 `alembic upgrade head` 和 `alembic downgrade -1`

## 2. 后端认证与权限上下文

- [x] 2.1 新增管理员认证 schema
  - 文件：`br-server/app/schemas/admin_auth.py`
  - 覆盖登录请求、token 响应、当前管理员响应、角色摘要、权限项、资料更新、密码更新
  - 响应格式要求：`permissions` 每项包含 `label` 和 `value`
  - 校验要求：`confirm_password` 必须与 `new_password` 一致

- [x] 2.2 新增管理员认证服务
  - 文件：`br-server/app/services/admin_auth_service.py`
  - 覆盖密码 hash、密码 verify、登录校验、disabled 用户拒绝、签发 admin access token
  - 覆盖当前管理员角色与权限聚合
  - 权限聚合要求：super admin 返回全部启用权限，普通管理员返回角色授权的 menu/button 权限

- [x] 2.3 扩展 JWT 或 token 服务以区分 admin token
  - 文件：`br-server/app/services/jwt_service.py` 或新增 `br-server/app/services/admin_token_service.py`
  - admin token payload 必须能解析出管理员 id，并与前台用户 token 语义隔离
  - 保持现有前台用户登录和测试不回归

- [x] 2.4 升级管理端依赖
  - 文件：`br-server/app/api/dependencies.py`
  - 新增 `AdminContext`，包含 `admin_id`、`username`、`is_super_admin`、`permission_codes`
  - 新增 `get_current_admin_context()`，支持 `Authorization: Bearer <token>` 和 legacy `X-Admin-Token`
  - 保留 `get_current_admin` 兼容入口，逐步改为返回或依赖 `AdminContext`
  - 新增 `require_admin_permission(permission_code)`，无认证返回 401，无权限返回 403
  - legacy `X-Admin-Token` 命中 `ADMIN_TOKEN` 时返回超级管理员上下文

- [x] 2.5 新增管理员认证路由
  - 文件：`br-server/app/api/routes/admin_auth.py`
  - 路由：`POST /api/v1/admin/auth/login`
  - 路由：`GET /api/v1/admin/auth/me`
  - 路由：`PUT /api/v1/admin/auth/profile`
  - 路由：`PUT /api/v1/admin/auth/password`
  - 行为要求：profile API 不允许修改 `username`；password API 校验旧密码和确认密码

- [x] 2.6 注册管理员认证路由
  - 文件：`br-server/app/main.py`
  - include `admin_auth_router`
  - 确认路由前缀与 spec 一致：`/api/v1/admin/auth/*`

## 3. 后端菜单与动态路由 API

- [x] 3.1 新增组件白名单定义
  - 文件：`br-server/app/services/admin_menu_service.py` 或 `br-server/app/core/admin_components.py`
  - 首批值：`LAYOUT`、`/dashboard/console/console`、`/system/menu/menu`、`/system/role/role`、`/setting/account/account`、`/setting/system/system`、`/room/list/index`、`/room/seats/index`、`/activity/list/index`、`/booking/list/index`
  - 创建/更新 directory 或 menu 时校验 component；非法值返回 422

- [x] 3.2 新增菜单 schema
  - 文件：`br-server/app/schemas/admin_menu.py`
  - 覆盖树节点响应、创建请求、更新请求、组件选项响应、动态路由响应
  - 字段命名需兼容 br-admin `generateRoutes`：`path`、`name`、`component`、`redirect`、`meta`、`children`
  - `meta` 必须包含 `title`、`icon`、`permissions`、`hidden`、`keepAlive`

- [x] 3.3 新增菜单服务
  - 文件：`br-server/app/services/admin_menu_service.py`
  - 支持完整权限树读取：directory/menu/button 全部返回
  - 支持菜单创建、更新、删除、启停、排序字段保存
  - 删除约束：有子节点返回 409；已被角色授权的节点返回 409
  - 动态路由树规则：只返回 enabled 的 directory/menu，不返回 button
  - 权限过滤规则：super admin 返回全部启用路由；普通管理员只返回授权节点并保留必要父级 directory

- [x] 3.4 新增菜单路由
  - 文件：`br-server/app/api/routes/admin_menu.py`
  - `GET /api/v1/admin/menus` 需要 `system:menu:view`
  - `POST /api/v1/admin/menus` 需要 `system:menu:create`
  - `PUT /api/v1/admin/menus/{menu_id}` 需要 `system:menu:update`
  - `DELETE /api/v1/admin/menus/{menu_id}` 需要 `system:menu:delete`
  - `GET /api/v1/admin/menus/component-options` 需要 `system:menu:view`
  - `GET /api/v1/admin/menus/routes` 需要已认证管理员上下文，不额外要求菜单管理权限

- [x] 3.5 注册菜单路由
  - 文件：`br-server/app/main.py`
  - include `admin_menu_router`
  - 确认 `/routes` 返回结构可被 `br-admin/src/router/generator.ts` 直接转换

## 4. 后端角色权限 API

- [x] 4.1 新增角色 schema
  - 文件：`br-server/app/schemas/admin_role.py`
  - 覆盖分页列表、角色详情、创建请求、更新请求、授权树响应、授权保存请求
  - 分页响应使用原生 REST 格式：`items`、`total`、`page`、`page_size`

- [x] 4.2 新增角色服务
  - 文件：`br-server/app/services/admin_role_service.py`
  - 支持角色分页、按 name/code 搜索、创建、更新、删除
  - 重复 `code` 返回 409
  - 删除已分配给管理员用户的角色返回 409
  - 授权读取返回完整 directory/menu/button 权限树和 checked menu ids
  - 授权保存允许 directory/menu/button 节点 id

- [x] 4.3 新增角色路由
  - 文件：`br-server/app/api/routes/admin_role.py`
  - `GET /api/v1/admin/roles` 需要 `system:role:view`
  - `POST /api/v1/admin/roles` 需要 `system:role:create`
  - `PUT /api/v1/admin/roles/{role_id}` 需要 `system:role:update`
  - `DELETE /api/v1/admin/roles/{role_id}` 需要 `system:role:delete`
  - `GET /api/v1/admin/roles/{role_id}/menus` 需要 `system:role:view`
  - `PUT /api/v1/admin/roles/{role_id}/menus` 需要 `system:role:assign`

- [x] 4.4 注册角色路由
  - 文件：`br-server/app/main.py`
  - include `admin_role_router`
  - 确认按钮授权后 `/api/v1/admin/auth/me` 能返回对应 permission code

## 5. 后端系统设置 API

- [x] 5.1 新增设置 schema
  - 文件：`br-server/app/schemas/admin_setting.py`
  - 覆盖基础设置：`site_name`、`icp_code`、`contact_phone`、`contact_address`、`login_captcha`、`system_open`、`close_text`、`login_desc`
  - 覆盖邮件设置：`smtp_host`、`smtp_port`、`smtp_username`、`smtp_password`、`smtp_sender`、`smtp_tls`、`smtp_password_set`
  - 读取响应不得包含 `smtp_password` 明文

- [x] 5.2 新增设置服务
  - 文件：`br-server/app/services/admin_setting_service.py`
  - key-value 存储，服务层提供结构化 basic/email 读写
  - 更新邮件设置不提交 `smtp_password` 时保留旧密码
  - 提交新 `smtp_password` 时更新 secret 值，并在后续读取中只返回 `smtp_password_set=true`

- [x] 5.3 新增邮件测试能力
  - 文件：`br-server/app/services/admin_setting_service.py`
  - 使用当前邮件设置发送测试邮件
  - 配置缺少 `smtp_host`、`smtp_port`、`smtp_sender` 或收件地址时返回 400
  - 若项目无现成邮件客户端，封装最小 smtp 客户端并通过测试替身覆盖

- [x] 5.4 新增设置路由
  - 文件：`br-server/app/api/routes/admin_setting.py`
  - `GET /api/v1/admin/settings` 需要 `system:settings:view`
  - `PUT /api/v1/admin/settings/basic` 需要 `system:settings:update`
  - `PUT /api/v1/admin/settings/email` 需要 `system:settings:update`
  - `POST /api/v1/admin/settings/email/test` 需要 `system:settings:email`

- [x] 5.5 注册设置路由
  - 文件：`br-server/app/main.py`
  - include `admin_setting_router`
  - 确认新 API 不包 `{ code, message, result }`

## 6. 现有管理接口权限校验

- [x] 6.1 为房间管理接口接入权限依赖
  - 文件：`br-server/app/api/routes/admin_study_room.py`
  - 列表/详情使用 `room:view`
  - 创建使用 `room:create`
  - 更新使用 `room:update`
  - 删除使用 `room:delete`
  - 状态变更使用 `room:status`

- [x] 6.2 为座位管理接口接入权限依赖
  - 文件：`br-server/app/api/routes/admin_seat.py`
  - 列表/详情使用 `seat:view`
  - 创建使用 `seat:create`
  - 批量创建使用 `seat:bulk_create`
  - 更新使用 `seat:update`
  - 删除使用 `seat:delete`
  - 状态变更使用 `seat:status`

- [x] 6.3 为活动管理接口接入权限依赖
  - 文件：`br-server/app/api/routes/admin_activity.py`
  - 列表/详情使用 `activity:view`
  - 创建使用 `activity:create`
  - 更新使用 `activity:update`
  - 删除使用 `activity:delete`
  - 状态变更使用 `activity:status`

- [x] 6.4 为订单管理接口接入权限依赖
  - 文件：`br-server/app/api/routes/admin_booking.py`
  - 列表/详情使用 `booking:view`
  - 取消订单使用 `booking:cancel`

- [x] 6.5 为上传和核销管理接口接入权限依赖
  - 文件：`br-server/app/api/routes/upload.py`
  - 上传使用 `upload:create`
  - 文件：`br-server/app/api/routes/booking_verification.py`
  - 管理端核销查询和操作继续支持 legacy token，并按实际管理动作补充权限码

- [x] 6.6 验证 legacy token 兼容
  - 所有已接入权限码的管理接口仍接受正确 `X-Admin-Token`
  - 错误或缺失 legacy token 且无 Bearer token 时返回 401

## 7. Seed 初始化

- [x] 7.1 创建幂等 seed 服务
  - 文件：`br-server/app/services/seed_admin.py`
  - 幂等创建默认管理员、超级管理员角色、默认菜单、按钮权限、系统设置
  - 可重复运行，不重复插入角色、菜单、权限或设置

- [x] 7.2 初始化默认管理员
  - 默认开发账号：`admin / 123456`
  - 支持环境变量：`ADMIN_DEFAULT_USERNAME`、`ADMIN_DEFAULT_PASSWORD`、`ADMIN_DEFAULT_EMAIL`
  - 生产环境未设置 `ADMIN_DEFAULT_PASSWORD` 时拒绝创建弱密码管理员

- [x] 7.3 初始化默认角色和授权
  - 创建 `super_admin` 角色
  - 将默认管理员绑定到 `super_admin`
  - 超级管理员角色授权全部默认 menu/button 权限

- [x] 7.4 初始化默认菜单和按钮权限
  - 覆盖系统设置：菜单设置、角色权限
  - 覆盖设置页面：个人设置、系统设置
  - 覆盖业务管理：房间、座位、活动、订单
  - 为每个核心操作创建按钮权限节点：view/create/update/delete/status/assign/cancel/upload 等
  - 动态路由 component 必须全部来自组件白名单

- [x] 7.5 初始化默认系统设置
  - 写入 basic 和 email 分组的默认 key
  - 邮件密码默认不写入明文弱值

- [x] 7.6 验证 seed 入口
  - 命令：在 `br-server` 执行 `python -m app.services.seed_admin`
  - 验证重复执行不改变记录数量

## 8. 后端测试

- [x] 8.1 新增模型和迁移测试
  - 文件：`br-server/tests/test_admin_models.py`
  - 覆盖唯一约束、关系表、菜单父子关系、设置 secret 标记

- [x] 8.2 新增管理员认证测试
  - 文件：`br-server/tests/test_admin_auth_api.py`
  - 覆盖登录成功、用户名不存在、密码错误、disabled 用户 403
  - 覆盖 `/auth/me` 返回 profile、roles、permissions
  - 覆盖 profile 更新不能改 username
  - 覆盖修改密码成功、旧密码错误、确认密码不一致

- [x] 8.3 新增权限依赖测试
  - 文件：`br-server/tests/test_admin_permissions.py`
  - 覆盖缺失 token 401、错误 legacy token 401、正确 legacy token super admin、Bearer admin token
  - 覆盖普通管理员有权限通过、无权限 403、super admin 跳过权限码

- [x] 8.4 新增菜单 API 测试
  - 文件：`br-server/tests/test_admin_menu_api.py`
  - 覆盖组件白名单查询、非法 component 422、菜单树 CRUD、删除有子节点 409
  - 覆盖动态路由排除 button、排除 disabled 节点、普通管理员按角色过滤、保留必要父目录

- [x] 8.5 新增角色 API 测试
  - 文件：`br-server/tests/test_admin_role_api.py`
  - 覆盖分页、搜索、创建、重复 code 409、更新、删除已分配角色 409
  - 覆盖授权树包含 directory/menu/button，保存 button 权限后 `/auth/me` 返回权限码

- [x] 8.6 新增系统设置 API 测试
  - 文件：`br-server/tests/test_admin_settings_api.py`
  - 覆盖读取 basic/email、更新 basic、更新 email 不传密码保留旧密码、传密码更新
  - 覆盖读取不返回 `smtp_password`，只返回 `smtp_password_set`
  - 覆盖邮件测试配置不完整返回 400

- [x] 8.7 更新现有管理接口测试
  - 文件：`br-server/tests/test_admin_room_routes.py`
  - 文件：`br-server/tests/test_admin_seat_routes.py`
  - 文件：`br-server/tests/test_api_admin_activity.py`
  - 文件：`br-server/tests/test_admin_booking_api.py`
  - 文件：`br-server/tests/test_api_upload.py`
  - 覆盖 Bearer 权限、403、legacy `X-Admin-Token` 兼容

- [x] 8.8 运行后端全量测试
  - 命令：在 `br-server` 执行 `pytest`
  - 预期：现有用户端、钱包、支付、城市、房间、活动、订单等测试不回归

## 9. br-admin API 与认证层改造

- [x] 9.1 改造用户 API
  - 文件：`br-admin/src/api/system/user.ts`
  - 登录改为 `POST /api/v1/admin/auth/login`
  - 当前用户改为 `GET /api/v1/admin/auth/me`
  - 新增 `PUT /api/v1/admin/auth/profile`
  - 新增 `PUT /api/v1/admin/auth/password`
  - 适配新后端不包 `{ code, message, result }` 的响应格式

- [x] 9.2 改造用户 store
  - 文件：`br-admin/src/store/modules/user.ts`
  - 登录保存 `access_token`
  - `getInfo` 保存 `nickname`、`avatar`、`roles`、`permissions`
  - 保持 `usePermission()` 读取的 permission item 格式为 `{ label, value }`
  - 登录失败时保持当前错误提示体验

- [x] 9.3 统一 Bearer token 请求头
  - 文件：`br-admin/src/utils/http/alova/index.ts`
  - 新 admin API 使用 `Authorization: Bearer <token>`
  - 现有 room/seat/activity/booking/upload API 在迁移后优先使用 Bearer token
  - 如需兼容旧接口，legacy `X-Admin-Token` 只作为 fallback，不作为新接口主路径

- [x] 9.4 改造菜单 API
  - 文件：`br-admin/src/api/system/menu.ts`
  - 接入菜单 CRUD：`/api/v1/admin/menus`
  - 接入组件白名单：`/api/v1/admin/menus/component-options`
  - 接入动态路由：`/api/v1/admin/menus/routes`
  - 输出结构兼容 `br-admin/src/router/generator.ts`

- [x] 9.5 改造角色 API
  - 文件：`br-admin/src/api/system/role.ts`
  - 接入 `/api/v1/admin/roles`
  - 适配 BasicTable：将后端 `items/total/page/page_size` 转成页面需要的分页结构
  - 接入角色授权读取和保存：`GET/PUT /api/v1/admin/roles/{role_id}/menus`

- [x] 9.6 新增系统设置 API
  - 文件：`br-admin/src/api/system/setting.ts`
  - 接入 `GET /api/v1/admin/settings`
  - 接入 `PUT /api/v1/admin/settings/basic`
  - 接入 `PUT /api/v1/admin/settings/email`
  - 接入 `POST /api/v1/admin/settings/email/test`

- [x] 9.7 更新业务管理 API header
  - 文件：`br-admin/src/api/room/index.ts`
  - 文件：`br-admin/src/api/seat/index.ts`
  - 文件：`br-admin/src/api/activity/index.ts`
  - 文件：`br-admin/src/api/booking/index.ts`
  - 移除手写 `X-Admin-Token` 主路径，改用统一 Bearer token 注入

## 10. br-admin 动态路由改造

- [x] 10.1 切换后端动态路由模式
  - 文件：`br-admin/src/settings/projectSetting.ts`
  - `permissionMode` 从 `FIXED` 改为 `BACK`
  - 确认登录后调用 `/api/v1/admin/menus/routes`

- [x] 10.2 校准动态路由生成器
  - 文件：`br-admin/src/router/generator.ts`
  - 确认后端 `LAYOUT` 和页面 component 能被 `LayoutMap` 与 `import.meta.glob('../views/**/*.{vue,tsx}')` 解析
  - 确认 `meta.hidden`、`meta.keepAlive`、`meta.permissions` 映射保留
  - 对无法匹配组件的情况保留清晰 console warning，避免白屏难查

- [x] 10.3 校准异步路由 store
  - 文件：`br-admin/src/store/modules/asyncRoute.ts`
  - BACK 模式下以后端 routes 为准，不再用 mock `/api/menus`
  - 权限过滤不应误删后端已经按角色过滤后的父级 directory
  - 空路由集合时能进入基础路由或 403 页面，而不是无限重定向

- [x] 10.4 清理 mock 菜单依赖
  - 文件：`br-admin/src/utils/http/alova/mocks.ts`
  - 移除或停用登录、`/admin_info`、`/api/menus` 对本次流程的依赖
  - 确认开发环境不会继续命中 mock 数据

## 11. br-admin 菜单设置页改造

- [x] 11.1 改造菜单列表加载
  - 文件：`br-admin/src/views/system/menu/menu.vue`
  - 打开页面调用 `GET /api/v1/admin/menus`
  - 展示 directory/menu/button 完整权限树
  - 移除“页面数据为 Mock 示例数据，非真实数据”提示

- [x] 11.2 改造菜单创建/编辑抽屉
  - 文件：`br-admin/src/views/system/menu/CreateDrawer.vue`
  - type 支持 `directory`、`menu`、`button`
  - directory/menu 显示 path、name、component、redirect、icon、sort、hidden、keep_alive、enabled
  - button 显示 title、permission_code、sort、enabled，不要求 component
  - component 使用 `/api/v1/admin/menus/component-options` 下拉选择

- [x] 11.3 接入菜单保存和删除
  - 文件：`br-admin/src/views/system/menu/menu.vue`
  - 新增调用真实创建接口
  - 编辑调用真实更新接口
  - 删除调用真实删除接口，409 时显示后端错误信息
  - 保存成功后刷新树

- [x] 11.4 校验菜单配置体验
  - 文件：`br-admin/src/views/system/menu/CreateDrawer.vue`
  - directory/menu 提交前校验 component 来自白名单
  - button 提交前校验 permission_code 非空
  - hidden、keepAlive、enabled 使用明确的开关控件

## 12. br-admin 角色权限页改造

- [x] 12.1 改造角色列表
  - 文件：`br-admin/src/views/system/role/role.vue`
  - 打开页面调用 `GET /api/v1/admin/roles`
  - 搜索按 name/code 传参
  - 表格分页使用后端真实 total

- [x] 12.2 改造角色创建和编辑
  - 文件：`br-admin/src/views/system/role/CreateModal.vue`
  - 文件：`br-admin/src/views/system/role/EditModal.vue`
  - 字段覆盖 `name`、`code`、`description`、`status`
  - 创建、更新、删除调用真实接口
  - 重复 code 或已分配角色删除失败时显示后端错误信息

- [x] 12.3 改造角色授权弹窗
  - 文件：`br-admin/src/views/system/role/role.vue`
  - 点击菜单权限时调用 `GET /api/v1/admin/roles/{role_id}/menus`
  - 权限树展示 directory/menu/button
  - 勾选结果保存到 `PUT /api/v1/admin/roles/{role_id}/menus`
  - 保存成功后刷新角色列表或当前授权状态

- [x] 12.4 适配按钮权限展示
  - 文件：`br-admin/src/views/system/role/columns.ts`
  - 文件：`br-admin/src/views/system/role/role.vue`
  - 角色页面操作按钮使用 `system:role:create/update/delete/assign`
  - 无权限时按钮隐藏或禁用

## 13. br-admin 个人设置页改造

- [x] 13.1 改造个人资料表单
  - 文件：`br-admin/src/views/setting/account/BasicSetting.vue`
  - 从 `/api/v1/admin/auth/me` 加载 `nickname`、`email`、`mobile`、`avatar`
  - 提交到 `PUT /api/v1/admin/auth/profile`
  - 删除联系地址字段
  - 保存成功后同步 user store 中的昵称和头像

- [x] 13.2 改造安全设置/修改密码
  - 文件：`br-admin/src/views/setting/account/SafetySetting.vue`
  - 表单字段：`old_password`、`new_password`、`confirm_password`
  - 提交到 `PUT /api/v1/admin/auth/password`
  - 旧密码错误显示失败提示；确认密码不一致在前端先校验

- [x] 13.3 校准账户设置容器页
  - 文件：`br-admin/src/views/setting/account/account.vue`
  - 保留个人资料和安全设置入口
  - 确认页面不依赖模板 mock 个人资料

## 14. br-admin 系统设置页改造

- [x] 14.1 改造系统设置容器
  - 文件：`br-admin/src/views/setting/system/system.vue`
  - 只保留基础设置和邮件设置 tab
  - 移除电商模板残留的显示设置 tab

- [x] 14.2 改造基础设置
  - 文件：`br-admin/src/views/setting/system/BasicSetting.vue`
  - 从 `GET /api/v1/admin/settings` 加载 `basic`
  - 提交到 `PUT /api/v1/admin/settings/basic`
  - 字段覆盖 `site_name`、`icp_code`、`contact_phone`、`contact_address`、`login_captcha`、`system_open`、`close_text`、`login_desc`

- [x] 14.3 改造邮件设置
  - 文件：`br-admin/src/views/setting/system/EmailSetting.vue`
  - 从 `GET /api/v1/admin/settings` 加载 `email`
  - 不展示 `smtp_password` 明文
  - 用 `smtp_password_set` 显示已设置/未设置状态
  - 提交到 `PUT /api/v1/admin/settings/email`
  - 不填写新密码时不发送 `smtp_password` 或发送空值并由 API 层清理
  - 测试邮件调用 `POST /api/v1/admin/settings/email/test`

- [x] 14.4 删除或停用无关系统设置组件
  - 文件：`br-admin/src/views/setting/system/RevealSetting.vue`
  - 若不再使用，移除引用；若保留文件，确保路由和 tab 不展示它

## 15. br-admin 按钮权限接入

- [x] 15.1 为房间管理页面补充权限码
  - 文件：`br-admin/src/views/room/list/index.vue`
  - 创建按钮使用 `room:create`
  - 编辑按钮使用 `room:update`
  - 删除按钮使用 `room:delete`
  - 状态按钮使用 `room:status`

- [x] 15.2 为座位管理页面补充权限码
  - 文件：`br-admin/src/views/room/seats/index.vue`
  - 创建按钮使用 `seat:create`
  - 批量创建按钮使用 `seat:bulk_create`
  - 编辑按钮使用 `seat:update`
  - 删除按钮使用 `seat:delete`
  - 状态按钮使用 `seat:status`

- [x] 15.3 为活动管理页面补充权限码
  - 文件：`br-admin/src/views/activity/list/index.vue`
  - 创建按钮使用 `activity:create`
  - 编辑按钮使用 `activity:update`
  - 删除按钮使用 `activity:delete`
  - 状态按钮使用 `activity:status`

- [x] 15.4 为订单管理页面补充权限码
  - 文件：`br-admin/src/views/booking/list/index.vue`
  - 查看按钮使用 `booking:view`
  - 取消按钮使用 `booking:cancel`

- [x] 15.5 为系统管理和设置页面补充权限码
  - 文件：`br-admin/src/views/system/menu/menu.vue`
  - 文件：`br-admin/src/views/system/role/role.vue`
  - 文件：`br-admin/src/views/setting/system/BasicSetting.vue`
  - 文件：`br-admin/src/views/setting/system/EmailSetting.vue`
  - 权限码覆盖 `system:menu:*`、`system:role:*`、`system:settings:*`

- [x] 15.6 验证权限指令和表格动作
  - 文件：`br-admin/src/directives/permission.ts`
  - 文件：`br-admin/src/hooks/web/usePermission.ts`
  - 文件：`br-admin/src/components/Table/src/components/TableAction.vue`
  - 确认后端返回 `{ label, value }` 后，`v-permission`、`TableAction`、列权限过滤均按 `value` 判断

## 16. 前端构建与手工验证

- [x] 16.1 运行 br-admin 类型检查/构建
  - 命令：在 `br-admin` 执行 `pnpm build`
  - 预期：构建通过，无动态 import 路径错误

- [x] 16.2 验证超级管理员登录流程
  - 前置：后端迁移完成并执行 `python -m app.services.seed_admin`
  - 操作：使用默认或环境变量管理员登录 br-admin
  - 预期：保存 access token，进入首页，`/auth/me` 返回 roles 和 permissions

- [x] 16.3 验证后端动态路由
  - 操作：登录后观察左侧菜单
  - 预期：菜单来自 `/api/v1/admin/menus/routes`，不是 mock `/api/menus`
  - 预期：刷新页面后动态路由仍可恢复

- [x] 16.4 验证普通角色菜单权限
  - 操作：创建普通角色，仅授权部分菜单，创建或绑定普通管理员后登录
  - 预期：左侧只显示授权菜单，未授权路由不可直接访问

- [x] 16.5 验证按钮权限
  - 操作：为普通角色取消某个按钮权限后登录
  - 预期：对应 `TableAction` 或 `v-permission` 按钮隐藏或禁用
  - 预期：直接调用未授权接口返回 403

- [x] 16.6 验证菜单设置页面
  - 操作：创建 directory、menu、button 节点
  - 预期：component 下拉来自白名单；button 不要求 component；非法 component 无法保存
  - 操作：删除有子节点菜单
  - 预期：显示 409 错误提示

- [x] 16.7 验证角色权限页面
  - 操作：创建、编辑、删除角色，保存 directory/menu/button 授权
  - 预期：授权保存后 `/auth/me` permissions 反映 button 权限

- [x] 16.8 验证个人设置页面
  - 操作：更新 nickname/email/mobile/avatar
  - 预期：资料保存到 br-server 并同步当前用户显示
  - 操作：修改密码后用新密码登录
  - 预期：旧密码失效，新密码可用

- [x] 16.9 验证系统设置页面
  - 操作：更新基础设置和邮件设置
  - 预期：刷新后配置持久化
  - 预期：SMTP 密码不明文回显，只显示已设置状态

- [x] 16.10 验证 legacy token 兼容
  - 操作：使用正确 `X-Admin-Token` 调用已有管理接口
  - 预期：仍按超级管理员上下文放行
  - 操作：使用错误 `X-Admin-Token`
  - 预期：返回 401

## 17. 文档与收尾

- [x] 17.1 更新 OpenSpec 变更文档状态
  - 文件：`openspec/changes/admin-rbac-dynamic-settings/tasks.md`
  - 实现过程中按完成情况勾选任务

- [x] 17.2 记录 seed 使用方式
  - 文件：`README.md` 或 `br-server/README.md`
  - 说明迁移后执行 `python -m app.services.seed_admin`
  - 说明 `ADMIN_DEFAULT_USERNAME`、`ADMIN_DEFAULT_PASSWORD`、`ADMIN_DEFAULT_EMAIL`
  - 说明生产环境必须显式设置默认密码

- [x] 17.3 记录管理端认证迁移说明
  - 文件：`br-admin/README.md` 或项目部署文档
  - 说明 br-admin 使用 Bearer admin token
  - 说明 legacy `X-Admin-Token` 仅用于兼容和应急

- [x] 17.4 记录 legacy token 后续移除计划
  - 文件：`deploy.md` 或项目维护文档
  - 说明移除前提：br-admin 全部接口已迁移 Bearer token，生产管理员账号和角色已初始化
  - 说明移除范围：`X-Admin-Token` header、legacy super admin context、相关兼容测试

- [x] 17.5 最终验证
  - 后端：在 `br-server` 执行 `pytest`
  - 前端：在 `br-admin` 执行 `pnpm build`
  - OpenSpec：执行项目当前 OpenSpec 校验命令，确认 `admin-rbac-dynamic-settings` 文档格式通过
