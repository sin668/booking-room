# student-review-api Specification

## Purpose
定义学员评价的数据契约、C 端查询与发表接口、后台审核接口，以及审核通过后课程与老师评分的聚合回写规则和评价可见性规则。
## Requirements
### Requirement: Review data model

系统 SHALL 以 `reviews` 表持久化学员评价。一条评价 MUST 关联一个预约订单，且同一订单 MUST 只能存在一条评价（由数据库唯一约束强制，而非应用层判断）。评价 SHALL 冗余记录课程与老师标识，以支持按课程、按老师两个维度的独立过滤查询；当订单不涉及课程或老师时，对应标识 SHALL 为空。评价 SHALL 包含综合星级评分（1 至 5 的整数）、文字内容、图片列表、标签列表、是否匿名，以及审核状态、驳回理由、机构回复内容与回复时间、审核人与审核时间。图片与标签 SHALL 以 JSON 数组存储，元素个数为 0 时 SHALL 序列化为空数组而非 `null`。系统 MUST NOT 存储评价的多维度子评分、追评、点赞数或举报记录。

#### Scenario: Create a review linked to a completed booking

- **GIVEN** 存在一个状态为 `completed` 的订单，归属当前登录用户
- **WHEN** 用户提交对该订单的评价
- **THEN** 系统持久化一条评价记录，其审核状态为 `pending`
- **AND** 记录同时写入该订单的课程标识与老师标识（若订单含有）

#### Scenario: Duplicate review for the same booking is rejected

- **GIVEN** 某订单已存在一条评价
- **WHEN** 用户再次对同一订单提交评价
- **THEN** 返回 HTTP 400
- **AND** 响应包含"该订单已评价"语义的错误信息
- **AND** 数据库中该订单仍只有一条评价记录

#### Scenario: Images and tags are stored as JSON arrays

- **WHEN** 用户提交包含 3 张图片和 2 个标签的评价
- **THEN** 评价记录的图片字段是长度为 3 的数组，标签字段是长度为 2 的数组
- **WHEN** 用户提交不含图片和标签的评价
- **THEN** 查询该评价时图片字段返回 `[]`，标签字段返回 `[]`，均不返回 `null`

### Requirement: Review status vocabulary

系统 SHALL 以单一事实源维护评价审核状态词表，取值为 `pending`（待审核）、`approved`（已通过）、`rejected`（已驳回）。新建评价的初始状态 MUST 为 `pending`。任何接口、服务或前端 MUST NOT 各自定义该状态的同义别名或第二套取值。审核状态变更 MUST 记录审核人标识与审核时间。

#### Scenario: New review defaults to pending

- **WHEN** 用户成功发表一条评价
- **THEN** 该评价的审核状态为 `pending`
- **AND** 审核人标识与审核时间为空

#### Scenario: Audit records the operator and timestamp

- **GIVEN** 某管理员拥有评价审核权限
- **WHEN** 该管理员将一条 `pending` 评价改为 `approved`
- **THEN** 该评价的审核人标识为当前管理员
- **AND** 审核时间被写入且为不带时区信息的业务本地时间

#### Scenario: Invalid status value is rejected

- **WHEN** 后台审核请求提交了一个不在状态词表内的状态值
- **THEN** 返回 HTTP 422
- **AND** 该评价的状态保持不变

### Requirement: Review visibility rules

系统 SHALL 按调用方与过滤维度控制评价可见性。面向课程维度或老师维度的公开查询 MUST 只返回 `approved` 状态的评价。"我的评价"查询 MUST 返回当前登录用户本人发表的全部状态的评价，包括 `pending` 与 `rejected`，并 SHALL 携带审核状态与驳回理由，以便用户了解审核进展。后台查询 MUST 返回全部状态的评价并支持按状态筛选。匿名评价在公开查询中 MUST NOT 暴露发表者的真实昵称与头像。

#### Scenario: Public course review list hides unaudited reviews

- **GIVEN** 某课程存在 3 条评价，状态分别为 `approved`、`pending`、`rejected`
- **WHEN** 任意用户按该课程标识查询评价列表
- **THEN** 只返回 1 条 `approved` 评价
- **AND** 分页总数为 1

#### Scenario: My reviews include all own statuses

- **GIVEN** 当前登录用户发表过 3 条评价，状态分别为 `approved`、`pending`、`rejected`
- **WHEN** 该用户查询"我的评价"
- **THEN** 返回全部 3 条
- **AND** 每条均携带审核状态字段
- **AND** `rejected` 的那条携带驳回理由

#### Scenario: My reviews never expose other users' reviews

- **GIVEN** 系统中存在其他用户发表的评价
- **WHEN** 当前登录用户查询"我的评价"
- **THEN** 返回结果不包含任何其他用户的评价

#### Scenario: Anonymous review masks the author

- **GIVEN** 存在一条匿名且已通过审核的评价
- **WHEN** 任意用户按课程或老师维度查询评价列表
- **THEN** 该条评价返回的昵称是脱敏形式（如"匿名用户"）
- **AND** 该条评价返回的头像为空
- **AND** 后台审核查询返回该条评价的真实昵称与头像

#### Scenario: Unauthenticated user can read public reviews

- **WHEN** 未登录用户按课程标识查询评价列表
- **THEN** 返回 HTTP 200 与已通过审核的评价
- **WHEN** 未登录用户查询"我的评价"
- **THEN** 返回 HTTP 401

### Requirement: Review list query API

系统 SHALL 提供 C 端评价列表查询接口，通过查询参数同时支撑三个入口：按课程过滤、按老师过滤、查询本人评价。课程标识与老师标识 MAY 同时传入，此时 SHALL 取交集。列表 SHALL 支持按评分档位筛选（全部 / 好评 4-5 星 / 中评 3 星 / 差评 1-2 星）与"仅看有图"筛选，并 SHALL 支持按最新发表与评分最高两种方式排序。分页参数 SHALL 为 `page` 与 `page_size`，`page_size` MUST 有不超过 50 的上限，超出时返回 HTTP 422。响应结构 SHALL 与仓库既有 C 端分页接口一致，包含条目数组与总条数。每条评价 SHALL 返回发表者昵称与头像、星级、文字内容、图片列表、标签列表、发表时间、所属课程名与老师名，以及机构回复内容与回复时间；查询本人评价时还 SHALL 返回审核状态与驳回理由。

#### Scenario: Filter reviews by course

- **GIVEN** 系统中存在分属两个课程的已通过评价
- **WHEN** 用户传入课程 A 的标识查询评价列表
- **THEN** 只返回课程 A 的评价

#### Scenario: Filter reviews by teacher

- **GIVEN** 系统中存在分属两位老师的已通过评价
- **WHEN** 用户传入老师 B 的标识查询评价列表
- **THEN** 只返回老师 B 的评价

#### Scenario: Filter by rating band

- **GIVEN** 某课程存在 5 星、4 星、3 星、1 星各一条已通过评价
- **WHEN** 用户按"好评"档位查询该课程评价
- **THEN** 返回 5 星与 4 星共 2 条
- **WHEN** 用户按"差评"档位查询该课程评价
- **THEN** 返回 1 星共 1 条

#### Scenario: Filter reviews with images

- **GIVEN** 某课程存在带图与不带图的已通过评价各若干
- **WHEN** 用户开启"仅看有图"筛选
- **THEN** 返回结果中每条评价的图片列表均非空

#### Scenario: Sort by highest rating

- **GIVEN** 某课程存在评分不同的多条已通过评价
- **WHEN** 用户选择按评分最高排序
- **THEN** 返回列表按星级降序排列

#### Scenario: Page size exceeding limit is rejected

- **WHEN** 用户以 `page_size=100` 查询评价列表
- **THEN** 返回 HTTP 422
- **AND** 不返回任何评价数据

#### Scenario: Pagination returns consistent total

- **GIVEN** 某课程存在 25 条已通过评价
- **WHEN** 用户以 `page=2`、`page_size=10` 查询
- **THEN** 返回 10 条记录
- **AND** 总条数字段为 25

### Requirement: Review summary API

系统 SHALL 提供评价概览接口，按课程或老师维度返回综合平均分、参与统计的评价总数、好评率，以及 1 至 5 星各自的数量分布。概览统计 MUST 只计入 `approved` 状态的评价。平均分 SHALL 保留一位小数。当某维度下没有任何已通过评价时，接口 MUST 返回 HTTP 200 且平均分与好评率为 0、各星级数量为 0、总数为 0，MUST NOT 返回 404 或除零错误。

#### Scenario: Summary of a course with approved reviews

- **GIVEN** 某课程存在 4 条已通过评价，星级分别为 5、5、4、3
- **WHEN** 用户查询该课程的评价概览
- **THEN** 返回平均分为 4.3
- **AND** 返回评价总数为 4
- **AND** 返回好评率为 75（4 星及以上占比）
- **AND** 星级分布中 5 星为 2、4 星为 1、3 星为 1、2 星与 1 星为 0

#### Scenario: Summary excludes unaudited reviews

- **GIVEN** 某课程存在 1 条已通过评价与 2 条待审核评价
- **WHEN** 用户查询该课程的评价概览
- **THEN** 返回评价总数为 1

#### Scenario: Summary of a target without reviews

- **WHEN** 用户查询一个尚无任何已通过评价的课程或老师的评价概览
- **THEN** 返回 HTTP 200
- **AND** 平均分为 0，评价总数为 0，好评率为 0，各星级数量为 0

#### Scenario: Summary requires a filter dimension

- **WHEN** 用户查询概览但既未传课程标识也未传老师标识
- **THEN** 返回 HTTP 422

### Requirement: Review submission API

系统 SHALL 提供 C 端评价发表接口，仅接受已登录用户调用。发表时系统 MUST 校验：目标订单存在、订单归属当前用户、订单状态为已完成、该订单尚未被评价。评分 MUST 为 1 至 5 的整数，文字内容 MUST 非空且长度不超过 500 字符，图片数量 MUST 不超过 9 张，标签数量 MUST 不超过 5 个。校验失败时 MUST 返回 4xx 且不写入任何数据。发表成功后 MUST 返回新建评价的完整信息，其审核状态为 `pending`。系统 MUST NOT 在发表时授予任何积分或奖励。

#### Scenario: Successful submission

- **GIVEN** 当前登录用户拥有一个状态为 `completed` 且未评价过的订单
- **WHEN** 用户提交评分为 5、内容为"老师讲得很清楚"的评价
- **THEN** 返回 HTTP 200 或 201
- **AND** 响应包含新建评价的标识与审核状态 `pending`

#### Scenario: Booking not completed cannot be reviewed

- **GIVEN** 当前登录用户拥有一个状态为 `pending_start` 的订单
- **WHEN** 用户尝试对该订单发表评价
- **THEN** 返回 HTTP 400
- **AND** 响应说明只有已完成的订单才能评价
- **AND** 数据库不新增评价记录

#### Scenario: Reviewing another user's booking is forbidden

- **GIVEN** 某订单归属其他用户且状态为 `completed`
- **WHEN** 当前登录用户尝试对该订单发表评价
- **THEN** 返回 HTTP 403 或 HTTP 404
- **AND** 数据库不新增评价记录

#### Scenario: Rating out of range is rejected

- **WHEN** 用户提交评分为 0 或 6 的评价
- **THEN** 返回 HTTP 422

#### Scenario: Content too long is rejected

- **WHEN** 用户提交内容长度超过 500 字符的评价
- **THEN** 返回 HTTP 422

#### Scenario: Empty content is rejected

- **WHEN** 用户提交内容为空白字符串的评价
- **THEN** 返回 HTTP 422

#### Scenario: Too many images is rejected

- **WHEN** 用户提交包含 10 张图片的评价
- **THEN** 返回 HTTP 422

#### Scenario: Unauthenticated submission is rejected

- **WHEN** 未携带有效登录凭证的请求尝试发表评价
- **THEN** 返回 HTTP 401

### Requirement: Query own review for a booking

系统 SHALL 支持按订单标识查询当前登录用户对该订单发表的评价，供发表页在进入时判断是否已评价并展示已提交内容。当该订单不存在本人评价时，接口 MUST 返回 HTTP 200 与空结果，MUST NOT 返回 404。查询他人订单 MUST 不返回该订单的评价。

#### Scenario: Booking already reviewed by current user

- **GIVEN** 当前登录用户已对某订单发表过评价
- **WHEN** 用户按该订单标识查询自己的评价
- **THEN** 返回 HTTP 200 与该条评价的完整信息

#### Scenario: Booking not reviewed yet

- **GIVEN** 当前登录用户尚未对某订单发表评价
- **WHEN** 用户按该订单标识查询自己的评价
- **THEN** 返回 HTTP 200
- **AND** 结果为空

#### Scenario: Cannot read another user's review by booking

- **GIVEN** 某订单归属其他用户且已被其评价
- **WHEN** 当前登录用户按该订单标识查询自己的评价
- **THEN** 返回 HTTP 200 且结果为空，或返回 HTTP 403
- **AND** 不泄露该评价的内容

### Requirement: Admin review list API

系统 SHALL 提供后台评价列表接口，MUST 由后端强制执行 `training:reviews:view` 权限，无权限时返回 HTTP 403。接口 SHALL 支持按审核状态筛选、按评分档位筛选、按关键词（评价内容或发表者昵称）模糊搜索，并 SHALL 返回全部状态的评价。每条记录 SHALL 携带后台审核所需的完整信息：发表者真实昵称与头像（含匿名评价）、星级、文字内容、图片列表、标签列表、是否匿名、所属订单标识、课程名、老师名、发表时间、审核状态、驳回理由、机构回复内容与回复时间、审核人与审核时间。分页契约 SHALL 与仓库既有后台分页接口一致。

#### Scenario: Admin lists pending reviews

- **GIVEN** 系统中存在 `pending`、`approved`、`rejected` 三种状态的评价
- **WHEN** 拥有查看权限的管理员按状态 `pending` 筛选
- **THEN** 只返回 `pending` 状态的评价

#### Scenario: Admin sees real identity of anonymous reviews

- **GIVEN** 存在一条匿名评价
- **WHEN** 管理员查询评价列表
- **THEN** 该记录返回发表者的真实昵称与头像
- **AND** 同时返回"匿名"标记为真

#### Scenario: Admin keyword search

- **GIVEN** 存在内容包含"讲解清晰"的评价
- **WHEN** 管理员以关键词"讲解"搜索
- **THEN** 返回内容匹配的评价

#### Scenario: Admin without permission is rejected

- **GIVEN** 某管理员不具备 `training:reviews:view` 权限且不是超级管理员
- **WHEN** 该管理员请求后台评价列表
- **THEN** 返回 HTTP 403

### Requirement: Admin review audit API

系统 SHALL 提供后台审核接口，将一条评价的状态改为 `approved` 或 `rejected`，MUST 由后端强制执行审核权限。改为 `rejected` 时 MUST 要求提供驳回理由且理由非空；改为 `approved` 时 SHALL 清空既有驳回理由。重复审核同一条已通过或已驳回的评价 SHALL 是幂等的，MUST NOT 报错。审核完成后系统 MUST 触发相关课程与老师的评分聚合重算。

#### Scenario: Approve a pending review

- **GIVEN** 存在一条 `pending` 评价，归属某课程与某老师
- **WHEN** 拥有审核权限的管理员将其改为 `approved`
- **THEN** 返回 HTTP 200
- **AND** 该评价状态为 `approved`，审核人与审核时间被写入
- **AND** 该课程与该老师的评分聚合被重算

#### Scenario: Reject requires a reason

- **WHEN** 管理员将一条评价改为 `rejected` 但未提供驳回理由
- **THEN** 返回 HTTP 422
- **AND** 该评价状态保持 `pending`

#### Scenario: Reject with reason

- **GIVEN** 存在一条 `pending` 评价
- **WHEN** 管理员将其改为 `rejected` 并提供理由"包含广告信息"
- **THEN** 返回 HTTP 200
- **AND** 该评价状态为 `rejected`，驳回理由被保存
- **AND** 该评价不再出现在 C 端公开列表中
- **AND** 该评价仍出现在发表者的"我的评价"中并携带该驳回理由

#### Scenario: Approving an already approved review is idempotent

- **GIVEN** 存在一条已为 `approved` 的评价
- **WHEN** 管理员再次将其改为 `approved`
- **THEN** 返回 HTTP 200
- **AND** 不产生错误，评分聚合结果保持不变

#### Scenario: Audit of a missing review

- **WHEN** 管理员对一个不存在的评价标识发起审核
- **THEN** 返回 HTTP 404

#### Scenario: Audit without permission is rejected

- **GIVEN** 某管理员不具备评价审核权限且不是超级管理员
- **WHEN** 该管理员尝试审核一条评价
- **THEN** 返回 HTTP 403
- **AND** 该评价状态不变

### Requirement: Admin review reply API

系统 SHALL 提供后台机构回复接口，为一条评价写入或更新回复内容，MUST 由后端强制执行回复权限。回复内容 MUST 非空且长度不超过 500 字符；提交空白内容 SHALL 视为清空回复并同步清空回复时间。回复成功后 MUST 在 C 端评价列表中随该条评价返回，且对已通过、待审核、已驳回的评价均允许回复。

#### Scenario: Reply to an approved review

- **GIVEN** 存在一条 `approved` 评价
- **WHEN** 拥有回复权限的管理员提交回复"感谢您的反馈"
- **THEN** 返回 HTTP 200
- **AND** 该评价的回复内容与回复时间被保存
- **AND** C 端公开列表查询该评价时返回此回复内容

#### Scenario: Update an existing reply

- **GIVEN** 某评价已有机构回复
- **WHEN** 管理员提交新的回复内容
- **THEN** 回复内容被覆盖为新值
- **AND** 回复时间更新为最新时间

#### Scenario: Clear a reply with blank content

- **GIVEN** 某评价已有机构回复
- **WHEN** 管理员提交仅含空白字符的回复内容
- **THEN** 该评价的回复内容被清空
- **AND** 回复时间被清空

#### Scenario: Overlong reply is rejected

- **WHEN** 管理员提交长度超过 500 字符的回复
- **THEN** 返回 HTTP 422

### Requirement: Rating aggregation write-back

系统 SHALL 在评价审核状态发生变化后，重新计算并回写受影响课程与老师的评分。计算 MUST 只统计 `approved` 状态的评价：平均分 SHALL 保留一位小数写入既有的评分字段，已通过评价条数 SHALL 写入新增的评价条数字段。当某课程或老师没有任何已通过评价时，其平均分与评价条数 MUST 被重置为 0，MUST NOT 保留历史残留值。聚合回写 MUST NOT 因单个目标无评价而中断其余目标的处理。评价为待审核或已驳回状态时 MUST NOT 参与聚合。

#### Scenario: Approving the first review overwrites the seeded rating

- **GIVEN** 某课程的评分字段原为种子数据写入的 4.8，且尚无已通过评价
- **WHEN** 管理员通过该课程下第一条评分为 5 的评价
- **THEN** 该课程的评分被回写为 5.0
- **AND** 该课程的评价条数被回写为 1

#### Scenario: Aggregate only counts approved reviews

- **GIVEN** 某课程存在评分 5 的已通过评价与评分 1 的待审核评价
- **WHEN** 聚合被触发
- **THEN** 该课程的平均分为 5.0，评价条数为 1

#### Scenario: Rejecting the only approved review resets the aggregate

- **GIVEN** 某课程仅有 1 条已通过评价，评分为 5.0，评价条数为 1
- **WHEN** 管理员将该评价改为 `rejected`
- **THEN** 该课程的评分被回写为 0
- **AND** 该课程的评价条数被回写为 0

#### Scenario: Teacher aggregate is updated independently

- **GIVEN** 某老师下存在两条分属不同课程的已通过评价，评分为 5 与 4
- **WHEN** 聚合被触发
- **THEN** 该老师的平均分为 4.5，评价条数为 2
- **AND** 两条评价各自所属课程的聚合互不干扰

#### Scenario: Review without a teacher does not break aggregation

- **GIVEN** 某评价所属订单不含老师标识
- **WHEN** 管理员通过该评价
- **THEN** 其所属课程的聚合被正常回写
- **AND** 系统不因老师标识为空而报错

