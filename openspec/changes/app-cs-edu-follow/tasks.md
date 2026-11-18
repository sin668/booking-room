# Tasks: app-cs-edu-follow

## 1. 后端

- [x] 1.1 C 端房间详情与课程详情新增 creator_username（schema + service），含单元测试（有创建人/创建人为空）
- [x] 1.2 room-follows 支持 follow_type=listing（路由 pattern + follow/list 服务分支，仅 approved），含单元测试（关注/幂等/取消/列表/非 approved 404/城市过滤）

## 2. 前端

- [ ] 2.1 新增 utils/customerService.js（平台客服常量 + openCSChat 回退逻辑）
- [ ] 2.2 学习室/培训室详情页：关注旁新增客服按钮；培训室「返回课程」改「查看课程」并定位本培训室课程列表
- [ ] 2.3 课程详情页：关注旁新增客服按钮（课程所在学习室创建人）
- [ ] 2.4 老师详情页：底部改为 关注 + 客服（平台客服）+ 返回培训室
- [ ] 2.5 教培供需详情页：底部「咨询」改为 关注 + 客服（平台客服），保留立即联系/编辑
- [ ] 2.6 我的关注：getAllFollowedCategories 增加 listing 分类，新增「关注供需」TAB 与列表渲染

## 3. 验收

- [ ] 3.1 后端全量 pytest 对照 19 基线零回归；br-app build:h5 构建通过
- [ ] 3.2 真实环境冒烟：四类页面客服会话对象与回退、查看课程定位、供需关注切换与关注供需 TAB、老师页底部三按钮；冒烟数据清理