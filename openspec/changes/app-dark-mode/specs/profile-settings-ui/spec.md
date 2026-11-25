# profile-settings-ui Delta Spec

## ADDED Requirements

### Requirement: Dark mode switch in General group

设置页「通用」分组 SHALL 提供可用的「深色模式」开关，开关状态反映当前主题，并即时驱动全 App 主题切换。

#### Scenario: Switch reflects current mode

- **GIVEN** 用户打开设置页
- **WHEN** 当前主题为深色
- **THEN** 「深色模式」开关 SHALL 显示为开启
- **AND** 当前主题为浅色时开关 SHALL 显示为关闭

#### Scenario: Switch applies immediately

- **GIVEN** 用户停留在设置页
- **WHEN** 用户点击「深色模式」开关
- **THEN** 设置页与全 App SHALL 立即切换到对应主题
- **AND** 不出现需要重新进入页面才生效的情况
