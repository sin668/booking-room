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

## BUG-12: 订单列表页面数据不显示

### 报错信息
```
Uncaught (in promise) ReferenceError: actions is not defined
```

### 根本原因
`br-admin/src/views/booking/list/index.vue` 中 `actionColumn` 的 `render` 函数引用了未定义的 `actions` 变量。该代码复制自活动管理页面（activity/list），活动页面定义了 `actions` 数组（编辑、删除按钮），但订单列表页只有下拉操作（取消），没有定义 `actions`。JavaScript 引擎抛出 `ReferenceError`，导致 `loadDataTable` 异步调用静默失败，BasicTable 组件无法渲染数据行。

### 解决方案
将 `actions` 替换为空数组 `actions: []`：

```diff
- actions,
+ actions: [],
```

**文件**: `br-admin/src/views/booking/list/index.vue`

**提交**: `3ec39c1` fix: resolve undefined `actions` reference in booking list page

---

## BUG-13: 预约详情页加载房间信息返回 422

### 报错信息
```
request.js:57 GET http://localhost:8000/api/v1/rooms?page=1&page_size=100 422 (Unprocessable Entity)
```

### 根本原因
`br-app/src/pages/booking/detail.vue` 在加载 `/booking/detail?room_id=1` 时，为了获取单个自习室信息，调用了列表接口：

```js
getRooms({ page: 1, page_size: 100 })
```

后端 `br-server/app/api/routes/study_room.py` 对列表接口的 `page_size` 参数限制为 `le=50`。前端传入 `page_size=100` 超出校验范围，FastAPI 返回 422。

同类问题也存在于 `br-app/src/pages/booking/seat-select.vue`：缺少 `room_name` 时同样通过 `page_size=100` 的列表接口反查房间名。

### 解决方案
改用已有的房间详情接口 `/api/v1/rooms/{room_id}`：

- `detail.vue` 的 `loadRoom()` 改为 `getRoom(this.roomId)`，不再拉取全量列表。
- `seat-select.vue` 缺少 `roomName` 时改为 `getRoom(this.roomId)`，避免进入选座页再次触发同样的 422。
- `br-app/src/api/rooms.js` 提供 `getRoom(roomId)` API 封装。

**文件**: `br-app/src/api/rooms.js`, `br-app/src/pages/booking/detail.vue`, `br-app/src/pages/booking/seat-select.vue`

---

## BUG-14: UniApp `<script setup>` 中 `onMounted` 导入错误

### 报错信息
```
SyntaxError: The requested module '/node_modules/@dcloudio/uni-app/dist/uni-app.es.js' does not provide an export named 'onMounted' (at index.vue:126:10)
```

### 根本原因
`@dcloudio/uni-app` 仅导出页面级生命周期钩子（`onLoad`、`onShow`、`onReachBottom` 等），不导出 Vue 组件标准生命周期钩子。`onMounted` 是 Vue 3 的标准 Composition API 钩子，应从 `vue` 包导入，而非 `@dcloudio/uni-app`。

### 解决方案
将 `onMounted` 从 `@dcloudio/uni-app` 的导入移至 `vue` 的导入：

```diff
- import { ref, computed } from 'vue'
- import { onMounted, onReachBottom } from '@dcloudio/uni-app'
+ import { ref, computed, onMounted } from 'vue'
+ import { onReachBottom } from '@dcloudio/uni-app'
```

**文件**: `br-app/src/pages/study-record/index.vue`

---

## BUG-15: 卡券时间字段混用 aware/naive datetime 导致下单 500

### 报错信息
调用卡券种子数据和预约下单接口时出现 500：

```
invalid input for query argument $9: datetime.datetime(2026, 5, 13, 2, 35, 11...)
(can't subtract offset-naive and offset-aware datetimes)
```

```
"POST /api/v1/bookings HTTP/1.1" 500 Internal Server Error
invalid input for query argument $3: datetime.datetime(2026, 5, 14, 3, 24, 46...)
(can't subtract offset-naive and offset-aware datetimes)
```

### 根本原因
`coupons.valid_from`、`coupons.expires_at`、`user_coupons.used_at` 等字段在 SQLAlchemy 模型中定义为普通 `DateTime`，对应数据库侧是 timezone-naive 时间字段。

但新增卡券 seed 和使用卡券下单流程里传入了带 `tzinfo` 的 aware datetime：

- `seed_data.py` 使用 `datetime.now(UTC)` 写入 `valid_from` / `expires_at`
- `coupon_service.mark_coupon_used()` 使用 UTC aware datetime 写入 `used_at`

asyncpg 在绑定 PostgreSQL timestamp 参数时遇到 offset-aware 和 offset-naive datetime 混用，触发 `can't subtract offset-naive and offset-aware datetimes`。

另外卡券有效期判断中，原逻辑把数据库里的 naive datetime 当作 UTC 处理，不符合业务要求的中国东八区时间。

### 解决方案
统一卡券相关业务时间为中国所在的东八区 `Asia/Shanghai`：

- seed 数据生成东八区当前时间，并在写入数据库前去掉 `tzinfo`，匹配现有 `DateTime` 字段。
- 卡券服务中有效期比较将数据库 naive datetime 解释为 `Asia/Shanghai`。
- 使用卡券下单时，`user_coupons.used_at` 写入东八区本地 naive datetime，避免 asyncpg 参数绑定错误。
- 保留 JWT、核销 token、短信签名等不写入普通 `DateTime` 数据库列的 UTC 时间逻辑。
- 增加回归测试，确认使用卡券创建预约后 `used_at.tzinfo is None`。

**文件**: `br-server/app/services/seed_data.py`, `br-server/app/services/coupon_service.py`, `br-server/tests/test_api_booking.py`

**验证**:
```
pytest tests/test_coupon_service.py tests/test_api_coupon.py tests/test_api_booking.py -q
# 40 passed
```

---

## BUG-16: 菜单更新接口 500 错误 (MissingGreenlet)

### 报错信息
```
fastapi.exceptions.ResponseValidationError: 5 validation errors:
  {'type': 'get_attribute_error', 'loc': ('response', 'children', 0, 'children'),
   'msg': "Error extracting attribute: MissingGreenlet: greenlet_spawn has not been called;
   can't call await_only() here. Was IO attempted in an unexpected place?"}
  ... (children[1]~[4] 同上)
```

### 根本原因
`AdminMenuService.update()` 方法返回原始 `AdminMenu` ORM 对象。FastAPI 将其序列化为 `AdminMenuNode`（含 `children` 字段）时，访问嵌套的 `children` 关系触发了 SQLAlchemy 的懒加载。在 async session 外部执行 IO 操作导致 `MissingGreenlet` 异常——SQLAlchemy 异步模式下，数据库查询只能在 async session 上下文中通过 greenlet 协程执行。

### 解决方案
将 `update()` 返回类型从 `AdminMenu` 改为 `AdminMenuNode`，复用 `_list_all()` + `_build_model_tree()` 构建纯 Pydantic 树，再通过新增的 `_find_node()` 递归查找目标节点返回。彻底避免返回带懒加载关系的 ORM 对象。

**文件**: `br-server/app/services/admin_menu_service.py`

---

## BUG-17: 座位管理页面 404 (No match found for /room/list/1/seats)

### 报错信息
```
No match found for location with path "/room/list/1/seats"
```

### 根本原因
数据库 `admin_menus` 表中，座位管理菜单（id=11）的 `path` 字段值为 `seats`。br-admin 使用动态路由，路由生成器将父路径 `/room` 与子路径 `seats` 拼接后得到 `/room/seats`，与前端实际访问路径 `/room/list/1/seats` 不匹配。

### 解决方案
将座位管理菜单的 `path` 从 `seats` 更新为 `list/:id/seats`，路由生成器拼接后得到 `/room/list/:id/seats`，与前端访问路径一致。

**修改**: 数据库 `admin_menus` 表 id=11 的 `path` 字段

---

## BUG-18: 角色权限页面 emit 'register' 警告

### 报错信息
```
[Vue warn]: Component emitted event "register" but it is neither declared in the emits option nor as an "onRegister" prop.
```

### 根本原因
`useModal.ts` 的 `register` 回调中调用了 `currentInstance?.emit('register', modalInstance)`，在调用组件（如 CreateModal、EditModal）的实例上触发 'register' 事件。但这些组件仅声明了 `defineEmits(['success'])`，未声明 'register'，导致 Vue 3 发出警告。实际上 register 回调已通过模板 `@register="modalRegister"` 直接传递给子组件 `basicModal`，这行 emit 是多余的。

### 解决方案
删除 `useModal.ts` 中多余的 `currentInstance?.emit('register', modalInstance)` 语句。

**文件**: `br-admin/src/components/Modal/src/hooks/useModal.ts`

---

## 已知行为: /system/menu 初始路由解析警告

### 现象
```
[Vue Router warn]: No match found for location with path "/system/menu"
```

### 说明
br-admin 使用动态路由，路由在 `beforeEach` 导航守卫中从后端 API 加载。浏览器刷新时，Vue Router 先用静态路由解析当前 URL，此时动态路由尚未注册，`/system/menu` 匹配失败产生警告。随后导航守卫触发、加载并注册动态路由，页面正常渲染。功能不受影响，属于 Vue Router 动态路由的预期行为。

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
| `br-admin/src/views/booking/list/index.vue` | #12 |
| `br-app/src/api/rooms.js` | #13 |
| `br-app/src/pages/booking/detail.vue` | #13 |
| `br-app/src/pages/booking/seat-select.vue` | #13 |
| `br-app/src/pages/study-record/index.vue` | #14 |
| `br-server/app/services/seed_data.py` | #15 |
| `br-server/app/services/coupon_service.py` | #15 |
| `br-server/tests/test_api_booking.py` | #15 |
| `br-server/app/services/admin_menu_service.py` | #16 |
| 数据库 `admin_menus` id=11 | #17 |
| `br-admin/src/components/Modal/src/hooks/useModal.ts` | #18 |
