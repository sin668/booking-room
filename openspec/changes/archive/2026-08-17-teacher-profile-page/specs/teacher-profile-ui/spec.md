## Purpose

教师简介前端页面展示教师的详细信息、主讲课程列表和学员评价，为 br-app 用户提供完整的教师认知和关注入口。

## ADDED Requirements

### Requirement: 教师简介页面路由

系统 SHALL 在 `pages/teacher/profile.vue` 注册教师简介页面，通过 `pages.json` 配置路由 `pages/teacher/profile`，接收 `teacher_id` 查询参数。页面使用自定义导航栏。

#### Scenario: 从课程详情页跳转到教师简介页

- **GIVEN** 用户在课程详情页，该课程关联了教师 id=1
- **WHEN** 用户点击教师信息卡
- **THEN** 跳转到 `/pages/teacher/profile?teacher_id=1`

### Requirement: 教师信息展示

页面 SHALL 展示教师 Hero 区（背景渐变、头像、姓名、认证标签、教龄/学历信息）、统计行（学员数量、授课课程数、综合评分）、个人简介区域。

#### Scenario: 加载教师详情数据

- **GIVEN** 教师 id=1 存在且后端返回有效数据
- **WHEN** 页面加载完成
- **THEN** 展示教师头像、姓名、认证标签、bio 信息
- **AND** 统计行显示学员数量、授课课程数（courses 数组长度）、综合评分

#### Scenario: 教师数据加载失败

- **WHEN** 后端 API 返回 404 或网络错误
- **THEN** 显示错误提示，不展示页面内容

### Requirement: 主讲课程列表

页面 SHALL 展示该教师的所有课程列表，卡片样式复用培训室概况页的"本培训室课程"卡片结构。每张课程卡片 SHALL 包含课程封面、课程名称、"共X课时 · 含资料"行（替换原"主讲老师"行）、评分和学员数、价格和预约按钮。

#### Scenario: 展示课程列表

- **GIVEN** 教师 id=1 关联了 2 门活跃课程
- **WHEN** 页面加载完成
- **THEN** 显示"主讲课程"标题和"共2门"副标题
- **AND** 展示 2 张课程卡片

#### Scenario: 课程卡片显示课时数

- **GIVEN** 一门课程关联了 12 个课时
- **WHEN** 课程卡片渲染完成
- **THEN** 显示"共12课时 · 含资料"

#### Scenario: 无课程时显示空状态

- **GIVEN** 教师未关联任何活跃课程
- **WHEN** 页面加载完成
- **THEN** 显示"暂无课程"空状态提示

### Requirement: 心状关注按钮

页面右上角 SHALL 显示心状关注按钮（未关注时为空心 `far fa-heart`，已关注时为实心 `fas fa-heart`）。点击按钮调用 `room_follows` API，`follow_type=teacher`。

#### Scenario: 关注教师

- **GIVEN** 用户未关注该教师
- **WHEN** 用户点击心状关注按钮
- **THEN** 调用 `POST /api/v1/room-follows/{teacher_id}?follow_type=teacher`
- **AND** 按钮变为已关注状态（实心心）
- **AND** 显示"已关注"Toast

#### Scenario: 取消关注教师

- **GIVEN** 用户已关注该教师
- **WHEN** 用户点击心状关注按钮
- **THEN** 调用 `DELETE /api/v1/room-follows/{teacher_id}?follow_type=teacher`
- **AND** 按钮变为未关注状态（空心心）
- **AND** 显示"已取消关注"Toast

### Requirement: 学员评价区域

页面 SHALL 展示学员评价区域，使用静态占位数据。评价区域包含标题"学员评价"、评价数量、评价列表和"查看全部评价"按钮。

#### Scenario: 展示静态评价数据

- **WHEN** 页面加载完成
- **THEN** 展示 3 条静态评价（包含头像、昵称、五星评分、评价内容、时间）
- **AND** 显示"查看全部评价"按钮（点击暂不跳转）

### Requirement: 底部返回课程按钮

页面底部操作栏 SHALL 显示"返回课程"按钮，点击跳转到 `/pages/training/index`（培训列表页 TabBar 入口）。

#### Scenario: 点击返回课程

- **WHEN** 用户点击"返回课程"按钮
- **THEN** 跳转到 `/pages/training/index`（switchTab）
