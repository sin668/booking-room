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
```

### 1.3 数据库迁移

```bash
# 创建数据库（PostgreSQL）
createdb booking_room

# 执行迁移
alembic upgrade head
```

如需回滚：
```bash
alembic downgrade base
```

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

## 二、前端部署 (br-app)

### 2.1 安装依赖

```bash
cd br-app
npm install
```

### 2.2 开发运行

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

### 2.3 生产构建

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

### 2.4 配置 API 地址

开发环境通过 H5 代理访问后端（已在 `manifest.json` 中配置）。

生产环境通过环境变量设置：
```bash
VITE_API_BASE_URL=https://your-api-domain.com npm run build:h5
```

## 三、前后端联调流程

### 3.1 启动服务

```bash
# 终端 1：启动后端
cd br-server && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 终端 2：启动前端 H5
cd br-app
npm run dev:h5
```

### 3.2 验证完整流程

1. **发送验证码**：注册 Tab → 输入手机号 → 点击获取验证码（开发阶段后端 mock 模式自动通过）
2. **注册**：填写手机号、验证码、密码 → 勾选协议 → 点击注册 → 自动跳转首页
3. **登录**：登录 Tab → 输入手机号和密码 → 点击登录 → 自动跳转首页
4. **Token 刷新**：等待 15 分钟 Access Token 过期 → 自动刷新无感知
5. **退出登录**：清除 Token → 跳转登录页

## 四、生产环境检查清单

- [ ] `JWT_SECRET_KEY` 设置为强随机值（`openssl rand -hex 32`）
- [ ] `COOKIE_SECURE` 设为 `true`（HTTPS 环境下）
- [ ] `DATABASE_URL` 使用非 root 用户，密码足够强
- [ ] Redis 设置密码（修改 `REDIS_URL` 为 `redis://:password@host:port/db`）
- [ ] 阿里云短信 AccessKey 配置正确
- [ ] 阿里云验证码 2.0 Scene ID 配置正确
- [ ] CORS `allow_origins` 限制为实际前端域名（修改 `app/main.py`）
- [ ] 数据库备份策略已配置
- [ ] 前端 `manifest.json` 中微信小程序 appid 已填写

## 五、项目结构

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
│   ├── tests/                  # 测试（48 个）
│   ├── .env.example
│   └── pyproject.toml
├── br-app/                     # 前端 uni-app (Vue3)
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

## 六、常用命令速查

| 命令 | 说明 |
|------|------|
| `cd br-server && pytest -v` | 运行后端测试 |
| `cd br-server && alembic upgrade head` | 执行数据库迁移 |
| `cd br-server && alembic downgrade base` | 回滚数据库迁移 |
| `cd br-server && uvicorn app.main:app --reload` | 启动后端开发服务器 |
| `cd br-app && npm run dev:h5` | 启动前端 H5 开发 |
| `cd br-app && npm run dev:mp-weixin` | 启动前端小程序开发 |
| `cd br-app && npm run build:mp-weixin` | 构建小程序生产包 |
| `cd br-app && npm run build:h5` | 构建 H5 生产包 |
