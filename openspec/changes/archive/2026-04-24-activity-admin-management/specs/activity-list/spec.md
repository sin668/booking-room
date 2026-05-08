## MODIFIED Requirements

### Requirement: List activities API
系统 SHALL 提供 `GET /api/v1/activities/` 接口，返回热门活动列表。仅返回 `is_active=true` 的活动，按 `sort_order` 升序排列。无需分页（活动数量有限，全量返回）此接口行为不变，仅在此声明管理端新增接口与此接口共存，公开接口不受管理端变更影响。

#### Scenario: Successful activities request
- **WHEN** 客户端发送 `GET /api/v1/activities/`
- **THEN** 返回 HTTP 200，响应为活动数组，仅包含 `is_active=true` 的记录，按 `sort_order` 升序

#### Scenario: No active activities
- **WHEN** 数据库中无 `is_active=true` 的活动
- **THEN** 返回 HTTP 200，响应为空数组 `[]`

#### Scenario: Admin deactivates activity
- **WHEN** 管理员通过管理端将某活动的 `is_active` 设为 false
- **THEN** 小程序端 `GET /api/v1/activities/` 不再返回该活动
