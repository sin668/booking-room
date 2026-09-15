## MODIFIED Requirements

### Requirement: My reviews entry on profile page

「我的」页 SHALL 在既有菜单列表中提供「我的评价」入口，其结构与样式 MUST 与相邻菜单项保持一致（图标色块 + 文案 + 右侧统计文案 + 右侧箭头）。入口右侧 SHALL 展示当前用户发表的评价总数，形如 `X条评论`；该数量 MUST 来自后端评价列表接口的 `total` 字段（含待审核与已驳回），MUST NOT 由前端在本地分页数据上推算；当前用户无任何评价时该统计文案 SHALL 留空而 MUST NOT 显示 `0条评论`。点击后 MUST 跳转到评价列表页并过滤为当前用户本人发表的评价。未登录用户点击时 SHALL 先提示登录再引导至登录页，MUST NOT 直接进入空白列表。

#### Scenario: Menu item rendered consistently

- **WHEN** 用户打开「我的」页
- **THEN** 菜单列表中出现「我的评价」项
- **AND** 其布局与相邻菜单项一致，含图标色块、文案、右侧统计文案与右侧箭头

#### Scenario: Menu item shows review count

- **GIVEN** 当前登录用户已发表 3 条评价（含待审核或已驳回状态）
- **WHEN** 用户打开「我的」页
- **THEN** 「我的评价」行右侧显示 `3条评论`

#### Scenario: Menu item hides count when no review

- **GIVEN** 当前登录用户尚未发表任何评价
- **WHEN** 用户打开「我的」页
- **THEN** 「我的评价」行右侧不显示统计文案
- **AND** 该行的图标、文案与箭头保持原样

#### Scenario: Navigate to my reviews

- **GIVEN** 用户已登录
- **WHEN** 用户点击「我的评价」
- **THEN** 跳转到评价列表页
- **AND** 列表页展示当前用户本人发表的全部状态评价

#### Scenario: Unauthenticated tap prompts login

- **GIVEN** 用户未登录
- **WHEN** 用户点击「我的评价」
- **THEN** 页面提示需要登录
- **AND** 引导用户前往登录页
