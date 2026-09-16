# edu-listing-api Specification

## Purpose
定义「教培供需」C 端后端能力：独立于老师/课程的供需信息数据模型、综合广场列表、详情、带认证前置校验的发布，以及发布者查看自己信息的列表。
## Requirements
### Requirement: 教培供需信息数据模型

系统 SHALL 提供独立的 `edu_listings` 表存储教培供需信息，与 teachers、courses、study_rooms 等业务表无任何外键关联。每条信息 MUST 包含：发布者用户 ID、信息类型 `listing_type`（`tutor` 家教 / `training` 培训班 / `demand` 求教）、标题、科目分类、授课/求学方式、价格、服务区域、详细描述、图片列表（最多 3 张）、审核状态、浏览次数、时间戳。审核状态 MUST 为 `pending`/`approved`/`rejected`/`offline` 之一，新建时默认 `pending`。

#### Scenario: 新建供需信息默认待审核

- **Given** 一个已登录用户提交合法的供需信息
- **When** 系统持久化该信息
- **Then** 记录的 `status` 为 `pending`，`view_count` 为 0，且不与任何老师/课程记录建立关联

#### Scenario: 图片数量上限

- **Given** 用户提交携带超过 3 张图片的供需信息
- **When** 系统校验请求
- **Then** 返回 422 校验错误，提示图片最多 3 张

### Requirement: 综合广场列表

系统 SHALL 提供 `GET /api/v1/edu-listings` 综合广场分页列表，将教（`tutor`/`training`）与学（`demand`）的已审核通过信息**混合**在同一个列表中返回，而非分成两个独立广场。列表 MUST 仅返回 `status == approved` 的信息，支持按 `listing_type`、科目、城市筛选与按发布时间/价格排序，分页参数为 `page`/`page_size`，响应为 `{ items, total, page, page_size }`。该接口 MUST 允许游客访问（无需登录）。

#### Scenario: 教与学混排

- **Given** 数据库中同时存在已通过的家教、培训班与求教信息
- **When** 游客请求综合广场列表且不传 `listing_type`
- **Then** 返回的 `items` 中同时包含教类与学类信息，按选定排序混排

#### Scenario: 仅展示已通过信息

- **Given** 存在 `pending`、`rejected`、`offline` 状态的供需信息
- **When** 任意用户请求综合广场列表
- **Then** 这些信息均不出现在 `items` 中

#### Scenario: 按类型筛选

- **Given** 综合广场存在多种类型信息
- **When** 用户请求列表并传 `listing_type=demand`
- **Then** 返回的 `items` 仅包含求教类信息

### Requirement: 供需信息详情

系统 SHALL 提供 `GET /api/v1/edu-listings/{listing_id}` 返回单条供需信息详情，并附带发布者昵称、头像及其学历/教师资格认证状态。每次成功获取详情 MUST 使该信息的浏览次数加 1。

#### Scenario: 详情自增浏览数

- **Given** 一条已通过、浏览次数为 N 的供需信息
- **When** 用户请求其详情
- **Then** 返回详情且该信息浏览次数变为 N+1

#### Scenario: 详情不存在

- **Given** 一个不存在的 `listing_id`
- **When** 用户请求详情
- **Then** 返回 404

### Requirement: 发布供需信息的认证前置校验

系统 SHALL 提供 `POST /api/v1/edu-listings` 供已登录用户发布供需信息，并在后端强制认证前置校验：发布 `tutor`（家教）MUST 要求发布者学历认证已通过；发布 `training`（培训班）MUST 要求发布者教师资格认证已通过；发布 `demand`（求教）MUST 要求发布者实名认证已通过。认证状态判断 MUST 同时接受 `approved` 与 `verified` 为已通过。校验不通过 MUST 返回 400 且不创建记录。

#### Scenario: 未认证发布家教被拒绝

- **Given** 一个学历认证未通过（无记录或状态非 approved/verified）的用户
- **When** 该用户发布 `listing_type=tutor` 的信息
- **Then** 返回 400 提示需先完成学历认证，且不创建记录

#### Scenario: 已认证发布培训班成功

- **Given** 一个教师资格认证状态为 `approved` 或 `verified` 的用户
- **When** 该用户发布 `listing_type=training` 的合法信息
- **Then** 创建成功，返回 201 且新记录 `status` 为 `pending`

#### Scenario: 未登录发布被拒绝

- **Given** 一个未携带有效登录态的请求
- **When** 调用发布接口
- **Then** 返回 401

### Requirement: 我发布的供需信息

系统 SHALL 提供 `GET /api/v1/edu-listings/mine` 返回当前登录用户发布的全部供需信息（含 `pending`/`rejected`/`offline` 等所有状态），按创建时间倒序分页。

#### Scenario: 查看自己待审核与已驳回信息

- **Given** 一个用户发布过状态分别为 pending、rejected、approved 的三条信息
- **When** 该用户请求「我发布的」列表
- **Then** 三条信息全部返回，且各自携带真实状态与驳回理由（如有）

