## ADDED Requirements

### Requirement: City database model
系统 SHALL 创建 `cities` 表，包含字段：`id`（主键，自增）、`name`（VARCHAR(50)，非空，城市名如"茂名市"）、`province`（VARCHAR(50)，非空，省份如"广东省"）、`sort_order`（INTEGER，默认 0，排序权重，值越小越靠前）、`status`（VARCHAR(20)，默认 "active"，枚举值 "active"/"inactive"）、`created_at`、`updated_at`。

#### Scenario: Create city record
- **WHEN** 向 `cities` 表插入一条记录，`name="茂名市"`，`province="广东省"`，`sort_order=1`
- **THEN** 记录成功创建，`id` 自增，`status` 默认为 "active"

#### Scenario: City name uniqueness
- **WHEN** 向 `cities` 表插入一条 `name="茂名市"` 的记录，且已存在同名记录
- **THEN** 插入失败，抛出唯一约束错误

### Requirement: List cities API
系统 SHALL 提供 `GET /api/v1/cities/` 接口，返回启用状态（`status=active`）的城市列表，按 `sort_order` 升序排列。不需要分页（城市数量有限）。响应字段包含：`id`（整数）、`name`（字符串）、`province`（字符串）。

#### Scenario: Successful list request
- **WHEN** 客户端发送 `GET /api/v1/cities/`
- **THEN** 返回 HTTP 200，响应为城市数组，按 `sort_order` 升序排列，仅包含 `status=active` 的城市

#### Scenario: No active cities
- **WHEN** 数据库中没有 `status=active` 的城市
- **THEN** 返回 HTTP 200，响应为空数组

### Requirement: Study room city association
StudyRoom 模型 SHALL 新增 `city_id`（INTEGER，可空，外键关联 cities.id）字段。现有自习室数据在迁移时 SHALL 被分配默认城市的 city_id。

#### Scenario: Add city_id to existing study room
- **WHEN** 执行 Alembic 迁移
- **THEN** `study_rooms` 表新增 `city_id` 列（可空），现有记录的 `city_id` 被设置为默认城市（茂名市）的 id

#### Scenario: Create study room with city
- **WHEN** 创建新自习室时指定 `city_id`
- **THEN** 自习室记录成功创建，`city_id` 关联到对应城市

#### Scenario: Study room without city
- **WHEN** 创建自习室时不指定 `city_id`
- **THEN** 自习室记录成功创建，`city_id` 为 null
