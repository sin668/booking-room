# 首页关注板块按城市过滤

## Why

br-app 首页的「关注自习室 / 关注培训室 / 关注课程 / 关注教师」四个板块目前只有自习室在前端做了城市过滤，培训室、课程、教师完全没有过滤（课程/教师接口返回的 city_id 恒为 null，前端也无从过滤）。用户切换城市后，首页关注板块仍展示其他城市的房间、课程和老师，与培训课程页已有的城市联动口径不一致。

## What Changes

- 后端 `GET /api/v1/room-follows` 新增可选查询参数 `city_id`（ge=1），对三种 `follow_type` 统一做服务端过滤：
  - room：按 `study_rooms.city_id` 过滤；
  - course：课程经 `courses.room_id → study_rooms.city_id` 过滤；
  - teacher：教师经 `teacher_rooms → study_rooms.city_id` 过滤；
  - 三种分支均保留「归属房间未设置城市」的豁免（city_id 为 NULL 始终可见；教师无任何房间关联时始终可见）。
- br-app 首页 `loadFollowedRooms` 传入当前城市 `city_id`，由服务端过滤；移除首页前端针对自习室的重复过滤逻辑。
- `api/roomFollows.js` / `services/followedRooms.js` 增加可选 `cityId` 透传参数，默认不传，收藏页（/pages/favorites）等其他调用方行为不变。

## Impact

- 影响的 capability：新增 `followed-rooms-city-filter`
- 影响的代码：`br-server/app/api/routes/room_follow.py`、`br-server/app/services/room_follow_service.py`、`br-server/tests/`（新增测试）、`br-app/src/api/roomFollows.js`、`br-app/src/services/followedRooms.js`、`br-app/src/pages/index/index.vue`
- 无破坏性变更：`city_id` 为可选参数，不传时接口行为与现状完全一致
