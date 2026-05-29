## Requirements

### Requirement: File upload API
系统 SHALL 提供图片上传接口，接收 multipart/form-data 格式的图片文件，校验通过后上传到阿里 OSS，并返回可访问的图片 URL。生产环境 URL SHALL 使用配置的 CDN/自定义公开域名。br-admin SHALL 继续使用 `POST /api/v1/admin/upload/` 入口且后端 MUST 强制 `upload:create` 权限；br-app SHALL 使用面向已登录用户的图片上传入口，且不得调用 admin 上传路由。上传响应 SHALL 至少包含 `url`、`object_key`、`size` 和 `content_type`。系统 MUST 支持通过配置切换到本地上传作为开发和回滚降级路径。文件大小限制 SHALL 按 scope 区分：`avatar` 最大 2MB，`activity-cover`、`room-cover`、`common` 最大 5MB。

#### Scenario: Successful admin image upload to OSS
- **GIVEN** 管理员拥有 `upload:create` 权限
- **AND** OSS 配置完整
- **WHEN** 管理员发送 `POST /api/v1/admin/upload/`，附带文件字段 `file`（图片类型）和受控 `scope`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 OSS 或 CDN 公开 URL
- **AND** 响应包含 `object_key`，格式为 `images/{scope}/YYYY/MM/DD/{uuid}.{ext}`
- **AND** 文件内容已写入阿里 OSS
- **AND** 响应 `url` 的域名来自 `OSS_PUBLIC_BASE_URL`

#### Scenario: Successful app image upload to OSS
- **GIVEN** 用户已登录
- **AND** OSS 配置完整
- **WHEN** 用户通过 br-app 上传头像图片
- **THEN** 返回 HTTP 200
- **AND** 响应包含可用于用户资料 `avatar` 字段的图片 URL
- **AND** 服务端不要求该用户拥有 admin 权限

#### Scenario: Unsupported file type
- **WHEN** 用户或管理员上传非图片文件（如 .exe、.sh）
- **THEN** 返回 HTTP 422
- **AND** 响应包含错误信息"仅支持图片文件"
- **AND** 系统不向 OSS 写入对象

#### Scenario: File size exceeds limit
- **WHEN** 用户或管理员上传超过当前 scope 大小上限的文件
- **THEN** 返回 HTTP 422
- **AND** 响应包含文件大小超限错误信息
- **AND** 系统不向 OSS 写入对象

#### Scenario: Avatar scope size limit
- **WHEN** 用户上传 scope 为 `avatar` 且大小超过 2MB 的图片
- **THEN** 返回 HTTP 422
- **AND** 系统不向 OSS 写入对象

#### Scenario: Cover scope size limit
- **WHEN** 管理员上传 scope 为 `activity-cover` 或 `room-cover` 且大小不超过 5MB 的图片
- **THEN** 系统继续执行类型校验和上传流程

#### Scenario: Missing file field
- **WHEN** 用户或管理员发送请求但未包含 `file` 字段
- **THEN** 返回 HTTP 422
- **AND** 响应包含校验错误信息

#### Scenario: OSS configuration missing
- **GIVEN** 上传存储驱动配置为 `oss`
- **AND** OSS 必填配置缺失
- **WHEN** 用户或管理员上传图片
- **THEN** 返回 HTTP 503
- **AND** 响应说明图片上传服务暂不可用
- **AND** 系统不得泄露 AccessKey、Secret 或内部异常堆栈

### Requirement: Uploaded file access
系统 SHALL 返回可直接被 br-app 和 br-admin 展示的图片 URL。生产环境图片 URL SHALL 使用配置的 CDN/自定义域名；本地降级模式 MAY 返回 `/uploads/{path}` 路径并继续通过本地静态文件服务访问。

#### Scenario: Access OSS uploaded file
- **GIVEN** 图片已成功上传到阿里 OSS
- **WHEN** br-app 或 br-admin 使用响应中的 `url` 渲染图片
- **THEN** 图片可以通过公开 URL 加载
- **AND** URL 域名来自配置的 CDN/自定义域名

#### Scenario: Access local fallback uploaded file
- **GIVEN** 上传存储驱动配置为 `local`
- **WHEN** 客户端请求响应中的 `/uploads/{path}` URL
- **THEN** 返回 HTTP 200，响应为图片文件内容

#### Scenario: File not found in local fallback
- **GIVEN** 上传存储驱动配置为 `local`
- **WHEN** 客户端请求不存在的 `/uploads/{path}` 文件路径
- **THEN** 返回 HTTP 404

### Requirement: Upload file naming
系统 SHALL 对上传图片使用 UUID 重命名，保留规范化后的原始扩展名，并按业务 scope、年、月、日生成对象 key。系统 MUST 忽略用户提供的目录路径，防止路径穿越和覆盖已有对象。

#### Scenario: OSS object key naming and directory structure
- **WHEN** 管理员上传名为 `photo.jpg` 的活动封面，scope 为 `activity-cover`
- **THEN** 对象 key 为 `images/activity-cover/YYYY/MM/DD/<uuid>.jpg`
- **AND** `<uuid>` 为随机生成的 UUID

#### Scenario: Strip unsafe filename path
- **WHEN** 用户上传原始文件名为 `../../avatar.png` 的图片
- **THEN** 系统仅使用扩展名 `.png`
- **AND** 生成的对象 key 不包含用户提供的目录片段

### Requirement: Unified image upload clients
br-admin 和 br-app SHALL 各自提供统一图片上传 API 客户端，所有业务图片上传入口 MUST 复用该客户端。业务模块不得继续从活动模块导入通用上传函数，也不得绕过后端直接携带 OSS Secret 上传。

#### Scenario: br-admin modules use shared upload client
- **GIVEN** br-admin 存在活动封面、自习室封面、账号头像或系统用户头像上传入口
- **WHEN** 这些入口上传图片
- **THEN** 它们 SHALL 调用共享上传 API 客户端
- **AND** 不从 `@/api/activity` 导入通用上传函数

#### Scenario: br-app avatar uses shared upload client
- **GIVEN** br-app 用户在“我的设置”页面修改头像
- **WHEN** 用户选择头像图片
- **THEN** 页面 SHALL 调用 br-app 共享上传 API 客户端
- **AND** 上传成功后使用返回的 `url` 更新用户头像资料

#### Scenario: Future br-app image upload uses shared upload client
- **GIVEN** br-app 后续新增其他生产图片上传入口
- **WHEN** 该入口上传图片
- **THEN** 它 SHALL 复用 br-app 共享上传 API 客户端

#### Scenario: Upload secret is not exposed to frontend
- **WHEN** 检查 br-app 和 br-admin 构建产物或源码配置
- **THEN** 不存在 OSS AccessKey Secret
- **AND** 前端只知道后端上传接口地址和公开图片 URL
