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

## BUG-19: br-admin 菜单图标不显示 + 自习室管理菜单不可点击 + 座位管理菜单不应显示

### 报错信息

1. 左侧菜单所有图标位置为空白（无图标渲染）
2. 点击「房间管理 > 自习室管理」菜单无响应，页面空白
3. 左侧一级菜单出现一个不可点击的「座位管理」菜单项（数据库已设置 `hidden=True`）

### 根本原因

本次修复涉及三个相互关联的问题：

**问题 1：菜单图标不显示**

`br-admin/src/router/icons.ts` 的 `constantRouterIcon` 映射表仅注册了 `DashboardOutlined` 一个图标。后端菜单数据返回的图标名称（`HomeOutlined`、`SettingOutlined`、`MenuOutlined`、`TeamOutlined`、`UserOutlined`、`ToolOutlined`、`AppsOutlined`、`GiftOutlined`、`CalendarOutlined`）在映射表中均无对应条目，前端路由生成器将其设为 `null`，导致图标不渲染。

另外 `AppsOutlined` 在 `@vicons/antd` 包中不存在，正确名称为 `AppstoreOutlined`。

**问题 2：自习室管理菜单不可点击**

后端 `seed_admin.py` 中目录类型菜单的 `path` 字段存储的是完整路径（如 `/room/list`、`/system/menu`），而非基路径（如 `/room`、`/system`）。前端路由生成器 `generator.ts` 会将父路径与子路径拼接：

```typescript
path: `${parentPath}/${itemPath}`
```

以 room 为例，父路径 `/room/list` + 子路径 `list` → 生成路由 `/room/list/list`，与实际页面路径 `/room/list` 不匹配，导致点击菜单后 Vue Router 找不到对应组件。

**问题 3：座位管理菜单不应显示**

前端在 BACK 权限模式下，为支持含动态参数的隐藏页面（如 `/room/list/:id/seats`），将静态路由模块中 `hideInMenu: true` 的子路由合并到动态路由中。但合并时仅在子路由的 `meta` 上设置了 `hideInMenu`，而前端菜单过滤函数 `filterRouter` 检查的是 `meta.hidden` 字段，两者不一致：

- 静态路由使用：`meta.hideInMenu = true`
- 菜单过滤检查：`meta.hidden === true`

导致合并后的隐藏路由未被 `filterRouter` 过滤，其父级 `/room`（Layout）作为无 `hidden` 标记的常规路由被渲染到菜单中，唯一的子项「座位管理」因此显示在侧边栏。又因该路由需要 `:id` 参数，点击后路径 `/room/list//seats` 无法匹配，表现为不可点击。

### 解决方案

**问题 1 修复**：扩展 `constantRouterIcon` 映射表，注册所有后端使用的图标：

```typescript
// br-admin/src/router/icons.ts
import { AppstoreOutlined, CalendarOutlined, DashboardOutlined, GiftOutlined,
  HomeOutlined, MenuOutlined, SettingOutlined, TeamOutlined, ToolOutlined,
  UserOutlined } from '@vicons/antd';

export const constantRouterIcon = {
  HomeOutlined, DashboardOutlined, SettingOutlined, MenuOutlined,
  TeamOutlined, UserOutlined, ToolOutlined, AppstoreOutlined,
  GiftOutlined, CalendarOutlined,
};
```

同时修正后端 seed 中的图标名 `AppsOutlined` → `AppstoreOutlined`。

**问题 2 修复**：将 `seed_admin.py` 中所有目录类型菜单的 `path` 改为基路径：

| 菜单 | 修改前 | 修改后 |
|------|--------|--------|
| 控制台 | `/dashboard/console` | `/dashboard` |
| 系统设置 | `/system/menu` | `/system` |
| 设置页面 | `/setting/account` | `/setting` |
| 房间管理 | `/room/list` | `/room` |
| 活动管理 | `/activity/list` | `/activity` |
| 预约管理 | `/booking/list` | `/booking` |

子菜单 `path` 保持相对路径不变（如 `list`、`menu`），前端生成器拼接后得到正确路由。

**问题 3 修复**：合并隐藏静态路由时，在父级和子级的 `meta` 上同时设置 `hidden: true`：

```typescript
// br-admin/src/store/modules/asyncRoute.ts
const hiddenChildren = route.children
  ?.filter((c) => c.meta?.hideInMenu)
  .map((c) => ({ ...c, meta: { ...c.meta, hidden: true } }));
if (hiddenChildren?.length) {
  accessedRouters.push({
    ...rest,
    meta: { ...rest.meta, hidden: true },
    children: hiddenChildren,
  });
}
```

同时在后端 `_build_route_tree` 中跳过 `hidden=True` 的菜单项，确保数据库中已设置 hidden 的菜单不会返回给前端。

**文件**:
- `br-admin/src/router/icons.ts`
- `br-admin/src/store/modules/asyncRoute.ts`
- `br-server/app/services/seed_admin.py`
- `br-server/app/services/admin_menu_service.py`

---

### 现象
```
[Vue Router warn]: No match found for location with path "/system/menu"
```

### 说明
br-admin 使用动态路由，路由在 `beforeEach` 导航守卫中从后端 API 加载。浏览器刷新时，Vue Router 先用静态路由解析当前 URL，此时动态路由尚未注册，`/system/menu` 匹配失败产生警告。随后导航守卫触发、加载并注册动态路由，页面正常渲染。功能不受影响，属于 Vue Router 动态路由的预期行为。

---

## BUG-20: 微信小程序 WXML 编译错误 — unexpected character `<`

### 报错信息
```
[ WXML 文件编译错误] ./pages/study-record/index.wxml
unexpected character `<`
```

### 根本原因
`br-app/src/pages/study-record/index.vue` 中日历组件的左右箭头使用 `&lt;` 和 `&gt;` HTML 实体。Vue 模板编译器在编译时将 HTML 实体解码回裸字符 `<` 和 `>`，生成的 WXML 中 `<text class="arrow-text"><</text>` 包含非法 XML 字符。微信小程序的 WXML 解析器将 `<` 误认为标签开始符，导致编译失败。

### 解决方案
将 `&lt;` 和 `&gt;` 替换为 Unicode 字符 `‹` (U+2039) 和 `›` (U+203A)。这两个字符是合法的 XML 文本内容，不会被 WXML 解析器误解，视觉上与 `<` `>` 接近。

**文件**: `br-app/src/pages/study-record/index.vue`

---

## BUG-21: 微信支付商户订单号长度不足导致下单失败

### 报错信息
在 `br-app` 订单确认页选择微信支付并点击确认支付时，后端调用微信支付 JSAPI 下单失败：

```
WeChat Pay API error [PARAM_ERROR] 商户订单号错误，请核实后再试
```

### 根本原因
微信支付对商户订单号 `out_trade_no` 有长度限制：必须为 6-32 位。

订单微信支付服务 `br-server/app/services/booking_payment_service.py` 原先使用 `BK-{booking_id}` 作为商户订单号。对于早期预约记录，`booking_id` 很小，例如 `booking_id=1` 时生成 `BK-1`，总长度只有 4 位，不满足微信支付 6 位下限，因此微信接口返回 `PARAM_ERROR`。

钱包充值流程使用 UUID 截断后的订单号，长度满足要求，所以该问题只影响新接入的预约订单微信支付。

### 解决方案
将预约订单微信支付商户订单号格式改为 `BK-{booking_id:03d}`：

- `booking_id=1` 生成 `BK-001`，长度为 6 位，满足微信 6-32 位限制。
- `booking_id>=1000` 仍生成完整 ID，例如 `BK-1000`，不会破坏原有唯一性。
- 回调解析逻辑继续通过 `int(value[len("BK-"):])` 还原预约 ID，兼容补零格式。
- 增加回归测试，断言小 ID 订单号长度在 6-32 位内，并验证回调解析能还原原始预约 ID。

**文件**: `br-server/app/services/booking_payment_service.py`, `br-server/tests/test_booking_payment_service.py`

**提交**: `e6cffde` fix: pad booking wechat payment order numbers

---

## BUG-22: API 请求返回 307 Temporary Redirect 或 404 Not Found

### 报错信息
```
"GET /api/v1/bookings/?page=1&page_size=20 HTTP/1.1" 307 Temporary Redirect
→ 重定向至 /api/v1/bookings?page=1&page_size=20

"GET /api/v1/activities/ HTTP/1.1" 404 Not Found

"GET /api/v1/cities HTTP/1.1" 404 Not Found

"GET /api/v1/rooms/1/seats/stats HTTP/1.1" 404 Not Found
```

### 根本原因
问题涉及两个层面：

**1. 307 重定向**：FastAPI 默认 `redirect_slashes=True`。当客户端请求带尾部斜杠（如 `/api/v1/bookings/`），但路由定义不带斜杠（`""`）时，FastAPI 自动返回 307 重定向到无斜杠版本，导致前端请求多一次网络往返，且某些 HTTP 客户端不自动跟随重定向。

**2. 404 Not Found**：部分路由文件使用了带尾部斜杠的路径定义（如 `@router.get("/{room_id}/seats/stats/")`），注册的实际路径是 `/api/v1/rooms/{room_id}/seats/stats/`。当客户端请求无斜杠版本 `/api/v1/rooms/1/seats/stats` 时，FastAPI 路由匹配失败返回 404。

涉及 8 处带尾部斜杠的路由定义：
- `cities.py`: `@router.get("/")`
- `seat.py`: `@router.get("/{room_id}/seats/stats/")`, `@router.get("/{room_id}/seats/")`
- `activity.py`: `@router.get("/{activity_id}/")`
- `booking.py`: `@router.post("/{booking_id}/cancel/")`（含一个冗余重复路由）
- `admin_study_room.py`: `@router.patch("/{room_id}/status/")`
- `admin_seat.py`: `@room_seats_router.post("/bulk/")`, `@flat_seats_router.patch("/{seat_id}/status/")`

### 解决方案
**两步修复**：

1. 在 `main.py` 中添加 `redirect_slashes=False` 禁用 307 自动重定向，并注册 `StripTrailingSlashMiddleware` ASGI 中间件，在路由匹配前自动去除请求路径的尾部斜杠（根路径 `/` 除外），使带或不带斜杠的请求都能命中路由：

```python
class StripTrailingSlashMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope["path"]
            if path != "/" and path.endswith("/"):
                scope["path"] = path.rstrip("/")
        await self.app(scope, receive, send)
```

2. 统一所有路由定义，去除路径中的尾部斜杠，保持项目风格一致：

| 文件 | 修改前 | 修改后 |
|------|--------|--------|
| `cities.py` | `@router.get("/")` | `@router.get("")` |
| `seat.py` | `"/{room_id}/seats/stats/"` | `"/{room_id}/seats/stats"` |
| `seat.py` | `"/{room_id}/seats/"` | `"/{room_id}/seats"` |
| `activity.py` | `"/{activity_id}/"` | `"/{activity_id}"` |
| `booking.py` | `"/{booking_id}/cancel/"` | `"/{booking_id}/cancel"`（删除冗余重复路由） |
| `admin_study_room.py` | `"/{room_id}/status/"` | `"/{room_id}/status"` |
| `admin_seat.py` | `"/bulk/"` | `"/bulk"` |
| `admin_seat.py` | `"/{seat_id}/status/"` | `"/{seat_id}/status"` |

**文件**: `br-server/app/main.py`, `br-server/app/api/routes/cities.py`, `br-server/app/api/routes/seat.py`, `br-server/app/api/routes/activity.py`, `br-server/app/api/routes/booking.py`, `br-server/app/api/routes/admin_study_room.py`, `br-server/app/api/routes/admin_seat.py`

---

## BUG-23: Naive UI 组件未注册导致活动列表页及卡券配置报错

### 报错信息
```
[Vue warn]: Failed to resolve component: n-flex
[Vue warn]: Failed to resolve component: n-image
[Vue warn]: Failed to resolve component: n-text
[Vue warn]: Failed to resolve component: n-empty
```

### 根本原因
`br-admin/src/plugins/naive.ts` 通过 Naive UI 的 `create()` 方法按需注册全局组件，但缺少以下 6 个组件的导入和注册：

- `NFlex` — 活动列表、房间列表、卡券列表、预约列表、座位管理等多个页面使用 `<n-flex>` 布局
- `NImage` — 活动编辑弹窗、房间编辑弹窗、用户编辑弹窗、系统设置等使用 `<n-image>` 展示图片
- `NText` — 卡券配置组件 (`ActivityCouponConfig`)、座位管理页等使用 `<n-text>` 展示文本
- `NEmpty` — 卡券配置组件、角色弹窗等使用 `<n-empty>` 展示空状态
- `NGi` — 表单组件 (`BasicForm`)、菜单管理、钱包流水等使用 `<n-gi>` 网格布局
- `NScrollbar` — 座位批量创建弹窗使用 `<n-scrollbar>` 滚动容器

`components.d.ts` 由 `unplugin-vue-components` 自动生成，仅提供 TypeScript 类型声明，不代表运行时注册。Vue 在模板中遇到未注册组件时视为原生自定义元素，导致组件逻辑（如 `onMounted`）不执行、布局样式失效。

卡券模板数据加载不出来也是因为 `n-text` 和 `n-empty` 未注册导致 `ActivityCouponConfig` 组件无法正常挂载，`onMounted` 中的 `loadCouponOptions()` 未执行。

### 解决方案
在 `br-admin/src/plugins/naive.ts` 的 `import` 和 `create()` 组件列表中补充缺失的 6 个组件：

```diff
  NSkeleton,
  NCascader,
+ NFlex,
+ NImage,
+ NText,
+ NEmpty,
+ NGi,
+ NScrollbar,
} from 'naive-ui';
```

**文件**: `br-admin/src/plugins/naive.ts`

---

## BUG-24: 钱包管理菜单路由路径错误（同 BUG-19 模式）

### 报错信息
钱包管理目录菜单 `path` 存储完整路径 `/wallet/transactions`，前端路由生成器拼接后子路由变为 `/wallet/transactions/transactions`，与实际页面路径 `/wallet/transactions` 不匹配。

### 根本原因
与 BUG-19 相同：`seed_admin.py` 中钱包管理目录类型菜单的 `path` 字段存储了完整路径而非基路径。前端路由生成器会将父路径与子路径拼接，导致子路由路径重复。

### 解决方案
将钱包管理目录的 `path` 从 `/wallet/transactions` 修正为 `wallet`（基路径），拼接后得到正确的路由 `/wallet/transactions`。

| 菜单 | 修改前 | 修改后 |
|------|--------|--------|
| 钱包管理 | `/wallet/transactions` | `/wallet` |

**文件**: `br-server/app/services/seed_admin.py`

---

## BUG-25: 排课保存后列表不刷新，需整页刷新才可见新数据

### 报错信息
无报错。现象：在排课管理弹窗中编辑排课并点击"更新"，提示"排课更新成功"，但弹窗内排课列表仍显示旧数据。关闭弹窗、刷新整个页面后重新进入弹窗，才能看到更新后的数据。浏览器 Network 面板中保存后看不到对应的 GET 请求（缓存命中不产生网络请求），容易误判为"前端没有重新拉取数据"。

### 根本原因
br-admin 使用 Alova v3 作为 HTTP 客户端，`createAlova` 配置中 `cacheFor: null` 处于注释状态。Alova 默认对所有 GET 请求启用内存缓存（`mode: 'memory'`，`expire: 300秒`）。

排课弹窗保存成功后虽然调用了 `loadSchedules()` 重新请求 `GET /api/v1/admin/courses/{course_id}/schedules`，但该请求命中了 Alova 内存缓存，直接返回 5 分钟内的旧响应，未真正访问后端，导致列表数据不变。整页刷新后内存缓存清空，重新打开弹窗才能拿到最新数据。

### 解决方案
分两步修复：

1. **全局关闭 Alova 请求缓存**（根本修复）：在 `createAlova` 中启用 `cacheFor: null`，所有 GET 请求均真实发起：

```diff
  export const Alova = createAlova({
    baseURL: apiUrl,
    statesHook: VueHook,
-   // 关闭全局请求缓存
-   // cacheFor: null,
+   // 关闭全局请求缓存，避免增删改后列表命中缓存返回旧数据
+   cacheFor: null,
```

2. **接口级兜底**：对需要实时数据的 `getCourseSchedules` 接口额外添加 `force: true` 参数，强制绕过缓存；若未来调整全局缓存配置，该参数仍能保证列表实时性：

```typescript
export function getCourseSchedules(courseId: number) {
  return Alova.Get<ScheduleRecord[]>(`/v1/admin/courses/${courseId}/schedules`, {
    meta: ADMIN_NATIVE_META,
    force: true,
  });
}
```

**经验教训**：排查此类问题时，若保存成功但列表不变，且 Network 面板看不到刷新请求，应优先怀疑 HTTP 客户端的请求缓存，而非前端状态更新逻辑。

**文件**: `br-admin/src/utils/http/alova/index.ts`, `br-admin/src/api/course/index.ts`

**提交**: `c06c18f`, `8438d36`

---

## BUG-26: Admin 取消"待确认"订单报 500 (MissingGreenlet)

### 报错信息
```
POST /api/v1/admin/bookings/75/cancel HTTP/1.1" 500 Internal Server Error
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here. Was IO attempted in an unexpected place?
```

### 根本原因
此 BUG 包含两层问题：

**第一层：`pending_confirm` 状态不在可取消范围内**

`admin_cancel_booking` 直接调用通用 `cancel_booking` 函数，该函数内有硬限制：

```python
if booking.status != "confirmed":
    raise BookingCancellationNotAllowedError("该预约不可取消")
```

`pending_confirm`（待确认）订单不满足 `confirmed` 条件，首先触发 400 错误。

**第二层：新增 pending_confirm 处理分支后触发 MissingGreenlet**

为 `pending_confirm` 订单添加专属取消逻辑后，在 `admin_cancel_booking` 中使用了 `with_for_update()` 行锁查询 Booking 和 User，随后 `cancel_booking` 的 fallback 路径也对同一行再次 `with_for_update()`，在异步上下文中形成锁冲突。此外，`db.flush()` 后直接访问修改过的 ORM 对象属性（`booking.seat_id`、`booking.room_id`）构建响应，可能触发 SQLAlchemy 的延迟加载，在 async session 外部执行 IO 导致 `MissingGreenlet` 异常。

### 解决方案

1. **在 `admin_cancel_booking` 中为 `pending_confirm` 订单增加专属处理分支**：全额退款（`penalty_amount=0`）、恢复优惠券、创建钱包退款交易记录，绕过通用 `cancel_booking` 的 `confirmed` 状态限制。

2. **移除所有 `with_for_update()` 行锁**：`admin_cancel_booking` 的 Booking 和 User 查询均不使用行锁，避免嵌套锁冲突。

3. **WalletTransaction 字段改为构造函数直接传参**：`payment_provider`、`payment_status`、`paid_at` 直接在构造时传入，不使用 `setattr`。

4. **统一使用 `admin_get_booking` 重新查询构建响应**：`pending_confirm` 路径和通用取消路径在 `flush`/`refresh` 后，均调用 `await admin_get_booking(db, booking_id)` 从数据库重新查询全新 ORM 对象构建响应，彻底避免 `flush` 后对象状态问题。

**文件**: `br-server/app/services/booking_service.py`

**提交**: `f174e70`, `2365213`, `986f1f0`

---

## BUG-27: 订单状态定时任务 `course_started` 计数分支永不可达（死分支）

### 报错信息
订单状态定时任务的统计日志中 `course_started` 恒为 0：课程订单从「待开始」推进到「进行中」时，该计数不自增。

### 根本原因
`order_status_scheduler._update_highlight` 的 `elif is_new_start: stats["course_started"] += 1` 分支永不可达——`highlighted_lesson_id` 在订单创建时从不赋值（恒为 `None`），当 `is_new_start=True` 时 `None != target_lesson.lesson_id` 必为真，控制流必进前一个 `if` 分支，`elif` 成为死代码（F5）。

### 解决方案
将状态推进判定下沉为领域层 transition 纯函数，`stats[transition.stat_key] += 1` 由转移类型统一驱动计数；`total_scanned`/`seat_started`/`seat_completed`/`course_started`/`course_highlight_updated`/`course_completed` 六个键名保持不变（避免 `main.py` 日志与既有断言破裂）。新增回归断言：`pending_start → in_progress` 转移时 `course_started` 自增。

**文件**: `br-server/app/services/order_status_scheduler.py`, `br-server/app/domain/booking_status.py`

**提交**: `4c731d1`

---

## BUG-28: 删除 `BOOKING_STATUS_LABELS.pending` 致未支付订单标签从「待支付」退化为「待开始」

### 报错信息
潜在缺陷（重构中识别，未上线）：br-app 订单页若直接删除 `BOOKING_STATUS_LABELS.pending = '待支付'`，未支付的座位订单标签会从「待支付」退化为「待开始」，用户无法区分「待支付」与「已支付待开始」。

### 根本原因
支付域语义（`payment_status='pending'` = 待支付）被错误挂在订单状态词表键 `BOOKING_STATUS_LABELS.pending` 上（同键双义，F23）。词表翻转要求剥离该支付域键，但直接删除会造成用户可见文案倒退，与「行为零变更」冲突。

### 解决方案
新增 `PAYMENT_STATUS_LABELS` 承载「待支付」语义，并在 `statusLabel()` 增加 `payment_status === 'pending'` 前置分支返回 `PAYMENT_STATUS_LABELS.pending`，先于订单状态判定；`BOOKING_STATUS_LABELS` 剥离支付域键（含死键 `confirmed: '已预约'`，F25）。用户可见文案零变更。

**文件**: `br-app/src/constants/booking.js`, `br-app/src/pages/orders/index.vue`

**提交**: `54a8e0e`

---

## BUG-29: 订单链路时区实现分裂（naive/aware 混用）存在比较崩溃隐患

### 报错信息
```
TypeError: can't compare offset-naive and offset-aware datetimes
```
领域纯函数若被 aware 与 naive 两类调用点共用，比较业务本地时间时会抛此异常。

### 根本原因
订单链路内存在 3 个同语义但仅 2 个同名的业务本地时间实现：`booking_cancellation_policy.booking_now`（naive）、`course_booking_service._now_naive`（naive）、`booking_verification_service._booking_now`（**aware**，唯一孤岛）；模块级 `CHINA_TIMEZONE` 常量 6 处重复定义 + 1 处等价变体（`seed_data.py` 用 `timezone(timedelta(hours=8))`）。全仓 `replace(tzinfo=None)` 达 12 处，表明 naive 是压倒性主流（F19/F21）。

### 解决方案
新建 `app/utils/timezone.py` 作为单一事实源：统一 `booking_now()` 返回 naive 的 `settings.BOOKING_TIMEZONE` 本地时间、`CHINA_TIMEZONE` 常量、`ensure_booking_timezone()` aware 归一化工具。订单链路内 3 个旧定义改为 import；`booking_verification_service` 作为 aware 孤岛保留内部 aware 用法，仅在调用领域函数时于边界 `.replace(tzinfo=None)` 降级一次。链路外 3 个函数按 Non-Goals 只改导入源、不改返回语义。

**文件**: `br-server/app/utils/timezone.py`（新建）, `br-server/app/services/booking_cancellation_policy.py`, `br-server/app/services/course_booking_service.py`, `br-server/app/services/booking_verification_service.py`

**提交**: `d9c257b`

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
| `br-app/src/pages/study-record/index.vue` | #14, #20 |
| `br-server/app/services/seed_data.py` | #15 |
| `br-server/app/services/coupon_service.py` | #15 |
| `br-server/tests/test_api_booking.py` | #15 |
| `br-server/app/services/admin_menu_service.py` | #16 |
| 数据库 `admin_menus` id=11 | #17 |
| `br-admin/src/components/Modal/src/hooks/useModal.ts` | #18 |
| `br-admin/src/router/icons.ts` | #19 |
| `br-admin/src/store/modules/asyncRoute.ts` | #19 |
| `br-server/app/services/seed_admin.py` | #19 |
| `br-server/app/services/admin_menu_service.py` | #19 |
| `br-server/app/services/booking_payment_service.py` | #21 |
| `br-server/tests/test_booking_payment_service.py` | #21 |
| `br-server/app/main.py` | #22 |
| `br-server/app/api/routes/cities.py` | #22 |
| `br-server/app/api/routes/seat.py` | #22 |
| `br-server/app/api/routes/activity.py` | #22 |
| `br-server/app/api/routes/booking.py` | #22 |
| `br-server/app/api/routes/admin_study_room.py` | #22 |
| `br-server/app/api/routes/admin_seat.py` | #22 |
| `br-admin/src/plugins/naive.ts` | #23 |
| `br-server/app/services/seed_admin.py` | #24 |
| `br-admin/src/utils/http/alova/index.ts` | #25 |
| `br-admin/src/api/course/index.ts` | #25 |
| `br-server/app/services/booking_service.py` | #26 |
| `br-server/app/services/order_status_scheduler.py` | #27 |
| `br-server/app/domain/booking_status.py` | #27 |
| `br-app/src/constants/booking.js` | #28 |
| `br-app/src/pages/orders/index.vue` | #28 |
| `br-server/app/utils/timezone.py` | #29 (新建) |
| `br-server/app/services/booking_verification_service.py` | #29 |
