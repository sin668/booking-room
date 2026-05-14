## MODIFIED Requirements

### Requirement: Homepage quick entry grid
首页 SHALL 展示快捷入口网格，4 列布局，每项包含圆形图标背景和文字标签。快捷入口 SHALL 包含：钱包充值（蓝色钱包图标）、卡券套餐（橙色票券图标）、学习记录（绿色书本图标）、自习室（紫色定位图标）。点击“卡券套餐” SHALL 跳转到 `/pages/coupon/index` 卡券包页面；点击“学习记录” SHALL 跳转到 `/pages/study-record/index`；点击“自习室” SHALL 通过 tabBar 切换到 `/pages/booking/index`。

#### Scenario: Display quick entries
- **GIVEN** 用户进入首页
- **WHEN** 首页渲染快捷入口区域
- **THEN** 首页展示 4 个快捷入口图标，横向等分排列
- **AND** 入口文字依次包含“钱包充值”、“卡券套餐”、“学习记录”、“自习室”

#### Scenario: Tap coupon package quick entry
- **GIVEN** 用户位于首页
- **WHEN** 用户点击“卡券套餐”快捷入口
- **THEN** 系统跳转到 `/pages/coupon/index` 卡券包页面

#### Scenario: Tap study record quick entry
- **GIVEN** 用户位于首页
- **WHEN** 用户点击“学习记录”快捷入口
- **THEN** 系统跳转到 `/pages/study-record/index`

#### Scenario: Tap study room quick entry
- **GIVEN** 用户位于首页
- **WHEN** 用户点击“自习室”快捷入口
- **THEN** 系统通过 tabBar 切换到 `/pages/booking/index`
