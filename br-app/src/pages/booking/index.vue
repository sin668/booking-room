<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Date selector -->
      <view class="date-section">
        <scroll-view class="date-scroll" scroll-x :show-scrollbar="false">
          <view class="date-list">
            <view
              v-for="day in dateList"
              :key="day.dateStr"
              :class="['date-item', { active: selectedDate === day.dateStr }]"
              @tap="onSelectDate(day)"
            >
              <text class="date-weekday">{{ day.weekday }}</text>
              <text class="date-day">{{ day.day }}</text>
              <text class="date-month">{{ day.month }}月</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Time slot selector -->
      <view class="section">
        <text class="section-title">选择时段</text>
        <view class="time-grid">
          <view
            v-for="slot in timeSlots"
            :key="slot.value"
            :class="['time-slot', {
              available: !slot.disabled,
              selected: selectedTimeSlot === slot.value && !slot.disabled,
              disabled: slot.disabled,
            }]"
            @tap="onSelectTimeSlot(slot)"
          >
            <text class="time-slot-text">{{ slot.label }}</text>
          </view>
        </view>
      </view>

      <!-- Zone filter -->
      <view class="section">
        <scroll-view class="zone-scroll" scroll-x :show-scrollbar="false">
          <view class="zone-list">
            <view
              v-for="zone in zones"
              :key="zone.value"
              :class="['zone-tab', { active: selectedZone === zone.value }]"
              @tap="onSelectZone(zone)"
            >
              <text class="zone-tab-text">{{ zone.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Seat map -->
      <view class="section">
        <view class="seat-card">
          <view class="seat-header">
            <text class="seat-room-name">{{ currentRoom ? currentRoom.name : '' }}</text>
            <text class="seat-remain">剩余 {{ availableCount }} 个座位</text>
          </view>

          <view v-if="seatsLoading" class="seat-loading">
            <text class="seat-loading-text">加载中...</text>
          </view>

          <view v-else-if="filteredSeats.length === 0" class="seat-empty">
            <text class="seat-empty-text">暂无可用座位</text>
          </view>

          <view v-else class="seat-map">
            <text class="seat-front">前方</text>
            <view v-for="row in seatRows" :key="row.rowNum" class="seat-row">
              <view
                v-for="seat in row.seats"
                :key="seat.id"
                :class="['seat', seatClass(seat)]"
                @tap="onTapSeat(seat)"
              >
                <text class="seat-number">{{ seat.seat_number }}</text>
                <view v-if="!seat.is_available" class="seat-line" />
              </view>
            </view>
          </view>

          <!-- Legend -->
          <view class="seat-legend">
            <view class="legend-item">
              <view class="legend-dot available" />
              <text class="legend-text">可选</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot selected" />
              <text class="legend-text">已选</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot occupied" />
              <text class="legend-text">已占</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot vip" />
              <text class="legend-text">VIP</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Seat info panel -->
      <view v-if="selectedSeat" class="section">
        <view class="info-panel">
          <view class="info-header">
            <view class="info-seat-info">
              <text class="info-seat-number">{{ selectedSeat.seat_number }}号座位</text>
              <text class="info-zone-tag">{{ zoneLabel(selectedSeat.zone) }}</text>
              <text class="info-pos-tag">{{ selectedSeat.position }}</text>
            </view>
          </view>
          <view class="info-detail">
            <view class="info-row">
              <text class="info-label">日期</text>
              <text class="info-value">{{ selectedDate }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">时段</text>
              <text class="info-value">{{ selectedTimeSlot }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">时长</text>
              <text class="info-value">{{ hours }}小时</text>
            </view>
            <view class="info-row">
              <text class="info-label">费用</text>
              <text class="info-price">
                <text class="info-price-symbol">¥</text>{{ totalPrice }}
              </text>
            </view>
          </view>
          <view class="info-actions">
            <view class="btn-change" @tap="onDeselectSeat">
              <text class="btn-change-text">换个座位</text>
            </view>
            <view class="btn-book" @tap="onBookSeat">
              <text class="btn-book-text">立即预约</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Bottom spacing for tab bar -->
      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { getRooms } from '@/api/rooms'
import { getSeats } from '@/api/seats'

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const TIME_SLOTS = [
  { label: '08:00-10:00', value: '08:00-10:00', start: '08:00', end: '10:00' },
  { label: '10:00-12:00', value: '10:00-12:00', start: '10:00', end: '12:00' },
  { label: '12:00-14:00', value: '12:00-14:00', start: '12:00', end: '14:00' },
  { label: '14:00-16:00', value: '14:00-16:00', start: '14:00', end: '16:00' },
  { label: '16:00-18:00', value: '16:00-18:00', start: '16:00', end: '18:00' },
  { label: '18:00-20:00', value: '18:00-20:00', start: '18:00', end: '20:00' },
  { label: '20:00-22:00', value: '20:00-22:00', start: '20:00', end: '22:00' },
]

const ZONES = [
  { label: '全部', value: '' },
  { label: '静音区', value: 'quiet' },
  { label: '键盘区', value: 'keyboard' },
  { label: 'VIP区', value: 'vip' },
]

function formatDate(d) {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export default {
  data() {
    const today = new Date()
    return {
      rooms: [],
      currentRoom: null,
      selectedDate: formatDate(today),
      dateList: this.generateDateList(today),
      timeSlots: TIME_SLOTS,
      selectedTimeSlot: TIME_SLOTS[0].value,
      zones: ZONES,
      selectedZone: '',
      seats: [],
      seatsLoading: false,
      selectedSeat: null,
    }
  },

  computed: {
    hours() {
      if (!this.selectedTimeSlot) return 2
      const parts = this.selectedTimeSlot.split('-')
      if (parts.length !== 2) return 2
      const [sh, sm] = parts[0].split(':').map(Number)
      const [eh, em] = parts[1].split(':').map(Number)
      return (eh * 60 + em - sh * 60 - sm) / 60
    },

    totalPrice() {
      if (!this.selectedSeat) return '0.00'
      return (this.selectedSeat.price_per_hour * this.hours).toFixed(2)
    },

    filteredSeats() {
      if (!this.selectedZone) return this.seats
      return this.seats.filter(s => s.zone === this.selectedZone)
    },

    availableCount() {
      return this.filteredSeats.filter(s => s.is_available).length
    },

    seatRows() {
      if (this.filteredSeats.length === 0) return []
      const rowMap = {}
      this.filteredSeats.forEach(seat => {
        const rowNum = seat.row || 1
        if (!rowMap[rowNum]) rowMap[rowNum] = []
        rowMap[rowNum].push(seat)
      })
      const sortedKeys = Object.keys(rowMap).sort((a, b) => Number(a) - Number(b))
      return sortedKeys.map(rowNum => ({
        rowNum: Number(rowNum),
        seats: rowMap[rowNum].sort((a, b) => (a.col || 0) - (b.col || 0)),
      }))
    },
  },

  onShow() {
    this.loadRooms()
  },

  methods: {
    generateDateList(startDate) {
      const list = []
      for (let i = 0; i < 7; i++) {
        const d = new Date(startDate)
        d.setDate(d.getDate() + i)
        list.push({
          dateStr: formatDate(d),
          weekday: WEEKDAYS[d.getDay()],
          day: d.getDate(),
          month: d.getMonth() + 1,
        })
      }
      return list
    },

    async loadRooms() {
      try {
        const data = await getRooms({ page: 1, page_size: 100 })
        this.rooms = data.items || []
        if (this.rooms.length > 0 && (!this.currentRoom || !this.rooms.find(r => r.id === this.currentRoom.id))) {
          this.currentRoom = this.rooms[0]
          this.loadSeats()
        }
      } catch {
        this.rooms = []
      }
    },

    async loadSeats() {
      if (!this.currentRoom) return
      this.seatsLoading = true
      this.selectedSeat = null
      try {
        const parts = this.selectedTimeSlot.split('-')
        const params = {
          date: this.selectedDate,
          start_time: parts[0],
          end_time: parts[1],
        }
        const data = await getSeats(this.currentRoom.id, params)
        this.seats = data || []
      } catch {
        this.seats = []
      } finally {
        this.seatsLoading = false
      }
    },

    onSelectDate(day) {
      this.selectedDate = day.dateStr
      this.loadSeats()
    },

    onSelectTimeSlot(slot) {
      if (slot.disabled) return
      this.selectedTimeSlot = slot.value
      this.loadSeats()
    },

    onSelectZone(zone) {
      this.selectedZone = zone.value
    },

    seatClass(seat) {
      if (this.selectedSeat && this.selectedSeat.id === seat.id) return 'selected'
      if (!seat.is_available) return 'occupied'
      if (seat.zone === 'vip') return 'vip'
      return 'available'
    },

    zoneLabel(zone) {
      const map = { quiet: '静音区', keyboard: '键盘区', vip: 'VIP区' }
      return map[zone] || zone
    },

    onTapSeat(seat) {
      if (!seat.is_available) return
      if (this.selectedSeat && this.selectedSeat.id === seat.id) {
        this.selectedSeat = null
      } else {
        this.selectedSeat = seat
      }
    },

    onDeselectSeat() {
      this.selectedSeat = null
    },

    onBookSeat() {
      if (!this.selectedSeat || !this.currentRoom) return
      const parts = this.selectedTimeSlot.split('-')
      const url = `/pages/booking/confirm?seat_id=${this.selectedSeat.id}&room_id=${this.currentRoom.id}&date=${this.selectedDate}&start_time=${parts[0]}&end_time=${parts[1]}`
      uni.navigateTo({ url })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
}

.content {
  height: calc(100vh - 100rpx);
}

/* Date selector */
.date-section {
  padding: 20rpx 0;
  background: #fff;
}

.date-scroll {
  white-space: nowrap;
}

.date-list {
  display: inline-flex;
  padding: 0 28rpx;
  gap: 16rpx;
}

.date-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 112rpx;
  height: 140rpx;
  border-radius: 24rpx;
  background: #fff;
  box-shadow: $shadow-sm;
  flex-shrink: 0;
  transition: all 0.2s;
}

.date-item.active {
  background: $primary;
  box-shadow: 0 4rpx 16rpx rgba(79, 110, 247, 0.3);
}

.date-weekday {
  font-size: 22rpx;
  color: $text-secondary;
}

.date-item.active .date-weekday {
  color: rgba(255, 255, 255, 0.8);
}

.date-day {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  margin-top: 4rpx;
}

.date-item.active .date-day {
  color: #fff;
}

.date-month {
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 2rpx;
}

.date-item.active .date-month {
  color: rgba(255, 255, 255, 0.7);
}

/* Section */
.section {
  margin-top: 24rpx;
  padding: 0 28rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 20rpx;
  display: block;
}

/* Time slot grid */
.time-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.time-slot {
  width: calc(33.33% - 12rpx);
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  border: 2rpx solid $border-color;
  background: #fff;
  transition: all 0.2s;
}

.time-slot.available:active {
  transform: scale(0.96);
}

.time-slot.selected {
  background: $primary;
  border-color: $primary;
}

.time-slot.disabled {
  background: #F0F0F0;
  border-color: #F0F0F0;
}

.time-slot-text {
  font-size: 24rpx;
  color: $text-secondary;
}

.time-slot.selected .time-slot-text {
  color: #fff;
}

.time-slot.disabled .time-slot-text {
  color: #ccc;
  text-decoration: line-through;
}

/* Zone filter */
.zone-scroll {
  white-space: nowrap;
}

.zone-list {
  display: inline-flex;
  gap: 16rpx;
}

.zone-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 60rpx;
  padding: 0 32rpx;
  border-radius: 30rpx;
  border: 2rpx solid $border-color;
  background: #fff;
  flex-shrink: 0;
  transition: all 0.2s;
}

.zone-tab.active {
  background: $primary;
  border-color: $primary;
}

.zone-tab-text {
  font-size: 26rpx;
  color: $text-secondary;
}

.zone-tab.active .zone-tab-text {
  color: #fff;
}

/* Seat card */
.seat-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: $shadow-sm;
}

.seat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.seat-room-name {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.seat-remain {
  font-size: 24rpx;
  color: $success;
}

.seat-loading,
.seat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300rpx;
}

.seat-loading-text,
.seat-empty-text {
  font-size: 28rpx;
  color: $text-muted;
}

/* Seat map */
.seat-map {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 0 12rpx;
}

.seat-front {
  font-size: 22rpx;
  color: $text-muted;
  padding: 8rpx 0 16rpx;
  border-bottom: 2rpx solid $border-color;
  width: 60%;
  text-align: center;
  margin-bottom: 8rpx;
}

.seat-row {
  display: flex;
  gap: 12rpx;
  justify-content: center;
}

.seat {
  position: relative;
  width: 64rpx;
  height: 64rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.seat.available {
  background: #E8F5E9;
  border: 2rpx solid #66BB6A;
}

.seat.available:active {
  transform: scale(0.9);
}

.seat.selected {
  background: $primary;
  border: 2rpx solid $primary;
}

.seat.occupied {
  background: #F0F0F0;
  border: 2rpx solid #F0F0F0;
}

.seat.vip {
  background: #FFF3E0;
  border: 2rpx solid #FFB74D;
}

.seat.vip:active {
  transform: scale(0.9);
}

.seat-number {
  font-size: 18rpx;
  color: $text-secondary;
}

.seat.selected .seat-number {
  color: #fff;
}

.seat.occupied .seat-number {
  color: #ccc;
}

.seat.vip .seat-number {
  color: #E65100;
}

.seat-line {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 140%;
  height: 2rpx;
  background: #ccc;
  transform: translate(-50%, -50%) rotate(-45deg);
}

/* Seat legend */
.seat-legend {
  display: flex;
  justify-content: center;
  gap: 32rpx;
  margin-top: 28rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid $border-color;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.legend-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 6rpx;
}

.legend-dot.available {
  background: #E8F5E9;
  border: 2rpx solid #66BB6A;
}

.legend-dot.selected {
  background: $primary;
  border: 2rpx solid $primary;
}

.legend-dot.occupied {
  background: #F0F0F0;
  border: 2rpx solid #F0F0F0;
}

.legend-dot.vip {
  background: #FFF3E0;
  border: 2rpx solid #FFB74D;
}

.legend-text {
  font-size: 22rpx;
  color: $text-secondary;
}

/* Info panel */
.info-panel {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: $shadow-sm;
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.info-seat-info {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.info-seat-number {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.info-zone-tag {
  font-size: 22rpx;
  color: $primary;
  background: $primary-light;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

.info-pos-tag {
  font-size: 22rpx;
  color: $text-secondary;
  background: $bg-color;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

.info-detail {
  margin-bottom: 24rpx;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 0;
}

.info-label {
  font-size: 26rpx;
  color: $text-muted;
}

.info-value {
  font-size: 26rpx;
  color: $text-primary;
}

.info-price {
  font-size: 32rpx;
  font-weight: 700;
  color: $danger;
}

.info-price-symbol {
  font-size: 22rpx;
}

.info-actions {
  display: flex;
  gap: 20rpx;
}

.btn-change {
  flex: 1;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  border: 2rpx solid $border-color;
  background: #fff;
}

.btn-change:active {
  background: $bg-color;
}

.btn-change-text {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-secondary;
}

.btn-book {
  flex: 2;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $primary;
}

.btn-book:active {
  background: $primary-dark;
}

.btn-book-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}
</style>
