## Why

当前图片上传仍落在后端本地 `uploads/` 目录，部署到多实例、容器或云环境后会遇到文件丢失、访问域名不统一和扩展性差的问题。需要将图片上传统一迁移到阿里 OSS，并把 br-app 与 br-admin 中所有图片上传入口关联到同一套上传能力。

## What Changes

- 将现有管理端图片上传 API 从本地文件存储改为上传到阿里 OSS，生产环境返回 CDN/自定义域名公开 URL。
- 增加后端 OSS 配置、上传服务、文件类型/大小校验、对象 key 命名规则和错误处理。
- 保留现有 `POST /api/v1/admin/upload` 入口兼容 br-admin，必要时增加面向 br-app 的认证上传入口。
- 统一 br-admin 中活动封面、自习室封面、账号头像等图片上传位置，避免继续手输 URL 或复用活动模块上传函数。
- 关联 br-app 中用户头像上传位置；后续新增小程序图片上传入口必须复用统一 API 客户端。
- 更新 API 文档、OpenSpec 规格和测试，覆盖 OSS 上传成功、配置缺失、非法文件、超大文件和前端上传失败提示。
- 回滚方案：保留可配置的本地上传实现作为降级路径，或通过环境变量切回本地 `uploads/` 存储；数据库中已保存的 OSS URL 不需要迁移回写。

## Capabilities

### New Capabilities

- 无

### Modified Capabilities

- `file-upload`: 图片上传从本地存储扩展为阿里 OSS 存储，并统一 br-app/br-admin 图片上传入口。
- `profile-settings-ui`: br-app 用户资料头像上传从 URL 字段扩展为选择图片并上传到统一图片上传服务。
- `activity-admin-ui`: 活动封面图上传必须走统一 OSS 上传客户端并展示 OSS URL 图片。
- `study-room-admin-ui`: 自习室封面图上传必须走统一 OSS 上传客户端并展示 OSS URL 图片。

## Impact

- 后端模块：`br-server/app/api/routes/upload.py`、新增/调整上传服务、配置项、Schema、测试和 `docs/api.md`。
- br-admin 模块：活动编辑弹窗、自习室编辑弹窗、账号基础设置头像、系统用户头像 URL 表单，以及上传 API 封装。
- br-app 模块：用户资料/设置头像上传 API 封装、图片选择、上传中状态和失败提示。
- 外部系统：阿里云 OSS Bucket、Endpoint、AccessKey/STS 或服务端凭据、CDN/自定义公开访问域名。
- 安全影响：需要严格限制图片 MIME/扩展名/大小，不向前端暴露 OSS AccessKey Secret，RBAC 权限继续在后端强制。
