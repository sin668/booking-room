## Why

用户需要查看自己的学习历史和统计数据，当前个人中心已有入口（`/pages/study-record/index`）但页面尚未实现。原型已设计完毕，需要落地为可用的前端页面和对应后端 API。

## What Changes

- 新增学习记录页面（`br-app/src/pages/study-record/index.vue`），包含统计卡片、月度日历、最近记录列表
- 新增后端学习记录 API，提供月度统计、日历打卡数据、记录列表查询
- 在 `pages.json` 中注册新页面路由

## Capabilities

### New Capabilities

- `study-record-api`: 后端学习记录 API — 月度统计汇总、日历打卡数据、学习记录列表分页查询
- `study-record-ui`: 前端学习记录页面 — 统计卡片、月度日历、记录列表，参考 `prototype/study-record.html` 高保真原型

### Modified Capabilities

（无需修改现有 spec 的需求定义）

## Impact

- **br-app**: 新增 `pages/study-record/index.vue` 页面，修改 `pages.json` 注册路由
- **br-server**: 新增 `api/routes/study_record.py`、`services/study_record.py`、`schemas/study_record.py`，复用现有 booking 数据模型
- **回滚方案**: 删除新增的路由文件和页面文件，移除 `pages.json` 中的路由注册即可完全回滚
