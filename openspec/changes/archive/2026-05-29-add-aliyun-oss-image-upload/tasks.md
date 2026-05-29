## 1. 现状梳理和范围确认

- [x] 1.1 检查 `br-server/app/api/routes/upload.py`，记录当前本地上传的路由、权限、文件校验、路径生成和响应结构。
- [x] 1.2 检查 `br-server/app/main.py` 中 `/uploads` 静态文件挂载，确认本地降级模式需要保留的行为。
- [x] 1.3 检查 `br-server/app/core/config.py`、`.env.example` 和 `br-server/pyproject.toml`，确认配置项和 OSS SDK 依赖的落点。
- [x] 1.4 检查 `br-server/tests/test_api_upload.py` 和 `br-server/tests/test_upload.py`，记录现有上传接口测试覆盖和需要改写的断言。
- [x] 1.5 检查 br-admin 生产上传入口：`src/views/activity/list/ActivityEditModal.vue`、`src/views/room/list/RoomEditModal.vue`、`src/views/setting/account/BasicSetting.vue`、`src/views/system/user/EditModal.vue`。
- [x] 1.6 检查 br-admin 示例上传入口：`src/views/comp/upload/index.vue`、`src/views/form/basicForm/index.vue`、`src/views/setting/system/RevealSetting.vue`，标记为 demo 或非本次生产改造范围。
- [x] 1.7 检查 br-app 用户头像入口：`src/pages/settings/index.vue`、`src/store/modules/user.js`、`src/api/userProfile.js`、`src/utils/request.js`。
- [x] 1.8 使用 `rg "uploadFile|chooseImage|n-upload|BasicUpload|头像|cover_image|avatar"` 复查 br-app/br-admin 图片上传入口，形成实现时的替换清单。

## 2. 后端配置和依赖

- [x] 2.1 在 `br-server/pyproject.toml` 增加阿里 OSS SDK 依赖，优先使用项目当前 Python 依赖管理方式。
- [x] 2.2 在 `br-server/app/core/config.py` 增加 `UPLOAD_STORAGE_DRIVER`，允许值为 `oss`、`local`，默认开发环境可使用 `local`。
- [x] 2.3 在 `br-server/app/core/config.py` 增加 `OSS_ENDPOINT`、`OSS_BUCKET_NAME`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_PUBLIC_BASE_URL`。
- [x] 2.4 在 `.env.example` 增加 OSS 上传配置示例，并说明生产环境 `OSS_PUBLIC_BASE_URL` 使用 CDN/自定义公开域名。
- [x] 2.5 在配置校验或上传服务初始化中处理 OSS 必填配置缺失，确保上传请求返回 503 而不是启动失败或泄露异常。

## 3. 后端上传领域模块

- [x] 3.1 新建上传 scope 枚举或常量，至少包含 `avatar`、`activity-cover`、`room-cover`、`common`。
- [x] 3.2 新建 scope 大小限制映射：`avatar=2MB`，`activity-cover=5MB`，`room-cover=5MB`，`common=5MB`。
- [x] 3.3 新建图片扩展名白名单，保持 `.jpg`、`.jpeg`、`.png`、`.gif`、`.webp` 兼容。
- [x] 3.4 新建图片 MIME 和基础文件头校验逻辑，避免只靠文件名扩展名判断。
- [x] 3.5 新建文件名规范化逻辑，只保留扩展名，忽略用户上传文件名中的路径片段。
- [x] 3.6 新建对象 key 生成逻辑，格式为 `images/{scope}/YYYY/MM/DD/{uuid}.{ext}`。
- [x] 3.7 新建上传结果数据结构，字段包含 `url`、`object_key`、`size`、`content_type`。
- [x] 3.8 新建统一异常类型或错误映射，覆盖缺少文件、非法类型、超出大小、OSS 配置缺失、OSS 上传失败。

## 4. 后端存储适配器

- [x] 4.1 新建存储适配器接口，定义上传对象输入和统一返回结果。
- [x] 4.2 实现本地存储适配器，继续写入 `uploads/YYYY/MM/DD/<uuid>.<ext>` 或等价路径，并返回 `/uploads/...`。
- [x] 4.3 实现阿里 OSS 存储适配器，使用服务端凭据调用 OSS 上传对象。
- [x] 4.4 OSS 适配器返回 URL 时必须用 `OSS_PUBLIC_BASE_URL` 拼接 `object_key`，不得返回内网 Endpoint。
- [x] 4.5 新建存储适配器工厂，根据 `UPLOAD_STORAGE_DRIVER` 选择 `oss` 或 `local`。
- [x] 4.6 确保 OSS 上传失败时转换为稳定业务错误，不向 API 响应暴露 AccessKey、Bucket 内部异常或堆栈。

## 5. 后端 API 接入

- [x] 5.1 将 `br-server/app/api/routes/upload.py` 中的本地写文件逻辑迁移到上传服务，路由只负责认证、接收参数和返回响应。
- [x] 5.2 保留 `POST /api/v1/admin/upload`，继续要求 `upload:create` 权限。
- [x] 5.3 为 admin 上传接口增加可选 `scope` 表单字段；未传时默认为 `common`。
- [x] 5.4 新增 br-app 已登录用户图片上传接口，例如 `POST /api/v1/upload/image`，不依赖 admin 权限。
- [x] 5.5 br-app 上传接口仅允许用户态认证；未登录返回 401。
- [x] 5.6 br-app 头像上传使用 `avatar` scope，若接口允许传 scope，服务端必须校验 scope 在白名单内。
- [x] 5.7 更新上传响应 Schema 所在文件，确保 admin/app 上传接口响应字段一致。
- [x] 5.8 确认 `br-server/app/main.py` 的 `/uploads` 静态挂载仍服务于 `local` 降级模式。

## 6. 后端测试

- [x] 6.1 新增图片校验单元测试，覆盖合法 jpg/png/webp、非法扩展名、伪造扩展名、空文件。
- [x] 6.2 新增 scope 大小限制测试，覆盖 `avatar` 超过 2MB 被拒绝，封面/通用不超过 5MB 可继续处理。
- [x] 6.3 新增对象 key 生成测试，覆盖日期目录、UUID 扩展名、scope 前缀和 `../../avatar.png` 路径剥离。
- [x] 6.4 新增本地存储适配器测试，验证文件写入路径和返回 `/uploads/...`。
- [x] 6.5 新增 OSS 适配器测试，使用 fake/mock OSS 客户端验证 bucket、object key、content type 和公开 URL。
- [x] 6.6 更新 admin 上传接口测试，覆盖成功上传返回 `url/object_key/size/content_type`。
- [x] 6.7 更新 admin 上传接口测试，覆盖无权限、缺少文件、非法类型、scope 超限和 OSS 配置缺失。
- [x] 6.8 新增 br-app 上传接口测试，覆盖未登录 401、已登录上传成功、无需 `upload:create` 权限。
- [x] 6.9 运行后端上传相关测试命令，并记录通过结果。

## 7. br-admin 通用上传客户端

- [x] 7.1 新建 `br-admin/src/api/upload/index.ts`，定义 `UploadScope`、`UploadResult` 和 `uploadImage(file, scope)`。
- [x] 7.2 `uploadImage` 调用 `/v1/admin/upload`，使用 `FormData` 传 `file` 和 `scope`。
- [x] 7.3 将 `br-admin/src/api/activity/index.ts` 中通用 `uploadFile` 迁移到新上传 API；如保留兼容导出，需要内部转调新客户端。
- [x] 7.4 确认通用上传客户端使用现有 Alova admin meta 和认证请求链路。
- [x] 7.5 增加或更新类型导出，避免业务模块重复定义上传响应类型。

## 8. br-admin 业务入口接入

- [x] 8.1 修改 `ActivityEditModal.vue`，活动封面上传调用 `uploadImage(file, 'activity-cover')`。
- [x] 8.2 修改 `ActivityEditModal.vue`，上传成功后写入 `formValues.cover_image = result.url` 并保留预览。
- [x] 8.3 修改 `ActivityEditModal.vue`，上传失败时展示失败提示且不清空已有封面。
- [x] 8.4 修改 `RoomEditModal.vue`，自习室封面上传调用 `uploadImage(file, 'room-cover')`。
- [x] 8.5 移除 `RoomEditModal.vue` 从 `@/api/activity` 导入上传函数的耦合。
- [x] 8.6 修改 `RoomEditModal.vue`，上传失败时展示失败提示且不清空已有封面。
- [x] 8.7 修改 `BasicSetting.vue`，账号头像从纯 URL 输入升级为图片上传加预览，并保存返回的 OSS URL。
- [x] 8.8 修改 `BasicSetting.vue`，头像上传失败时保留原头像，提交资料时仍走现有 profile 更新接口。
- [x] 8.9 修改 `system/user/EditModal.vue`，系统用户头像支持统一上传客户端；如保留手动 URL 输入，需要与上传结果共用同一个 `avatar` 字段。
- [x] 8.10 使用 `rg "@/api/activity.*upload|uploadActivityFile|n-upload|BasicUpload|头像URL"` 复查生产路径，确认无生产入口绕过统一上传客户端。

## 9. br-app 上传客户端

- [x] 9.1 新建 `br-app/src/api/upload.js`，封装 `uploadImage(filePath, scope)`。
- [x] 9.2 `uploadImage` 使用 `uni.uploadFile` 调用 br-server 用户上传接口，表单字段包含 `file` 和 `scope`。
- [x] 9.3 `uploadImage` 复用现有登录 token 获取方式，确保请求头携带用户认证信息。
- [x] 9.4 `uploadImage` 解析后端 JSON 响应，返回 `url/object_key/size/content_type`。
- [x] 9.5 `uploadImage` 统一处理 HTTP 非 2xx、业务错误和 JSON 解析失败，向页面抛出可展示错误。

## 10. br-app 设置页头像上传

- [x] 10.1 修改 `br-app/src/pages/settings/index.vue`，移除头像点击时“头像上传暂未开放”的逻辑。
- [x] 10.2 头像点击后调用 `uni.chooseImage`，限制选择 1 张图片并优先选择压缩图或等价移动端友好配置。
- [x] 10.3 用户取消选择图片时不提示错误、不修改头像。
- [x] 10.4 选择图片后调用 `uploadImage(tempFilePath, 'avatar')`。
- [x] 10.5 上传中禁止重复点击头像，并展示现有风格的 loading 或禁用状态。
- [x] 10.6 上传成功后调用 `userStore.updateProfile({ avatar: result.url })` 或现有用户资料更新 API。
- [x] 10.7 用户资料保存成功后刷新设置页头像和“我的”页头像。
- [x] 10.8 上传失败时展示“头像上传失败，请重试”，并保留原头像。
- [x] 10.9 用户资料保存失败时展示“头像保存失败，请重试”，并保留原头像。
- [x] 10.10 使用 `rg "chooseImage|uploadFile|头像上传暂未开放|avatar"` 复查 br-app，确认本次只新增头像上传生产入口。

## 11. 文档和 OpenSpec

- [x] 11.1 更新 `docs/api.md`，记录 `POST /api/v1/admin/upload` 的权限、请求字段、scope、响应字段和错误码。
- [x] 11.2 更新 `docs/api.md`，记录 br-app 用户图片上传接口的认证要求、请求字段、scope、响应字段和错误码。
- [x] 11.3 更新 `.env.example` 或部署说明，记录 OSS Bucket、Endpoint、AccessKey、Secret、`OSS_PUBLIC_BASE_URL`、`UPLOAD_STORAGE_DRIVER`。
- [x] 11.4 文档中明确生产图片 URL 使用 CDN/自定义公开域名，小程序需配置该域名为合法域名。
- [x] 11.5 文档中明确回滚方式：`UPLOAD_STORAGE_DRIVER=local`，前端无需改接口。
- [x] 11.6 实现完成后同步 OpenSpec 主规格：`file-upload`、`profile-settings-ui`、`activity-admin-ui`、`study-room-admin-ui`。

## 12. 验证和审查

- [x] 12.1 运行后端上传单元测试和接口测试：`DATABASE_URL=sqlite+aiosqlite:///:memory: pytest tests/test_upload.py tests/test_api_upload.py tests/test_api_user_profile.py -q`，30 passed。
- [x] 12.2 运行现有用户资料测试，确认头像字段更新未回归：同 12.1 覆盖 `tests/test_api_user_profile.py`，通过。
- [x] 12.3 运行 br-admin 类型检查或构建，确认活动、自习室、账号头像、系统用户头像上传入口编译通过：`pnpm run build` 通过。
- [x] 12.4 运行 br-app 构建，确认设置页头像上传流程无编译错误：`npm run build:mp-weixin` 通过。
- [x] 12.5 使用 `rg` 复查 br-admin/br-app 生产上传入口，确认没有绕过统一上传客户端。
- [x] 12.6 审查 Clean Architecture 分层：路由不包含 OSS 细节，存储适配器不包含 HTTP 认证逻辑，前端业务页不重复封装上传协议。
- [x] 12.7 审查安全边界：AccessKey Secret 只存在服务端配置，前端源码和构建配置不包含密钥。
- [x] 12.8 运行 `openspec status --change add-aliyun-oss-image-upload`，确认所有工件完成。
- [x] 12.9 运行 `git diff --check`，确认无格式和空白错误。
