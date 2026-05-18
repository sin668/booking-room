# 去K书 - 部署文档

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.12 |
| Node.js | >= 18 |
| PostgreSQL | >= 15 |
| Redis | >= 6.0 |

## 一、后端部署 (br-server)

### 1.1 安装依赖

```bash
cd br-server
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -e ".[dev]"
```

### 1.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 填入实际值：

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/booking_room

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT（必须设置，生成方式见下方）
JWT_SECRET_KEY=  # 运行: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# 阿里云短信服务
ALIYUN_SMS_ACCESS_KEY_ID=your_access_key_id
ALIYUN_SMS_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_SMS_SIGN_NAME=去K书
ALIYUN_SMS_TEMPLATE_CODE=SMS_504980114
ALIYUN_CAPTCHA_SCENE_ID=your_captcha_scene_id

# Cookie 安全
COOKIE_SECURE=false  # 生产环境 HTTPS 设为 true

# 功能开关
REGISTRATION_ENABLED=true

# 管理后台默认账号 seed（admin RBAC 动态设置迁移后使用）
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=change-me
ADMIN_DEFAULT_EMAIL=admin@example.com
```

### 1.3 数据库迁移

```bash
# 创建数据库（PostgreSQL）
createdb booking_room

# 执行迁移
alembic upgrade head

# 初始化默认管理员、角色、菜单、按钮权限和系统设置
python -m app.services.seed_admin
```

如需回滚：
```bash
alembic downgrade base
```

`python -m app.services.seed_admin` 必须保持幂等，可重复执行且不重复插入默认数据。开发环境默认账号为 `admin / 123456`；生产环境必须显式设置 `ADMIN_DEFAULT_PASSWORD`，不得依赖弱默认密码。

### 1.4 启动服务

**开发环境：**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**生产环境：**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 1.5 运行测试

```bash
# 运行全部测试（48 个）
pytest tests/ -v

# 带覆盖率
pytest tests/ -v --cov=app --cov-report=term-missing
```

## 二、管理后台部署 (br-admin)

基于 [Naive UI Admin](https://github.com/jekip/naive-ui-admin) 模板，使用 Vue3 + NaiveUI + Alova + TypeScript。

### 2.1 安装依赖

```bash
cd br-admin
pnpm install
```

> 需要 pnpm >= 8，安装：`npm install -g pnpm`

### 2.2 配置环境变量

开发环境（`.env.development`）：

```bash
# 开发服务端口
VITE_PORT = 8001

# 是否开启 Mock（开发阶段可开启，跳过后端）
VITE_USE_MOCK = true

# API 接口地址（留空则使用相对路径 + 代理）
VITE_GLOB_API_URL =

# 接口前缀（Alova 会自动添加到请求 URL 前）
VITE_GLOB_API_URL_PREFIX = /api

# legacy 管理后台 Token（迁移期间仅作为兼容 fallback）
VITE_ADMIN_TOKEN =
```

生产环境（`.env.production`）：

```bash
VITE_USE_MOCK = false
VITE_GLOB_API_URL = https://your-api-domain.com
VITE_GLOB_API_URL_PREFIX = /api
VITE_ADMIN_TOKEN = your_legacy_emergency_admin_token
```

admin RBAC 动态设置迁移完成后，`br-admin` 以 `POST /api/v1/admin/auth/login` 返回的 admin access token 为主认证路径，并在请求中发送 `Authorization: Bearer <token>`。`VITE_ADMIN_TOKEN` / `X-Admin-Token` 仅用于兼容旧管理接口和紧急恢复，不应用于新 admin API 的常规访问。

### 2.3 配置开发代理

开发环境下，前端通过 Vite 代理转发 API 请求到后端，避免跨域。

在 `.env.development` 中取消注释并配置代理：

```bash
VITE_PROXY = [["/api","http://localhost:8000"],["/uploads","http://localhost:8000"]]
```

- `/api` — 转发所有 API 请求到后端
- `/uploads` — 转发上传文件的静态资源请求

### 2.4 开发运行

```bash
cd br-admin
pnpm dev
```

访问 http://localhost:8001

> 开发模式下会自动生成 `app.config.js` 配置文件，无需手动维护。

### 2.5 生产构建

```bash
cd br-admin
pnpm build
```

产物在 `dist/` 目录，可部署到任意静态文件服务器。

### 2.6 Nginx 部署示例

```nginx
server {
    listen 80;
    server_name admin.your-domain.com;

    root /path/to/br-admin/dist;
    index index.html;

    # 前端路由 history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 反向代理 API 请求到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 反向代理上传文件请求
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 三、用户端前端部署 (br-app)

### 3.1 安装依赖

```bash
cd br-app
npm install
```

### 3.2 开发运行

**H5 模式（浏览器）：**
```bash
npm run dev:h5
```
访问 http://localhost:8080

**微信小程序模式：**
```bash
npm run dev:mp-weixin
```
用微信开发者工具导入 `dist/dev/mp-weixin` 目录

### 3.3 生产构建

**微信小程序：**
```bash
npm run build:mp-weixin
```
产物在 `dist/build/mp-weixin`，用微信开发者工具上传

**H5：**
```bash
npm run build:h5
```
产物在 `dist/build/h5`

### 3.4 配置 API 地址

开发环境通过 H5 代理访问后端（已在 `manifest.json` 中配置）。

生产环境通过环境变量设置：
```bash
VITE_API_BASE_URL=https://your-api-domain.com npm run build:h5
```

## 四、前后端联调流程

### 4.1 启动服务

```bash
# 终端 1：启动后端
cd br-server && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 终端 2：启动前端 H5
cd br-app
npm run dev:h5
```

### 4.2 验证完整流程

1. **发送验证码**：注册 Tab → 输入手机号 → 点击获取验证码（开发阶段后端 mock 模式自动通过）
2. **注册**：填写手机号、验证码、密码 → 勾选协议 → 点击注册 → 自动跳转首页
3. **登录**：登录 Tab → 输入手机号和密码 → 点击登录 → 自动跳转首页
4. **Token 刷新**：等待 15 分钟 Access Token 过期 → 自动刷新无感知
5. **退出登录**：清除 Token → 跳转登录页

## 五、生产环境检查清单

### 后端
- [ ] `JWT_SECRET_KEY` 设置为强随机值（`openssl rand -hex 32`）
- [ ] `ADMIN_TOKEN` 设置为强随机值
- [ ] `COOKIE_SECURE` 设为 `true`（HTTPS 环境下）
- [ ] `DATABASE_URL` 使用非 root 用户，密码足够强
- [ ] Redis 设置密码（修改 `REDIS_URL` 为 `redis://:password@host:port/db`）
- [ ] 阿里云短信 AccessKey 配置正确
- [ ] 阿里云验证码 2.0 Scene ID 配置正确
- [ ] CORS `allow_origins` 限制为实际前端域名（修改 `app/main.py`）
- [ ] 数据库备份策略已配置

### 管理后台 (br-admin)
- [ ] `VITE_USE_MOCK` 设为 `false`
- [ ] `VITE_GLOB_API_URL` 指向生产后端地址
- [ ] 已执行 `python -m app.services.seed_admin` 初始化生产管理员、角色、菜单、按钮权限和系统设置
- [ ] `ADMIN_DEFAULT_PASSWORD` 已显式设置为强密码，未使用开发默认密码
- [ ] br-admin 使用 `Authorization: Bearer <admin access token>` 调用新 admin API
- [ ] 如仍保留 `VITE_ADMIN_TOKEN`，仅作为 legacy `X-Admin-Token` 兼容和应急通道
- [ ] `uploads/` 目录通过 Nginx 反向代理到后端
- [ ] HTTPS 已启用（生产环境必须）

### 用户端 (br-app)
- [ ] 前端 `manifest.json` 中微信小程序 appid 已填写

## 六、Legacy X-Admin-Token 移除计划

`X-Admin-Token` 是 admin RBAC 迁移期的兼容和应急超级管理员通道。满足以下前提后再移除：

- br-admin 登录、动态路由、菜单设置、角色权限、个人设置、系统设置均已迁移到 Bearer admin token。
- 房间、座位、活动、订单、上传等现有业务管理接口已优先使用统一 Bearer token。
- 生产环境管理员账号、`super_admin` 角色、默认菜单、按钮权限和系统设置已通过 seed 初始化。
- 生产运维已确认无需通过 `ADMIN_TOKEN` 进行紧急后台访问。
- 后端和前端测试已覆盖 Bearer 认证、权限通过、权限拒绝和未认证 401。

移除范围：

- 后端 `X-Admin-Token` header 读取逻辑。
- legacy super admin context 分支。
- 前端 `VITE_ADMIN_TOKEN` 配置和手写 `X-Admin-Token` 请求头。
- legacy token 兼容测试，改为 Bearer admin token 和权限码测试。

建议移除步骤：

1. 先发布 Bearer-only 代码到预发环境，确认 br-admin 全流程可用。
2. 在生产环境短期保留 `ADMIN_TOKEN` 配置但不再由前端发送。
3. 观察管理接口认证日志，确认无 `X-Admin-Token` 流量。
4. 删除代码和环境变量，运行后端 `pytest`、前端 `pnpm build`。
5. 发布后再次验证管理员登录、动态菜单、按钮权限和核心管理接口。

## 七、项目结构

```
booking-room/
├── br-server/                  # 后端 FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py # 共享依赖（认证中间件）
│   │   │   └── routes/         # API 路由
│   │   ├── core/               # 配置、数据库、Redis
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # Pydantic Schema
│   │   ├── services/           # 业务逻辑
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移
│   ├── tests/                  # 测试（137 个）
│   ├── uploads/                # 上传文件存储目录
│   ├── .env.example
│   └── pyproject.toml
├── br-admin/                   # 管理后台 (Vue3 + NaiveUI)
│   ├── src/
│   │   ├── api/                # API 接口封装（Alova）
│   │   ├── views/              # 页面视图
│   │   ├── components/         # 通用组件（BasicTable, BasicForm 等）
│   │   ├── router/             # 路由配置
│   │   └── utils/              # 工具函数
│   ├── .env.development       # 开发环境变量
│   ├── .env.production        # 生产环境变量
│   └── package.json
├── br-app/                     # 用户端 uni-app (Vue3)
│   ├── src/
│   │   ├── api/                # API 接口封装
│   │   ├── pages/              # 页面
│   │   ├── store/              # Pinia 状态管理
│   │   ├── utils/              # 工具函数（request.js）
│   │   ├── App.vue
│   │   └── main.js
│   ├── manifest.json
│   └── package.json
├── docs/
│   └── api.md                  # API 接口文档
└── deploy.md                   # 本文件
```

## 八、常用命令速查

| 命令 | 说明 |
|------|------|
| `cd br-server && pytest -v` | 运行后端测试 |
| `cd br-server && alembic upgrade head` | 执行数据库迁移 |
| `cd br-server && python -m app.services.seed_admin` | 初始化或补齐 admin RBAC 默认数据 |
| `cd br-server && alembic downgrade base` | 回滚数据库迁移 |
| `cd br-server && uvicorn app.main:app --reload` | 启动后端开发服务器 |
| `cd br-admin && pnpm install` | 安装管理后台依赖 |
| `cd br-admin && pnpm dev` | 启动管理后台开发（端口 8001） |
| `cd br-admin && pnpm build` | 构建管理后台生产包 |
| `cd br-app && npm run dev:h5` | 启动用户端 H5 开发 |
| `cd br-app && npm run dev:mp-weixin` | 启动用户端小程序开发 |
| `cd br-app && npm run build:mp-weixin` | 构建小程序生产包 |
| `cd br-app && npm run build:h5` | 构建 H5 生产包 |
