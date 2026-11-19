# app-detail-cs-follow Specification

## Purpose
TBD - created by archiving change app-cs-edu-follow. Update Purpose after archive.
## Requirements
### Requirement: 客服会话对象与平台客服回退

br-app SHALL 提供统一的客服会话入口 `openCSChat(creatorUsername)`：未登录先引导登录；IM 初始化失败时提示错误不跳转。会话对象为传入的创建人 IM 用户名；当其为空或等于当前用户自己的 IM id 时，SHALL 回退打开平台客服会话。平台客服为用户 id `bd7f84cc-3d8b-480f-9327-30ee827cf386`，其 IM 用户名按 UUID hex 规则为 `bd7f84cc3d8b480f932730ee827cf386`。会话通过 `/TUIKit/components/TUIChat/index?conversationID=C2C{username}` 打开。

老师详情页与教培供需详情页的客服按钮 SHALL 固定打开平台客服会话。

#### Scenario: 打开创建人会话

- **Given** 已登录用户在学习室/课程详情页，创建人 IM 用户名存在且不是自己
- **When** 点击客服按钮
- **Then** 打开 C2C + 创建人 IM 用户名的单聊会话

#### Scenario: 创建人为空或自己时回退平台客服

- **Given** 学习室/课程创建人为空（存量数据）或为当前用户自己
- **When** 点击客服按钮
- **Then** 打开平台客服会话

#### Scenario: 老师页与供需页固定平台客服

- **Given** 已登录用户在老师详情页或教培供需详情页
- **When** 点击客服按钮
- **Then** 打开平台客服会话

#### Scenario: 未登录点击客服

- **Given** 游客在任一含客服按钮的详情页
- **When** 点击客服按钮
- **Then** 引导登录，不打开会话

### Requirement: C 端详情返回创建人 IM 用户名

`GET /api/v1/rooms/{room_id}` SHALL 返回 `creator_username` 字段：学习室创建人（created_by）的 IM 用户名（UUID hex），创建人为空时为 null。课程详情接口 SHALL 返回 `creator_username` 字段：课程所在学习室创建人的 IM 用户名，学习室或创建人为空时为 null。

#### Scenario: 房间详情含创建人 IM 用户名

- **Given** 学习室由某管理员创建
- **When** C 端请求房间详情
- **Then** 响应 `creator_username` 为该管理员 UUID 的 hex 形式

#### Scenario: 存量房间创建人为空

- **Given** 学习室 created_by 为空
- **When** C 端请求房间详情
- **Then** 响应 `creator_username` 为 null

#### Scenario: 课程详情取所在学习室创建人

- **Given** 课程在学习室 R 上课，R 由管理员 A 创建
- **When** C 端请求课程详情
- **Then** 响应 `creator_username` 为 A 的 UUID hex，与课程自身创建人无关

### Requirement: 老师详情页底部操作栏

老师详情页（`pages-sub/teacher/profile.vue`）底部固定栏 SHALL 为：心状关注按钮（切换教师关注，行为与原导航栏关注一致）+ 戴耳机客服按钮（平台客服）+「返回培训室」按钮（跳转培训课程列表页）。原空实现的聊天按钮 SHALL 移除。

#### Scenario: 底部三按钮

- **Given** 用户进入老师详情页
- **When** 页面加载完成
- **Then** 底部显示关注、客服、返回培训室三个按钮

#### Scenario: 底部关注切换

- **Given** 已登录用户未关注该教师
- **When** 点击底部关注按钮
- **Then** 关注成功，心形变红；再次点击取消关注

#### Scenario: 返回培训室

- **When** 点击「返回培训室」按钮
- **Then** 切换到培训课程列表页（`pages/training/index`）

### Requirement: 教培供需关注

room-follows 接口 SHALL 支持 `follow_type=listing`：关注目标为教培供需信息（edu_listings.id），仅 `status=approved` 的信息可关注（否则 404）；关注幂等（重复关注返回 200）；取消关注删除记录。关注列表（`GET /api/v1/room-follows?follow_type=listing`）SHALL 仅返回仍为 approved 的信息，映射为关注列表通用结构（room_type='listing'，name=标题，cover_image=首图，min_price=价格，address=区域），按关注时间倒序；传入 city_id 时按信息城市匹配或城市为空过滤。

#### Scenario: 关注供需信息

- **Given** 已登录用户与一条 approved 供需信息
- **When** POST `/api/v1/room-follows/{id}?follow_type=listing`
- **Then** 创建关注记录并返回 201 与列表结构；重复请求返回 200

#### Scenario: 非 approved 不可关注

- **Given** 供需信息状态为 pending/rejected/offline 或不存在
- **When** 以 follow_type=listing 关注
- **Then** 返回 404

#### Scenario: 关注列表仅 approved

- **Given** 用户关注了 2 条供需信息，其中 1 条被下架（offline）
- **When** 请求 follow_type=listing 的关注列表
- **Then** 仅返回仍为 approved 的 1 条

#### Scenario: 取消关注

- **Given** 用户已关注某供需信息
- **When** DELETE `/api/v1/room-follows/{id}?follow_type=listing`
- **Then** 返回 204，关注列表不再包含该信息

### Requirement: 我的关注「关注供需」TAB

我的关注页（`pages-sub/favorites/index.vue`）SHALL 在既有四个 TAB 后新增「关注供需」TAB，展示 follow_type=listing 的关注列表（封面图、标题、描述摘要、价格），点击跳转供需详情页；无数据时显示空状态与去教培供需广场入口。既有四个 TAB 的行为不变。

#### Scenario: 查看关注供需列表

- **Given** 用户关注了若干 approved 供需信息
- **When** 进入我的关注并切到「关注供需」TAB
- **Then** 展示关注的供需信息列表，点击进入对应详情页

#### Scenario: 空状态

- **Given** 用户未关注任何供需信息
- **When** 切到「关注供需」TAB
- **Then** 显示空状态提示与去教培供需广场入口

