# Tasks: 连续签到与补签

## 1. 后端数据层

- [x] 1.1 新增 `app/models/checkin.py`：`CheckinRecord`（user_id + checkin_date 唯一约束、source=daily/makeup）与 `UserCheckinStats`（user_id 主键、points、makeup_cards），并在 `app/models/__init__.py` 导出
- [x] 1.2 新增 Alembic 迁移创建两张表及唯一约束/索引，`down_revision` 指向当前 head；确认 `downgrade()` 可完整删除

## 2. 后端服务与接口

- [x] 2.1 新增 `app/schemas/checkin.py`：汇总、日历标记、签到/补签请求与响应模型
- [x] 2.2 新增 `app/services/checkin_service.py`：统计行懒初始化（初始 2 张补签卡）、`Asia/Shanghai` 今日口径、连续天数、漏签与 30 天补签窗口、积分/补签卡奖励、签到与补签事务
- [x] 2.3 新增 `app/api/routes/checkin.py`：`GET /api/v1/checkin/summary`、`POST /api/v1/checkin`、`POST /api/v1/checkin/makeup`，在 `app/main.py` 注册路由
- [x] 2.4 在 `docs/api.md` 补充三个签到接口的路径、参数与响应说明

## 3. 后端测试

- [x] 3.1 新增 `tests/test_checkin.py`：汇总（有/无记录、未登录、漏签窗口）、签到（首签、连续 7 天奖励、连续 30 天补签卡、重复签到 400）、补签（成功扣卡、卡不足 400、窗口外 400、已有记录 400、未登录 401）
- [x] 3.2 运行 `pytest tests/test_checkin.py` 与相关回归测试通过

## 4. 前端 API 与路由

- [x] 4.1 新增 `src/api/checkin.js`（汇总/签到/补签三个方法），沿用 `utils/request`
- [x] 4.2 在 `src/pages.json` 注册 `pages-sub/checkin/index`（签到日历）与 `pages-sub/checkin/makeup`（补签中心）

## 5. 签到日历页

- [x] 5.1 实现渐变签到头图（连续天数、累计天数、积分、补签卡）、签到按钮与已签到态
- [x] 5.2 实现周一起始日历：已签 ✓、漏签 ✗ 可跳补签、未来日期显示预计连续天数、今日未签显示「签」，支持切换月份与图例
- [x] 5.3 实现连续奖励进度、补签入口与签到规则卡片
- [x] 5.4 实现签到成功弹窗（连续天数/本次积分/累计天数/奖励进度）与失败轻提示，成功后刷新页面状态

## 6. 补签中心页

- [x] 6.1 实现剩余补签卡与规则说明、可补签日期列表和日历选日联动
- [x] 6.2 实现选择上限（不超过剩余卡数）、底部「已选 N 天」确认栏、成功后扣卡与日期状态刷新、空状态

## 7. 入口与深色模式

- [x] 7.1 个人中心「学习服务」新增「每日签到」入口并跳转签到日历页
- [x] 7.2 两个新页面绑定 `themeClass` 并全部使用语义色变量，检查深色模式下卡片、文字、日历标记、弹窗与底部操作栏无硬编码浅色亮块
- [x] 7.3 补充签到所需图标（火焰/日历/关闭）到 `src/static/icons/iconfont.css`

## 8. 构建验证

- [x] 8.1 运行后端测试与 `npm run build:mp-weixin`（或项目等价构建命令）通过
