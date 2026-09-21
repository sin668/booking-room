# training-course-list-ui Specification

## Purpose
培训课程列表页面提供培训室浏览和分类课程查看功能，用户可切换分类 TAB 查看不同类型的课程列表，在"全部"TAB 查看培训室列表及其热门推荐课程。

## Requirements

### Requirement: Training course list page entry

系统 SHALL 在 br-app 底部导航栏增加"培训"入口，点击后导航到培训课程列表页面 `pages/training/index`。页面参考 `prototype/training.html` 高保真原型图，保持总体风格一致。

#### Scenario: Navigate to training page

- **GIVEN** 用户在 br-app 首页
- **WHEN** 用户点击底部导航栏"培训"入口
- **THEN** 导航到培训课程列表页面，默认显示"全部"TAB 的培训室列表

### Requirement: Category tab switching

培训课程列表页面 SHALL 显示横向滚动的分类 TAB 栏，包含"全部"和 4 个分类标签（小学辅导、中学辅导、公考备考、技能提升）。默认选中"全部"TAB。点击不同 TAB 时切换显示内容。各 TAB 对应的 category 枚举值：小学辅导=primaryschool、中学辅导=middleschool、公考备考=civil_service、技能提升=skills。

#### Scenario: Default tab is all

- **GIVEN** 用户刚进入培训课程列表页面
- **WHEN** 页面加载完成
- **THEN** "全部"TAB 处于选中状态，页面显示培训室列表

#### Scenario: Switch to category tab

- **GIVEN** 用户在"全部"TAB
- **WHEN** 用户点击"小学辅导"TAB
- **THEN** "小学辅导"TAB 处于选中状态，页面切换为 category=primaryschool 的课程列表

#### Scenario: Switch back to all tab

- **GIVEN** 用户在"小学辅导"TAB
- **WHEN** 用户点击"全部"TAB
- **THEN** "全部"TAB 处于选中状态，页面切换回培训室列表

### Requirement: Training room card with expandable courses

"全部"TAB 的培训室列表 SHALL 显示培训室卡片。每张卡片包含培训室封面图、名称、营业状态标签、评分、距离、地址、设施标签和"热门推荐课程"展开按钮。点击卡片可跳转到培训室详情页（详情页不在本次范围内，预留跳转入口）。点击"热门推荐课程"展开按钮可展开/收起热门课程列表。

#### Scenario: Display training room card

- **GIVEN** 培训室列表有数据
- **WHEN** 用户在"全部"TAB
- **THEN** 显示培训室卡片列表，每张卡片包含封面图、名称、营业状态、评分、地址、设施标签

#### Scenario: Expand hot courses

- **GIVEN** 培训室卡片处于收起状态
- **WHEN** 用户点击"热门推荐课程"展开按钮
- **THEN** 卡片下方展开热门课程列表，展开图标旋转 180 度

#### Scenario: Collapse hot courses

- **GIVEN** 培训室卡片处于展开状态
- **WHEN** 用户再次点击"热门推荐课程"展开按钮
- **THEN** 热门课程列表收起，展开图标恢复原位

#### Scenario: Hot course item display

- **GIVEN** 培训室卡片已展开，有热门课程数据
- **WHEN** 用户查看展开的课程列表
- **THEN** 每条课程显示封面图、课程名称、教师姓名、报名人数和价格

### Requirement: Course card display

分类 TAB 的课程列表 SHALL 显示课程卡片。每张卡片包含课程封面图、名称、状态标签（热销/新课/名师/推荐）、教师头像和姓名、所属培训室名称、评分、报名人数、价格（/课时）和"预约"按钮。课程封面图 SHALL 叠加两个与培训室卡片一致的角标：左上角显示"可预约"状态标签，右下角显示"课程"类型标签。点击课程卡片跳转到课程详情页。

#### Scenario: Display course card

- **GIVEN** 分类课程列表有数据
- **WHEN** 用户在某个分类 TAB
- **THEN** 显示课程卡片列表，每张卡片包含封面图、名称、状态标签、教师信息、所属培训室、评分、报名人数、价格和预约按钮

#### Scenario: Course card cover badges

- **GIVEN** 分类课程列表有数据
- **WHEN** 用户查看课程卡片
- **THEN** 封面图左上角显示"可预约"状态标签，右下角显示"课程"类型标签，样式与培训室卡片的"可预约"/"培训"角标一致

#### Scenario: Course card without status tag

- **GIVEN** 课程没有特殊状态标签（热销/新课/名师/推荐）
- **WHEN** 用户查看课程卡片
- **THEN** 课程卡片右上角不显示状态标签，但封面图左上角"可预约"与右下角"课程"角标仍正常显示

### Requirement: Search bar UI

培训课程列表页面 SHALL 在顶部显示搜索栏，placeholder 为"搜索课程、老师"。搜索栏为纯 UI 展示，不实现后端搜索功能。

#### Scenario: Search bar display

- **GIVEN** 用户进入培训课程列表页面
- **WHEN** 页面加载完成
- **THEN** 顶部显示搜索栏，placeholder 为"搜索课程、老师"

#### Scenario: Search bar input without backend

- **GIVEN** 用户在搜索栏输入文字
- **WHEN** 用户点击搜索或回车
- **THEN** 不触发后端搜索请求（仅 UI 展示，后端搜索功能留待后续）

### Requirement: Page loading and empty states

培训课程列表页面 SHALL 在数据加载时显示加载状态，在无数据时显示空状态提示。

#### Scenario: Loading state

- **GIVEN** 用户进入培训课程列表页面或切换 TAB
- **WHEN** 数据正在加载
- **THEN** 显示加载中状态

#### Scenario: Empty training room list

- **GIVEN** 没有培训室数据
- **WHEN** 用户在"全部"TAB
- **THEN** 显示"暂无培训室"空状态提示

#### Scenario: Empty course list

- **GIVEN** 某分类下没有课程
- **WHEN** 用户在该分类 TAB
- **THEN** 显示"暂无课程"空状态提示

### Requirement: Course list city linkage

培训课程列表页面 SHALL 在分类课程 TAB 按当前所选城市过滤课程，请求 `GET /api/v1/training/courses` 时携带当前城市 `city_id`。当用户切换城市后重新进入页面，SHALL 按当前激活的 TAB 刷新对应列表：处于"全部"TAB 刷新培训室列表，处于分类 TAB 刷新课程列表。

#### Scenario: Course tab passes city_id

- **GIVEN** 用户已选择城市且处于某个分类课程 TAB
- **WHEN** 页面请求课程列表
- **THEN** 请求携带当前城市的 `city_id` 参数，仅展示该城市（及未设置城市的培训室）下的课程

#### Scenario: City switch refreshes active tab

- **GIVEN** 用户在分类课程 TAB 下切换了城市后重新进入页面
- **WHEN** 页面检测到当前城市与上次记录不一致
- **THEN** 按当前激活 TAB 刷新：分类 TAB 重新拉取课程列表，"全部"TAB 重新拉取培训室列表
