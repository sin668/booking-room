# student-review-ui 变更（delta）

## ADDED Requirements

### Requirement: 我的评价卡片评价对象行

在「我的评价」入口下，每条评价卡片 SHALL 在卡片末行展示评价对象，内容 MUST 依据评价的 `booking_type` 生成：课程评价展示 `课程名 · 老师名`（字段缺失项自动省略，分隔符不残留）；自习室评价展示 `自习室名称 · N号座位`。当评价对象的可展示信息完全缺失时，该行 SHALL 整体隐藏，MUST NOT 展示空行或残留分隔符。该行仅在「我的评价」入口展示，课程/老师维度入口的公开列表 MUST NOT 出现此行。

#### Scenario: 自习室评价展示自习室与座位

- **GIVEN** 一条 `booking_type` 为 seat 且已通过审核的评价，后端返回 `room_name` 为「星航自习室」、`seat_number` 为「8」
- **WHEN** 用户查看「我的评价」并渲染该卡片
- **THEN** 卡片末行展示「星航自习室 · 8号座位」

#### Scenario: 课程评价保持既有展示

- **GIVEN** 一条 `booking_type` 为 course 的评价，含课程名与老师名
- **WHEN** 用户查看「我的评价」并渲染该卡片
- **THEN** 卡片末行展示「课程名 · 老师名」
- **AND** 与本变更前渲染结果一致

#### Scenario: 自习室名称缺失时仅展示座位

- **GIVEN** 一条自习室评价的 `room_name` 为空但 `seat_number` 存在
- **WHEN** 卡片渲染评价对象行
- **THEN** 仅展示「N号座位」
- **AND** 不出现前导或尾随的「 · 」

#### Scenario: 评价对象信息完全缺失时隐藏该行

- **GIVEN** 一条历史自习室评价的 `room_name` 与 `seat_number` 均为空
- **WHEN** 卡片渲染
- **THEN** 不渲染评价对象行
- **AND** 卡片不出现空白分隔线或空行
