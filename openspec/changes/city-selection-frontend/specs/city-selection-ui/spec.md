## ADDED Requirements

### Requirement: City selection page
系统 SHALL 提供城市选择页面（`pages/city-select/index.vue`）。页面包含：搜索框（顶部固定）、热门城市网格、全部城市列表（按省份分组）。搜索框输入时实时过滤城市列表（匹配城市名或省份名）。热门城市由后端 `sort_order` 决定（前 N 个城市作为热门城市）。

#### Scenario: Display city selection page
- **WHEN** 用户从预约页或首页点击城市名称进入城市选择页
- **THEN** 页面展示搜索框、热门城市网格、按省份分组的全部城市列表

#### Scenario: Search cities
- **WHEN** 用户在搜索框输入"茂"
- **THEN** 城市列表实时过滤，仅显示名称或省份包含"茂"的城市

#### Scenario: Search with no results
- **WHEN** 用户在搜索框输入不匹配任何城市的文字
- **THEN** 显示"未找到该城市"空状态提示

#### Scenario: Select a city
- **WHEN** 用户点击某个城市
- **THEN** 当前城市更新为所选城市，返回上一页，上一页（预约页或首页）城市名显示为所选城市名

#### Scenario: Select current city (no change)
- **WHEN** 用户点击当前已选中的城市
- **THEN** 直接返回上一页，不做额外操作

### Requirement: City persistence
用户选择的城市 SHALL 通过 Vuex store 管理，并持久化到本地存储（`uni.setStorageSync`）。App 启动时 SHALL 从本地存储恢复上次选择的城市，若无则使用默认城市（服务端 sort_order 最小的 active 城市）。

#### Scenario: Persist city selection
- **GIVEN** 用户在城市选择页选择了"广州市"
- **WHEN** 用户返回预约页或首页
- **THEN** 城市名显示为"广州市"，且自习室列表按广州市过滤

#### Scenario: Restore city on app restart
- **GIVEN** 用户上次选择了"深圳市"并关闭了 App
- **WHEN** 用户重新打开 App
- **THEN** 预约页城市名显示为"深圳市"

#### Scenario: Default city when no selection
- **GIVEN** 用户首次使用 App，无本地存储的城市偏好
- **WHEN** App 启动加载预约页
- **THEN** 使用服务端 sort_order 最小的 active 城市作为默认城市
