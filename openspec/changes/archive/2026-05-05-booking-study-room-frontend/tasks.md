## 1. Backend - Seat Model & Migration

- [ ] 1.1 Create `Seat` model (`br-server/app/models/seat.py`) + export in `__init__.py`
- [ ] 1.2 Create `Booking` model (`br-server/app/models/booking.py`) + export in `__init__.py`
- [ ] 1.3 Generate & apply alembic migration for seats + bookings tables
- [ ] 1.4 Write seat seed data script (`br-server/app/services/seed_seats.py`) — 静音区28座 / 键盘区28座 / VIP区24座

## 2. Backend - Seat API

- [ ] 2.1 Create Seat schemas (`br-server/app/schemas/seat.py`) — SeatResponse with `is_available` field
- [ ] 2.2 Create SeatService (`br-server/app/services/seat_service.py`) — list_seats with availability check
- [ ] 2.3 Create seat route (`br-server/app/api/routes/seat.py`) — `GET /api/v1/rooms/{room_id}/seats/`
- [ ] 2.4 Register seat router in `main.py`
- [ ] 2.5 Write Seat unit + integration tests

## 3. Backend - Booking API

- [ ] 3.1 Create Booking schemas (`br-server/app/schemas/booking.py`) — Create/List/Response with SeatBrief+RoomBrief
- [ ] 3.2 Create BookingService (`br-server/app/services/booking_service.py`) — create/list/get/cancel with conflict detection
- [ ] 3.3 Create booking route (`br-server/app/api/routes/booking.py`) — POST/GET/GET{id}/POST{id}cancel
- [ ] 3.4 Register booking router in `main.py`
- [ ] 3.5 Write Booking integration tests (success/401/409/422 scenarios)
- [ ] 3.6 Run all backend tests — verify pass

## 4. Frontend - API Layer

- [ ] 4.1 Create `br-app/src/api/seats.js` — getSeats(roomId, params)
- [ ] 4.2 Create `br-app/src/api/bookings.js` — createBooking/getBookings/getBooking/cancelBooking

## 5. Frontend - Booking Tab Page

- [ ] 5.1 Rewrite `pages/booking/index.vue` — 日期选择器(近7天横向滚动)
- [ ] 5.2 Implement 时段选择网格(2小时一档, 7个slot)
- [ ] 5.3 Implement 区域筛选标签(全部/静音区/键盘区/VIP区)
- [ ] 5.4 Implement 座位平面图(row/col网格, 可选/已占/已选/VIP样式)
- [ ] 5.5 Implement 底部座位信息栏 + "立即预约"按钮 → 跳转confirm页

## 6. Frontend - Store Detail Page

- [ ] 6.1 Create `pages/booking/detail.vue` — 封面大图 + 门店信息卡片(名称/状态/评分/地址/营业时间/区域标签)
- [ ] 6.2 Implement 环境照片横向滚动 + 座位概况统计(总/可用/已占/维护中)
- [ ] 6.3 Implement 底部固定栏(收藏 + "立即预约" → seat-select页)
- [ ] 6.4 Register route in `pages.json`

## 7. Frontend - Seat Select Page

- [ ] 7.1 Create `pages/booking/seat-select.vue` — 区域tab(含单价) + 日期/时段选择器
- [ ] 7.2 Implement 座位平面图(分区域展示, 桌面/过道/靠窗标记)
- [ ] 7.3 Implement 底部已选座位信息 + "确认选座" → confirm页
- [ ] 7.4 Register route in `pages.json`

## 8. Frontend - Order Confirm Page

- [ ] 8.1 Create `pages/booking/confirm.vue` — 门店信息 + 座位信息 + 日期时段 + 费用明细
- [ ] 8.2 Implement "立即支付" → createBooking API + 预约成功弹窗 → 跳转orders tab
- [ ] 8.3 Handle 409冲突 / 网络错误
- [ ] 8.4 Register route in `pages.json`

## 9. Frontend - Orders List Page

- [ ] 9.1 Rewrite `pages/orders/index.vue` — 预约记录列表 + 状态标签(已确认绿/已取消灰/已完成蓝)
- [ ] 9.2 Implement 状态筛选(全部/已确认/已取消/已完成) + 分页
- [ ] 9.3 Implement 空状态("暂无预约记录" + "去预约"按钮)

## 10. Frontend - Navigation Updates

- [ ] 10.1 Update home page `onTapRoom` → navigate to `/pages/booking/detail?room_id=X`

## 11. 收尾

- [ ] 11.1 Update `docs/api.md` — 补充 seats + bookings 接口文档
- [ ] 11.2 Final verification: backend tests pass + frontend build + smoke test full flow
