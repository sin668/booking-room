## Purpose

定义 br-app 小程序端学员评价的界面行为：评价列表页在课程、老师、我的评价三种入口下的过滤与展示，发表评价页的打分与提交交互，以及四个既有页面上的评价入口。

## ADDED Requirements

### Requirement: Review list page entry modes

评价列表页 SHALL 依据进入时携带的参数决定展示哪一批评价，并 SHALL 相应调整标题与概览区：携带课程标识时展示该课程的评价且标题体现课程名；携带老师标识时展示该老师的评价且标题体现老师名；携带"我的评价"标记时展示当前登录用户本人发表的全部评价。三个入口 MUST 复用同一个页面与同一个列表接口，MUST NOT 为每个入口新建独立页面。参数缺失时页面 SHALL 展示空状态而非崩溃。

#### Scenario: Enter from course detail

- **GIVEN** 用户在课程详情页点击「查看全部评价」
- **WHEN** 评价列表页打开
- **THEN** 页面只展示该课程的评价
- **AND** 页面标题或概览区体现该课程名称

#### Scenario: Enter from teacher profile

- **GIVEN** 用户在老师简介页点击「查看全部评价」
- **WHEN** 评价列表页打开
- **THEN** 页面只展示对该老师的评价
- **AND** 页面标题或概览区体现该老师名称

#### Scenario: Enter from my reviews

- **GIVEN** 用户在「我的」页点击「我的评价」
- **WHEN** 评价列表页打开
- **THEN** 页面只展示当前用户本人发表的评价
- **AND** 展示范围包含待审核与已驳回的评价

#### Scenario: Missing filter parameter

- **WHEN** 评价列表页在既无课程标识、也无老师标识、也无"我的评价"标记的情况下打开
- **THEN** 页面展示空状态提示
- **AND** 不发起无过滤条件的全量查询

### Requirement: Review summary display

在课程维度与老师维度下，评价列表页 SHALL 在列表上方展示概览区，包含综合平均分、参与统计的评价总数与好评率，并 SHALL 以进度条形式展示 1 至 5 星各自的数量分布。概览数据 MUST 来自后端概览接口，MUST NOT 在前端由当前页数据推算。当尚无任何已通过评价时，概览区 SHALL 展示 0 分与全 0 分布，MUST NOT 出现 `NaN`、`undefined` 或空白。"我的评价"入口 MAY 不展示概览区。

#### Scenario: Summary rendered for a reviewed course

- **GIVEN** 某课程已有若干条已通过评价
- **WHEN** 用户从课程详情进入评价列表
- **THEN** 概览区展示后端返回的平均分、总数与好评率
- **AND** 星级分布条按后端返回的各星级数量渲染

#### Scenario: Summary of a course without approved reviews

- **GIVEN** 某课程尚无任何已通过评价
- **WHEN** 用户进入该课程的评价列表
- **THEN** 概览区展示平均分 0、总数 0、好评率 0
- **AND** 各星级分布条宽度为 0
- **AND** 页面不出现 `NaN` 或 `undefined` 文本

### Requirement: Review filtering and sorting controls

在课程维度与老师维度下，评价列表页 SHALL 提供评分档位筛选（全部 / 好评 / 中评 / 差评）与"仅看有图"筛选，并 SHALL 提供排序切换（最新发表 / 评分最高）。筛选与排序条件变更时 MUST 重置到第一页并重新请求，MUST NOT 沿用上一页的分页游标。当前生效的筛选项 SHALL 有明确的选中态视觉区分。"我的评价"入口 MAY 不提供上述筛选控件。

#### Scenario: Switch rating band resets pagination

- **GIVEN** 用户已上拉加载到评价列表第 3 页
- **WHEN** 用户切换到「好评」档位
- **THEN** 列表内容被替换为好评结果
- **AND** 分页从第 1 页重新开始

#### Scenario: Enable image-only filter

- **WHEN** 用户开启「仅看有图」筛选
- **THEN** 列表只展示带图片的评价
- **AND** 该筛选项呈现选中态

#### Scenario: Change sort order

- **GIVEN** 列表当前按最新发表排序
- **WHEN** 用户切换到「评分最高」
- **THEN** 列表按星级从高到低重新排列

#### Scenario: No result after filtering

- **WHEN** 用户选择的筛选条件下没有任何评价
- **THEN** 列表区展示空状态提示
- **AND** 概览区仍正常展示未过滤的总分数据

### Requirement: Review card display

评价列表中的每条评价 SHALL 以卡片形式展示发表者头像与昵称、星级、发表时间、文字内容、图片与标签，若存在机构回复则 SHALL 在卡片内以区别于正文的样式展示回复内容。星级 MUST 按实际评分渲染实心与空心数量，MUST NOT 固定渲染 5 颗实心星。图片 SHALL 以网格排列，点击任意一张 MUST 调用系统原生图片预览能力浏览该条评价的全部图片。匿名评价在公开列表中 SHALL 展示脱敏昵称与默认头像。发表时间 SHALL 以可读的短格式展示（如相对时间或年月日），MUST NOT 直接展示含 `T` 分隔符与时区后缀的原始 ISO 字符串。

#### Scenario: Render star rating faithfully

- **GIVEN** 某条评价评分为 3 星
- **WHEN** 卡片渲染
- **THEN** 展示 3 颗实心星与 2 颗空心星

#### Scenario: Preview review images

- **GIVEN** 某条评价包含 4 张图片
- **WHEN** 用户点击其中第 2 张
- **THEN** 打开系统原生图片预览
- **AND** 预览定位到第 2 张
- **AND** 可左右浏览该条评价的其余 3 张

#### Scenario: Show merchant reply

- **GIVEN** 某条评价已有机构回复
- **WHEN** 卡片渲染
- **THEN** 卡片内展示回复内容
- **AND** 回复区块的视觉样式与评价正文明显区分

#### Scenario: Render anonymous review in public list

- **GIVEN** 某条已通过评价标记为匿名
- **WHEN** 其他用户浏览该课程或老师的评价列表
- **THEN** 该卡片展示脱敏昵称与默认头像
- **AND** 不展示发表者真实身份

#### Scenario: Review without images or tags

- **GIVEN** 某条评价不含图片与标签
- **WHEN** 卡片渲染
- **THEN** 不展示图片网格区与标签区
- **AND** 卡片布局不出现空白占位或错位

#### Scenario: Display readable timestamp

- **WHEN** 卡片渲染发表时间
- **THEN** 展示的是可读的短格式时间
- **AND** 不出现形如 `2026-09-07T10:00:00` 的原始字符串

### Requirement: My review audit status display

在"我的评价"入口下，每条评价卡片 SHALL 额外展示其审核状态标识（待审核 / 已通过 / 已驳回），且三种状态 MUST 有可区分的视觉样式。状态为已驳回时 MUST 展示后端返回的驳回理由。待审核与已驳回的评价在"我的评价"中 MUST 可见，MUST NOT 因未通过审核而被前端过滤掉。

#### Scenario: Pending review badge

- **GIVEN** 用户发表的评价处于待审核状态
- **WHEN** 用户查看「我的评价」
- **THEN** 该卡片展示「待审核」标识

#### Scenario: Rejected review shows the reason

- **GIVEN** 用户发表的评价被驳回，驳回理由为"包含广告信息"
- **WHEN** 用户查看「我的评价」
- **THEN** 该卡片展示「已驳回」标识
- **AND** 卡片展示驳回理由"包含广告信息"

#### Scenario: Approved review badge

- **GIVEN** 用户发表的评价已通过审核
- **WHEN** 用户查看「我的评价」
- **THEN** 该卡片展示「已通过」标识
- **AND** 不展示驳回理由区块

### Requirement: Review list pagination and states

评价列表页 SHALL 支持下拉刷新与上拉加载更多，分页参数 MUST 使用 `page` 与 `page_size` 且 `page_size` MUST NOT 超过 50。首次加载时 SHALL 展示加载态，加载失败时 SHALL 给出错误提示且 MUST NOT 让页面停留在无限加载状态。列表为空时 SHALL 展示空状态文案。已加载全部数据后继续上拉 SHALL 展示"没有更多了"且 MUST NOT 重复请求同一页。接口返回错误时 MUST 由页面自行提示，因为全局请求封装不做统一 toast。

#### Scenario: Load more on reaching bottom

- **GIVEN** 评价总数大于单页容量
- **WHEN** 用户滚动到列表底部
- **THEN** 追加请求下一页并将结果拼接到列表末尾

#### Scenario: Pull to refresh resets to first page

- **GIVEN** 用户已加载多页评价
- **WHEN** 用户下拉刷新
- **THEN** 列表重置为第 1 页数据

#### Scenario: No more data

- **GIVEN** 已加载的评价条数等于后端返回的总数
- **WHEN** 用户继续上拉
- **THEN** 展示"没有更多了"提示
- **AND** 不再发起新的分页请求

#### Scenario: Request failure is surfaced

- **WHEN** 评价列表接口请求失败
- **THEN** 页面展示错误提示
- **AND** 加载态被结束，页面可再次触发刷新

#### Scenario: Page size stays within backend limit

- **WHEN** 页面发起任意评价列表请求
- **THEN** 传入的 `page_size` 不超过 50
- **AND** 不出现 HTTP 422 分页参数校验错误

### Requirement: Review submission page

发表评价页 SHALL 展示被评价订单的课程或房间名称、老师名称与完成时间等上下文信息，并提供：1 至 5 星的综合评分选择（未选时 MUST 有引导文案，选中后 SHALL 展示对应星级文案）、可多选的评价标签、限制 500 字并实时显示已输入字数的文字输入框、最多 9 张的图片上传区、以及匿名开关。页面 MUST NOT 展示任何积分、奖励或"预计可得积分"相关文案与数值。图片上传 SHALL 复用既有的用户端图片上传能力并使用评价专用的上传场景标识，上传中 SHALL 有明确的进行中反馈，上传失败的图片 MUST NOT 混入待提交列表。已上传的图片 SHALL 可单独删除。

#### Scenario: Select overall rating

- **GIVEN** 用户进入发表评价页且尚未打分
- **WHEN** 用户点击第 4 颗星
- **THEN** 前 4 颗星呈现选中态
- **AND** 展示与 4 星对应的评分文案

#### Scenario: Character counter for content

- **WHEN** 用户在文字输入框中输入 30 个字符
- **THEN** 字数计数展示为 30 / 500
- **WHEN** 用户输入达到 500 字符
- **THEN** 无法继续输入更多字符

#### Scenario: Upload review images

- **GIVEN** 用户已选择 3 张图片上传成功
- **WHEN** 用户再次选择 2 张图片
- **THEN** 图片区展示 5 张已上传图片
- **AND** 上传过程中展示进行中反馈

#### Scenario: Image upload limit

- **GIVEN** 用户已上传 9 张图片
- **WHEN** 用户尝试继续添加图片
- **THEN** 系统阻止继续添加并提示已达上限

#### Scenario: Failed image upload is excluded

- **WHEN** 某张图片上传失败
- **THEN** 该图片不出现在待提交列表中
- **AND** 页面提示上传失败
- **AND** 其余已上传成功的图片保持可用

#### Scenario: Delete an uploaded image

- **GIVEN** 用户已上传 3 张图片
- **WHEN** 用户删除第 2 张
- **THEN** 图片区剩余 2 张，且不含被删除的那张

#### Scenario: Toggle anonymous

- **WHEN** 用户开启匿名开关
- **THEN** 开关呈现开启态
- **AND** 提交后该评价在公开列表中展示脱敏身份

#### Scenario: No points or reward copy

- **WHEN** 发表评价页渲染完成
- **THEN** 页面任何位置都不出现积分、奖励数值或"预计可得积分"文案

### Requirement: Review submission validation and result

发表评价页在提交前 MUST 校验已选择星级且文字内容非空；校验不通过时 MUST 阻止提交并给出明确的缺失项提示，MUST NOT 发起请求。提交按钮在请求进行中 MUST 处于不可重复点击状态，避免重复提交产生多条评价。提交成功后 SHALL 给出成功反馈并告知评价需经审核后展示，随后 MUST 返回来源页面。若后端返回"该订单已评价"，页面 MUST 展示该提示且 MUST NOT 让用户误以为提交成功。

#### Scenario: Submit without rating

- **GIVEN** 用户已填写文字但未选择星级
- **WHEN** 用户点击提交
- **THEN** 页面提示需要先选择评分
- **AND** 不发起提交请求

#### Scenario: Submit without content

- **GIVEN** 用户已选择星级但文字内容为空或仅含空白字符
- **WHEN** 用户点击提交
- **THEN** 页面提示需要填写评价内容
- **AND** 不发起提交请求

#### Scenario: Successful submission

- **GIVEN** 用户已选择星级并填写了有效内容
- **WHEN** 用户点击提交且后端返回成功
- **THEN** 页面展示提交成功反馈
- **AND** 反馈中包含"审核通过后展示"语义的说明
- **AND** 随后返回来源页面

#### Scenario: Prevent duplicate tap during submission

- **WHEN** 用户连续快速点击提交按钮两次
- **THEN** 只发起一次提交请求
- **AND** 请求进行中提交按钮不可点击

#### Scenario: Backend reports already reviewed

- **GIVEN** 该订单已被评价过
- **WHEN** 用户提交评价
- **THEN** 页面展示"该订单已评价"语义的错误提示
- **AND** 不展示成功反馈

### Requirement: Review entry on teacher profile page

老师简介页的既有「学员评价」区块 SHALL 由硬编码假数据改为真实接口数据，展示该老师最新若干条已通过评价，并在区块头部展示评价条数。区块 MUST 保留既有的视觉结构与样式类名，MUST NOT 因接入真实数据而重做整块 UI。当该老师尚无任何已通过评价时，区块 SHALL 展示空状态文案，MUST NOT 展示假数据或空白错位。「查看全部评价」入口 MUST 可点击并跳转到按该老师过滤的评价列表页。

#### Scenario: Real reviews replace hardcoded data

- **GIVEN** 某老师已有若干条已通过评价
- **WHEN** 用户打开该老师简介页
- **THEN** 评价区块展示来自接口的真实评价
- **AND** 不出现原硬编码的假昵称与假头像

#### Scenario: Teacher without approved reviews

- **GIVEN** 某老师尚无任何已通过评价
- **WHEN** 用户打开该老师简介页
- **THEN** 评价区块展示空状态文案
- **AND** 区块头部的评价条数为 0

#### Scenario: Navigate to filtered review list

- **WHEN** 用户点击老师简介页的「查看全部评价」
- **THEN** 跳转到评价列表页
- **AND** 列表页按该老师标识过滤

#### Scenario: Review block does not break the page on API failure

- **WHEN** 评价接口请求失败
- **THEN** 老师简介页其余信息仍正常展示
- **AND** 评价区块降级为空状态而非白屏

### Requirement: Review entry on course detail page

课程详情页的既有「学员评价」区块 SHALL 由硬编码假数据改为真实接口数据，展示该课程最新若干条已通过评价。区块既有的评分汇总头部 SHALL 展示来自后端的真实平均分与评价条数，MUST NOT 展示后端未返回字段导致的空白或 `undefined`。区块 MUST 提供可点击的「查看全部」入口，跳转到按该课程过滤的评价列表页。

#### Scenario: Real rating summary

- **GIVEN** 某课程已有已通过评价
- **WHEN** 用户打开该课程详情页
- **THEN** 评分汇总展示后端返回的真实平均分与评价条数
- **AND** 页面不出现 `undefined` 或空白数值

#### Scenario: Course without approved reviews

- **GIVEN** 某课程尚无任何已通过评价
- **WHEN** 用户打开该课程详情页
- **THEN** 评分汇总展示 0 分与 0 条
- **AND** 评价区块展示空状态文案

#### Scenario: Navigate to filtered review list

- **WHEN** 用户点击课程详情页的「查看全部」评价入口
- **THEN** 跳转到评价列表页
- **AND** 列表页按该课程标识过滤

### Requirement: My reviews entry on profile page

「我的」页 SHALL 在既有菜单列表中新增「我的评价」入口，其结构与样式 MUST 与相邻菜单项保持一致（图标色块 + 文案 + 右侧箭头）。点击后 MUST 跳转到评价列表页并过滤为当前用户本人发表的评价。未登录用户点击时 SHALL 先提示登录再引导至登录页，MUST NOT 直接进入空白列表。

#### Scenario: Menu item rendered consistently

- **WHEN** 用户打开「我的」页
- **THEN** 菜单列表中出现「我的评价」项
- **AND** 其布局与相邻菜单项一致，含图标色块、文案与右侧箭头

#### Scenario: Navigate to my reviews

- **GIVEN** 用户已登录
- **WHEN** 用户点击「我的评价」
- **THEN** 跳转到评价列表页
- **AND** 列表页展示当前用户本人发表的全部状态评价

#### Scenario: Unauthenticated tap prompts login

- **GIVEN** 用户未登录
- **WHEN** 用户点击「我的评价」
- **THEN** 页面提示需要登录
- **AND** 引导用户前往登录页

### Requirement: Review entry on completed orders

订单列表中状态为已完成的订单 SHALL 在既有操作按钮区新增「去评价」按钮，点击后跳转到发表评价页并携带该订单标识。该按钮 MUST 只对已完成订单出现，MUST NOT 出现在待确认、待开始、进行中或已取消的订单上。若该订单已被当前用户评价过，页面 SHALL 不再引导重复评价（隐藏按钮或改为不可提交的已评价态）。新增按钮 MUST NOT 破坏既有按钮（如「再来一单」）的布局与功能。

#### Scenario: Completed order shows review button

- **GIVEN** 某订单状态为已完成且尚未评价
- **WHEN** 用户查看订单列表
- **THEN** 该订单卡片展示「去评价」按钮

#### Scenario: Non-completed order hides review button

- **GIVEN** 某订单状态为待开始、进行中或已取消
- **WHEN** 用户查看订单列表
- **THEN** 该订单卡片不展示「去评价」按钮

#### Scenario: Navigate to submission page with booking context

- **WHEN** 用户点击某已完成订单的「去评价」
- **THEN** 跳转到发表评价页
- **AND** 发表评价页展示该订单的课程或房间与老师信息

#### Scenario: Already reviewed order does not invite another review

- **GIVEN** 某已完成订单已被当前用户评价过
- **WHEN** 用户查看订单列表
- **THEN** 不再展示可提交新评价的「去评价」入口，或该入口进入后展示已评价状态并禁止再次提交

#### Scenario: Existing order actions remain intact

- **GIVEN** 某已完成订单同时具备「再来一单」与「去评价」入口
- **WHEN** 用户分别点击两个按钮
- **THEN** 两者均按各自预期跳转
- **AND** 按钮区布局不错位、不溢出

### Requirement: App review pages platform compatibility

新增与改造的评价页面 MUST 兼容微信小程序编译：页面模板 MUST NOT 使用 HTML 实体转义字符（如小于号、大于号的实体写法），需要此类符号时 SHALL 使用等价的 Unicode 字符；Vue 标准生命周期钩子 MUST 从 `vue` 导入，页面级生命周期钩子 MUST 从 uni-app 运行时导入，两者 MUST NOT 混用；用户交互事件 SHALL 使用小程序兼容的点击事件绑定方式。图片元素 MUST 显式指定填充模式以避免小程序端默认拉伸变形。使用自定义导航栏的页面 MUST 处理状态栏高度，避免内容顶入刘海区域；使用底部固定操作栏的页面 MUST 预留安全区内边距并为滚动内容留出底部占位，避免内容被遮挡。

#### Scenario: Pages compile for WeChat mini program

- **WHEN** 执行小程序端构建
- **THEN** 全部评价相关页面编译通过
- **AND** 不出现模板非法字符导致的编译错误

#### Scenario: Lifecycle hooks imported from correct modules

- **WHEN** 检查评价页面的脚本导入
- **THEN** 标准 Vue 钩子来自 `vue`
- **AND** 页面级钩子来自 uni-app 运行时
- **AND** 运行时不出现"模块未导出某钩子"的错误

#### Scenario: Custom navigation bar clears the status bar

- **GIVEN** 某评价页面使用自定义导航栏
- **WHEN** 页面在真机或模拟器渲染
- **THEN** 导航栏顶部留出状态栏高度
- **AND** 页面内容不被刘海或状态栏遮挡

#### Scenario: Bottom action bar does not cover content

- **GIVEN** 发表评价页存在底部固定提交栏
- **WHEN** 用户滚动到内容底部
- **THEN** 最后一项内容完整可见
- **AND** 提交栏预留了安全区内边距
