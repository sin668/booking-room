# Bug Fixed

记录 user-registration 功能开发过程中发现并修复的所有 BUG。

---

## BUG-1: 前端页面无法渲染

### 报错信息
```
DEPRECATION WARNING [import]: Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  src/App.vue 26:9  root stylesheet
```

### 根本原因
`App.vue` 中使用 `@import '@/uni.scss'` 导入 SCSS 变量，与新版 Sass（Dart Sass 3.0 废计划废弃 `@import`）产生冲突，导致页面渲染失败。而 uni-app 框架会自动将 `uni.scss` 中的变量注入到每个组件的 `<style lang="scss">` 中，无需手动导入。

### 解决方案
从 `src/App.vue` 的 `<style>` 中移除 `@import '@/uni.scss'` 行。

---

## BUG-2: Token 刷新竞态条件

### 报错信息
多个并发 401 请求排队等待 Token 刷新时，重试请求仍使用旧 Token。

### 根本原因
`request.js` 中，排队等待的请求重试时直接创建新的 `uni.request`，但使用的是外层作用域的 `header` 引用，未携带刷新后的新 Token。

### 解决方案
将请求逻辑提取为 `buildRequest(tokenValue)` 内部函数，每次调用时基于传入的 `tokenValue` 构建全新的 header。

**文件**: `br-app/src/utils/request.js`

---

## BUG-3: 验证码倒计时定时器内存泄漏

### 报错信息
页面切换后倒计时继续运行，定时器无法被清理。

### 根本原因
`startCountdown()` 中 `setInterval` 返回的 timer ID 仅存储在函数局部变量中，页面卸载时无引用可清理。

### 解决方案
- 将 timer 存储为模块级变量 `let countdownTimer = null`
- `startCountdown` 前检查并清理旧 timer
- 添加 `onUnmounted()` 生命周期钩子清理定时器
- 增加 `sendCodeLoading` 状态防止重复点击

**文件**: `br-app/src/pages/login/login.vue`

---

## BUG-4: 登录后立即退出

### 报错信息
注册/登录成功后，调用 `fetchUserInfo()` 失败导致用户被自动登出。

### 根本原因
`user.js` 的 `register()` 和 `login()` 中 `await this.fetchUserInfo()`，而 `fetchUserInfo()` 内部 catch 块直接调用 `this.logout()` 清除 Token，导致刚登录成功的用户立即被登出。

### 解决方案
将 `fetchUserInfo` 调用改为非阻塞：`this.fetchUserInfo().catch(() => {})`，登录/注册流程不因获取用户信息失败而中断。

**文件**: `br-app/src/store/modules/user.js`

---

## BUG-5: 后端硬编码生产凭据

### 报错信息
`config.py` 中硬编码了数据库密码、Redis 地址、JWT 密钥和阿里云 AccessKey。

### 根本原因
开发阶段将真实凭据直接写入代码并提交到仓库，存在严重安全风险。

### 解决方案
- 所有敏感配置项默认值设为空字符串 `""`
- 创建 `.env.example` 模板，用户复制为 `.env` 填写实际值
- JWT 密钥生成说明：`openssl rand -hex 32`

**文件**: `br-server/app/core/config.py`, `br-server/.env.example`

---

## BUG-6: Cookie secure 参数硬编码

### 报错信息
`response.set_cookie(secure=False)` 写死，生产环境 HTTPS 下 Cookie 不安全。

### 根本原因
缺少配置项控制 Cookie 安全属性，生产环境部署时容易遗漏。

### 解决方案
新增 `COOKIE_SECURE: bool = False` 配置项，`_set_refresh_token_cookie()` 读取配置值。

**文件**: `br-server/app/core/config.py`, `br-server/app/api/routes/auth.py`

---

## BUG-7: 重复的认证依赖函数

### 报错信息
`_get_current_user_id()` 在 `auth.py` 和 `user.py` 中各定义一份，违反 DRY 原则。

### 根本原因
两个路由文件独立定义了相同的认证依赖函数，后续维护需同步修改两处。

### 解决方案
提取到 `app/api/dependencies.py`，两个路由文件统一导入。

**文件**: `br-server/app/api/dependencies.py`（新建）, `br-server/app/api/routes/auth.py`, `br-server/app/api/routes/user.py`

---

## BUG-8: JWT Token 生成代码重复 3 处

### 报错信息
`auth.py` 的 `register`、`login`、`refresh` 三个路由中，解码 Access Token → 提取 user_id → 创建 Refresh Token → 解码 RT → 存储的代码完全相同。

### 根本原因
未将 Token 对生成逻辑抽象为公共方法，导致 3 处重复约 15 行代码。

### 解决方案
提取 `_issue_cookie_token(jwt_svc, access_token)` 辅助函数到路由模块。

**文件**: `br-server/app/api/routes/auth.py`

---

## BUG-9: 短信发送 500 错误 (JSONDecodeError)

### 报错信息
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### 根本原因
`AliyunSMSProvider.send()` 对阿里云 API 发起 GET 请求，但未按阿里云 API 规范签名（缺少 HMAC-SHA1 Signature），API 返回非 JSON 响应，`resp.json()` 抛出 `JSONDecodeError`。该异常未被 `httpx.HTTPError` 捕获。

### 解决方案
将异常捕获从 `httpx.HTTPError` 扩展为 `Exception`，确保 JSON 解析错误也被捕获。

**文件**: `br-server/app/services/sms_service.py`

---

## BUG-10: 短信 API 未正确签名

### 报错信息
```
Aliyun SMS error: isv.BUSINESS_LIMIT_CONTROL
```

（签名修复前 API 返回签名无效错误；修复后可正常调用。）

### 根本原因
阿里云 Dysms API 要求请求必须包含 HMAC-SHA1 签名参数（Signature、SignatureMethod、SignatureVersion、SignatureNonce、Timestamp 等），原代码仅发送裸参数，API 拒绝请求。

### 解决方案
实现完整的阿里云 API 签名流程：
1. 构建公共参数（Action、Version、Format、RegionId、AccessKeyId 等）
2. 按参数名排序，URL 编码后拼接 canonical query string
3. 构造待签名字符串：`GET&%2F&<编码后的query string>`
4. 使用 Access Key Secret + "&" 作为密钥，HMAC-SHA1 签名
5. Base64 编码后加入 Signature 参数

同时移除 dev mode 降级逻辑，API 调用失败时直接抛出包含错误码的 HTTPException。

**文件**: `br-server/app/services/sms_service.py`

---

## BUG-11: bcrypt 密码长度限制 (passlib + bcrypt 5.0.0 不兼容)

### 报错信息
```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

### 根本原因
`bcrypt >= 4.1` 完全移除了 >72 字节密码支持（直接抛 ValueError）。`passlib` 在初始化时使用长字符串检测 bcrypt wrap bug，触发此限制。`bcrypt 5.0.0` 与 `passlib` 完全不兼容。

### 解决方案
移除 `passlib` 依赖，直接使用 `bcrypt` 库：
- `bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())` 替代 `pwd_context.hash()`
- `bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))` 替代 `pwd_context.verify()`

**文件**: `br-server/app/services/auth_service.py`, `br-server/tests/test_auth_service.py`

---

## 修改文件汇总

| 文件 | BUG |
|------|-----|
| `br-app/src/App.vue` | #1 |
| `br-app/src/utils/request.js` | #2 |
| `br-app/src/pages/login/login.vue` | #3 |
| `br-app/src/store/modules/user.js` | #4 |
| `br-server/app/core/config.py` | #5, #6 |
| `br-server/.env.example` | #5 |
| `br-server/app/api/dependencies.py` | #7 (新建) |
| `br-server/app/api/routes/auth.py` | #6, #8 |
| `br-server/app/api/routes/user.py` | #7 |
| `br-server/app/services/sms_service.py` | #9, #10 |
| `br-server/app/services/auth_service.py` | #11 |
| `br-server/tests/test_auth_service.py` | #11 |
