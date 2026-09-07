## MODIFIED Requirements

### Requirement: File upload API
系统 SHALL 提供图片上传接口，接收 multipart/form-data 格式的图片文件，校验通过后上传到阿里 OSS，并返回可访问的图片 URL。生产环境 URL SHALL 使用配置的 CDN/自定义公开域名。br-admin SHALL 继续使用 `POST /api/v1/admin/upload/` 入口且后端 MUST 强制 `upload:create` 权限；br-app SHALL 使用面向已登录用户的图片上传入口，且不得调用 admin 上传路由。br-app 用户端上传入口 SHALL 只接受 `avatar` 与 `review` 两种 scope，其余 scope MUST 返回 HTTP 422 并提示上传场景不支持。上传响应 SHALL 至少包含 `url`、`object_key`、`size` 和 `content_type`。系统 MUST 支持通过配置切换到本地上传作为开发和回滚降级路径。文件大小限制 SHALL 按 scope 区分：`avatar` 最大 2MB，`activity-cover`、`room-cover`、`room-environment`、`common`、`review` 最大 5MB。

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

#### Scenario: Successful app review image upload
- **GIVEN** 用户已登录
- **AND** OSS 配置完整
- **WHEN** 用户通过 br-app 以 `review` scope 上传一张不超过 5MB 的评价图片
- **THEN** 返回 HTTP 200
- **AND** 响应 `object_key` 的路径前缀为 `images/review/`
- **AND** 响应 `url` 可直接用于评价记录的 `images` 数组

#### Scenario: App upload rejects unsupported scope
- **GIVEN** 用户已登录
- **WHEN** 用户通过 br-app 用户端上传入口以 `common` 或 `activity-cover` 等非白名单 scope 上传图片
- **THEN** 返回 HTTP 422
- **AND** 响应包含"上传场景不支持"语义的错误信息
- **AND** 系统不向 OSS 写入对象

#### Scenario: Review scope requires login
- **WHEN** 未携带有效登录凭证的请求以 `review` scope 调用 br-app 用户端上传入口
- **THEN** 返回 HTTP 401
- **AND** 系统不向 OSS 写入对象

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

#### Scenario: Review scope size limit
- **WHEN** 用户上传 scope 为 `review` 且大小超过 5MB 的图片
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
