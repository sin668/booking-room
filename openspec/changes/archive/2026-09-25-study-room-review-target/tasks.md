# 任务：我的评价页自习室评价对象行

## 1. 实现

- [x] 1.1 `br-app/src/pages/review/list.vue`：`targetText` 增加 `booking_type === 'seat'` 分支，返回 `自习室名称 · N号座位`（缺失项省略）
- [x] 1.2 同文件：评价对象行图标改为 `targetIcon(item)` 方法驱动（seat 用 `icon-location`，其余 `icon-book`），模板不引入表达式

## 2. 验证

- [x] 2.1 构建/静态检查通过（`npm run build:mp-weixin` 或项目等价命令）
- [x] 2.2 手工验证三种卡片：课程评价、自习室评价（正常）、自习室评价（字段缺失隐藏末行）
