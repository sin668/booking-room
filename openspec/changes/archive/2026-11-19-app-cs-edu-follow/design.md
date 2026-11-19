# Design: app-cs-edu-follow

## 客服会话口径

- IM 用户名 = 用户 UUID hex（`app/core/im.py:to_im_user_id`）。平台客服用户 id `bd7f84cc-3d8b-480f-9327-30ee827cf386` → IM 用户名 `bd7f84cc3d8b480f932730ee827cf386`，前端常量固化（转换是确定性纯函数，无需新增接口）。
- 客服对象：
  - 自习室/培训室/综合室详情：`room.creator_username`（StudyRoom.created_by）。
  - 课程详情：`creator_username` = 课程所在学习室（Course.room_id → StudyRoom.created_by）的 IM 用户名。
  - 老师详情、教培供需详情：固定平台客服。
- 回退：`creator_username` 为空，或等于当前登录用户自己的 IM id（userInfo.id 去连字符）时，改用平台客服。
- 会话打开通用流程（复用 edu-market/detail.vue openChat 模式）：`ensureLogin()` → `ensureIM()`（失败 toast 带 getIMLastError）→ `uni.navigateTo('/TUIKit/components/TUIChat/index?conversationID=C2C' + username)`。

## 后端

### C 端详情 creator_username

- `StudyRoomResponse` 增 `creator_username: str | None = None`；`get_study_room` 组装时 `to_im_user_id(room.created_by) if room.created_by else None`。列表接口不加（仅详情需要）。
- `CourseDetailResponse` 增 `creator_username: str | None = None`；`get_course_detail` 已 join StudyRoom，取 `study_room.created_by` 转换；study_room 为 None 时置 None。

### listing 关注

- 路由 `room_follow.py` 三端点 pattern 改 `^(room|course|teacher|listing)$`。
- `follow_room` listing 分支：`db.get(EduListing, room_id)`，不存在或 `status != "approved"` 抛 ValueError（路由转 404）；幂等创建 RoomFollow(follow_type='listing')；返回 FollowedRoomResponse：id、name=title、description=description or ''、cover_image=images[0]（无图 None）、address=area or ''、status='active'、min_price=price or 0、room_type='listing'、followed_at。
- `list_followed_rooms` listing 分支：join EduListing，过滤 `EduListing.status == "approved"`（下架/拒绝后自动从关注列表消失，与课程 active 口径一致）；city_id 传入时按 `EduListing.city_id == city_id OR IS NULL` 过滤（与房间口径一致）；按 RoomFollow.created_at desc 排序；映射同上。
- `unfollow_room` 无需改动（按 user_id/room_id/follow_type 通用删除）。
- 不改表结构：room_follows.room_id 无外键，follow_type String(20) 容纳 'listing'。

## 前端

### utils/customerService.js（新增）

```js
export const PLATFORM_CS_IM_ID = 'bd7f84cc3d8b480f932730ee827cf386'
export async function openCSChat(creatorUsername) {
  if (!ensureLogin()) return
  const ownImId = (useUserStore().userInfo?.id || '').replace(/-/g, '')
  const target = creatorUsername && creatorUsername !== ownImId ? creatorUsername : PLATFORM_CS_IM_ID
  uni.showLoading({ title: '正在连接...' })
  const ok = await ensureIM()
  uni.hideLoading()
  if (!ok) { uni.showToast({ title: '消息服务初始化失败：' + getIMLastError(), icon: 'none', duration: 3000 }); return }
  uni.navigateTo({ url: `/TUIKit/components/TUIChat/index?conversationID=C2C${target}` })
}
```

### 各页面

- `pages/booking/detail.vue`：bottom-bar 在 fav-btn 后加 `cs-btn`（🎧 文本，圆形样式同 fav-btn），`onCS() => openCSChat(this.room.creator_username)`。培训室 back-btn 文案「返回课程」→「查看课程」，`onBackToCourses` 改为定位本页课程区块：课程列表容器加 `id="room-courses"`，`uni.createSelectorQuery().select('#room-courses').boundingClientRect` + `uni.pageScrollTo({ scrollTop: rect.top + 当前滚动偏移 - 导航高度, duration: 300 })`（页面为整页滚动）。
- `pages/training/course-detail.vue`：fav-btn 旁加 cs-btn；`onCS() => openCSChat(this.creatorUsername)`，loadCourseDetail 时保存顶层 `data.creator_username`（course 嵌套对象不含该字段）。
- `pages-sub/teacher/profile.vue`：bottom-bar 改为 fav-btn（♥，复用 onToggleFav）+ cs-btn（🎧，`openCSChat()` 固定平台客服）+ action-btn「返回培训室」（原 switchTab 逻辑不变，仅改文案）；移除空实现 chat-btn。顶部导航心形保留不动。
- `pages-sub/edu-market/detail.vue`：action-bar 左侧「咨询」替换为两个图标按钮：关注（♥  active 红色，`onToggleFav`）+ 客服（🎧，`openCSChat()` 平台客服）；保留右侧 立即联系（非发布者）/编辑（发布者）。关注态：onLoad 登录后 `getFollowedRooms('listing')` 判断 id 是否在列表；切换用 `followRoom(id, 'listing')` / `unfollowRoom(id, 'listing')`，toast 文案「已加入关注供需」/「已取消关注」。
- `services/followedRooms.js`：`getAllFollowedCategories` 的 Promise.allSettled 增加 `getFollowedRooms('listing', cityId)`，返回增加 `listings`（normalizeRoom 通用映射已兼容：name/cover_image/min_price/address/description）。
- `pages-sub/favorites/index.vue`：tabs 增加 `{ key: 'listing', label: '关注供需' }`；data 增 listings；loadData 赋值；新增列表区块（封面图、标题、描述摘要、价格），点击 `navigateTo('/pages-sub/edu-market/detail?id=' + item.id)`；空状态「暂无关注供需」+ 去逛逛按钮跳教培供需广场（switchTab）。

## 不改项

不改数据库 schema、不改权限码、不改管理端、不改首页关注板块（仍四类）、不改既有 room/course/teacher 关注行为。

## 验证

- pytest：新增 creator_username（房间/课程详情，含创建人为空）与 listing 关注测试（关注/幂等/取消/列表仅 approved/非 approved 404/城市过滤）；全量对照 19 基线失败零回归。
- br-app `npm run build:h5` 构建通过。
- 真实环境冒烟（CDP Chrome + H5）：四类页面客服按钮会话对象正确（创建人/平台客服回退）、培训室查看课程定位、供需关注切换与「关注供需」TAB 列表、老师页底部三按钮。