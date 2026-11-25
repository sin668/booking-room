# app-dark-mode-ui Delta Spec

## ADDED Requirements

### Requirement: Theme mode switching

小程序 SHALL 支持浅色与深色两种主题模式，并以「设置 - 通用 - 深色模式」开关作为唯一入口。

#### Scenario: Toggle dark mode on

- **GIVEN** 用户处于浅色模式并打开设置页
- **WHEN** 用户打开「深色模式」开关
- **THEN** 当前页面 SHALL 立即切换为深色配色
- **AND** 其他已加载页面与后续打开的页面 SHALL 使用深色配色

#### Scenario: Toggle dark mode off

- **GIVEN** 用户处于深色模式
- **WHEN** 用户关闭「深色模式」开关
- **THEN** 全 App SHALL 立即恢复浅色配色

### Requirement: Theme persistence

客户端 SHALL 将主题模式持久化到本地存储，并在下次启动时恢复。

#### Scenario: Restore theme after relaunch

- **GIVEN** 用户已选择深色模式
- **WHEN** 用户关闭并重新打开小程序
- **THEN** 首屏 SHALL 以深色模式渲染，不出现浅色闪烁
- **AND** 设置页开关 SHALL 保持开启状态

### Requirement: Theme coverage

主题 token SHALL 覆盖除 `src/TUIKit/**` 之外的全部业务页面，包括页面背景、卡片、文本、边框、输入框、弹层与状态标签。

#### Scenario: Business pages follow theme

- **GIVEN** 用户处于深色模式
- **WHEN** 用户浏览首页、自习、培训、广场、我的及其二级业务页面
- **THEN** 页面背景与卡片 SHALL 使用深色 token，不得出现大面积浅色残留

#### Scenario: Chat pages excluded

- **GIVEN** 用户处于深色模式
- **WHEN** 用户进入基于 TUIKit 的聊天页面
- **THEN** 聊天页面 MAY 保持浅色配色，且不得因主题切换出现样式破损

### Requirement: Native chrome sync

主题切换 SHALL 同步原生导航栏、状态栏与 TabBar 配色。

#### Scenario: Native bars follow theme

- **GIVEN** 用户切换主题模式
- **WHEN** 当前页面使用系统导航栏或底部 TabBar
- **THEN** 导航栏背景、状态栏文字颜色与 TabBar 背景/文字颜色 SHALL 同步切换
