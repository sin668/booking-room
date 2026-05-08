## ADDED Requirements

### Requirement: File upload API
系统 SHALL 提供 `POST /api/v1/admin/upload/` 接口，接收 multipart/form-data 格式的文件上传，存储到本地 `uploads/` 目录，返回可访问的 URL 路径。

#### Scenario: Successful image upload
- **WHEN** 管理员发送 `POST /api/v1/admin/upload/`，附带文件字段 `file`（图片类型）
- **THEN** 返回 HTTP 200，响应包含 `url`（可访问的文件路径，如 `/uploads/2026/04/23/abc123.jpg`）

#### Scenario: Unsupported file type
- **WHEN** 管理员上传非图片文件（如 .exe、.sh）
- **THEN** 返回 HTTP 422，响应包含错误信息"仅支持图片文件"

#### Scenario: File size exceeds limit
- **WHEN** 管理员上传超过 5MB 的文件
- **THEN** 返回 HTTP 422，响应包含错误信息"文件大小不能超过5MB"

#### Scenario: Missing file field
- **WHEN** 管理员发送请求但未包含 `file` 字段
- **THEN** 返回 HTTP 422，响应包含校验错误信息

### Requirement: Uploaded file access
系统 SHALL 通过 `GET /uploads/{path}` 路由提供已上传文件的访问能力。

#### Scenario: Access uploaded file
- **WHEN** 客户端请求 `GET /uploads/2026/04/23/abc123.jpg`
- **THEN** 返回 HTTP 200，响应为图片文件内容

#### Scenario: File not found
- **WHEN** 客户端请求不存在的文件路径
- **THEN** 返回 HTTP 404

### Requirement: Upload file naming
系统 SHALL 对上传文件使用 UUID 重命名，保留原始扩展名，按年/月/日目录结构存储。

#### Scenario: File naming and directory structure
- **WHEN** 管理员上传名为 `photo.jpg` 的文件
- **THEN** 文件存储到 `uploads/2026/04/23/<uuid>.jpg`，其中 `<uuid>` 为随机生成的 UUID
