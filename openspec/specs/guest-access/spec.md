# guest-access Specification

## Purpose
TBD - created by archiving change guest-access-open-pages. Update Purpose after archive.

## Requirements

### Requirement: 游客可浏览公开内容

小程序 SHALL 允许未登录用户（游客）直接访问公开浏览页面，不强制跳转登录页。公开页面包括：首页、自习室列表、门店详情、培训课程列表、课程详情、老师简介、活动详情（浏览部分）、学员评价列表（非"我的"）、搜索、城市选择。

#### Scenario: 游客访问首页

- **Given** 用户未登录（本地无 access_token 与 refresh_token）
- **When** 用户打开小程序首页
- **Then** 首页正常展示公开内容，不跳转登录页

#### Scenario: 游客浏览公开页面触发的附加登录态请求失败不弹回登录页

- **Given** 用户未登录并正在浏览公开页面（如门店详情）
- **When** 页面附带发起的需登录接口（如关注状态查询）返回 401 且无法刷新
- **Then** 用户停留在当前页面，页面主体内容正常展示，不发生全局跳转登录页

### Requirement: 必须登录的操作主动引导登录

对于必须登录才能完成的操作（下单、支付、充值、领券、开会员、关注、评价、核销、查看订单/钱包/卡券/学习记录/消息/设置等），页面 SHALL 在入口处主动检查登录态：未登录时给出提示并跳转登录页，而不是放行请求后依赖 401 兜底。

#### Scenario: 游客进入订单 Tab

- **Given** 用户未登录
- **When** 用户切换到订单 Tab
- **Then** 提示需要登录并跳转登录页，不发起注定失败的订单列表请求

#### Scenario: 游客点击需登录操作按钮

- **Given** 用户未登录并在课程详情页
- **When** 用户点击"立即预约"按钮
- **Then** 提示需要登录并跳转登录页，预约流程不发起

### Requirement: 登录成功后返回来源页面

登录成功后小程序 SHALL 返回用户此前的浏览位置：登录页由 `navigateTo` 进入时返回上一页；由 `reLaunch`/`switchTab` 进入时回首页。

#### Scenario: 从公开页跳登录后返回

- **Given** 游客在门店详情页被引导至登录页
- **When** 登录成功
- **Then** 自动返回门店详情页
