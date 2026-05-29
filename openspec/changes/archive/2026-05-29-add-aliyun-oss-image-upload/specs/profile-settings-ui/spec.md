## MODIFIED Requirements

### Requirement: Settings page layout
小程序 SHALL 提供“我的设置”页面，并保持与 `prototype/settings.html` 的总体视觉风格一致，包括顶部导航、头像资料卡、白色圆角分组卡片、个人资料、账号与安全、通知设置、通用、关于和退出登录入口。头像资料卡 SHALL 支持点击头像选择本地图片并上传，上传成功后更新当前用户头像。

#### Scenario: Open settings from profile
- **GIVEN** 用户已登录并停留在“我的”页面
- **WHEN** 用户点击设置入口
- **THEN** 小程序导航到“我的设置”页面
- **AND** 页面展示头像资料卡和设置分组列表

#### Scenario: Settings page visual hierarchy
- **GIVEN** 用户进入“我的设置”页面
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 使用浅灰背景、白色圆角卡片、紧凑列表行和右侧箭头/开关控件呈现内容

#### Scenario: Upload avatar from settings
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击头像并选择一张图片
- **THEN** 小程序调用统一图片上传接口上传该图片
- **AND** 上传请求使用 `avatar` scope，图片大小不得超过 2MB
- **AND** 上传成功后调用当前用户资料更新接口保存 `avatar` 为返回的图片 URL
- **AND** 页面头像和“我的”页面头像刷新为新 URL

#### Scenario: Avatar upload failure
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户选择头像图片但上传接口失败
- **THEN** 页面展示上传失败提示
- **AND** 当前用户头像保持原值

#### Scenario: Avatar profile save failure
- **GIVEN** 用户头像图片已上传成功
- **WHEN** 保存用户资料接口失败
- **THEN** 页面展示保存失败提示
- **AND** 当前用户头像保持原值
