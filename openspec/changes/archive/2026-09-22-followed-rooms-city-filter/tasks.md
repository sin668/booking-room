# Tasks

## 1. 后端

- [x] 1.1 `room_follow_service.list_followed_rooms` 增加 `city_id` 可选参数：room/course/teacher 三分支按 design D2–D4 过滤，count 与列表使用同一谓词
- [x] 1.2 `routes/room_follow.py` GET 接口增加 `city_id: int | None = Query(None, ge=1)` 并传入 service
- [x] 1.3 新增测试 `tests/test_follow_city_filter.py`：房间城市过滤、NULL 城市豁免、课程按所属房间过滤、teacher EXISTS 三种情形、不传 city_id 行为不变、非法 city_id 422

## 2. 前端（br-app）

- [x] 2.1 `api/roomFollows.js` `getFollowedRooms(followType, cityId?)` 拼装查询参数
- [x] 2.2 `services/followedRooms.js` `getFollowedRooms`/`getAllFollowedCategories` 增加可选 `cityId` 透传
- [x] 2.3 `pages/index/index.vue` `loadFollowedRooms` 传 `currentCityId`，移除自习室前端城市过滤

## 3. 验证

- [x] 3.1 pytest 新增用例与既有 follow 相关测试全部通过
- [x] 3.2 `npm run build:mp-weixin` 构建通过（br-app 内记录 comet check 证据并通过 guard）
