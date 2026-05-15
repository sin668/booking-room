## 1. 后端数据模型

- [x] 1.1 创建 City 模型 `br-server/app/models/city.py`
  - 参照 `br-server/app/models/study_room.py` 的 SQLAlchemy 2.0 Mapped 风格
  - 字段：id (Integer, PK, autoincrement), name (String(50), unique, not null), province (String(50), not null), sort_order (Integer, default=0), status (String(20), default="active"), created_at, updated_at
  - 验证：`python -c "from app.models.city import City; print('OK')"`

- [x] 1.2 StudyRoom 模型新增 `city_id` 可空外键 `br-server/app/models/study_room.py`
  - 添加 `city_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cities.id"), nullable=True)`
  - 需要导入 ForeignKey
  - 验证：`python -c "from app.models.study_room import StudyRoom; print('OK')"`

- [x] 1.3 在 `br-server/app/models/__init__.py` 导入 City 模型
  - 添加 `from app.models.city import City` 确保 Alembic autogenerate 能检测到新表
  - 验证：`alembic check` 无报错

## 2. 数据库迁移

- [x] 2.1 生成 Alembic 迁移脚本
  - 运行 `alembic revision --autogenerate -m "add_cities_table_and_room_city_id"`
  - 检查生成的迁移文件，确认包含：create_table(cities) + add_column(study_rooms.city_id)

- [x] 2.2 编辑迁移脚本，在 upgrade() 中添加 seed 数据
  - 插入广东省城市：茂名市(sort_order=1)、广州市(sort_order=2)、深圳市(sort_order=3)、东莞市(sort_order=4)、佛山市(sort_order=5)、珠海市(sort_order=6)，全部 status="active"
  - 批量 UPDATE study_rooms SET city_id = (SELECT id FROM cities WHERE name='茂名市') WHERE city_id IS NULL
  - 验证：检查迁移 SQL 逻辑正确

- [x] 2.3 执行迁移并验证
  - 运行 `alembic upgrade head`
  - 验证：`psql -c "SELECT * FROM cities ORDER BY sort_order;"` 返回 6 条城市记录
  - 验证：`psql -c "SELECT id, name, city_id FROM study_rooms;"` 确认现有自习室 city_id 已填充

## 3. 后端 Schemas

- [x] 3.1 创建 `br-server/app/schemas/city.py`
  - CityResponse(BaseModel)：id: int, name: str, province: str
  - 使用 Pydantic V2 + ConfigDict(from_attributes=True)，参照现有 schema 风格
  - 验证：`python -c "from app.schemas.city import CityResponse; print('OK')"`

- [x] 3.2 修改 `br-server/app/schemas/study_room.py`
  - StudyRoomResponse 新增两个字段：`city_id: int | None = None`, `city_name: str | None = None`
  - 验证：现有测试不回归

## 4. 后端 Service

- [x] 4.1 创建 `br-server/app/services/city_service.py`
  - `get_active_cities(db: AsyncSession) -> list[City]`：查询 status="active"，按 sort_order 升序
  - 参照 `br-server/app/services/study_room_service.py` 的依赖注入模式（AsyncSession）
  - 验证：`python -c "from app.services.city_service import get_active_cities; print('OK')"`

## 5. 后端 Routes

- [x] 5.1 创建 `br-server/app/api/routes/cities.py`
  - `router = APIRouter(prefix="/api/v1/cities", tags=["cities"])`
  - `GET /` 路由：调用 city_service.get_active_cities，返回 CityResponse 列表
  - 参照 `br-server/app/api/routes/study_room.py` 的路由定义风格
  - 验证：`python -c "from app.api.routes.cities import router; print('OK')"`

- [x] 5.2 在 `br-server/app/api/routes/__init__.py` 注册 cities 路由
  - 添加 `from app.api.routes.cities import router as cities_router`
  - 添加 `app.include_router(cities_router)`，放在其他路由附近
  - 验证：服务启动无报错

- [x] 5.3 修改 `br-server/app/api/routes/study_room.py`（或对应 rooms 路由文件）
  - 自习室列表路由增加可选查询参数 `city_id: int | None = None`
  - 传递给 service 层进行过滤（WHERE city_id = :city_id，仅当 city_id 不为 None 时）
  - service 层查询时 LEFT JOIN cities 获取 city_name
  - 验证：启动服务后 `curl localhost:8000/api/v1/cities/` 返回城市列表

## 6. 后端测试

- [x] 6.1 City 模型单元测试 `br-server/tests/test_city_model.py`
  - 测试创建城市记录成功
  - 测试 name 唯一约束（重复 name 抛异常）
  - 测试 status 默认值为 "active"
  - 验证：`pytest br-server/tests/test_city_model.py -v`

- [x] 6.2 City API 集成测试 `br-server/tests/test_city_api.py`
  - GET /api/v1/cities/ 返回 200 和城市列表
  - 仅返回 status="active" 的城市（创建 inactive 城市不出现）
  - 空列表场景（无 active 城市）
  - 按 sort_order 排序
  - 验证：`pytest br-server/tests/test_city_api.py -v`

- [x] 6.3 自习室列表 city_id 过滤测试（追加到现有 rooms 测试文件）
  - 传入 city_id 仅返回该城市的自习室
  - 不传 city_id 返回全部自习室
  - 传入不存在的 city_id 返回空列表（200，items=[]）
  - 响应包含 city_id 和 city_name 字段
  - 验证：`pytest br-server/tests/ -k "city" -v`

- [x] 6.4 运行全量测试确认无回归
  - 验证：`pytest br-server/tests/` 全部通过

## 7. 前端 API 层

- [x] 7.1 创建 `br-app/src/api/cities.js`
  - `getCities()` 函数，调用 `GET /api/v1/cities/`
  - 参照 `br-app/src/api/rooms.js` 的导入和请求风格（使用 `get` 工具函数）
  - 验证：文件存在且导出正确

- [x] 7.2 修改 `br-app/src/api/rooms.js`
  - `getRooms(params)` 已支持 params 传参，确认 city_id 可通过 params 传入即可
  - 如需调整请验证：调用方传 `{ city_id: 1 }` 时请求 URL 包含 `?city_id=1`

## 8. 前端 Pinia Store

- [x] 8.1 创建 `br-app/src/store/modules/city.js`
  - 使用 `defineStore('city', { ... })` Options API 风格，参照 `store/modules/user.js`
  - state: currentCity (null), cities ([])
  - getters: currentCityName
  - actions: fetchCities（调用 getCities API）、initCity（从 uni.getStorageSync 恢复，无缓存则取 cities[0]）、setCity（更新 currentCity + uni.setStorageSync）
  - 验证：`import { useCityStore } from '@/store/modules/city'` 无报错

- [x] 8.2 App 启动时初始化城市
  - 在 `App.vue` 的 onLaunch 中调用 `cityStore.initCity()`
  - 或在预约页/首页的 onLoad 中调用，取决于现有 App.vue 是否已有启动逻辑
  - 验证：首次启动后 currentCity 有值

## 9. 前端城市选择页面

- [x] 9.1 创建 `br-app/src/pages/city-select/index.vue`
  - 搜索框（顶部 fixed）+ 热门城市网格 + 全部城市列表（按 province 分组）
  - 热门城市：取 cities 前 6 个（或按 sort_order 前 N 个）
  - 全部城市：按 province 分组展示（computed 属性处理分组）
  - 当前选中城市高亮显示（左侧绿色勾图标）
  - 参照现有页面风格（uni-app + tailwindCSS）

- [x] 9.2 实现搜索过滤功能
  - 搜索框 input 事件触发过滤，匹配 city.name 或 city.province
  - 无结果时显示"未找到该城市"空状态

- [x] 9.3 实现选择城市并返回
  - 点击城市调用 `cityStore.setCity(city)` 更新 Pinia store + localStorage
  - `uni.navigateBack()` 返回上一页
  - 如果点击当前城市，直接返回不更新

- [x] 9.4 在 `br-app/src/pages.json` 注册路由
  - 添加 `pages/city-select/index` 路径
  - 验证：`uni.navigateTo({ url: '/pages/city-select/index' })` 可正常跳转

## 10. 前端页面改造

- [x] 10.1 修改 `br-app/src/pages/booking/index.vue`
  - 移除硬编码 `茂名市`，改为 `cityStore.currentCityName`
  - 导入 `import { useCityStore } from '@/store/modules/city'`
  - `onTapCity()` 改为 `uni.navigateTo({ url: '/pages/city-select/index' })`
  - 验证：预约页顶部显示动态城市名，点击可跳转选城页

- [x] 10.2 预约页自习室列表增加城市过滤
  - 请求自习室列表时传入 `{ city_id: cityStore.currentCity?.id }`
  - 在 onShow 生命周期中监听城市变化并刷新列表
  - 验证：选择新城市后返回，列表按新城市过滤

- [x] 10.3 修改首页 `br-app/src/pages/index/index.vue`
  - 顶部添加城市选择器（与预约页风格一致）
  - 自习室列表请求增加 city_id 参数
  - 点击城市跳转城市选择页
  - 验证：首页显示城市名，列表按城市过滤

- [x] 10.4 修改详情页 `br-app/src/pages/booking/detail.vue`
  - 地址显示：当 room.city_name 存在时显示为 `city_name + address`，否则仅显示 address
  - 验证：有城市的自习室显示 "茂名市 茂南区..."，无城市的仅显示地址

## 11. API 文档与代码审查

- [x] 11.1 更新 `docs/api.md`
  - 补充 `GET /api/v1/cities/` 接口文档（响应字段、示例）
  - 更新 `GET /api/v1/rooms/` 文档：增加 city_id 可选参数说明，响应新增 city_id/city_name 字段

- [x] 11.2 代码审查
  - 确认 Clean Architecture 分层：routes → services → models → schemas
  - 确认前端分层：pages → api → store/modules
  - 确认前后端字段命名一致
  - 确认无重复代码
