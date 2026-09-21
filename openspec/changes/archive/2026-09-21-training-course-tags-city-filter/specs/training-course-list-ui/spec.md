## MODIFIED Requirements

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

## ADDED Requirements

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
