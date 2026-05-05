<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Zone tabs -->
      <view class="zone-section">
        <scroll-view class="zone-scroll" scroll-x :show-scrollbar="false">
          <view class="zone-list">
            <view
              v-for="zone in zoneTabs"
              :key="zone.value"
              :class="['zone-tab', { active: selectedZone === zone.value }]"
              @tap="onSelectZone(zone)"
            >
              <text class="zone-tab-text">{{ zone.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Date & time picker -->
      <view v-if="!hasTimeParams" class="picker-section">
        <!-- Date -->
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

        <!-- Time slots -->
        <view class="time-scroll-wrap">
          <scroll-view class="time-scroll" scroll-x :show-scrollbar="false">
            <view class="time-list">
              <view
                v-for="slot in timeSlots"
                :key="slot.value"
                :class="['time-slot', {
                  selected: selectedTimeSlot === slot.value && !slot.disabled,
                  disabled: slot.disabled,
                }]"
                @tap="onSelectTimeSlot(slot)"
              >
                <text class="time-slot-text">{{ slot.label }}</text>
              </view>
            </view>
          </scroll-view>
        </view>
      </view>

      <!-- Seat map card -->
      <view class="seat-section">
        <view class="seat-card">
          <!-- Card header -->
          <view class="card-header">
            <text class="card-room-name">{{ roomName }}</text>
            <text class="card-floor"> · 3楼平面图</text>
          </view>

          <!-- Window indicator -->
          <view class="window-strip">
            <text class="window-text">靠窗座位</text>
          </view>

          <!-- Loading -->
          <view v-if="seatsLoading" class="seat-loading">
            <text class="seat-loading-text">加载中...</text>
          </view>

          <!-- Empty -->
          <view v-else-if="seatSections.length === 0" class="seat-empty">
            <text class="seat-empty-text">暂无可用座位</text>
          </view>

          <!-- Zone sections -->
          <view v-else class="seat-zones">
            <view v-for="section in seatSections" :key="section.zone" class="zone-section-block">
              <!-- Section label -->
              <view :class="['section-label', section.zone]">
                <text class="section-label-text">{{ section.icon }} {{ section.name }}</text>
                <text class="section-label-range">{{ section.rowRange }}</text>
              </view>

              <!-- Seat rows with desk indicators -->
              <view v-for="(row, idx) in section.rows" :key="row.rowNum" class="zone-row-group">
                <view v-if="idx > 0" class="desk-indicator">
                  <view class="desk-line" />
                  <text class="desk-text">{{ row.rowNum }}排桌面</text>
                  <view class="desk-line" />
                </view>
                <view class="seat-row">
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

      <!-- Bottom spacing for fixed bar -->
      <view :style="{ height: selectedSeat ? '240rpx' : '40rpx' }" />
    </scroll-view>

    <!-- Fixed bottom bar -->
    <view v-if="selectedSeat" class="bottom-bar">
      <view class="bottom-info">
        <view class="bottom-seat-info">
          <text class="bottom-seat-number">{{ selectedSeat.seat_number }}号座位</text>
          <text class="bottom-sep"> · </text>
          <text class="bottom-zone">{{ zoneLabel(selectedSeat.zone) }}</text>
          <text class="bottom-sep"> · </text>
          <text class="bottom-position">{{ selectedSeat.position }}</text>
        </view>
        <view class="bottom-detail">
          <text class="bottom-time">{{ selectedDate }} {{ selectedTimeSlot }}</text>
          <text class="bottom-hours"> · {{ hours }}小时</text>
        </view>
      </view>
      <view class="bottom-price-row">
        <text class="bottom-price">
          <text class="bottom-price-symbol">¥</text>{{ totalPrice }}
        </text>
        <view class="btn-confirm" @tap="onConfirm">
          <text class="btn-confirm-text">确认选座</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getSeats } from '@/api/seats'
import { getRooms } from '@/api/rooms'

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

const ZONE_CONFIG = {
  quiet: { label: '静音区', icon: '🤫', color: 'blue' },
  keyboard: { label: '键盘区', icon: '⌨️', color: 'orange' },
  vip: { label: 'VIP区', icon: '👑', color: 'purple' },
}

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
      roomId: null,
      roomName: '',
      hasTimeParams: false,
      selectedDate: formatDate(today),
      dateList: this.generateDateList(today),
      timeSlots: TIME_SLOTS,
      selectedTimeSlot: TIME_SLOTS[0].value,
      selectedZone: '',
      seats: [],
      seatsLoading: false,
      selectedSeat: null,
    }
  },

  computed: {
    zoneTabs() {
      const prices = { quiet: '¥6/h', keyboard: '¥8/h', vip: '¥12/h' }
      const tabs = [{ label: '全部', value: '' }]
      Object.keys(ZONE_CONFIG).forEach(key => {
        tabs.push({ label: `${ZONE_CONFIG[key].label} ${prices[key]}`, value: key })
      })
      return tabs
    },

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

    seatSections() {
      const filtered = this.filteredSeats
      if (filtered.length === 0) return []

      const zoneMap = {}
      filtered.forEach(seat => {
        const zone = seat.zone || 'quiet'
        if (!zoneMap[zone]) zoneMap[zone] = []
        zoneMap[zone].push(seat)
      })

      const zoneOrder = ['quiet', 'keyboard', 'vip']
      const sections = []
      zoneOrder.forEach(zone => {
        if (!zoneMap[zone]) return
        const config = ZONE_CONFIG[zone] || { label: zone, icon: '', color: 'blue' }
        const zoneSeats = zoneMap[zone]

        const rowMap = {}
        zoneSeats.forEach(seat => {
          const rowNum = seat.row || 1
          if (!rowMap[rowNum]) rowMap[rowNum] = []
          rowMap[rowNum].push(seat)
        })
        const sortedKeys = Object.keys(rowMap).sort((a, b) => Number(a) - Number(b))
        const rows = sortedKeys.map(rowNum => ({
          rowNum: Number(rowNum),
          seats: rowMap[rowNum].sort((a, b) => (a.col || 0) - (b.col || 0)),
        }))

        const rowNumbers = sortedKeys.map(Number)
        const minRow = Math.min(...rowNumbers)
        const maxRow = Math.max(...rowNumbers)
        const rowRange = minRow === maxRow ? `第${minRow}排` : `第${minRow}-${maxRow}排`

        sections.push({
          zone,
          name: config.label,
          icon: config.icon,
          color: config.color,
          rowRange,
          rows,
        })
      })

      return sections
    },
  },

  onLoad(options) {
    this.roomId = Number(options.room_id)
    this.roomName = options.room_name || ''

    if (options.date && options.start_time && options.end_time) {
      this.hasTimeParams = true
      this.selectedDate = options.date
      this.selectedTimeSlot = `${options.start_time}-${options.end_time}`
    }

    this.loadSeats()
  },

  methods: {
    generateDateList(startDate) {
      const list = []
      for (let i = 0; i < 4; i++) {
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

    async loadSeats() {
      if (!this.roomId) return
      this.seatsLoading = true
      this.selectedSeat = null
      try {
        const parts = this.selectedTimeSlot.split('-')
        const params = {
          date: this.selectedDate,
          start_time: parts[0],
          end_time: parts[1],
        }
        const data = await getSeats(this.roomId, params)
        this.seats = data || []

        if (!this.roomName) {
          try {
            const roomsData = await getRooms({ page: 1, page_size: 100 })
            const items = roomsData.items || []
            const room = items.find(r => r.id === this.roomId)
            if (room) this.roomName = room.name
          } catch {
            // ignore
          }
        }
      } catch {
        this.seats = []
      } finally {
        this.seatsLoading = false
      }
    },

    onSelectZone(zone) {
      this.selectedZone = zone.value
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

    seatClass(seat) {
      if (this.selectedSeat && this.selectedSeat.id === seat.id) return 'selected'
      if (!seat.is_available) return 'occupied'
      if (seat.zone === 'vip') return 'vip'
      return 'available'
    },

    zoneLabel(zone) {
      const config = ZONE_CONFIG[zone]
      return config ? config.label : zone
    },

    onTapSeat(seat) {
      if (!seat.is_available) return
      if (this.selectedSeat && this.selectedSeat.id === seat.id) {
        this.selectedSeat = null
      } else {
        this.selectedSeat = seat
      }
    },

    onConfirm() {
      if (!this.selectedSeat || !this.roomId) return
      const parts = this.selectedTimeSlot.split('-')
      const url = `/pages/booking/confirm?seat_id=${this.selectedSeat.id}&room_id=${this.roomId}&date=${this.selectedDate}&start_time=${parts[0]}&end_time=${parts[1]}`
      uni.navigateTo({ url })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
  position: relative;
}

.content {
  height: 100vh;
  padding-bottom: 0;
}

/* Zone tabs */
.zone-section {
  padding: 20rpx 28rpx;
  background: #fff;
}

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
  height: 64rpx;
  padding: 0 32rpx;
  border-radius: 32rpx;
  background: $bg-color;
  flex-shrink: 0;
  transition: all 0.2s;
}

.zone-tab.active {
  background: $primary;
}

.zone-tab-text {
  font-size: 26rpx;
  color: $text-secondary;
}

.zone-tab.active .zone-tab-text {
  color: #fff;
}

/* Date & time picker */
.picker-section {
  padding: 16rpx 28rpx;
  background: #fff;
  margin-top: 2rpx;
}

.date-scroll {
  white-space: nowrap;
  margin-bottom: 16rpx;
}

.date-list {
  display: inline-flex;
  gap: 12rpx;
}

.date-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 104rpx;
  height: 120rpx;
  border-radius: 20rpx;
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
  font-size: 20rpx;
  color: $text-secondary;
}

.date-item.active .date-weekday {
  color: rgba(255, 255, 255, 0.8);
}

.date-day {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  margin-top: 2rpx;
}

.date-item.active .date-day {
  color: #fff;
}

.date-month {
  font-size: 18rpx;
  color: $text-muted;
  margin-top: 2rpx;
}

.date-item.active .date-month {
  color: rgba(255, 255, 255, 0.7);
}

/* Time slots */
.time-scroll-wrap {
  margin-top: 4rpx;
}

.time-scroll {
  white-space: nowrap;
}

.time-list {
  display: inline-flex;
  gap: 12rpx;
}

.time-slot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 56rpx;
  padding: 0 20rpx;
  border-radius: 28rpx;
  border: 2rpx solid $border-color;
  background: #fff;
  flex-shrink: 0;
  transition: all 0.2s;
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

/* Seat map section */
.seat-section {
  padding: 24rpx 28rpx;
}

.seat-card {
  background: #fff;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: $shadow-sm;
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.card-room-name {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.card-floor {
  font-size: 26rpx;
  color: $text-secondary;
}

/* Window indicator */
.window-strip {
  background: #EBF2FF;
  border-radius: 12rpx;
  padding: 8rpx 0;
  text-align: center;
  margin-bottom: 24rpx;
}

.window-text {
  font-size: 20rpx;
  color: $primary;
}

/* Loading / Empty */
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

/* Zone sections */
.seat-zones {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.zone-section-block {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Section labels */
.section-label {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 20rpx;
  border-radius: 12rpx;
  margin-bottom: 12rpx;
  border-left: 6rpx solid transparent;
}

.section-label.quiet {
  background: linear-gradient(135deg, #E8EDFF, #F0F3FF);
  border-left-color: $primary;
}

.section-label.keyboard {
  background: linear-gradient(135deg, #FFF8E1, #FFFDF5);
  border-left-color: #FFA726;
}

.section-label.vip {
  background: linear-gradient(135deg, #F3E5F5, #FAFAFE);
  border-left-color: $purple;
}

.section-label-text {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.section-label-range {
  font-size: 22rpx;
  color: $text-muted;
}

/* Desk indicators */
.zone-row-group {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.desk-indicator {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8rpx 0;
  gap: 12rpx;
}

.desk-line {
  flex: 1;
  height: 1rpx;
  border-top: 2rpx dashed #D0D0D0;
}

.desk-text {
  font-size: 20rpx;
  color: $text-muted;
  flex-shrink: 0;
}

/* Seat rows */
.seat-row {
  display: flex;
  gap: 12rpx;
  justify-content: center;
  padding: 8rpx 0;
}

/* Seats */
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
  border: 2rpx solid $primary-dark;
  box-shadow: 0 4rpx 12rpx rgba(79, 110, 247, 0.3);
}

.seat.occupied {
  background: #F0F0F0;
  border: 2rpx solid #E0E0E0;
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
  color: #388E3C;
}

.seat.selected .seat-number {
  color: #fff;
}

.seat.occupied .seat-number {
  color: #BDBDBD;
}

.seat.vip .seat-number {
  color: #F57C00;
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

/* Legend */
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

/* Fixed bottom bar */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 20rpx 28rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.bottom-info {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  margin-bottom: 16rpx;
}

.bottom-seat-info {
  display: flex;
  align-items: center;
}

.bottom-seat-number {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.bottom-sep {
  font-size: 24rpx;
  color: $text-muted;
}

.bottom-zone {
  font-size: 24rpx;
  color: $primary;
}

.bottom-position {
  font-size: 24rpx;
  color: $text-secondary;
}

.bottom-detail {
  display: flex;
  align-items: center;
}

.bottom-time {
  font-size: 24rpx;
  color: $text-secondary;
}

.bottom-hours {
  font-size: 24rpx;
  color: $text-muted;
}

.bottom-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bottom-price {
  font-size: 40rpx;
  font-weight: 700;
  color: $primary;
}

.bottom-price-symbol {
  font-size: 26rpx;
}

.btn-confirm {
  height: 88rpx;
  padding: 0 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 44rpx;
  background: $primary;
  transition: all 0.2s;
}

.btn-confirm:active {
  background: $primary-dark;
}

.btn-confirm-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}
</style>
