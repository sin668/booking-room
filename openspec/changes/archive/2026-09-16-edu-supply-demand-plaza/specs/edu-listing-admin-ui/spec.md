## Purpose

定义 br-admin「教培供需信息审核」页面能力，以及将现有「认证审核」页面对齐到全站标准列表控件（搜索区 + 表格）的行为要求。

## ADDED Requirements

### Requirement: 教培供需信息审核页面

br-admin SHALL 提供「教培供需信息审核」页面，复用全站标准列表控件：顶部 `BasicForm` 搜索区（关键词、类型、状态筛选）+ `BasicTable` 列表 + `TableAction` 行操作。列表 MUST 展示信息（标题+发布时间）、发布者、类型、价格、认证状态、审核状态与操作列。行操作 MUST 提供通过 / 拒绝 / 下架 / 详情，拒绝时 MUST 要求填写理由。页面 MUST 通过后端动态菜单注册并按权限码控制操作按钮可见性。

#### Scenario: 标准搜索区筛选

- **Given** 教培供需审核页面
- **When** 管理员在搜索区选择状态「待审核」并提交
- **Then** 表格通过 `BasicTable` 的 `request` 重新加载，仅展示待审核信息

#### Scenario: 行内通过

- **Given** 列表中一条待审核信息
- **When** 管理员点击「通过」并确认
- **Then** 调用审核接口成功后表格刷新，该信息状态变为已通过

#### Scenario: 行内拒绝需理由

- **Given** 列表中一条待审核信息
- **When** 管理员点击「拒绝」
- **Then** 弹出要求填写拒绝理由的交互，未填写不允许提交

#### Scenario: 菜单与权限

- **Given** 后端 seed 已注册教培供需审核菜单与权限码
- **When** 管理员登录后加载动态路由
- **Then** 侧边栏出现该菜单，点击进入页面，无权限的操作按钮被隐藏

### Requirement: 认证审核页面对齐标准列表控件

br-admin「认证审核」页面（`/training/certification-audit`）SHALL 重构为与全站一致的标准列表页：使用 `BasicForm` 搜索区 + `BasicTable` 列表替代原手写筛选行与裸 `n-data-table`。搜索区 MUST 包含状态、类型筛选与关键词搜索，关键词 MUST 实际传入后端（按用户昵称/手机号/学校匹配）。审核操作 MUST 通过 `TableAction` 行操作承载并带权限码。重构 MUST 保持既有审核通过/拒绝行为与后端契约不变。

#### Scenario: 关键词搜索生效

- **Given** 重构后的认证审核页面
- **When** 管理员输入关键词并提交搜索
- **Then** 关键词作为查询参数传入后端，列表按匹配结果刷新（不再是无效的假搜索框）

#### Scenario: 标准控件渲染

- **Given** 重构后的认证审核页面
- **When** 页面加载
- **Then** 使用 `BasicForm` + `BasicTable`（`:request` 分页）渲染，与其他列表页风格一致

#### Scenario: 审核行为不回归

- **Given** 一条待审核认证记录
- **When** 管理员执行通过或拒绝（拒绝填写理由）
- **Then** 调用既有审核接口成功，记录状态正确更新，行为与重构前一致
