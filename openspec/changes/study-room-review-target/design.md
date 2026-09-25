# 设计：我的评价页自习室评价对象行

## 实现说明

- `br-app/src/pages/review/list.vue` 的 `targetText(item)`（约 335 行）增加分支：`booking_type === 'seat'` 时返回 `[room_name, seat_number ? seat_number + '号座位' : ''].filter(Boolean).join(' · ')`；其余分支保持课程原逻辑。
- 模板评价对象行（约 159-162 行）图标改为 `targetIcon(item)` 方法驱动：seat 用 `icon-location`，其余保持 `icon-book`。
- 拼接逻辑全部放在 method 内，模板不出现比较/拼接表达式，遵守该文件既有的 BUG-20 模板防线约定。
- 分隔符与文案对齐仓库现有口径：` · ` 连接、座位渲染为 `N号座位`（参考 `pages/review/submit.vue` 的 `seatText` 与 `orderTypeIcon`）。
- `room_name` 与 `seat_number` 均为空时 `targetText` 返回空串，行随现有 `v-if` 自动隐藏，覆盖历史脏数据场景。

## 验证方式

- br-app 无单测基建依赖时以现有构建/静态检查 + 真机/H5 手工验证三种卡片：课程、自习室（有座位）、自习室（字段缺失）。
