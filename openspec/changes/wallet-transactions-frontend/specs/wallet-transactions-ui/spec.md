## ADDED Requirements

### Requirement: 钱包流水页面路由
应用 SHALL 提供 `/pages/wallet/transactions` 钱包流水页面，页面导航标题为“钱包流水”。

#### Scenario: 从个人中心打开钱包流水
- **GIVEN** 用户已登录并位于个人中心页面
- **WHEN** 用户点击“钱包流水”菜单项
- **THEN** 应用跳转到 `/pages/wallet/transactions`
- **AND** 页面标题显示“钱包流水”

#### Scenario: 从充值页打开交易明细
- **GIVEN** 用户已登录并位于钱包充值页面
- **WHEN** 用户点击余额卡片区域的“交易明细”入口
- **THEN** 应用跳转到 `/pages/wallet/transactions`
- **AND** 页面标题显示“钱包流水”

### Requirement: 钱包流水摘要
钱包流水页面 SHALL 在顶部展示账户余额摘要，并展示本页可理解的收入、支出统计入口或统计值。余额数据 SHALL 来自现有余额查询接口。

#### Scenario: 页面加载余额摘要
- **GIVEN** 用户进入钱包流水页面
- **WHEN** `GET /api/v1/wallet/balance` 请求成功
- **THEN** 页面展示当前余额和累计充值金额
- **AND** 余额金额按人民币两位小数展示

#### Scenario: 余额摘要加载失败
- **GIVEN** 用户进入钱包流水页面
- **WHEN** `GET /api/v1/wallet/balance` 请求失败
- **THEN** 页面展示“余额加载失败”提示
- **AND** 流水列表仍可继续加载

### Requirement: 钱包流水筛选
钱包流水页面 SHALL 提供紧凑的流水类型筛选，至少包含“全部”和“充值”。筛选项切换后 SHALL 重新从第一页加载流水。

#### Scenario: 默认展示全部流水
- **GIVEN** 用户首次进入钱包流水页面
- **WHEN** 页面初始化
- **THEN** “全部”筛选项处于激活状态
- **AND** 页面通过 `GET /api/v1/wallet/transactions?page=1&page_size=20&type=all` 加载流水

#### Scenario: 切换到充值流水
- **GIVEN** 用户正在查看全部流水
- **WHEN** 用户点击“充值”筛选项
- **THEN** “充值”筛选项变为激活状态
- **AND** 页面清空旧列表并通过 `type=recharge` 从第一页重新加载

### Requirement: 钱包流水列表
钱包流水页面 SHALL 将每条流水展示为列表项，包含标题、状态、创建时间、金额、优惠赠送金额、支付方式和交易后余额。收入类金额 SHALL 使用正向视觉样式，支出类金额 SHALL 使用弱化或负向视觉样式。

#### Scenario: 展示充值成功流水
- **GIVEN** 后端返回一条 `type=recharge` 且 `status=completed` 的流水
- **WHEN** 页面渲染流水列表
- **THEN** 列表项展示“充值到账”标题、完成状态、支付方式、创建时间、`+¥amount` 和交易后余额
- **AND** 若 `bonus_amount` 大于 0，展示“赠送 ¥bonus_amount”

#### Scenario: 展示待处理流水
- **GIVEN** 后端返回一条 `status=pending` 的流水
- **WHEN** 页面渲染流水列表
- **THEN** 列表项展示待处理状态
- **AND** 金额不得展示为已到账成功样式

#### Scenario: 展示充值失败流水
- **GIVEN** 后端返回一条 `type=recharge` 且 `status=failed` 的流水
- **WHEN** 页面渲染流水列表
- **THEN** 列表项展示“充值失败”标题和失败状态
- **AND** 金额不得展示为已到账成功样式

### Requirement: 钱包流水分页加载
钱包流水页面 SHALL 支持分页加载更多；当后端返回 `has_more=false` 时 SHALL 停止继续请求下一页并展示到底状态。

#### Scenario: 上拉加载下一页
- **GIVEN** 当前流水响应包含 `has_more=true`
- **WHEN** 用户滚动到列表底部
- **THEN** 页面请求下一页流水
- **AND** 新数据追加到当前列表末尾

#### Scenario: 没有更多流水
- **GIVEN** 当前流水响应包含 `has_more=false`
- **WHEN** 用户滚动到列表底部
- **THEN** 页面不再请求下一页
- **AND** 页面展示“没有更多流水了”

### Requirement: 钱包流水空状态和错误重试
钱包流水页面 SHALL 在当前筛选条件无数据时展示空状态；当流水接口失败时 SHALL 展示错误提示并提供重试入口。

#### Scenario: 全部流水为空
- **GIVEN** 后端返回空列表且 `total=0`
- **WHEN** 页面完成流水加载
- **THEN** 页面展示空状态
- **AND** 文案为“暂无钱包流水”
- **AND** 页面提供前往钱包充值的行动入口

#### Scenario: 流水加载失败后重试
- **GIVEN** 用户位于钱包流水页面
- **WHEN** `GET /api/v1/wallet/transactions` 请求失败
- **THEN** 页面展示“流水加载失败，请重试”
- **AND** 用户点击重试后，页面按当前筛选条件重新加载第一页

### Requirement: 钱包流水页面视觉一致性
钱包流水页面 SHALL 与现有移动端页面保持一致的视觉语言，使用项目主色、白色卡片、圆角列表项、弱化分隔线和安全区底部留白。页面 SHALL 使用余额摘要卡、紧凑筛选、稳定列表项尺寸和明确的金额正负视觉，不引入新的独立金融主题。

#### Scenario: 页面视觉检查
- **GIVEN** 钱包流水页面渲染完成
- **WHEN** 用户查看页面
- **THEN** 页面布局、配色、间距与个人中心、充值页和卡券页风格一致
- **AND** 文本在常见移动端宽度下不得溢出或互相遮挡
