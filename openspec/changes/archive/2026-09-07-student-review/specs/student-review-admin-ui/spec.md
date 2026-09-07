## Purpose

定义 br-admin 后台评价审核页面的界面行为：待审与已审评价的检索、审核（通过 / 驳回）、机构回复，以及支撑该页面可达的动态菜单与按钮级权限。

## ADDED Requirements

### Requirement: Admin review list page

后台 SHALL 在「培训管理」目录下提供「评价审核」列表页，复用仓库既有的后台列表页骨架（搜索表单 + 数据表格 + 行内操作），MUST NOT 自建一套分页或表格机制。列表 SHALL 展示：发表者昵称（含匿名标记）、星级、评价内容摘要、图片数量、所属课程、所属老师、所属订单标识、发表时间、审核状态、机构回复状态。列表 SHALL 支持按审核状态筛选、按评分档位筛选、按关键词搜索，并 SHALL 分页展示。分页请求参数 SHALL 使用后台既有的分页契约（`page` / `pageSize` 入参，返回 `{ list, itemCount, pageCount, page }` 结构），关键词与状态为空时 MUST NOT 作为空字符串发给后端。表格 MUST 有稳定的行主键，横向内容过宽时 SHALL 支持横向滚动且操作列固定在右侧。

#### Scenario: List pending reviews by default

- **GIVEN** 系统中存在多种审核状态的评价
- **WHEN** 管理员打开「评价审核」页
- **THEN** 表格展示评价数据
- **AND** 每行展示发表者、星级、内容、课程、老师、发表时间与审核状态

#### Scenario: Filter by audit status

- **WHEN** 管理员在搜索表单选择状态「待审核」并提交
- **THEN** 表格只展示待审核的评价

#### Scenario: Keyword search

- **WHEN** 管理员输入关键词并提交搜索
- **THEN** 表格只展示内容或发表者昵称匹配该关键词的评价

#### Scenario: Reset clears filters

- **GIVEN** 管理员已应用了状态与关键词筛选
- **WHEN** 管理员点击重置
- **THEN** 筛选条件被清空
- **AND** 表格恢复展示全部评价

#### Scenario: Empty filter values are not sent

- **WHEN** 管理员未填写关键词且未选择状态就提交搜索
- **THEN** 发出的请求不包含空的关键词与状态参数
- **AND** 后端不因此返回校验错误

#### Scenario: Table renders rows without silent failure

- **WHEN** 列表数据加载成功
- **THEN** 表格正常渲染数据行
- **AND** 浏览器控制台不出现未定义变量引用错误导致的渲染中断

#### Scenario: Pagination works

- **GIVEN** 评价总数超过单页容量
- **WHEN** 管理员切换到第 2 页
- **THEN** 表格展示第 2 页数据
- **AND** 分页器展示的总条数与后端返回一致

#### Scenario: Anonymous review is marked

- **GIVEN** 存在一条匿名评价
- **WHEN** 列表渲染该行
- **THEN** 展示发表者真实昵称
- **AND** 同时展示「匿名」标记

### Requirement: Admin review detail and audit modal

后台 SHALL 通过弹窗展示单条评价的完整内容并承载审核操作，弹窗 MUST 在打开时才拉取或渲染该条数据，关闭后重新打开另一条 MUST 不残留上一条的内容。弹窗 SHALL 完整展示：发表者昵称与头像、是否匿名、星级、评价全文、全部图片（可点击放大预览并在同一条评价的多张图片间前后翻阅）、全部标签、所属订单标识与课程名与老师名、发表时间、当前审核状态、既有驳回理由、既有机构回复。弹窗 SHALL 提供「通过」与「驳回」两个审核动作；选择驳回时 MUST 要求填写驳回理由，理由为空时 MUST 阻止提交并给出提示。弹窗 SHALL 提供机构回复输入区，限制 500 字。审核或回复成功后 MUST 关闭弹窗、刷新列表并给出成功提示。弹窗 MUST NOT 声明或触发注册类事件，以免产生未声明事件的框架警告。

#### Scenario: Open detail modal

- **WHEN** 管理员点击某条评价的审核操作
- **THEN** 弹窗打开并展示该条评价的完整内容与图片
- **AND** 展示当前审核状态

#### Scenario: Preview review images with group navigation

- **GIVEN** 某条评价包含 4 张图片
- **WHEN** 管理员点击其中一张图片
- **THEN** 打开图片预览
- **AND** 可在该条评价的 4 张图片间前后翻阅

#### Scenario: Approve from modal

- **GIVEN** 弹窗中展示的是一条待审核评价
- **WHEN** 管理员点击「通过」
- **THEN** 请求成功
- **AND** 弹窗关闭
- **AND** 列表刷新后该条评价状态变为已通过
- **AND** 页面给出成功提示

#### Scenario: Reject without reason is blocked

- **WHEN** 管理员选择「驳回」但未填写驳回理由就提交
- **THEN** 提交被阻止
- **AND** 弹窗提示驳回理由必填
- **AND** 不发起审核请求

#### Scenario: Reject with reason

- **GIVEN** 弹窗中展示的是一条待审核评价
- **WHEN** 管理员填写驳回理由并点击「驳回」
- **THEN** 请求成功
- **AND** 弹窗关闭
- **AND** 列表刷新后该条评价状态变为已驳回并展示驳回理由

#### Scenario: Save merchant reply

- **GIVEN** 弹窗中展示的评价尚无机构回复
- **WHEN** 管理员输入回复内容并保存
- **THEN** 请求成功
- **AND** 列表刷新后该条评价标记为已回复

#### Scenario: Reply length limit

- **WHEN** 管理员在回复输入区输入超过 500 字符
- **THEN** 输入被限制在 500 字符以内，或提交时给出长度超限提示

#### Scenario: Reopening modal shows the newly selected review

- **GIVEN** 管理员刚查看完评价 A 的弹窗并关闭
- **WHEN** 管理员打开评价 B 的弹窗
- **THEN** 弹窗展示评价 B 的内容
- **AND** 不残留评价 A 的图片、正文或审核状态

#### Scenario: Modal emits no undeclared events

- **WHEN** 弹窗组件被打开与关闭
- **THEN** 浏览器控制台不出现"组件触发了未声明事件"的框架警告

#### Scenario: Audit failure surfaces an error

- **WHEN** 审核请求被后端拒绝（如权限不足或状态非法）
- **THEN** 页面展示后端返回的错误信息
- **AND** 弹窗保持打开或列表状态不被错误地标记为已变更

### Requirement: Admin review action permissions

后台评价审核页的每个操作 MUST 受按钮级权限控制，无对应权限时该操作入口 MUST NOT 渲染，且后端 MUST 独立强制同一权限（前端隐藏不作为唯一防线）。查看列表 SHALL 要求 `training:reviews:view`，审核通过或驳回 SHALL 要求审核权限，保存机构回复 SHALL 要求回复权限。

#### Scenario: Admin with view-only permission

- **GIVEN** 某管理员仅拥有 `training:reviews:view` 权限
- **WHEN** 该管理员打开评价审核页
- **THEN** 表格数据正常展示
- **AND** 审核与回复的操作入口不渲染

#### Scenario: Admin with audit permission

- **GIVEN** 某管理员拥有审核权限
- **WHEN** 该管理员打开评价审核页
- **THEN** 审核操作入口可见且可用

#### Scenario: Backend enforces permission independently

- **GIVEN** 某管理员不具备审核权限
- **WHEN** 该管理员绕过前端直接调用审核接口
- **THEN** 后端返回 HTTP 403
- **AND** 评价状态不变

### Requirement: Admin review menu registration

后台 SHALL 通过后端动态菜单机制暴露「评价审核」入口，菜单 MUST 由种子脚本幂等写入，MUST NOT 依赖前端静态路由表。菜单项 MUST 挂在既有的「培训管理」目录下，其路径 MUST 存储为相对于父目录基路径的相对路径，避免路由生成器拼接出重复路径段。菜单 MUST 关联 `training:reviews:view` 权限码，且其图标名称 MUST 是前端图标映射表中已注册的名称，否则图标将渲染为空白。菜单对应的组件路径 MUST 存在于后端组件白名单中，以便后续在菜单管理界面编辑。写入菜单后 MUST 提示管理员重新登录以刷新权限与路由缓存。

#### Scenario: Menu appears under training directory

- **GIVEN** 已执行菜单种子脚本且管理员重新登录
- **WHEN** 管理员查看左侧菜单
- **THEN** 「培训管理」目录下出现「评价审核」菜单项

#### Scenario: Menu route resolves to the review page

- **WHEN** 管理员点击「评价审核」菜单
- **THEN** 路由解析成功并渲染评价审核列表页
- **AND** 不出现路径段重复导致的 404 或空白页

#### Scenario: Menu icon renders

- **WHEN** 「评价审核」菜单渲染
- **THEN** 菜单项左侧展示图标
- **AND** 图标位置不是空白

#### Scenario: Menu is hidden without view permission

- **GIVEN** 某管理员不具备 `training:reviews:view` 权限
- **WHEN** 该管理员登录后台
- **THEN** 左侧菜单不展示「评价审核」项

#### Scenario: Seed script is idempotent

- **GIVEN** 菜单种子脚本已执行过一次
- **WHEN** 再次执行同一脚本
- **THEN** 不产生重复的菜单记录
- **AND** 已有的菜单权限码保持不变

#### Scenario: Menu component path is editable in menu management

- **WHEN** 管理员在「系统设置 > 菜单管理」中编辑「评价审核」菜单
- **THEN** 其组件路径通过后端白名单校验
- **AND** 保存不返回"菜单组件不在白名单中"的错误

### Requirement: Admin review UI component registration

评价审核页使用的每一个 Naive UI 组件 MUST 在项目的组件按需注册插件中登记。未登记的组件在模板中使用时会静默失败（页面不报错但组件不渲染），因此新增组件时 MUST 同时在导入语句与注册列表两处补齐。评价审核页 SHALL 至少需要星级展示组件与图片预览分组组件，二者均由项目已安装的 Naive UI 版本提供，MUST NOT 为此新增第三方依赖或自行实现星级与灯箱。

#### Scenario: Star rating component renders in table and modal

- **WHEN** 评价审核页渲染星级列与弹窗中的星级
- **THEN** 星级组件正常渲染
- **AND** 浏览器控制台不出现"未解析的组件"警告

#### Scenario: Image preview group component renders

- **WHEN** 弹窗中渲染评价图片并点击图片
- **THEN** 预览正常打开且支持同组图片前后翻阅
- **AND** 不出现组件未注册导致的空白区域

#### Scenario: Build passes after registration

- **WHEN** 执行后台前端的生产构建
- **THEN** 构建成功且无错误
- **AND** 代码风格检查通过
