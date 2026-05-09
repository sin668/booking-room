## 1. 后端 Schema 定义

- [ ] 1.1 创建 `br-server/app/schemas/study_record.py`，参照 `br-server/app/schemas/booking.py` 的 Pydantic BaseModel 风格，定义以下 schema：
  - `StudyRecordItem`：id、room_name（str）、seat_number（str）、date（date）、start_time（time）、end_time（time）、hours（float）、total_price（Decimal）
  - `StudyRecordListResponse`：items（list[StudyRecordItem]）、total（int）、page（int）、page_size（int）
  - `CalendarMark`：date（date）、studied（bool）
  - `StudyRecordSummaryResponse`：monthly_hours（float）、monthly_bookings（int）、max_streak_days（int）、total_hours（float）、calendar_mark（list[CalendarMark])
  所有 schema 使用 `ConfigDict(from_attributes=True)`

## 2. 后端 Service 层

- [ ] 2.1 创建 `br-server/app/services/study_record_service.py`，参照 `br-server/app/services/booking_service.py` 的函数式风格（非类），实现 `get_monthly_summary(db: AsyncSession, user_id: uuid.UUID, month: date)` 函数：
  - 查询 `bookings` 表 `user_id` 匹配且 `status='completed'` 且 `date` 在目标月份范围内的记录
  - 通过 `seat_id` 关联 `seats` 表获取 seat_number，通过 `room_id` 关联 `study_rooms` 表获取 room_name
  - 计算月度学习时长（复用 `booking_service._calculate_hours`，或在该文件中 import 使用）
  - 计算最长连续学习天数（将已学习日期排序后计算最长连续子序列）
  - 计算累计学习总时长（不限月份，查该用户所有 completed booking）
  - 生成 calendar_mark：当月每一天的 studied 状态
  - 返回 `StudyRecordSummaryResponse`

- [ ] 2.2 在同一文件中实现 `list_study_records(db: AsyncSession, user_id: uuid.UUID, page: int, page_size: int, month: date | None)` 函数：
  - 分页查询 `status='completed'` 的 booking，按 `date desc, start_time desc` 排序
  - 批量关联 seat 和 room 表获取 seat_number 和 room_name（参照 `booking_service.list_bookings` 的批量查询模式）
  - 可选 month 参数按月筛选
  - 返回 `StudyRecordListResponse`

## 3. 后端 Routes 层

- [ ] 3.1 创建 `br-server/app/api/routes/study_record.py`，参照 `br-server/app/api/routes/booking.py` 的路由风格：
  - `router = APIRouter(prefix="/api/v1/study-records", tags=["study-records"])`
  - `GET /summary`：接受 `month: str` Query 参数（格式 YYYY-MM），依赖 `get_current_user_id` 认证，调用 `study_record_service.get_monthly_summary`
  - `GET /`：接受 `page`、`page_size`、`month`（可选）Query 参数，依赖 `get_current_user_id` 认证，调用 `study_record_service.list_study_records`

- [ ] 3.2 在 `br-server/app/main.py` 中注册路由：
  - 添加 `from app.api.routes.study_record import router as study_record_router`
  - 添加 `app.include_router(study_record_router)`
  - 注意：原 tasks.md 3.2 提到 `__init__.py`，实际路由在 `main.py` 中注册，`__init__.py` 为空文件

## 4. 后端测试

- [ ] 4.1 创建 `br-server/tests/test_study_record_service.py`，编写 service 层单元测试，覆盖以下场景：
  - 有 completed 记录的月份 → 正确返回统计和日历标记
  - 无 completed 记录的月份 → 统计为 0，calendar_mark 为空
  - 连续天数计算（跨周末等场景）
  - 分页列表查询正确性和按月筛选

- [ ] 4.2 创建 `br-server/tests/test_api_study_record.py`，参照 `br-server/tests/test_api_booking.py` 的集成测试风格（httpx AsyncClient + seed fixture），覆盖：
  - summary 端点正常返回 200
  - list 端点正常返回 200 及分页
  - 未认证请求返回 401
  - 需创建 `seed_completed_bookings` fixture 插入已完成的预约记录

## 5. 前端 API 层

- [ ] 5.1 创建 `br-app/src/api/studyRecords.js`，参照 `br-app/src/api/bookings.js` 的风格：
  - `import { get } from '@/utils/request'`
  - `getMonthlySummary(params)` → `get('/api/v1/study-records/summary', params)`
  - `getStudyRecordList(params)` → `get('/api/v1/study-records/', params)`

## 6. 前端页面实现

- [ ] 6.1 在 `br-app/src/pages.json` 的 pages 数组中添加路由注册：
  ```json
  {
    "path": "pages/study-record/index",
    "style": {
      "navigationBarTitleText": "学习记录"
    }
  }
  ```

- [ ] 6.2 创建 `br-app/src/pages/study-record/index.vue`，参照 `prototype/study-record.html` 高保真原型和现有页面风格（如 `br-app/src/pages/profile/index.vue` 的 SCSS 变量体系），实现完整页面：
  - **统计摘要卡片**：渐变背景（`$primary` → `$purple`），2x2 网格展示本月学习时长、本月预约次数、最长连续天数、累计学习时长
  - **月度日历**：月份选择器（左右箭头切换）、星期标题行（日一二三四五六）、日期网格（已学习绿色圆点、今日蓝色圆圈、未来灰色文字）、图例说明
  - **学习记录列表**：卡片式记录（图标 + 门店名/座位号 + 金额 + 时间段/时长），触底加载更多（onReachBottom 分页）
  - **加载状态**：首次加载显示加载提示
  - 使用 `<script setup>` + Composition API 风格
  - 页面数据：调用 `getMonthlySummary`（月份切换时刷新）、`getStudyRecordList`（分页加载）
  - 无需拆分子组件，单文件实现

## 7. 文档与收尾

- [ ] 7.1 更新 `docs/api.md`，参照现有 API 文档格式，补充学习记录两个接口的文档（请求参数、响应格式、错误码）

- [ ] 7.2 代码审查：检查后端分层是否正确（routes → services → schemas）、前端是否遵循项目组件风格、有无重复代码
