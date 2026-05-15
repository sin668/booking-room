<template>
  <view class="page">
    <view class="hero-section">
      <view class="hero-topline">
        <view>
          <text class="hero-kicker">预约自习</text>
          <text class="hero-title">选择自习室</text>
        </view>
        <view class="hero-city" @tap="onTapCity">
          <view class="icon icon-location hero-city-icon" />
          <text class="hero-city-text">{{ currentCityName }}</text>
        </view>
      </view>

      <view class="search-bar" @tap="onTapSearch">
        <view class="icon icon-search search-icon" />
        <text class="search-placeholder">搜索自习室、商圈或地址</text>
      </view>

      <scroll-view class="filter-scroll" scroll-x :show-scrollbar="false">
        <view class="filter-row">
          <view
            v-for="filter in filters"
            :key="filter.value"
            :class="['filter-pill', { active: selectedFilter === filter.value }]"
            @tap="onSelectFilter(filter)"
          >
            <text class="filter-pill-text">{{ filter.label }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <scroll-view
      class="content"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullDownRefresh"
      @scrolltolower="onReachBottom"
    >
      <view class="list-header">
        <view>
          <text class="section-title">全部自习室</text>
          <text class="section-subtitle">{{ roomTotalText }}</text>
        </view>
        <view class="sort-pill" @tap="onTapSort">
          <text class="sort-text">{{ currentSortLabel }}</text>
          <view class="icon icon-arrow-down sort-icon" />
        </view>
      </view>

      <view v-if="roomsLoading && rooms.length === 0" class="room-skeleton">
        <view v-for="i in 4" :key="i" class="room-card-skeleton">
          <view class="skeleton-image" />
          <view class="skeleton-info">
            <view class="skeleton-line long" />
            <view class="skeleton-line short" />
            <view class="skeleton-line medium" />
          </view>
        </view>
      </view>

      <view v-else-if="rooms.length === 0" class="empty-state">
        <view class="icon icon-book empty-icon" />
        <text class="empty-title">暂无可预约自习室</text>
        <text class="empty-text">下拉刷新试试</text>
      </view>

      <view v-else class="room-list">
        <view
          v-for="(room, index) in displayedRooms"
          :key="room.id"
          class="room-card"
          @tap="onTapRoom(room)"
        >
          <view class="room-cover-wrap">
            <image class="room-cover" :src="roomCover(room, index)" mode="aspectFill" />
            <view :class="['cover-status', room.status === 'open' ? 'open' : 'closed']">
              <text class="cover-status-text">{{ room.status === 'open' ? '可预约' : '休息中' }}</text>
            </view>
            <view class="cover-chip">
              <text class="cover-chip-text">实景</text>
            </view>
          </view>
          <view class="room-info">
            <view>
              <view class="room-title-row">
                <text class="room-name">{{ room.name }}</text>
              </view>
              <view class="room-location-row">
                <view class="icon icon-location room-location-icon" />
                <text class="room-address">{{ room.address || '地址待完善' }}</text>
              </view>
            </view>

            <view class="room-detail-grid">
              <view class="room-detail-item">
                <text class="detail-value">{{ roomDistance(room, index) }}</text>
                <text class="detail-label">距离</text>
              </view>
              <view class="room-detail-item">
                <text class="detail-value">{{ roomHours(room) }}</text>
                <text class="detail-label">营业</text>
              </view>
              <view class="room-detail-item">
                <text class="detail-value">{{ roomSeatHint(room, index) }}</text>
                <text class="detail-label">座位</text>
              </view>
            </view>

            <view class="room-meta">
              <view class="room-tags">
                <text
                  v-for="tag in roomTags(room)"
                  :key="tag"
                  :class="['room-tag', tag === '在线选座' ? 'accent' : '']"
                >{{ tag }}</text>
              </view>
              <text class="room-price">
                <text class="room-price-symbol">¥</text>{{ room.min_price || 0 }}
                <text class="room-price-unit">起</text>
              </text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="rooms.length > 0" class="load-more">
        <text class="load-more-text">{{ loadMoreText }}</text>
      </view>

      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { getRooms } from '@/api/rooms'
import { useCityStore } from '@/store/modules/city'

const REAL_ROOM_COVERS = [
  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=720&h=520&fit=crop&q=85',
]

const FILTERS = [
  { label: '附近优先', value: 'nearby' },
  { label: '空座优先', value: 'available' },
  { label: '价格友好', value: 'price' },
  { label: '安静环境', value: 'quiet' },
]

export default {
  data() {
    return {
      refreshing: false,
      rooms: [],
      roomsLoading: false,
      roomPage: 1,
      roomPageSize: 10,
      roomTotal: 0,
      lastCityId: null,
      selectedFilter: FILTERS[0].value,
      filters: FILTERS,
    }
  },

  computed: {
    cityStore() {
      return useCityStore()
    },

    currentCity() {
      return this.cityStore.currentCity
    },

    currentCityName() {
      return this.cityStore.currentCityName
    },

    currentCityId() {
      return this.currentCity?.id || null
    },

    hasMoreRooms() {
      return this.rooms.length < this.roomTotal
    },

    roomTotalText() {
      if (this.roomsLoading && this.rooms.length === 0) return '正在加载附近门店'
      if (this.roomTotal > 0) return `共 ${this.roomTotal} 家可预约`
      return '选择门店后查看详情与座位'
    },

    loadMoreText() {
      if (this.roomsLoading) return '加载更多...'
      return this.hasMoreRooms ? '上拉加载更多' : '没有更多了'
    },

    currentSortLabel() {
      const current = this.filters.find(filter => filter.value === this.selectedFilter)
      return current ? current.label : '附近优先'
    },

    displayedRooms() {
      const rooms = [...this.rooms]
      if (this.selectedFilter === 'price') {
        return rooms.sort((a, b) => Number(a.min_price || 0) - Number(b.min_price || 0))
      }
      if (this.selectedFilter === 'available') {
        return rooms.sort((a, b) => this.seatSortValue(b) - this.seatSortValue(a))
      }
      if (this.selectedFilter === 'quiet') {
        return rooms.sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN'))
      }
      return rooms.sort((a, b) => this.distanceSortValue(a) - this.distanceSortValue(b))
    },
  },

  onShow() {
    const cityChanged = this.lastCityId !== this.currentCityId
    if (this.rooms.length === 0 || cityChanged) {
      this.loadRooms(true)
    }
  },

  methods: {
    roomCover(room, index = 0) {
      if (room.cover_image) return room.cover_image
      const key = Number(room.id || index)
      return REAL_ROOM_COVERS[key % REAL_ROOM_COVERS.length]
    },

    roomDistance(room, index = 0) {
      if (room.distance) return room.distance
      return index === 0 ? '附近' : '门店'
    },

    distanceSortValue(room) {
      if (room.distance_value !== undefined) return Number(room.distance_value)
      if (typeof room.distance === 'number') return room.distance
      const parsed = Number(String(room.distance || '').replace('km', ''))
      if (!Number.isNaN(parsed) && parsed > 0) return parsed
      return Number.MAX_SAFE_INTEGER
    },

    roomHours(room) {
      if (room.business_hours) return room.business_hours.replace('营业时间 ', '')
      return room.status === 'open' ? '营业中' : '休息中'
    },

    roomSeatHint(room) {
      if (room.available_seats !== undefined) return `${room.available_seats}座`
      return '可选座'
    },

    seatSortValue(room) {
      if (room.available_seats !== undefined) return Number(room.available_seats)
      return -1
    },

    roomTags(room) {
      const tags = ['在线选座', '静音区']
      if (Number(room.min_price || 0) <= 8) tags.push('高性价比')
      else tags.push('环境优选')
      return tags
    },

    async loadRooms(reset = false) {
      if (this.roomsLoading) return
      if (reset) {
        this.roomPage = 1
        this.roomTotal = 0
      }

      this.roomsLoading = true
      try {
        if (!this.cityStore.initialized) {
          await this.cityStore.initCity()
        }
        const params = { page: this.roomPage, page_size: this.roomPageSize }
        if (this.currentCityId) {
          params.city_id = this.currentCityId
        }
        const data = await getRooms(params)
        const items = data.items || []
        this.rooms = reset ? items : [...this.rooms, ...items]
        this.roomTotal = data.total || this.rooms.length
        this.lastCityId = this.currentCityId
      } catch {
        if (reset) {
          this.rooms = []
          this.roomTotal = 0
        }
      } finally {
        this.roomsLoading = false
      }
    },

    onPullDownRefresh() {
      this.refreshing = true
      this.loadRooms(true).finally(() => {
        this.refreshing = false
      })
    },

    onReachBottom() {
      if (!this.hasMoreRooms || this.roomsLoading) return
      this.roomPage += 1
      this.loadRooms()
    },

    onSelectFilter(filter) {
      this.selectedFilter = filter.value
    },

    onTapRoom(room) {
      uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
    },

    onTapCity() {
      uni.navigateTo({ url: '/pages/city-select/index' })
    },

    onTapSearch() {
      // Future: search page
    },

    onTapSort() {
      // Future: sorting selector
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
}

.hero-section {
  padding: 28rpx 28rpx 22rpx;
  background: #fdfdff;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.04);
}

.hero-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-kicker {
  display: block;
  font-size: 22rpx;
  color: $text-muted;
}

.hero-title {
  display: block;
  margin-top: 8rpx;
  font-size: 40rpx;
  line-height: 1.15;
  font-weight: 800;
  color: $text-primary;
}

.hero-city {
  display: flex;
  align-items: center;
  height: 56rpx;
  padding: 0 18rpx;
  border-radius: 28rpx;
  background: $primary-light;
  transition: transform 0.18s ease-out;
}

.hero-city:active {
  transform: scale(0.96);
}

.hero-city-icon {
  font-size: 24rpx;
  color: $primary;
}

.hero-city-text {
  margin-left: 6rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
}

.search-bar {
  display: flex;
  align-items: center;
  height: 72rpx;
  margin-top: 26rpx;
  padding: 0 24rpx;
  border-radius: 36rpx;
  background: $bg-color;
  border: 1rpx solid rgba(79, 110, 247, 0.06);
  transition: transform 0.18s ease-out, background-color 0.18s ease-out;
}

.search-bar:active {
  transform: scale(0.99);
  background: #eef2ff;
}

.search-icon {
  font-size: 28rpx;
  color: $text-muted;
  margin-right: 12rpx;
}

.search-placeholder {
  font-size: 26rpx;
  color: $text-muted;
}

.filter-scroll {
  white-space: nowrap;
  margin-top: 20rpx;
}

.filter-row {
  display: inline-flex;
  gap: 14rpx;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 56rpx;
  padding: 0 22rpx;
  border-radius: 28rpx;
  background: $bg-color;
  border: 1rpx solid transparent;
  transition: transform 0.18s ease-out, background-color 0.18s ease-out, border-color 0.18s ease-out;
}

.filter-pill:active {
  transform: scale(0.96);
}

.filter-pill.active {
  background: $primary;
  border-color: $primary;
  box-shadow: 0 8rpx 18rpx rgba(79, 110, 247, 0.16);
}

.filter-pill-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-secondary;
}

.filter-pill.active .filter-pill-text {
  color: #fdfdff;
}

.content {
  height: calc(100vh - 282rpx - 100rpx);
}

.list-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 30rpx 28rpx 20rpx;
}

.section-title {
  display: block;
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
}

.section-subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.sort-pill {
  display: flex;
  align-items: center;
  height: 52rpx;
  padding: 0 18rpx;
  border-radius: 26rpx;
  background: #fdfdff;
  box-shadow: $shadow-sm;
  transition: transform 0.18s ease-out;
}

.sort-pill:active {
  transform: scale(0.96);
}

.sort-text {
  font-size: 22rpx;
  color: $text-secondary;
}

.sort-icon {
  margin-left: 6rpx;
  font-size: 14rpx;
  color: $text-muted;
}

.room-list {
  padding: 0 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.room-card {
  display: flex;
  min-height: 244rpx;
  background: #fdfdff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 24rpx rgba(45, 52, 54, 0.06);
  border: 1rpx solid rgba(79, 110, 247, 0.05);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.room-card:active {
  transform: scale(0.985);
  box-shadow: 0 4rpx 14rpx rgba(45, 52, 54, 0.07);
}

.room-cover-wrap {
  position: relative;
  width: 236rpx;
  min-height: 244rpx;
  flex-shrink: 0;
  overflow: hidden;
  background: #eef1fb;
}

.room-cover {
  width: 100%;
  height: 244rpx;
}

.cover-status {
  position: absolute;
  top: 14rpx;
  left: 14rpx;
  padding: 7rpx 13rpx;
  border-radius: 18rpx;
  background: rgba(249, 250, 255, 0.94);
}

.cover-status.open .cover-status-text {
  color: $success;
}

.cover-status.closed .cover-status-text {
  color: $danger;
}

.cover-status-text {
  font-size: 20rpx;
  font-weight: 700;
}

.cover-chip {
  position: absolute;
  right: 14rpx;
  bottom: 14rpx;
  padding: 6rpx 12rpx;
  border-radius: 16rpx;
  background: rgba(45, 52, 54, 0.54);
}

.cover-chip-text {
  font-size: 19rpx;
  font-weight: 600;
  color: #fdfdff;
}

.room-info {
  flex: 1;
  min-width: 0;
  padding: 20rpx 22rpx 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.room-title-row {
  display: flex;
  align-items: center;
}

.room-name {
  flex: 1;
  min-width: 0;
  font-size: 29rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-location-row {
  display: flex;
  align-items: center;
  margin-top: 12rpx;
  min-width: 0;
}

.room-location-icon {
  flex-shrink: 0;
  margin-right: 6rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.room-address {
  flex: 1;
  min-width: 0;
  font-size: 23rpx;
  line-height: 1.35;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8rpx;
  margin: 16rpx 0;
}

.room-detail-item {
  min-width: 0;
  padding: 10rpx 8rpx;
  border-radius: 14rpx;
  background: #f6f8fe;
}

.detail-value {
  display: block;
  font-size: 22rpx;
  line-height: 1.1;
  font-weight: 800;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-label {
  display: block;
  margin-top: 5rpx;
  font-size: 18rpx;
  color: $text-muted;
}

.room-meta {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12rpx;
}

.room-tags {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
  flex-wrap: wrap;
}

.room-tag {
  padding: 6rpx 12rpx;
  border-radius: 18rpx;
  background: $bg-color;
  color: $text-secondary;
  font-size: 20rpx;
  line-height: 1;
}

.room-tag.accent {
  background: $primary-light;
  color: $primary;
}

.room-price {
  flex-shrink: 0;
  font-size: 34rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.room-price-symbol {
  font-size: 22rpx;
}

.room-price-unit {
  font-size: 20rpx;
  font-weight: 400;
}

.room-skeleton {
  padding: 0 28rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.room-card-skeleton {
  display: flex;
  background: #fdfdff;
  border-radius: 24rpx;
  overflow: hidden;
  padding: 16rpx;
  box-shadow: 0 8rpx 24rpx rgba(45, 52, 54, 0.05);
}

.skeleton-image {
  width: 200rpx;
  height: 160rpx;
  border-radius: 14rpx;
  background: linear-gradient(90deg, #f5f5f5 25%, #eee 50%, #f5f5f5 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-info {
  flex: 1;
  padding: 8rpx 16rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  justify-content: center;
}

.skeleton-line {
  height: 24rpx;
  border-radius: 6rpx;
  background: linear-gradient(90deg, #f5f5f5 25%, #eee 50%, #f5f5f5 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.long { width: 80%; }
.skeleton-line.medium { width: 60%; }
.skeleton-line.short { width: 40%; }

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 30rpx 28rpx 0;
  padding: 132rpx 0;
  border-radius: 24rpx;
  background: #fdfdff;
  box-shadow: $shadow-sm;
}

.empty-icon {
  font-size: 84rpx;
  color: #ccd2dc;
}

.empty-title {
  margin-top: 22rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
}

.empty-text {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-muted;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 34rpx 0;
}

.load-more-text {
  font-size: 24rpx;
  color: $text-muted;
}
</style>
