## 1. 订单列表页：修复 viewSeat 跳转

- [x] 1.1 修改 `pages/orders/index.vue:250-255` 的 `viewSeat(order)` 方法，将跳转目标从 `/pages/booking/detail` 改为 `/pages/booking/seat-select`，传递完整参数 `room_id`、`seat_id`、`date`、`start_time`、`end_time`、`mode=view`

## 2. 座位选择页：viewMode 状态与数据加载

- [x] 2.1 在 `pages/booking/seat-select.vue` 的 `data()` 中新增 `isViewMode: false` 和 `viewSeatId: null`
- [x] 2.2 在 `onLoad(options)` 中解析 `options.mode === 'view'` 设置 `isViewMode = true`，解析 `options.seat_id` 设置 `viewSeatId = Number(options.seat_id)`。已有逻辑会自动将 `date`、`start_time`、`end_time` 赋值给 `selectedDate`、`selectedTimeSlot` 并设置 `hasTimeParams = true`

## 3. 座位选择页：viewMode UI 控制

- [x] 3.1 viewMode 下隐藏底部确认栏：修改模板第 141 行 `v-if="selectedSeat"` 为 `v-if="selectedSeat && !isViewMode"`
- [x] 3.2 viewMode 下调整底部间距：修改模板第 137 行，viewMode 时固定 `height: '40rpx'` 而非依赖 `selectedSeat`
- [x] 3.3 viewMode 下禁用座位点击：在 `onTapSeat(seat)` 方法开头添加 `if (this.isViewMode) return`

## 4. 座位选择页：预定座位高亮

- [x] 4.1 修改 `seatClass(seat)` 方法：当 `isViewMode && viewSeatId && seat.id === viewSeatId` 时返回 `'booked'`（新样式类）
- [x] 4.2 修改座位模板（第 100-108 行）：为预定座位显示小人图标，在 `seat-number` 下方条件渲染 `<text v-if="isBookedSeat(seat)" class="seat-person">🧑</text>`
- [x] 4.3 添加 `isBookedSeat(seat)` 方法：返回 `this.isViewMode && this.viewSeatId && seat.id === this.viewSeatId`
- [x] 4.4 添加 `.seat.booked` 样式：高亮背景色（如 `$primary-light`）+ 边框色，与可选/已占/VIP 明显区分
- [x] 4.5 添加 `.seat-person` 样式：绝对定位在座位元素上方，显示小人 emoji

## 5. 图例更新

- [x] 5.1 viewMode 下在图例区域追加"我的座位"图例项（带 `.legend-dot.booked` 样式），使用 `v-if="isViewMode"` 条件渲染

## 6. 验证

- [x] 6.1 确认正常选座流程（无 mode 参数）不受影响：日期/时段可选、座位可点击、底部栏正常显示
- [x] 6.2 确认 viewMode 下：无底部栏、座位不可点击、预定座位显示小人图标、其他座位保持原样式
